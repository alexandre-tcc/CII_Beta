from urllib.request import urlopen

import certifi
import json

import pandas as pd
import fmpsdk
import numpy as np
import base64


import os
from dotenv import load_dotenv

#bundle import
import gpt
import da

api_key_fmp_env=os.getenv('FMP_API_KEY')
#'2723105eaade3c1ca8d66ca5c567b590'

def get_data_url(url):  # Get data using API link - NOT fmpsdk lib
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
    data = json.loads(data)
    return pd.DataFrame(data)

def data_merge(ticker, period):  # get and merge data from BSS; CFS; IS; and ratios - input period and ticker

    apikey = api_key_fmp_env

    symbol: str = ticker

    data_BSS = pd.DataFrame(fmpsdk.balance_sheet_statement(apikey=apikey, symbol=symbol, period=period))
    data_CFS = pd.DataFrame(fmpsdk.cash_flow_statement(apikey=apikey, symbol=symbol, period=period))
    data_IS = pd.DataFrame(fmpsdk.income_statement(apikey=apikey, symbol=symbol, period=period))
    data_ratios = pd.DataFrame(fmpsdk.financial_ratios(apikey=apikey, symbol=symbol, period=period))

    data_CFS.pop('inventory')
    data_CFS.pop('netIncome')
    data_CFS.pop('depreciationAndAmortization')

    data_annual = data_BSS.copy()
    data_annual = data_annual.merge(data_CFS, how='inner',
                                    on=['date', 'cik', 'period', 'reportedCurrency', 'symbol', 'link', 'finalLink',
                                        'fillingDate', 'acceptedDate', 'calendarYear'])
    data_annual = data_annual.merge(data_IS, how='inner',
                                    on=['date', 'cik', 'period', 'reportedCurrency', 'symbol', 'link', 'finalLink',
                                        'fillingDate', 'acceptedDate', 'calendarYear'])
    data_annual = data_annual.merge(data_ratios, how='inner', on=['date', 'period', 'symbol'])

    return data_annual




def get_competitors(ticker):  # Get competitors - NOT fmpsdk lib
    apikey = api_key_fmp_env

    url = (f'https://financialmodelingprep.com/api/v4/stock_peers?symbol={ticker}&apikey={apikey}')

    data = get_data_url(url)
    return data['peersList'][0]


def get_latest_earnings_transcript(ticker):
    apikey = api_key_fmp_env

    url = f'https://financialmodelingprep.com/api/v3/earning_call_transcript/{ticker}?apikey={apikey}'

    data = get_data_url(url)

    # Check if transcripts are available
    return data['date'].iloc[0], data['content'].iloc[0]

def get_org_chart(ticker):
    apikey = api_key_fmp_env
    url = f'https://financialmodelingprep.com/api/v3/key-executives/{ticker}?apikey={apikey}'
    df_ = get_data_url(url)
    df_ = df_[['title'] + ['name']]
    df_ = df_.drop_duplicates(subset='name')
    # df_=df_.drop_duplicates(subset='title', inplace=True)
    return df_


def get_data_peers(ticker):
    frames_ = []
    peers_ = get_competitors(ticker)
    for peer in peers_:
        try:
            data_peer = data_merge(ticker, 'annual')
            data_peer_last = data_peer.iloc[0]
            frames_.append(data_peer_last)
        except:
            pass
    dt = pd.concat(frames_)
    return dt


def get_scores_url(ticker):
    apikey = api_key_fmp_env
    url = f'https://financialmodelingprep.com/api/v4/score?symbol={ticker}&apikey={apikey}'
    data_ = get_data_url(url)

    try:
        altmanz = data_['altmanZScore'].iloc[0]
        piotroski = data_['piotroskiScore'].iloc[0]
        marketcap = data_['marketCap'].iloc[0]
    except:
        altmanz = 0
        piotroski = 0
        marketcap = 0

    return altmanz, piotroski, marketcap


def return_tickers_industry(tck):
    # Get company profile and industry from the ticker
    company_info = fmpsdk.company_profile(symbol=tck, apikey=api_key_fmp_env)
    industry_ = company_info[0]['industry']

    # Read CSV and filter by industry
    data_ = pd.read_csv('assets/TCC companies mapping 10142024.csv')
    filtered_indus_ = data_[data_['Industry'] == industry_]

    # Return the list of tickers from the same industry
    # return filtered_indus_['ticker'].to_list()
    list_tck = filtered_indus_['ticker'].to_list()
    return list_tck