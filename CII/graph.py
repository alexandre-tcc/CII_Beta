
from urllib.request import urlopen


import certifi
import json

import plotly.graph_objects as go
import plotly.express as px


import pandas as pd
import fmpsdk
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
import gpt
import da
import fmp




def line_graph(fields, data):
    traces = []

    x_values = data['date']

    for field in fields:
        y_values = data[field]

        trace = go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines',
            name=field
        )

        traces.append(trace)

    layout = go.Layout(
        # title='Line Graph Example',
        xaxis=dict(title='date'),
        yaxis=dict(title=da.format_string(field)),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=1.1,
            xanchor='center',
            x=0.5
        )
    )

    return go.Figure(data=traces, layout=layout)

def line_graph_cycles(fields, data):
    data = pd.DataFrame(data)
    traces = []

    if data['period'].iloc[0] == 'FY':
        x_values = data['calendarYear_x']
    else:
        x_values = data['date']

    for field in fields:
        y_values = data[field]

        trace = go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines',
            name=field
        )

        traces.append(trace)

    if data['period'].iloc[0] == 'FY':
        layout = go.Layout(
            # title='Line Graph Example',
            xaxis=dict(title='date', autorange='reversed'),
            yaxis=dict(title='DAYS'),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5,
                traceorder='reversed',  # Reverses the legend order to match the lines
                bgcolor='rgba(0,0,0,0)'  # Sets a transparent background for the legend
            ),
            height=600,
        )
    else:
        layout = go.Layout(
            # title='Line Graph Example',
            xaxis=dict(title='date'),
            yaxis=dict(title='DAYS'),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5,
                traceorder='reversed',  # Reverses the legend order to match the lines
                bgcolor='rgba(0,0,0,0)'  # Sets a transparent background for the legend
            ),
            height=600,
        )

    return go.Figure(data=traces, layout=layout)


def stock_price(ticker):
    stock_prices = fmpsdk.historical_price_full(apikey='2723105eaade3c1ca8d66ca5c567b590', symbol=ticker)
    # Extract the date and closing price from the stock price data
    dates = [price['date'] for price in stock_prices]
    closing_prices = [price['close'] for price in stock_prices]

    # Extract the latest date and closing price
    latest_price = closing_prices[0]
    latest_date = dates[0]

    # Create the plot using plotly
    fig = go.Figure(data=go.Scatter(x=dates, y=closing_prices, name=' ', line=dict(color=da.orange_tcc)))
    fig.add_trace(go.Scatter(x=[latest_date], y=[latest_price], mode='markers+text', name='Latest', text=[latest_price],
                             textposition='middle right', marker=dict(size=12, color=da.blue_tcc)))

    fig.update_layout(xaxis_title='Date',
                      yaxis_title='Closing Price',
                      showlegend=False,
                      plot_bgcolor='#f5f5f5',
                      width=1200)
    return fig

def WC_elasticity_graph(data, prg_total):
    df_ = pd.DataFrame(data)
    prg_total_ = int(prg_total) * 1000000
    df_ = df_[df_['calendarYear_x'].astype(int) > 2019].copy()

    # generate with 1TCC row
    first_row = df_.iloc[[0]]  # Select the first row
    df_ = pd.concat([first_row, df_], ignore_index=True)
    df_['calendarYear_x'].iloc[0] = 'With 1TCC'
    df_['inventory'].iloc[0] = int(df_['inventory'].iloc[0]) - int(prg_total_)
    df_['accountsPayables'].iloc[0] = int(df_['accountsPayables'].iloc[0]) + int(prg_total_)

    fig = px.bar(df_, x="calendarYear_x", text_auto=True, y=["inventory", "accountsPayables", "accountsReceivables"],
                 height=600)
    fig.update_layout(xaxis=dict(autorange='reversed'))

    fig.update_layout(legend=dict(
        orientation="h",
        title=None,
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(
            size=18,
            color="black"
        ),
    ))

    fig.update_xaxes(title=None)
    fig.update_yaxes(title='($)')

    return fig


def quadrant_compare(amount, vari, tck, period, data_annual, data_quarter, label_bg, label_x, label_y):
    amount_ = int(amount) * 10 ** 6

    x_ = vari[0]
    y_ = vari[1]

    tck_1tcc = tck + ' (with 1TCC)'

    tickers_industry_ = fmp.return_tickers_industry(tck)

    if period == 'quarter':
        df_ = pd.read_csv('assets/TCC_focus_companies_data_financials_quarter.csv')
        df_industry = df_[df_['symbol'].isin(tickers_industry_)]
        df_tck = pd.DataFrame(data_quarter)


    else:
        df_ = pd.read_csv('assets/TCC_focus_companies_data_financials_annual.csv')
        df_industry = df_[df_['symbol'].isin(tickers_industry_)]
        df_tck = pd.DataFrame(data_annual)

    # Industry within
    df_filtered_indus = df_industry[df_industry['symbol'] != tck].copy()
    df_filtered_indus = df_filtered_indus.sort_values('acceptedDate', ascending=False)
    df_filtered_indus['acceptedDate'] = pd.to_datetime(df_filtered_indus['acceptedDate'])  # Convert to datetime
    latest_dates_indus = df_filtered_indus.groupby('symbol')['acceptedDate'].idxmax()
    df_latest_indus = df_filtered_indus.loc[latest_dates_indus]
    df_latest_indus = df_latest_indus[df_latest_indus['inventory'] >= 300000000]

    # Ticker base
    df_tck = df_tck.sort_values('acceptedDate', ascending=False)
    df_tck['acceptedDate'] = pd.to_datetime(df_tck['acceptedDate'])  # Convert to datetime
    latest_dates_tck = df_tck.groupby('symbol')['acceptedDate'].idxmax()
    df_latest_tck = df_tck.loc[latest_dates_tck]

    # Ticker base + 1TCC
    # duplicate row Tck base
    df_duplicate = df_latest_tck[df_latest_tck['symbol'] == tck].copy()
    df_latest_tck = pd.concat([df_latest_tck, df_duplicate], ignore_index=True)
    # make change to (with tcc)
    df_latest_tck.at[df_latest_tck.index[-1], 'symbol'] = tck_1tcc
    df_latest_tck.at[df_latest_tck.index[-1], 'inventory'] -= amount_
    df_latest_tck.at[df_latest_tck.index[-1], 'cashAndCashEquivalents'] += amount_
    df_latest_tck.at[df_latest_tck.index[-1], 'totalAssets'] -= amount_
    df_latest_tck.at[df_latest_tck.index[-1], 'daysOfInventoryOutstanding'] = 30
    dso_ = df_latest_tck[df_latest_tck['symbol'] == tck_1tcc]['daysOfSalesOutstanding'].iloc[0]
    df_latest_tck.at[df_latest_tck.index[-1], 'cashConversionCycle'] += 30 + dso_ - 90

    df_combined = pd.concat([df_latest_tck, df_latest_indus])

    # color bubble
    df_combined['color_'] = 'grey'
    df_combined.loc[df_combined['symbol'] == tck_1tcc, 'color_'] = da.orange_tcc
    df_combined.loc[df_combined['symbol'] == tck, 'color_'] = '#3384BA'

    # size font
    df_combined['f_size_'] = 16
    df_combined.loc[df_combined['symbol'] == tck, 'f_size_'] = 22
    df_combined.loc[df_combined['symbol'] == tck_1tcc, 'f_size_'] = 22

    # Create scatter plot
    fig = px.scatter(df_combined, x=x_, y=y_, color_discrete_sequence=[da.orange_tcc],
                     text="symbol", labels={x_: label_x, y_: label_y},  # size='totalAssets',
                     template="simple_white", height=1000)

    fig.update_traces(marker=dict(color=df_combined['color_'], size=30, opacity=0.75))
    fig.update_traces(textfont=dict(size=df_combined['f_size_'], color=df_combined['color_']))

    # Format text above the bubbles
    fig.update_traces(
        texttemplate='%{text}',
        textposition='top center',
        # hovertemplate='Symbol: %{text}<br>Amount: $%{x}M<br>TCC Supplier Rating: %{y}<br>'
    )

    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        text=label_bg,
        showarrow=False,
        font=dict(
            color="black",
            size=52
        ),
        opacity=0.15
    )

    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.1,
        text='Refer to correspondence table at the end of the section to get company names',
        showarrow=False,
        font=dict(
            color="black",
            size=16
        ),
        opacity=0.25
    )

    return fig


def fcf_ffo_graph(data, prg_total):
    df_ = pd.DataFrame(data)
    prg_total_ = int(prg_total) * 1000000
    df_ = df_[df_['calendarYear_x'].astype(int) > 2018].copy()

    # generate with 1TCC row
    first_row = df_.iloc[[0]]  # Select the first row
    df_ = pd.concat([first_row, df_], ignore_index=True)
    df_['calendarYear_x'].iloc[0] = 'With 1TCC'
    df_['inventory'].iloc[0] = int(df_['inventory'].iloc[0]) - int(prg_total_)
    df_['accountsPayables'].iloc[0] = int(df_['accountsPayables'].iloc[0]) - int(prg_total_)

    df_['WC'] = df_['inventory'] + df_['accountsPayables'] + df_['accountsReceivables']
    df_['FFO'] = df_['netIncome'] + df_['depreciationAndAmortization'] - df_['interestIncome']

    df_['freeCashFlow'].iloc[0] = int(df_['freeCashFlow'].iloc[1]) + int(df_['WC'].iloc[1]) - int(df_['WC'].iloc[0])
    df_['FFO'].iloc[0] = int(df_['FFO'].iloc[1]) + int(df_['WC'].iloc[1]) - int(df_['WC'].iloc[0])

    fig = px.line(df_, x="calendarYear_x", y=["freeCashFlow", "FFO", "WC"],
                  markers=True, height=600)
    fig.update_layout(xaxis=dict(autorange='reversed'))

    fig.data[0].name = "Free Cash Flow"
    fig.data[1].name = "Funds From Operation"
    fig.data[2].name = "Working Capital"

    fig.update_layout(legend=dict(
        orientation="h",
        title=None,
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(
            size=18,
            color="black"
        ),
    ))

    fig.update_xaxes(title=None)
    fig.update_yaxes(title='($)')

    return fig


def avg_industry(vari, tck, period, data_annual, data_quarter, label):
    company_info = fmpsdk.company_profile(symbol=tck, apikey='2723105eaade3c1ca8d66ca5c567b590')
    industry_ = company_info[0]['industry']

    tickers_industry_ = fmp.return_tickers_industry(tck)

    if period == 'quarter':
        df_ = pd.read_csv('assets/TCC_focus_companies_data_financials_quarter.csv')
        df_industry = df_[df_['symbol'].isin(tickers_industry_)]
        df_industry['date_formated'] = df_industry['calendarYear'].astype(str) + df_industry['period']
        df_tck = data_quarter
        df_tck['date_formated'] = df_tck['calendarYear_x'].astype(str) + df_tck['period']
    else:
        df_ = pd.read_csv('assets/TCC_focus_companies_data_financials_annual.csv')
        df_industry = df_[df_['symbol'].isin(tickers_industry_)]
        df_industry['date_formated'] = df_industry['calendarYear']
        df_tck = data_annual
        df_tck['date_formated'] = df_tck['calendarYear_x']

    numeric_cols = df_industry.select_dtypes(include=['number']).columns
    df_industry_grouped = df_industry.groupby(['date_formated'])[numeric_cols].mean()
    df_industry_grouped['symbol'] = industry_
    try:
        df_industry_grouped.drop(columns=['date_formated'], inplace=True)
    except:
        print('no date_formated colmumn')
    df_industry_grouped.reset_index(inplace=True)
    print(df_industry_grouped['date_formated'])


    # Group and calculate mean for ticker data
    numeric_cols_tck = df_tck.select_dtypes(include=['number']).columns
    df_tck_grouped = df_tck.groupby('date_formated')[numeric_cols_tck].mean()
    df_tck_grouped['symbol'] = tck
    try:
        df_tck_grouped.drop(columns=['date_formated'], inplace=True)
    except:
        print('no date_formated colmumn')
    df_tck_grouped.reset_index(inplace=True)
    print(df_tck_grouped['date_formated'])


    df_plot = pd.concat([df_industry_grouped, df_tck_grouped], axis=0)
    #df_plot.reset_index(drop=True, inplace=True)

    fig_ind = px.line(df_plot, x='date_formated', y=vari, color='symbol',
                      labels={"date": ""}, height=600, markers=True)  # text=vari,

    fig_ind.update_xaxes(tickvals=list(df_plot['date_formated']))
    fig_ind.update_traces(textposition='top center')

    # fig_ind.update_layout(xaxis = dict(tickfont = dict(size=25)))
    # fig_ind.update_layout(xaxis= {'tickformat': '%Y'})
    fig_ind.update_xaxes(title=None)
    fig_ind.update_yaxes(title=None)
    fig_ind.update_layout(legend=dict(
        orientation="h",
        title=None,
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(
            size=18,
            color="black"
        ),
    ))

    fig_ind.add_annotation(
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        text=label,
        showarrow=False,
        font=dict(
            color="black",
            size=70
        ),
        opacity=0.15
    )

    return fig_ind
