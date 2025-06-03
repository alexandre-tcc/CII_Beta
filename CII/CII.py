#!/usr/bin/env python
# coding: utf-8

# In[1]:


'''
Last Update: 01/02/2024 | Creation Date: 03/03/2023 | Python Notebook

Author: Alexandre Courtois

Purpose: CaaS insights and Intelligence tool

Version: Beta 1.0

neccessary files to run :
    *logo_dark.png
    *logo.png
    *TCC companies mapping 10142023.csv
    *TCC companies mapping 24052024.csv
    *TCC_focus_companies_data_financials_quarter.csv
    *TCC_focus_companies_data_financials_annual.csv

APIs necessary :
    /OPEN AI
        -Key: [Located in .env file.]
    /FMP
        -Key: [Located in .env file.]

To convert this file to a .py file, run the following command:
    python -m jupyter nbconvert --to script cii.ipynb

'''

import fmpsdk
import openai
import ast
import time

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

import certifi
import json

import plotly.graph_objects as go
import plotly.express as px


import pandas as pd
import numpy as np
import dash
import base64
from dash import dcc
from dash import html
from dash_table import DataTable
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import Input, Output, State

import hashlib  # To support SHA-256 hashing.

import os
from dotenv import load_dotenv

#bundle import
from CII import gpt
from CII import graph
from CII import da
from CII import fmp

load_dotenv()

def create_dataframe_from_list(supplier_list):
    try:
        df = pd.DataFrame(ast.literal_eval(supplier_list), columns=['Name Supplier', 'Ticker', 'Main Supply provided'])
        return df
    except:
        return ''



def credit_rating(ticker):
    df_ = pd.read_csv('CII/assets/TCC companies mapping 10142024.csv')
    if ticker in df_['ticker'].to_list():
        return df_[df_['ticker'] == ticker]['S&P rating'].iloc[0], df_[df_['ticker'] == ticker]['Moody rating'].iloc[0]
    else:
        return 'NA', 'NA'


def average_calc(ticker, field, period):  # input a value and return avg competitors - NOT fmpsdk lib
    competitors = fmp.get_competitors(ticker)

    df_rtr = pd.DataFrame()
    for comp in competitors:
        try:
            data_comp = fmp.data_merge(comp, period)
            data_comp = data_comp[['calendarYear', 'period', field]]
            df_rtr = pd.concat([df_rtr, data_comp], ignore_index=True)
        except:
            pass

    averaged_df = df_rtr.groupby('calendarYear')[field].mean().reset_index()

    return averaged_df


def cycles(data):
    data['date'] = pd.to_datetime(data['date'])  # Convert 'date' column to datetime format

    current_year = pd.Timestamp.now().year
    start_year = current_year - 3

    data_3y = data.copy()
    data_3y = data[data['date'] >= pd.Timestamp(start_year, 1, 1)]

    vals = []

    vals.append(data.iloc[0]['daysOfInventoryOutstanding'])
    vals.append(data_3y['daysOfInventoryOutstanding'].mean())
    vals.append(data['daysOfInventoryOutstanding'].mean())

    vals.append(data.iloc[0]['daysOfSalesOutstanding'])
    vals.append(data_3y['daysOfSalesOutstanding'].mean())
    vals.append(data['daysOfSalesOutstanding'].mean())

    vals.append(data.iloc[0]['daysOfPayablesOutstanding'])
    vals.append(data_3y['daysOfPayablesOutstanding'].mean())
    vals.append(data['daysOfPayablesOutstanding'].mean())

    vals.append(data.iloc[0]['cashConversionCycle'])
    vals.append(data_3y['cashConversionCycle'].mean())
    vals.append(data['cashConversionCycle'].mean())

    vals.append(data.iloc[0]['operatingCycle'])
    vals.append(data_3y['operatingCycle'].mean())
    vals.append(data['operatingCycle'].mean())

    keys = ['last_dio', 'avg_dio_3y', 'avg_dio',
            'last_dso', 'avg_dso_3y', 'avg_dso',
            'last_dpo', 'avg_dpo_3y', 'avg_dpo',
            'last_ccc', 'avg_ccc_3y', 'avg_ccc',
            'last_oc', 'avg_oc_3y', 'avg_oc']
    return dict(zip(keys, vals))


def inv_cash(data):
    data['date'] = pd.to_datetime(data['date'])  # Convert 'date' column to datetime format

    data['inv_total_assets'] = (data['inventory'] / data['totalAssets'])  # .apply(lambda x: '{:.2f}'.format(x))
    data['cash_total_assets'] = (
                data['cashAndCashEquivalents'] / data['totalAssets'])  # .apply(lambda x: '{:.2f}'.format(x))

    current_year = pd.Timestamp.now().year
    start_year = current_year - 3

    currency_ = data['reportedCurrency'].iloc[0]

    data_3y = data.copy()
    data_3y = data[data['date'] >= pd.Timestamp(start_year, 1, 1)]

    vals = []

    vals.append(format_currency(data.iloc[-1]['inventory'], currency_))
    vals.append(format_currency(data_3y['inventory'].mean(), currency_))
    vals.append(format_currency(data['inventory'].mean(), currency_))

    vals.append(format_currency(data.iloc[-1]['cashAndCashEquivalents'], currency_))
    vals.append(format_currency(data_3y['cashAndCashEquivalents'].mean(), currency_))
    vals.append(format_currency(data['cashAndCashEquivalents'].mean(), currency_))

    vals.append('{:.2f}'.format(data.iloc[-1]['inv_total_assets']))
    vals.append('{:.2f}'.format(data_3y['inv_total_assets'].mean()))
    vals.append('{:.2f}'.format(data['inv_total_assets'].mean()))

    vals.append('{:.2f}'.format(data.iloc[-1]['cash_total_assets']))
    vals.append('{:.2f}'.format(data_3y['cash_total_assets'].mean()))
    vals.append('{:.2f}'.format(data['cash_total_assets'].mean()))

    keys = ['last_inv', 'avg_inv_3y', 'avg_inv',
            'last_cash', 'avg_cash_3y', 'avg_cash',
            'last_inv_TA', 'avg_inv_TA_3y', 'avg_inv_TA',
            'last_cash_TA', 'avg_cash_TA_3y', 'avg_cash_TA']
    return dict(zip(keys, vals))


def get_table_competition(ticker_):
    tickers = fmp.return_tickers_industry(ticker_)
    print(tickers)
    print(ticker_)
    df_ = pd.read_csv('CII/assets/TCC companies mapping 10142024.csv')
    df_r = df_[df_['ticker'].isin(tickers)]
    return df_r[['name'] + ['ticker']]


def calculate_cash_flow_and_ratios(PRG, df_test):
    df_test_IS = pd.DataFrame(columns=[' ', 'Free Cash Flow', 'Funds from Operation', 'Inventory',
                                       'Payables', 'Net Working Capital', 'Cash Conversion Cycle',
                                       'Debt/Equity Ratio', 'Debt/EBITDA Ratio'])
    # First row - current values
    df_test_IS.loc[0] = ['Current',
                         df_test['freeCashFlow'].iloc[0],
                         df_test['netIncome'].iloc[0] + df_test['depreciationAndAmortization'].iloc[0] -
                         df_test['interestIncome'].iloc[0],
                         df_test['inventory'].iloc[0],
                         df_test['accountPayables'].iloc[0],
                         df_test['inventory'].iloc[0] - df_test['accountPayables'].iloc[0] +
                         df_test['netReceivables'].iloc[0],
                         df_test['daysOfInventoryOutstanding'].iloc[0] + df_test['daysOfSalesOutstanding'].iloc[0] -
                         df_test['daysOfPayablesOutstanding'].iloc[0],
                         df_test['totalDebt'].iloc[0] / df_test['totalEquity'].iloc[0],
                         df_test['totalDebt'].iloc[0] / df_test['ebitda'].iloc[0]]

    # Inventory calculation with PRG
    Inventory_1TCC = df_test['inventory'].iloc[0] - PRG * 1000000

    # Payables calculation with PRG
    Payables_1TCC = (df_test['accountPayables'].iloc[0]
                     + (PRG * 1000000 * df_test['daysOfPayablesOutstanding'].iloc[0] /
                        df_test['daysOfInventoryOutstanding'].iloc[0])
                     - (PRG * 1000000 * 30 / 180))

    # NWC (Net Working Capital) calculation with PRG
    NWC_1TCC = Inventory_1TCC - Payables_1TCC + df_test['netReceivables'].iloc[0]

    # FFO (Funds From Operations) calculation with PRG
    FFO_1TCC = df_test_IS['Funds from Operation'].iloc[0] + df_test_IS['Net Working Capital'].iloc[0] - NWC_1TCC

    # FCF (Free Cash Flow) calculation with PRG
    FCF_1TCC = df_test_IS['Free Cash Flow'].iloc[0] - df_test_IS['Funds from Operation'].iloc[0] + FFO_1TCC

    # CCC (Cash Conversion Cycle) calculation with PRG
    CCC_1TCC = -180 + df_test['daysOfSalesOutstanding'].iloc[0] + 30

    # EBITDA calculation with PRG
    EBITDA_1TCC = df_test['ebitda'].iloc[0] + (-PRG * 1000000 * 0.077)

    # Debt to Equity ratio with PRG
    DtoE_1TCC = (df_test['totalDebt'].iloc[0] - (df_test_IS['Net Working Capital'].iloc[0] - NWC_1TCC)) / \
                df_test['totalEquity'].iloc[0]

    # Debt to EBITDA ratio with PRG
    DtoEBITDA_1TCC = (df_test['totalDebt'].iloc[0] - (
                df_test_IS['Net Working Capital'].iloc[0] - NWC_1TCC)) / EBITDA_1TCC

    # Second row - with 1TCC program
    df_test_IS.loc[1] = ['With 1TCC Program',
                         FCF_1TCC,
                         FFO_1TCC,
                         Inventory_1TCC,
                         Payables_1TCC,
                         NWC_1TCC,
                         CCC_1TCC,
                         DtoE_1TCC,
                         DtoEBITDA_1TCC]

    return df_test_IS




# fonts
title_size = da.title_size
body_size = da.body_size

# styles
button_style = da.button_style

orange_tcc = da.orange_tcc
blue_tcc = da.blue_tcc

add_icon = html.I(className="fa-regular fa-floppy-disk me-2")
clear_icon = html.I(className="fa-solid fa-trash me-2")
change_icon = html.I(className="fa-solid fa-wrench me-2")
warning_icon = html.I(className="fa-solid fa-circle-exclamation me-2")
ok_icon = html.I(className="fa-solid fa-circle-check me-2")
edit_icon = html.I(className="fa-solid fa-floppy-disk me-2")
enter_icon = html.I(className="fa-solid fa-right-to-bracket me-2")
dl_icon = html.I(className="fa-solid fa-download me-2")
exit_icon = html.I(className="fa-solid fa-circle-arrow-left")

image_filename = 'CII/assets/logo.png'
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

# #### User Authentication

# In[14]:


# This dictionary stores username and hash pairs for user authentication.

username_to_hash = {
    "test": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
"1TCC_temporary_access": "eaac55ca6b8de61746c7ff44a129fcc07530c898e0fbbd20e1fe35f55adb982c",
}


# In[15]:


# To add a username and password pair to the above dictionary, add the username as a key.
# To get the hash, run the following line and let the output be the string value in the
# dictionary.

# hashlib.sha256("test".encode()).hexdigest()


# ## Function

# In[16]:


def ticker_test(ticker):
    test = True
    test_data = fmpsdk.company_profile(symbol=ticker, apikey='2723105eaade3c1ca8d66ca5c567b590')
    if test_data == []:
        test = False

    return test


def format_currency(value, currency):
    # Format the value with a thousands separator and currency symbol
    formatted_value = f"{value:,.0f}"

    # Append the currency code or symbol
    formatted_value += f" {currency}"

    return formatted_value


# ## App layout

# ### Login layout

# In[17]:


# Defines the username and password input region. This is written as a function so that if
# the user inputs a wrong combination, the region can be reset with the values they entered
# rather than clearing the input.

def input_region(username, password):
    return [

        # Username Entry

        dbc.Input(id="username", type="text", placeholder="Username", value=username, style={
            'color': 'black',
            'width': '300px',
            'display': 'inline-block',
            'border-color': 'rgb(79, 79, 79)'
        }, autofocus=True),

        html.Br(), html.Br(),

        # Password Entry

        dbc.Input(id="password", type="password", placeholder="Password", value=password, style={
            'color': 'black',
            'width': '300px',
            'display': 'inline-block',
            'border-color': 'rgb(79, 79, 79)'
        })
    ]


# Defines the HTML layout of the login page. The variable is named sign_in_layout to
# avoid conflicts with other variable names.

sign_in_layout = html.Div([

    # Page Banner (same as from other layouts)

    html.Div(children=[
        html.Div(children=[
            dbc.Row(
                html.H3('CaaS Insights & Intelligence', style={'color': 'white', 'font-family': 'sans-serif',
                                                               'fontSize': 45, 'verticalAlign': 'top',
                                                               'display': 'inline-block',
                                                               'margin': '10px 10px 10px 10px', 'width': '90',
                                                               'align-items': 'center', 'justify-content': 'left'}),
            ),

        ], style={'verticalAlign': 'top',
                  'margin': '10px', 'width': '5%',
                  'align-items': 'center', 'flex': 1,
                  'display': 'flex', 'justify-content': 'left'}),

        html.Div(children=[
            html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode())),
        ], style={'verticalAlign': 'top',
                  'margin': '10px', 'width': '5%',
                  'align-items': 'center', 'flex': 1,
                  'display': 'flex', 'justify-content': 'right'}),

    ], style={'background-color': 'rgb(52, 56, 52)', 'display': 'flex',
              'flex': 'row', 'horizontalAlign': 'center', 'height': '120px'}, ),

    # Login Page Components

    html.Div(children=[

        html.H2(children="Login"),

        html.Br(), html.Br(),

        html.Div(id="input-region", children=input_region("", "")),

        html.Br(), html.Br(),

        # Submit Button

        dbc.Button(id="sign-in-button", children="Sign In", n_clicks=0, style=button_style),

        # Dialog Box in case sign in fails.

        html.Div(id="sign-in-fail")

    ],

        style={'width': '100%', "height": "100vh", 'padding': '100px',
               'background-color': 'white', 'color': 'rgb(79, 79, 79)',
               "justify-content": "center",
               "align-items": "center",
               "text-align": "center"})
])

# #### 403 Page Layout

# In[18]:


# Defines the HTML layout of the 403 Forbidden Access page.

page_403_layout = html.Div([

    # Page Banner (same as from other layouts)

    html.Div(children=[
        html.Div(children=[
            dbc.Row(
                html.H3('CaaS Insights & Intelligence', style={'color': 'white', 'font-family': 'sans-serif',
                                                               'fontSize': 45, 'verticalAlign': 'top',
                                                               'display': 'inline-block',
                                                               'margin': '10px 10px 10px 10px', 'width': '90',
                                                               'align-items': 'center', 'justify-content': 'left'}),
            ),

        ], style={'verticalAlign': 'top',
                  'margin': '10px', 'width': '5%',
                  'align-items': 'center', 'flex': 1,
                  'display': 'flex', 'justify-content': 'left'}),

        html.Div(children=[
            html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode())),
        ], style={'verticalAlign': 'top',
                  'margin': '10px', 'width': '5%',
                  'align-items': 'center', 'flex': 1,
                  'display': 'flex', 'justify-content': 'right'}),

    ], style={'background-color': 'rgb(52, 56, 52)', 'display': 'flex',
              'flex': 'row', 'horizontalAlign': 'center', 'height': '120px'}, ),

    # 403 Page Components

    html.Div(children=[

        html.H1(children="403 FORBIDDEN ACCESS"),

        html.Br(), html.Br(),

        html.H1(children=[
            "Please sign in ",
            html.A(children="here", href="/sign-in"),
            "."
        ])

    ],

        style={'width': '100%', "height": "100vh", 'padding': '100px',
               'background-color': 'white', 'color': 'rgb(79, 79, 79)',
               "justify-content": "center",
               "align-items": "center",
               "text-align": "center"}),

    html.Div(id="input-region")  # Empty region necessary so that a non-existent input
    # error is not called.
])

# ### Dashboard layout

# In[19]:


dashboard_layout = html.Div([

    html.Div(children=[
        html.Div(children=[
            dbc.Row(
                html.H3('CaaS Insights & Intelligence', style={'color': 'white', 'font-family': 'sans-serif',
                                                               'fontSize': 45, 'verticalAlign': 'top',
                                                               'display': 'inline-block',
                                                               'margin': '10px 10px 10px 10px', 'width': '90',
                                                               'align-items': 'center', 'justify-content': 'left'}),
            ),

        ], style={'verticalAlign': 'top',
                  'margin': '10px', 'width': '5%',
                  'align-items': 'center', 'flex': 1,
                  'display': 'flex', 'justify-content': 'left'}),

        html.Div(children=[
            html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode())),
        ], style={'verticalAlign': 'top',
                  'margin': '10px', 'width': '5%',
                  'align-items': 'center', 'flex': 1,
                  'display': 'flex', 'justify-content': 'right'}),

    ], style={'background-color': 'rgb(52, 56, 52)', 'display': 'flex',
              'flex': 'row', 'horizontalAlign': 'center', 'height': '120px'}, ),

    html.Div(children=[

        html.Div(children=[
            html.A([exit_icon, " Analyse another company"], href="/welcome", style={'margin': '20px', 'font-size': 20}),
        ]),

        # -----------------------------------------  COMPANY GENERALE -----------------------------------------------
        html.Div(children=[

            html.Div(children=[

                dcc.Loading(
                    id="ticker-analysis",
                    type="dot",
                    className="loading-component",
                    style={'color': 'orange'}  # ,'height':'200px'}
                ),

                html.Br(),

            ], style={

                "display": "flex",
                "flex-direction": "column",
            })

        ], style={'border': 'px solid orange',
                  'background-color': 'white',
                  'box-shadow': '5px 5px 15px 8px lightgrey',
                  'border-radius': 20,
                  'margin': '30px',
                  'padding': '100px',
                  'flex': 'row',
                  'horizontalAlign': 'center',
                  "align-items": "center"}, ),

        # -----------------------------------------  Cycles -----------------------------------------------

        html.Div(children=[

            html.Div(children=[

                html.Div(
                    id='cycles_display'),

                html.Br(),

            ], style={

                "display": "flex",
                "flex-direction": "column",
                "justify-content": "left",
                "align-items": "left",
            })

        ], style={'border': 'px solid orange',
                  'background-color': 'white',
                  'box-shadow': '5px 5px 15px 8px lightgrey',
                  'border-radius': 20,
                  'margin': '30px',
                  'padding': '100px',
                  'flex': 'row',
                  'horizontalAlign': 'center',
                  "align-items": "center"}, ),

        # -----------------------------------------  inventory and cash -----------------------------------------------

        html.Div(children=[

            html.Div(children=[

                html.Div(id='inv_cash_display'),

                html.Br(),

            ], style={

                "display": "flex",
                "flex-direction": "column",
                "justify-content": "left",
                "align-items": "left",
            })

        ], style={'border': 'px solid orange',
                  'background-color': 'white',
                  'box-shadow': '5px 5px 15px 8px lightgrey',
                  'border-radius': 20,
                  'margin': '30px',
                  'padding': '100px',
                  'flex': 'row',
                  'horizontalAlign': 'center',
                  "align-items": "center"}, ),

        # ----------------------------------------- WC elasticity -----------------------------------------------

        html.Div(children=[

            html.Div(children=[

                html.Div(
                    id='WC_elasticity_display'
                ),

                html.Br(),

            ], style={

                "display": "flex",
                "flex-direction": "column",
                "justify-content": "left",
                "align-items": "left",
            })

        ], style={'border': 'px solid orange',
                  'background-color': 'white',
                  'box-shadow': '5px 5px 15px 8px lightgrey',
                  'border-radius': 20,
                  'margin': '30px',
                  'padding': '100px',
                  'flex': 'row',
                  'horizontalAlign': 'center',
                  "align-items": "center"}, ),

        # ---------------------------------------------------------------------------------------
        # -----------------------------------------  Summary -----------------------------------------------

        html.Div(children=[

            html.Div(children=[

                html.Div(
                    id='summary_display'),

                html.Br(),

            ], style={

                "display": "flex",
                "flex-direction": "column",
                "justify-content": "left",
                "align-items": "left",
            })

        ], style={'border': 'px solid orange',
                  'background-color': 'white',
                  'box-shadow': '5px 5px 15px 8px lightgrey',
                  'border-radius': 20,
                  'margin': '30px',
                  'padding': '100px',
                  'flex': 'row',
                  'horizontalAlign': 'center',
                  "align-items": "center"}, ),

        # ----------------------------------------- QUADRANTS -----------------------------------------------

        html.Div(children=[

            html.Div(children=[

                html.Div(id='quadrants_display'),

                html.Br(),

            ], style={

                "display": "flex",
                "flex-direction": "column",
                "justify-content": "left",
                "align-items": "left",
            })

        ], style={'border': 'px solid orange',
                  'background-color': 'white',
                  'box-shadow': '5px 5px 15px 8px lightgrey',
                  'border-radius': 20,
                  'margin': '30px',
                  'padding': '100px',
                  'flex': 'row',
                  'horizontalAlign': 'center',
                  "align-items": "center"}, ),

        # ---------------------------------------------------------------------------------------

        # ----------------------------------------- Transcript -----------------------------------------------

        html.Div(children=[

            html.Div(children=[

                html.Div(id='transcript'),

                html.Br(),

            ], style={

                "display": "flex",
                "flex-direction": "column",
                "justify-content": "left",
                "align-items": "left",
            })

        ], style={'border': 'px solid orange',
                  'background-color': 'white',
                  'box-shadow': '5px 5px 15px 8px lightgrey',
                  'border-radius': 20,
                  'margin': '30px',
                  'padding': '100px',
                  'flex': 'row',
                  'horizontalAlign': 'center',
                  "align-items": "center"}, ),

        # ---------------------------------------------------------------------------------------

        # Closing
    ],
        style={'width': '100%', "height": "100vh", 'padding': '10px',
               'background-color': 'white', 'color': 'rgb(79, 79, 79)',
               "justify-content": "center",
               "align-items": "center", }),

    html.Div(id="input-region")  # Empty region necessary so that a non-existent input
    # error is not called.
])

# In[20]:


login_layout = html.Div([

    html.Div(children=[
        html.Div(children=[
            dbc.Row(
                html.H3('CaaS Insights & Intelligence', style={'color': 'white', 'font-family': 'sans-serif',
                                                               'fontSize': 45, 'verticalAlign': 'top',
                                                               'display': 'inline-block',
                                                               'margin': '10px 10px 10px 10px', 'width': '90',
                                                               'align-items': 'center', 'justify-content': 'left'}),
            ),

        ], style={'verticalAlign': 'top',
                  'margin': '10px', 'width': '5%',
                  'align-items': 'center', 'flex': 1,
                  'display': 'flex', 'justify-content': 'left'}),

        html.Div(children=[
            html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode())),
        ], style={'verticalAlign': 'top',
                  'margin': '10px', 'width': '5%',
                  'align-items': 'center', 'flex': 1,
                  'display': 'flex', 'justify-content': 'right'}),

    ], style={'background-color': 'rgb(52, 56, 52)', 'display': 'flex',
              'flex': 'row', 'horizontalAlign': 'center', 'height': '120px'}, ),

    html.Div(children=[

        html.Div(children=[

            html.Div(children=[

                html.H1(children='Welcome to CII engine'),
                html.Br(),
                html.Div(children=[
                    dbc.Input(id='ticker-in', placeholder='Ticker', type='text',
                              style={"text-transform": "uppercase",
                                     'opacity': '60%',
                                     "text-align": "center",
                                     'fontSize': 45}),
                ]),

                html.Br(),
                dbc.Button('Generate CII report', id='login-button', n_clicks=0, style=button_style),
                html.Div(id='login-status'),
                # html.Div(id='login-display'),

                html.Br(),

                html.Div(children=["Can't access ticker? ",
                                   html.A("Check the database", href="https://1tcc.com/tcc-contact/",
                                          target="_blank")]),

            ], style={

                "display": "flex",
                "flex-direction": "column",
                "justify-content": "center",
                "align-items": "center",
            })

        ], style={'border': 'px solid orange',
                  'background-color': 'white',
                  'box-shadow': '5px 5px 15px 8px lightgrey',
                  'border-radius': 20,
                  'margin': '30px',
                  'padding': '100px',
                  'flex': 'row',
                  'horizontalAlign': 'center',
                  "align-items": "center"}, ),

        # Closing
    ],
        style={'width': '100%', "height": "100vh", 'padding': '100px',
               'background-color': 'white', 'color': 'rgb(79, 79, 79)',
               "justify-content": "center",
               "align-items": "center", }),

    html.Div(id="input-region")  # Empty region necessary so that a non-existent input
    # error is not called.
])

# ### Call back functions
#
# #### Sign In Functions

# In[21]:


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY, dbc.icons.FONT_AWESOME, dbc.icons.BOOTSTRAP])


# When the user signs in, this function checks that the username / password combination is
# valid and redirects to the correct page.

@app.callback(
    Output("sign-in-fail", "children"),
    Output("authentication-data", "data"),
    Output("url", "pathname", allow_duplicate=True),
    Input("sign-in-button", "n_clicks"),
    State("username", "value"),
    State("password", "value"),
    prevent_initial_call=True
)
def sign_in(n_clicks, username, password):
    if n_clicks == 0:
        return "", {
            "is-authenticated": False
        }, "/"

    # Temporary

    if username not in username_to_hash:
        return dcc.ConfirmDialog(
            id="sign-in-error",
            message="The username is not valid.",
            displayed=True
        ), {
                   "is-authenticated": False
               }, "/"

    hash = hashlib.sha256(password.encode()).hexdigest()

    if hash != username_to_hash[username]:

        return dcc.ConfirmDialog(
            id="sign-in-error",
            message="The password is incorrect.",
            displayed=True
        ), {
                   "is-authenticated": False
               }, "/"

    else:

        return "", {
            "is-authenticated": True
        }, "/welcome"


# #### Dashboard / Login Functions

# In[22]:


@app.callback(
    Output("inv-cash_graph", "children"),
    Input("inv-cash_graph_period", "value"),
    Input("data_annual", "data"),
    Input("data_quarter", "data"),
)
def inv_cash_graph(period, data_annual, data_quarter):
    if period == 'annual':
        df_ = pd.DataFrame(data_annual)
    else:
        df_ = pd.DataFrame(data_quarter)

    return dcc.Graph(
        id='rank-graph',
        figure=graph.line_graph(['inventory', 'cashAndCashEquivalents'], df_)
    ),


@app.callback(
    Output("inv_graph", "children"),
    Input("inv-cash_graph_period", "value"),
    Input("ticker-store", "data"),
    Input("data_annual", "data"),
    Input("data_quarter", "data"),
)
def Inv_graph(period, ticker, data_annual, data_quarter):
    data_annual_ = pd.DataFrame(data_annual)
    data_quarter_ = pd.DataFrame(data_quarter)

    return dcc.Graph(
        id='cash_graph_',
        figure=graph.avg_industry('inventory', ticker, period, data_annual_, data_quarter_, 'Inventory'),
    ),


@app.callback(
    Output("cash_graph", "children"),
    Input("inv-cash_graph_period", "value"),
    Input("ticker-store", "data"),
    Input("data_annual", "data"),
    Input("data_quarter", "data"),
)
def Cash_graph(period, ticker, data_annual, data_quarter):
    data_annual_ = pd.DataFrame(data_annual)
    data_quarter_ = pd.DataFrame(data_quarter)

    return dcc.Graph(
        id='cash_graph_',
        figure=graph.avg_industry('cashAndCashEquivalents', ticker, period, data_annual_, data_quarter_, 'Cash')
    ),


@app.callback(
    Output("stock_graph", "children"),
    Input("ticker-store", "data"),
)
def stock_graph(ticker):
    return html.Div(children=[
        dcc.Graph(
            id='stock-graph',
            figure=graph.stock_price(ticker),
            # style={'width': '100%'}
        ), ])


@app.callback(
    Output("transcript", "children"),
    Input("ticker-store", "data"),
)
def stock_graph(ticker):
    data_ = fmp.get_latest_earnings_transcript(ticker)
    date = data_[0]
    text_ = data_[1]
    return html.Div(
        children=[
            html.H1('Latest earning transcript'),
            html.Br(),

            html.H3('date: ' + str(date)),
            html.Br(),
            html.P(str(text_)),

        ],
        className="row",
        style={"display": "flex"}
    ),


@app.callback(
    Output("WC_elasticity_graph_display", "children"),
    Output("fcf_ffo_graph", "children"),
    Input("data_annual", "data"),
    Input("prg_amount", "value"),
)
def stock_graph(data, prg_amount):
    df_ = pd.DataFrame(data)
    return html.Div(children=[
        dcc.Graph(
            id='stock-graph',
            figure=graph.WC_elasticity_graph(df_, prg_amount),
        ), ]), html.Div(children=[
        dcc.Graph(
            id='stock-graph',
            figure=graph.fcf_ffo_graph(df_, prg_amount),
        ), ])


@app.callback(
    Output("cycles_graph", "children"),
    Input("data_annual", "data"),
)
def cycles_graph(data_):
    return html.Div(children=[
        dcc.Graph(
            id='stock-graph',
            figure=graph.line_graph_cycles(['daysOfInventoryOutstanding',
                                      'daysOfPayablesOutstanding',
                                      'daysOfSalesOutstanding',
                                      'cashConversionCycle'], data_),
            style={'width': '100%'},
            className='graph-container'
        ), ])


# Define the callback function for the submit button
@app.callback(
    Output("login-status", "children"),
    Output("url", "pathname"),
    Output("url", "search"),
    Output("ticker-in", "value"),
    Input("login-button", "n_clicks"),
    # Input("url", "pathname"),
    State("ticker-in", "value"),
)
def login(n_clicks, ticker):
    if n_clicks > 0:
        ticker_test_result = ticker_test(ticker)

        if ticker_test_result:
            # If the login is successful, redirect the user to the dashboard page
            return "", "/Dashboard", f"?ticker={ticker}", ticker
        else:
            # If the login fails, display a popup window
            return dcc.ConfirmDialog(
                id="ticker-error",
                message="Can't run analysis on this ticker",
                displayed=True,
            ), "/welcome", "", ""

    return "", "/welcome", "", ticker  # Return the current ticker value


# This callback function redirects the user to the correct page depending on the url. If
# the page needs the user to be authenticated, this function redirects the user to the 403
# page. If the user is being sent back to the sign-in page after incorrectly signing in,
# this function also passes in the prior input so that the user doesn't have to retype it.

@app.callback(
    Output("page-content", "children"),
    Output("input-region", "children"),
    Input("url", "pathname"),
    State("url", "search"),
    State("authentication-data", "data"),
    State("input-region", "children"),
)
def display_page(pathname, search, auth_data, input):
    if pathname == "/welcome":
        if not auth_data["is-authenticated"]:
            return page_403_layout, ""
        return login_layout, ""

    elif pathname == "/sign-in":
        username = ""
        password = ""
        if (input != None):
            username = input[0]['props']['value']
            password = input[3]['props']['value']
        return sign_in_layout, input_region(username, password)

    elif pathname == "/Dashboard":
        if not auth_data["is-authenticated"]:
            return page_403_layout, ""
        # Get the ticker value from the URL search parameter
        ticker = search.split("=")[1] if search else ""
        return html.Div([dashboard_layout, dcc.Store(id="ticker-store", data=ticker)]), ""

    elif pathname == "/":
        if auth_data["is-authenticated"]:
            return login_layout, ""
        username = ""
        password = ""
        if (input != None):
            username = input[0]['props']['value']
            password = input[3]['props']['value']
        return sign_in_layout, input_region(username, password)

    else:
        return "404 Page not found", ""


@app.callback(Output("ticker-analysis", "children"), Input("ticker-store", "data"))
def general_section(ticker):
    df_quarter = fmp.data_merge(ticker, 'quarter')
    df_annual = fmp.data_merge(ticker, 'annual')
    company_info = fmpsdk.company_profile(symbol=ticker, apikey='2723105eaade3c1ca8d66ca5c567b590')

    org_chart_ = fmp.get_org_chart(ticker)

    currency = company_info[0]['currency']

    if df_quarter.shape[0] != 0:
        most_recent_date = df_quarter['fillingDate'].max()
        most_recent_inventory = df_quarter[df_quarter['fillingDate'] == most_recent_date]['inventory']
    else:
        most_recent_date = df_annual['fillingDate'].max()
        most_recent_inventory = df_annual[df_annual['fillingDate'] == most_recent_date]['inventory']

    CR_ = credit_rating(ticker)

    # scores analysis >>>>>>>>>>>>>>>>>>>>>>>>>>>>
    scores_ = fmp.get_scores_url(ticker)

    piotroski_ = fmp.get_scores_url(ticker)[1]
    altman_ = fmp.get_scores_url(ticker)[0]

    if piotroski_ >= 8:
        piotroski_analysis = f"A score of {piotroski_} is considered to be STRONG"
    elif piotroski_ <= 2:
        piotroski_analysis = f"A score of {piotroski_} is considered to be WEAK"
    else:
        piotroski_analysis = f"A score of {piotroski_} is considered to be AVERAGE"

    if altman_ >= 3:
        altman_analysis = f"A score of {altman_} is considered to be STRONG. scores above 3 are not likely to go bankrupt. Investors may consider purchasing a stock if its Altman Z-Score value is closer to 3 and selling, or shorting, a stock if the value is closer to 1.8"
    elif altman_ <= 0:
        altman_analysis = f"A score of {altman_} is considered to be WEAK. A score below 0 signals the company is likely headed for bankruptcy"
    else:
        altman_analysis = f"A score of {altman_} is considered to be AVERAGE"

    if CR_[0] != 'NA':
        general_info = html.Div(
            children=[

                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.H3('Sector', style={'margin': '40px 100px 20px 0px'}),
                                html.H4(company_info[0]['sector'], style={'font-size': body_size,
                                                                          'margin': '20px 100px 20px 0px'}),
                            ]),
                        html.Div(
                            children=[
                                html.H3('Industry', style={'margin': '40px 100px 20px 0px'}),
                                html.H4(company_info[0]['industry'], style={'font-size': body_size,
                                                                            'margin': '20px 100px 20px 0px'}),
                            ]),
                        html.Div(
                            children=[
                                html.H3('Exchange', style={'margin': '40px 100px 20px 0px'}),
                                html.H4(company_info[0]['exchange'], style={'font-size': body_size,
                                                                            'margin': '20px 100px 20px 0px'}),
                            ]),
                        html.Div(
                            children=[
                                html.H3('Country', style={'margin': '40px 100px 20px 0px'}),
                                html.H4(company_info[0]['country'], style={'font-size': body_size,
                                                                           'margin': '20px 100px 20px 0px'}),
                            ]),
                        html.Div(
                            children=[
                                html.H3('Credit Rating (S&P)', style={'margin': '40px 100px 20px 0px'}),
                                html.H4(CR_[0], style={'font-size': body_size,
                                                       'margin': '20px 100px 20px 0px'}),
                            ]),
                        html.Div(
                            children=[
                                html.H3('Credit Rating (Moody)', style={'margin': '40px 100px 20px 0px'}),
                                html.H4(CR_[1], style={'font-size': body_size,
                                                       'margin': '20px 100px 20px 0px'}),
                            ]),

                    ],
                    style={'display': 'flex', 'width': '100%'}
                )

            ],
            className="row",
            style={"display": "flex"}
        )
    else:
        general_info = html.Div(
            children=[

                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.H3('Sector', style={'margin': '40px 100px 20px 0px'}),
                                html.H4(company_info[0]['sector'], style={'font-size': body_size,
                                                                          'margin': '20px 100px 20px 0px'}),
                            ]),
                        html.Div(
                            children=[
                                html.H3('Industry', style={'margin': '40px 100px 20px 0px'}),
                                html.H4(company_info[0]['industry'], style={'font-size': body_size,
                                                                            'margin': '20px 100px 20px 0px'}),
                            ]),
                        html.Div(
                            children=[
                                html.H3('Exchange', style={'margin': '40px 100px 20px 0px'}),
                                html.H4(company_info[0]['exchange'], style={'font-size': body_size,
                                                                            'margin': '20px 100px 20px 0px'}),
                            ]),
                        html.Div(
                            children=[
                                html.H3('Country', style={'margin': '40px 100px 20px 0px'}),
                                html.H4(company_info[0]['country'], style={'font-size': body_size,
                                                                           'margin': '20px 100px 20px 0px'}),
                            ]),

                    ],
                    style={'display': 'flex', 'width': '100%'}
                )

            ],
            className="row",
            style={"display": "flex"}
        )

    return html.Div(
        children=[
                     html.H1(company_info[0]['companyName']),

                     html.H3('Company description', style={'margin': '40px 0px 20px 0px'}),
                     html.H4(company_info[0]['description'], style={'font-size': body_size,
                                                                    'margin': '0px 40px 0px 0px'}),
                     general_info,
                     html.Div(
                         children=[

                             html.Div(
                                 children=[
                                     html.Div(
                                         children=[

                                             html.Div(
                                                 children=[
                                                     html.H3('Capitalization', style={'margin': '40px 100px 20px 0px'}),
                                                     html.H4(format_currency(company_info[0]['mktCap'], currency),
                                                             style={'font-size': body_size,
                                                                    'margin': '20px 100px 20px 0px'}),
                                                 ]),

                                             html.H3('Stock Price', style={'margin': '40px 0px -20px 0px',
                                                                           'position': 'absolute',
                                                                           'z-index': '2'}),
                                             html.Div(id='stock_graph'),

                                         ]), html.Br(),
                                     html.Div(
                                         children=[
                                             html.H3('Key Executives', style={'margin': '40px 0px 20px 0px'}),
                                             DataTable(
                                                 id='datatable-org',
                                                 columns=[
                                                     {"name": i, "id": i, "selectable": True} for i in
                                                     org_chart_.columns
                                                 ],
                                                 data=org_chart_.to_dict('records'),
                                                 # editable=True,
                                                 style_header={'padding': '10px', 'font-family': 'sans-serif',
                                                               'fontSize': title_size},
                                                 style_cell={'padding': '10px', 'font-family': 'sans-serif',
                                                             'fontSize': body_size},
                                                 style_data={
                                                     "whiteSpace": "normal",
                                                     "height": "auto"
                                                 },
                                                 sort_action="native",
                                                 sort_mode="multi",
                                                 # style_table={'overflowX': 'scroll','overflowY': 'scroll'},
                                                 # row_selectable="single",
                                                 page_action="native",
                                                 page_current=0,
                                                 page_size=50,
                                             ),
                                         ]),

                                 ],
                                 # style={'display': 'flex'}
                             )

                         ],
                         # className="row",
                         # style={"display": "flex"}
                     ), html.Br(), html.Br(),

                     # +++++++ CARD
                     html.Div(
                         children=[
                             html.H3('Financial Health Assessment and Impact'),

                             html.Div(children=[
                                 html.Div(
                                     children=[dbc.Row(
                                         [
                                             dbc.Col(
                                                 dbc.Card(
                                                     [
                                                         dbc.CardHeader("Current Piotroski Score",
                                                                        id="hover-target-piotroski"),
                                                         dbc.CardBody(
                                                             [

                                                                 dbc.Popover(
                                                                     [
                                                                         dbc.PopoverHeader("Piotroski Score"),
                                                                         dbc.PopoverBody(
                                                                             "The Piotroski score is a discrete score between zero and nine that reflects nine criteria used to determine the strength of a firm's financial position. The Piotroski score is used to determine the best value stocks, with nine being the best and zero being the worst."),
                                                                     ],

                                                                     target="hover-target-piotroski",
                                                                     body=True,
                                                                     trigger="hover",
                                                                 ),
                                                                 html.H1(str(piotroski_), className="card-title"),

                                                                 dcc.Markdown(
                                                                     piotroski_analysis,
                                                                     className="card-text",
                                                                 ),
                                                                 # html.H4('How 1TCC impact the Piotroski score', className="card-title"),
                                                             ]
                                                         ),
                                                     ]

                                                     , color='info', inverse=True)
                                             ),

                                         ],
                                         className="mb-4",
                                     ), ], style={'margin': '30px 30px 30px 0px', 'width': '50%'}),

                                 html.Div(
                                     children=[dbc.Row(
                                         [
                                             dbc.Col(
                                                 dbc.Card(
                                                     [
                                                         dbc.CardHeader("Current Altman Z-Score",
                                                                        id="hover-target-altman"),
                                                         dbc.CardBody(
                                                             [
                                                                 dbc.Popover(
                                                                     [
                                                                         dbc.PopoverHeader("Altman Z-score"),
                                                                         dbc.PopoverBody(
                                                                             "The Altman Z-score, a variation of the traditional z-score in statistics, is based on five financial ratios that can be calculated from data found on a company's annual 10-K report. It uses profitability, leverage, liquidity, solvency, and activity to predict whether a company has a high probability of becoming insolvent."),
                                                                     ],

                                                                     target="hover-target-altman",
                                                                     body=True,
                                                                     trigger="hover",
                                                                 ),
                                                                 html.H1(str('{:.2f}'.format(altman_)),
                                                                         className="card-title"),
                                                                 dcc.Markdown(
                                                                     altman_analysis,
                                                                     className="card-text",
                                                                 ),
                                                                 # html.H4('How 1TCC impact the Altman-Z score', className="card-title"),
                                                             ]
                                                         ),
                                                     ]

                                                     , color='info', inverse=True)
                                             ),

                                         ],
                                         className="mb-4",
                                     ), ], style={'margin': '30px 0px 30px 30px', 'width': '50%'}),
                             ], style={'display': 'flex', 'align-items': 'to2'}
                             ),

                         ],
                         className="row",
                         style={"display": "flex"}
                     ),
                     # +++++++ CARD

                 ] + [  # STORE Relevant data *******************************************************
                     dcc.Store(id="data_annual", data=df_annual.to_dict('records')),
                     dcc.Store(id="data_quarter", data=df_quarter.to_dict('records'))
                 ]
    )


@app.callback(Output("cycles_gpt", "children"),
              Input("ticker-store", "data"),
              Input("data_annual", "data"),
              Input("data_quarter", "data"))
def cycles_section(ticker, data_annual, data_quarter):
    if pd.DataFrame(data_quarter).shape[0] < 1:
        data_ = pd.DataFrame(data_annual)
    else:
        data_ = pd.DataFrame(data_quarter)

    company_info = fmpsdk.company_profile(symbol=ticker, apikey='2723105eaade3c1ca8d66ca5c567b590')
    name_ = company_info[0]['companyName']
    cycles_ = cycles(data_)
    tcc_nlp_cycles_ = gpt.gpt_cycles(cycles_, name_)
    # tcc_nlp_cycles_='Test gpt here'
    return dcc.Markdown(
        tcc_nlp_cycles_,
        className="card-text",
    ),


@app.callback(Output("summary_table", "children"),
              Input("ticker-store", "data"),
              Input("data_annual", "data"),
              Input("data_quarter", "data"),
              Input("prg_amount_summary", "value"))
def summary_table_return(ticker, data_annual, data_quarter, PRG):
    if pd.DataFrame(data_quarter).shape[0] < 1:
        data_ = pd.DataFrame(data_annual)
    else:
        data_ = pd.DataFrame(data_quarter)

    PRG = int(PRG)
    summary_ = calculate_cash_flow_and_ratios(PRG, data_)

    return html.Div(
        children=[

            html.Div(
                children=[
                    html.H3('----------------------', style={'margin': '40px 100px 20px 0px', 'color': 'white'}),
                    html.H4(f"Current", style={'font-size': body_size,
                                               'margin': '20px 100px 20px 0px'}),
                    html.H4(f"With 1TCC Program", style={'font-size': body_size,
                                                         'margin': '20px 100px 20px 0px',
                                                         'width': '300px'}),
                ], style={
                    "width": "300px"
                }),
            html.Div(
                children=[
                    html.H3('FCF $M', style={'margin': '40px 100px 20px 0px'}),
                    html.H4(f"{summary_['Free Cash Flow'].iloc[0] / 10 ** 6}", style={'font-size': body_size,
                                                                                      'margin': '20px 100px 20px 0px'}),
                    html.H4(f"{summary_['Free Cash Flow'].iloc[1] / 10 ** 6:.0f}", style={'font-size': body_size,
                                                                                          'margin': '20px 100px 20px 0px'}),
                ]),
            html.Div(
                children=[
                    html.H3('FFO $M', style={'margin': '40px 100px 20px 0px'}),
                    html.H4(f"{summary_['Funds from Operation'].iloc[0] / 10 ** 6}", style={'font-size': body_size,
                                                                                            'margin': '20px 100px 20px 0px'}),
                    html.H4(f"{summary_['Funds from Operation'].iloc[1] / 10 ** 6:.0f}", style={'font-size': body_size,
                                                                                                'margin': '20px 100px 20px 0px'}),
                ]),
            html.Div(
                children=[
                    html.H3('Inventory $M', style={'margin': '40px 100px 20px 0px'}),
                    html.H4(f"{summary_['Inventory'].iloc[0] / 10 ** 6}", style={'font-size': body_size,
                                                                                 'margin': '20px 100px 20px 0px'}),
                    html.H4(f"{summary_['Inventory'].iloc[1] / 10 ** 6:.0f}", style={'font-size': body_size,
                                                                                     'margin': '20px 100px 20px 0px'}),
                ]),
            html.Div(
                children=[
                    html.H3('Payables $M', style={'margin': '40px 100px 20px 0px'}),
                    html.H4(f"{summary_['Payables'].iloc[0] / 10 ** 6}", style={'font-size': body_size,
                                                                                'margin': '20px 100px 20px 0px'}),
                    html.H4(f"{summary_['Payables'].iloc[1] / 10 ** 6:.0f}", style={'font-size': body_size,
                                                                                    'margin': '20px 100px 20px 0px'}),
                ]),

            html.Div(
                children=[
                    html.H3('NWC $M', style={'margin': '40px 100px 20px 0px'}),
                    html.H4(f"{summary_['Net Working Capital'].iloc[0] / 10 ** 6}", style={'font-size': body_size,
                                                                                           'margin': '20px 100px 20px 0px'}),
                    html.H4(f"{summary_['Net Working Capital'].iloc[1] / 10 ** 6:.0f}", style={'font-size': body_size,
                                                                                               'margin': '20px 100px 20px 0px'}),
                ]),
            html.Div(
                children=[
                    html.H3('CCC (d)', style={'margin': '40px 100px 20px 0px'}),
                    html.H4(f"{summary_['Cash Conversion Cycle'].iloc[0]:.2f}", style={'font-size': body_size,
                                                                                       'margin': '20px 100px 20px 0px'}),
                    html.H4(f"{summary_['Cash Conversion Cycle'].iloc[1]:.2f}", style={'font-size': body_size,
                                                                                       'margin': '20px 100px 20px 0px'}),
                ]), html.Div(
                children=[
                    html.H3('Debt/Equity r', style={'margin': '40px 100px 20px 0px'}),
                    html.H4(f"{summary_['Debt/Equity Ratio'].iloc[0]:.4f}", style={'font-size': body_size,
                                                                                   'margin': '20px 100px 20px 0px'}),
                    html.H4(f"{summary_['Debt/Equity Ratio'].iloc[1]:.4f}", style={'font-size': body_size,
                                                                                   'margin': '20px 100px 20px 0px'}),
                ]),
            html.Div(
                children=[
                    html.H3('Debt/EBITDA r', style={'margin': '40px 100px 20px 0px'}),
                    html.H4(f"{summary_['Debt/EBITDA Ratio'].iloc[0]:.4f}", style={'font-size': body_size,
                                                                                   'margin': '20px 100px 20px 0px'}),
                    html.H4(f"{summary_['Debt/EBITDA Ratio'].iloc[1]:.4f}", style={'font-size': body_size,
                                                                                   'margin': '20px 100px 20px 0px'}),
                ]),

        ],
        style={'display': 'flex', 'align-items': 'center'}
    ),


@app.callback(Output("summary_display", "children"),
              # Output("prg_amount_summary", "children"),
              Input("ticker-store", "children"))
def cycles_section(ticker):
    return html.Div(
        children=[
            html.H1('Impact summary'),

            html.Div(
                children=[
                    html.H3('Program amount ($M)', style={'margin': '0px 100px 20px 0px'}),
                    dbc.Input(
                        id="prg_amount_summary",
                        placeholder="Program amount",
                        type="value",
                        value=100,
                        style={
                            'color': 'blue',
                            'width': '20%',
                            'font-family': 'sans-serif',
                            'fontSize': body_size,
                            'margin': '10px',
                            'width': '250px',
                            'align-items': 'center',
                            'flex': 1,
                            'display': 'flex',
                            'justify-content': 'left'
                        }
                    ),
                ], style={'border': 'px solid orange',
                          'background-color': '#E5ECF6',
                          'box-shadow': '2px 2px 7px 4px lightgrey',
                          'border-radius': 20,
                          'margin': '30px 0px 30px 0px',
                          'padding': '10px',
                          'flex': 'row',
                          'horizontalAlign': 'center',
                          "align-items": "center",
                          "width": "30%"}, ),

            html.Div(id="summary_table",
                     style={'display': 'flex', 'align-items': 'center'}
                     ),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Legend"),
                                dbc.CardBody(
                                    [
                                        html.P(
                                            "FCF: Free Cash Flow, is the cash a company generates after accounting for operating expenses and capital expenditures. It represents the cash available for dividends, debt repayment, or reinvestment in the business.",
                                            className="card-text",
                                        ),
                                        html.P(
                                            "FFO: Funds from operations, is a financial measure used by real estate companies, representing net income excluding depreciation, amortization, and gains or losses from property sales. It indicates cash generated from core operating activities.",
                                            className="card-text",
                                        ),
                                        html.P(
                                            "NWC: Net working capital, is the difference between a company's current assets (e.g., cash, inventory, receivables) and current liabilities (e.g., payables, debts). It measures short-term liquidity and the ability to meet operational obligations.",
                                            className="card-text",
                                        ),
                                        html.P(
                                            "CCC: The cash conversion cycle, is a metric that measures the time it takes for a company to convert its investments in inventory and other resources into cash from sales. It includes the time to sell inventory, collect receivables, and pay off payables, indicating efficiency in managing working capital.",
                                            className="card-text",
                                        ),
                                    ]
                                ),
                            ]

                            , color="light", inverse=False)
                    ),

                ],
                className="mb-4", style={'margin': '50px 0px 0px 0px'}
            ),

        ],
        className="row",
        style={"display": "flex"}
    ),


@app.callback(Output("cycles_display", "children"),
              Input("ticker-store", "data"),
              Input("data_annual", "data"),
              Input("data_quarter", "data"))
def cycles_section(ticker, data_annual, data_quarter):
    if pd.DataFrame(data_quarter).shape[0] < 1:
        data_ = pd.DataFrame(data_annual)
    else:
        data_ = pd.DataFrame(data_quarter)

    cycles_annual_ = cycles(pd.DataFrame(data_annual))
    cycles_ = cycles(pd.DataFrame(data_))

    return html.Div(
        children=[
            html.H1('Operating performance ratios'),
            html.Div(
                children=[

                    html.Div(
                        children=[
                            html.H3('-', style={'margin': '40px 100px 20px 0px', 'color': 'white'}),
                            html.H4(f"Current", style={'font-size': body_size,
                                                       'margin': '20px 100px 20px 0px'}),
                            html.H4(f"Average last 3 years", style={'font-size': body_size,
                                                                    'margin': '20px 100px 20px 0px',
                                                                    'width': '300px'}),
                            html.H4(f"Average all-time", style={'font-size': body_size,
                                                                'margin': '20px 100px 20px 0px'}),
                        ], style={
                            "width": "300px"
                        }),
                    html.Div(
                        children=[
                            html.H3('DIO', style={'margin': '40px 100px 20px 0px'}),
                            html.H4(f"{cycles_annual_['last_dio']:.2f}", style={'font-size': body_size,
                                                                                'margin': '20px 100px 20px 0px'}),
                            html.H4(f"{cycles_annual_['avg_dio_3y']:.2f}", style={'font-size': body_size,
                                                                                  'margin': '20px 100px 20px 0px'}),
                            html.H4(f"{cycles_annual_['avg_dio']:.2f}", style={'font-size': body_size,
                                                                               'margin': '20px 100px 20px 0px'}),
                        ]),
                    html.Div(
                        children=[
                            html.H3('DSO', style={'margin': '40px 100px 20px 0px'}),
                            html.H4(f"{cycles_annual_['last_dso']:.2f}", style={'font-size': body_size,
                                                                                'margin': '20px 100px 20px 0px'}),
                            html.H4(f"{cycles_annual_['avg_dso_3y']:.2f}", style={'font-size': body_size,
                                                                                  'margin': '20px 100px 20px 0px'}),
                            html.H4(f"{cycles_annual_['avg_dso']:.2f}", style={'font-size': body_size,
                                                                               'margin': '20px 100px 20px 0px'}),
                        ]),
                    html.Div(
                        children=[
                            html.H3('DPO', style={'margin': '40px 100px 20px 0px'}),
                            html.H4(f"{cycles_annual_['last_dpo']:.2f}", style={'font-size': body_size,
                                                                                'margin': '20px 100px 20px 0px'}),
                            html.H4(f"{cycles_annual_['avg_dpo_3y']:.2f}", style={'font-size': body_size,
                                                                                  'margin': '20px 100px 20px 0px'}),
                            html.H4(f"{cycles_annual_['avg_dpo']:.2f}", style={'font-size': body_size,
                                                                               'margin': '20px 100px 20px 0px'}),
                        ]),
                    html.Div(
                        children=[
                            html.H3('CCC', style={'margin': '40px 100px 20px 0px'}),
                            html.H4(f"{cycles_annual_['last_ccc']:.2f}", style={'font-size': body_size,
                                                                                'margin': '20px 100px 20px 0px'}),
                            html.H4(f"{cycles_annual_['avg_ccc_3y']:.2f}", style={'font-size': body_size,
                                                                                  'margin': '20px 100px 20px 0px'}),
                            html.H4(f"{cycles_annual_['avg_ccc']:.2f}", style={'font-size': body_size,
                                                                               'margin': '20px 100px 20px 0px'}),
                        ]),

                    html.Div(
                        children=
                        [
                            html.Div(id='cycles_graph'),
                        ],
                        style={'width': '50%'}

                    ),

                ],
                style={'display': 'flex', 'align-items': 'center'}
            ),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("TCC NLP generation"),
                                dbc.CardBody(
                                    [
                                        html.H3("CII analysis", className="card-title"),
                                        html.Div(
                                            id='cycles_gpt',
                                        ),
                                    ]
                                ),
                            ]

                            , color="primary", inverse=True)
                    ),

                ],
                className="mb-4",
            ),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Legend"),
                                dbc.CardBody(
                                    [
                                        html.P(
                                            "DIO: Days Inventory Outstanding, The average number of days a company takes to sell its inventory, indicating inventory management efficiency.",
                                            className="card-text",
                                        ),
                                        html.P(
                                            "DPO: Days Payable Outstnading, The average number of days it takes to collect payment after a sale, reflecting the effectiveness of receivables collection.",
                                            className="card-text",
                                        ),
                                        html.P(
                                            "DSO: Days Sales Outstanding, The average number of days a company takes to pay its suppliers, showing how well it manages its payables.",
                                            className="card-text",
                                        ),
                                        html.P(
                                            "CCC: The cash conversion cycle, is a metric that measures the time it takes for a company to convert its investments in inventory and other resources into cash from sales. It includes the time to sell inventory, collect receivables, and pay off payables, indicating efficiency in managing working capital.",
                                            className="card-text",
                                        ),
                                    ]
                                ),
                            ]

                            , color="light", inverse=False)
                    ),

                ],
                className="mb-4",
            ),

        ],
        className="row",
        style={"display": "flex"}
    ),


@app.callback(Output("inv_cash_display", "children"),
              Input("ticker-store", "data"),
              Input("data_annual", "data"),
              Input("data_quarter", "data"))
def cycles_section(ticker, data_annual, data_quarter):
    if pd.DataFrame(data_quarter).shape[0] < 1:
        data_ = pd.DataFrame(data_annual)
    else:
        data_ = pd.DataFrame(data_quarter)

    inv_cash_annual_ = inv_cash(pd.DataFrame(data_annual))
    inv_cash_ = inv_cash(pd.DataFrame(data_))

    company_info = fmpsdk.company_profile(symbol=ticker, apikey='2723105eaade3c1ca8d66ca5c567b590')
    name_ = company_info[0]['companyName']

    return html.Div(
        children=[
            html.H1('Cash and Inventory'),

            html.Div(children=[
                html.H3('Display period', style={'margin': '0px 100px 20px 0px'}),
                dcc.RadioItems(id='inv-cash_graph_period', value='annual',
                               options={'annual': ' Annual', 'quarter': ' Quartal'}
                               , labelStyle={'margin': "10px 20px 10px 20px"})
            ], style={'border': 'px solid orange',
                      'background-color': '#E5ECF6',
                      'box-shadow': '2px 2px 7px 4px lightgrey',
                      'border-radius': 20,
                      'margin': '30px 0px 30px 0px',
                      'padding': '10px',
                      'flex': 'row',
                      'horizontalAlign': 'center',
                      "align-items": "center",
                      "width": "30%"}, ),

            html.Div(
                children=[

                    html.Div(children=[
                        html.Div(id='inv_graph'),
                    ], style={'width': '50%'}),

                    html.Div(children=[
                        html.Div(id='cash_graph'),
                    ], style={'width': '50%'}),

                ],
                style={'display': 'flex', 'align-items': 'top', 'width': '100%'}
            ),

            html.Div(
                children=[

                    html.Div(
                        children=[
                            html.H3('-', style={'margin': '40px 100px 20px 0px', 'color': 'white'}),
                            html.H4(f"Current", style={'font-size': body_size,
                                                       'margin': '20px 100px 20px 0px'}),
                            html.H4(f"Average last 3 years", style={'font-size': body_size,
                                                                    'margin': '20px 100px 20px 0px'}),
                            html.H4(f"Average all-time", style={'font-size': body_size,
                                                                'margin': '20px 100px 20px 0px'}),
                        ]),
                    html.Div(
                        children=[
                            html.H3('Inventory', style={'margin': '40px 100px 20px 0px'}),
                            html.H4(inv_cash_['last_inv'], style={'font-size': body_size,
                                                                  'margin': '20px 100px 20px 0px'}),
                            html.H4(inv_cash_annual_['avg_inv_3y'], style={'font-size': body_size,
                                                                           'margin': '20px 100px 20px 0px'}),
                            html.H4(inv_cash_annual_['avg_inv'], style={'font-size': body_size,
                                                                        'margin': '20px 100px 20px 0px'}),
                        ]),
                    html.Div(
                        children=[
                            html.H3('Cash', style={'margin': '40px 100px 20px 0px'}),
                            html.H4(inv_cash_['last_cash'], style={'font-size': body_size,
                                                                   'margin': '20px 100px 20px 0px'}),
                            html.H4(inv_cash_annual_['avg_cash_3y'], style={'font-size': body_size,
                                                                            'margin': '20px 100px 20px 0px'}),
                            html.H4(inv_cash_annual_['avg_cash'], style={'font-size': body_size,
                                                                         'margin': '20px 100px 20px 0px'}),
                        ]),
                    html.Div(
                        children=[
                            html.H3('Inventory to total asset ratio', style={'margin': '40px 100px 20px 0px'}),
                            html.H4(inv_cash_['last_inv_TA'], style={'font-size': body_size,
                                                                     'margin': '20px 100px 20px 0px'}),
                            html.H4(inv_cash_annual_['avg_inv_TA_3y'], style={'font-size': body_size,
                                                                              'margin': '20px 100px 20px 0px'}),
                            html.H4(inv_cash_annual_['avg_inv_TA'], style={'font-size': body_size,
                                                                           'margin': '20px 100px 20px 0px'}),
                        ]),
                    html.Div(
                        children=[
                            html.H3('Cash  to total asset ratio', style={'margin': '40px 100px 20px 0px'}),
                            html.H4(inv_cash_['last_cash_TA'], style={'font-size': body_size,
                                                                      'margin': '20px 100px 20px 0px'}),
                            html.H4(inv_cash_annual_['avg_cash_TA_3y'], style={'font-size': body_size,
                                                                               'margin': '20px 100px 20px 0px'}),
                            html.H4(inv_cash_annual_['avg_cash_TA'], style={'font-size': body_size,
                                                                            'margin': '20px 100px 20px 0px'}),
                        ]),

                ],
                style={'display': 'flex', 'align-items': 'center', 'margin': '-20px 0px 50px 0px'}
            ),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("TCC NLP generation"),
                                dbc.CardBody(
                                    [
                                        html.H3("CII analysis", className="card-title"),
                                        dcc.Markdown(
                                            gpt.gpt_inv_cash(inv_cash_, name_),
                                            # 'Test gpt here',
                                            className="card-text",
                                        ),
                                    ]
                                ),
                            ]

                            , color="primary", inverse=True)
                    ),

                ],
                className="mb-4",
            ),

        ],
        className="row",
        style={"display": "flex"}
    ),


@app.callback(Output("WC_elasticity_display", "children"),
              Input("ticker-store", "data"),
              Input("data_annual", "data"),
              Input("data_quarter", "data"))
def WC_elasticity_section(ticker, data_annual, data_quarter):
    if pd.DataFrame(data_quarter).shape[0] < 1:
        data_ = pd.DataFrame(data_annual)
    else:
        data_ = pd.DataFrame(data_quarter)

    inv_cash_annual_ = inv_cash(pd.DataFrame(data_annual))
    inv_cash_ = inv_cash(pd.DataFrame(data_))

    return html.Div(
        children=[
            html.H1('Working Capital elasticity and positive impact on FCF & FFO'),

            html.Div(
                children=[
                    html.H3('Program amount ($M)', style={'margin': '0px 100px 20px 0px'}),
                    dbc.Input(
                        id="prg_amount",
                        placeholder="Program amount",
                        type="value",
                        value=100,
                        style={
                            'color': 'blue',
                            'width': '20%',
                            'font-family': 'sans-serif',
                            'fontSize': body_size,
                            'margin': '10px',
                            'width': '250px',
                            'align-items': 'center',
                            'flex': 1,
                            'display': 'flex',
                            'justify-content': 'left'
                        }
                    ),
                ], style={'border': 'px solid orange',
                          'background-color': '#E5ECF6',
                          'box-shadow': '2px 2px 7px 4px lightgrey',
                          'border-radius': 20,
                          'margin': '30px 0px 30px 0px',
                          'padding': '10px',
                          'flex': 'row',
                          'horizontalAlign': 'center',
                          "align-items": "center",
                          "width": "30%"}, ),

            html.Div(
                children=[

                    html.Div(children=[
                        html.Div(id='WC_elasticity_graph_display'),
                    ], style={'width': '50%'}),

                    html.Div(children=[
                        html.Div(id='fcf_ffo_graph'),
                    ], style={'width': '50%'}),

                ],
                style={'display': 'flex', 'align-items': 'center'}
            ),

        ],
        className="row",
        style={"display": "flex"}
    ),


@app.callback(Output("financial_health_display", "children"),
              Input("ticker-store", "data"),
              Input("data_annual", "data"),
              Input("data_quarter", "data"))
def financial_health_section(ticker, data_annual, data_quarter):
    if pd.DataFrame(data_quarter).shape[0] < 1:
        data_ = pd.DataFrame(data_annual)
    else:
        data_ = pd.DataFrame(data_quarter)

    scores_ = fmp.get_scores_url(ticker)

    piotroski_ = fmp.get_scores_url(ticker)[1]
    altman_ = fmp.get_scores_url(ticker)[0]

    return html.Div(
        children=[
            html.H1('Financial Health Assessment and Impact'),

            html.Div(children=[
                html.Div(
                    children=[dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Current Piotroski Score", id="hover-target-piotroski"),
                                        dbc.CardBody(
                                            [

                                                dbc.Popover(
                                                    [
                                                        dbc.PopoverHeader("Piotroski Score"),
                                                        dbc.PopoverBody(
                                                            "The Piotroski score is a discrete score between zero and nine that reflects nine criteria used to determine the strength of a firm's financial position. The Piotroski score is used to determine the best value stocks, with nine being the best and zero being the worst."),
                                                    ],

                                                    target="hover-target-piotroski",
                                                    body=True,
                                                    trigger="hover",
                                                ),
                                                html.H3(str(piotroski_), className="card-title"),
                                                html.P(
                                                    'Test gpt here'
                                                ),
                                            ]
                                        ),
                                    ]

                                    , color='info', inverse=True)
                            ),

                        ],
                        className="mb-4",
                    ), ], style={'margin': '30px'}),

                html.Div(
                    children=[dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Current Altman Z-Score", id="hover-target-altman"),
                                        dbc.CardBody(
                                            [
                                                dbc.Popover(
                                                    [
                                                        dbc.PopoverHeader("Altman Z-score"),
                                                        dbc.PopoverBody(
                                                            "The Altman Z-score, a variation of the traditional z-score in statistics, is based on five financial ratios that can be calculated from data found on a company's annual 10-K report. It uses profitability, leverage, liquidity, solvency, and activity to predict whether a company has a high probability of becoming insolvent."),
                                                    ],

                                                    target="hover-target-altman",
                                                    body=True,
                                                    trigger="hover",
                                                ),
                                                html.H3(str('{:.2f}'.format(altman_)), className="card-title"),
                                                html.P(
                                                    'Test gpt here'
                                                ),
                                            ]
                                        ),
                                    ]

                                    , color='info', inverse=True)
                            ),

                        ],
                        className="mb-4",
                    ), ], style={'margin': '30px'}),
            ], style={'display': 'flex', 'align-items': 'center'}
            ),

        ],
        className="row",
        style={"display": "flex"}
    ),


@app.callback(Output("quadrants_process", "children"),
              Input("ticker-store", "data"),
              Input("data_annual", "data"),
              Input("data_quarter", "data"),
              Input("quadrants_amount", "value"))
def financial_health_section(ticker, data_annual, data_quarter, amount):
    data_annual = pd.DataFrame(data_annual)
    data_quarter = pd.DataFrame(data_quarter)

    print(str(amount) + str(type(amount)))

    return html.Div(
        children=[

            html.Div(children=[
                dcc.Graph(
                    id='quadrant1-graph',
                    figure=graph.quadrant_compare(amount, ['inventory', 'cashAndCashEquivalents'], ticker, 'annual',
                                            data_annual, data_quarter, 'Inventory vs Cash', 'Inventory $', 'Cash $'),
                ), ]),

            html.Div(children=[
                dcc.Graph(
                    id='quadrant2-graph',
                    figure=graph.quadrant_compare(amount, ['cashAndCashEquivalents', 'daysOfInventoryOutstanding'], ticker,
                                            'annual', data_annual, data_quarter, 'Inventory vs DIO', 'Inventory $',
                                            'DIO (days)'),
                ), ]),

            html.Div(children=[
                dcc.Graph(
                    id='quadrant2-graph',
                    figure=graph.quadrant_compare(amount, ['cashAndCashEquivalents', 'cashConversionCycle'], ticker, 'annual',
                                            data_annual, data_quarter, 'Cash vs CCC', 'Cash $', 'CCC (days)'),
                ), ]),

            html.Div(children=[
                dcc.Graph(
                    id='quadrant2-graph',
                    figure=graph.quadrant_compare(amount, ['inventory', 'totalAssets'], ticker, 'annual', data_annual,
                                            data_quarter, 'Inventory vs Total Assets', 'Inventory $', 'Total Assets $'),
                ), ]),

        ],
        className="row",
        style={"display": "flex"}
    ),


@app.callback(Output("quadrants_display", "children"),
              Input("ticker-store", "data"))
def financial_health_section(ticker):
    comp_industry = get_table_competition(ticker)

    return html.Div(
        children=[
            html.H1('Industry comparison'),

            html.Div(
                children=[
                    html.H3('Program amount ($M)', style={'margin': '0px 100px 20px 0px'}),
                    dbc.Input(
                        id="quadrants_amount",
                        placeholder="Program amount",
                        type="value",
                        value=100,
                        style={
                            'color': 'blue',
                            'width': '20%',
                            'font-family': 'sans-serif',
                            'fontSize': body_size,
                            'margin': '10px',
                            'width': '250px',
                            'align-items': 'center',
                            'flex': 1,
                            'display': 'flex',
                            'justify-content': 'left'
                        }
                    ),
                ], style={'border': 'px solid orange',
                          'background-color': '#E5ECF6',
                          'box-shadow': '2px 2px 7px 4px lightgrey',
                          'border-radius': 20,
                          'margin': '30px 0px 30px 0px',
                          'padding': '10px',
                          'flex': 'row',
                          'horizontalAlign': 'center',
                          "align-items": "center",
                          "width": "30%"}, ),

            html.Div(id='quadrants_process'),

            html.H3('Tikers list', style={'margin': '40px 100px 20px 0px'}),

            DataTable(
                id='datatable-competion',
                columns=[
                    {"name": i, "id": i, "selectable": True} for i in comp_industry.columns
                ],
                data=comp_industry.to_dict('records'),
                # editable=True,
                style_header={'padding': '10px', 'font-family': 'sans-serif', 'fontSize': title_size},
                style_cell={'padding': '10px', 'font-family': 'sans-serif', 'fontSize': body_size},
                sort_action="native",
                sort_mode="multi",
                style_table={'overflowX': 'scroll', 'overflowY': 'scroll'},
                # row_selectable="single",
                page_action="native",
                page_current=0,
                page_size=50,
            ),

        ],
        className="row",
        style={"display": "flex"}
    ),


@app.callback(Output("supplier_test", "children"),
              Input("ticker-store", "data"))
def financial_health_section(ticker):
    company_info = fmpsdk.company_profile(symbol=ticker, apikey='2723105eaade3c1ca8d66ca5c567b590')
    name_ = company_info[0]['companyName']

    data_suppliers_ = gpt.gpt_suppliers(name_)

    if data_suppliers_ == '':
        return ''

    else:
        df_suppliers_ = create_dataframe_from_list(data_suppliers_)
        return html.Div(children=[

            html.Div(children=[

                html.H1('Known Partnerships', style={'margin': '00px 0px 40px 0px'}),

                html.Div(
                    children=[

                        html.Br(),
                        html.H2('Suppliers', style={'margin': '00px 0px 40px 0px'}),
                        DataTable(
                            id='datatable-org',
                            columns=[
                                {"name": i, "id": i, "selectable": True} for i in df_suppliers_.columns
                            ],
                            data=df_suppliers_.to_dict('records'),
                            # editable=True,
                            style_header={'padding': '10px', 'font-family': 'sans-serif', 'fontSize': title_size},
                            style_cell={'padding': '10px', 'font-family': 'sans-serif', 'fontSize': body_size},
                            sort_action="native",
                            sort_mode="multi",
                            style_table={'overflowX': 'scroll', 'overflowY': 'scroll'},
                            # row_selectable="single",
                            page_action="native",
                            page_current=0,
                            page_size=50,
                            # style={'margin':'40px 0px 20px 0px'},
                        ),

                    ],
                    className="row",
                    style={"display": "flex"}
                ),

                html.Div(
                    children=[

                        html.Br(),
                        html.H2('Banks', style={'margin': '40px 0px 40px 0px'}),
                        dcc.Markdown(
                            gpt.banks(name_),
                            style={'font-size': 20}
                        ),

                    ],
                    className="row",
                    style={"display": "flex"}
                ),

                html.Br(),

            ], style={

                "display": "flex",
                "flex-direction": "column",
                "justify-content": "left",
                "align-items": "left",
            })

        ], style={'border': 'px solid orange',
                  'background-color': 'white',
                  'box-shadow': '5px 5px 15px 8px lightgrey',
                  'border-radius': 20,
                  'margin': '30px',
                  'padding': '100px',
                  'flex': 'row',
                  'horizontalAlign': 'center',
                  "align-items": "center"}, )


# ## app layout

#

# In[23]:


# Assign the initial layout to the app
app.layout = html.Div(
    [
        # Storing whether or not the user is signed in so that the user does not have to
        # sign in again every time they visit a new page.
        dcc.Store(id="authentication-data", storage_type="session", data={
            "is-authenticated": False
        }),

        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content", children=sign_in_layout)
    ]
)


#server = app.server
app.config.suppress_callback_exceptions = True  # Prevents error messages from missing IDs.
'''if __name__ == '__main__':

    port = int(os.getenv("PORT", 8000))
    serve(app.server, host='0.0.0.0', port=8080)
    #app.run_server(port=8000, debug=True, use_reloader=False)'''

application = app.server

app.title= "CaaS Insights and Intelligence"

if __name__ == '__main__':
    app.run_server(debug=True)





