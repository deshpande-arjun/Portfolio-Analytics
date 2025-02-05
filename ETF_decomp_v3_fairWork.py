# -*- coding: utf-8 -*-
"""
Created on Thu Jan 30 12:14:43 2025

@author: Arjun Deshpande

"""

import pandas as pd
import os
import requests
import json


# =============================================================================
# Unused
import yfinance as yf
from pyetfdb_scraper.etf import ETF
# =============================================================================

wd = 'C:\ArjunDesktop\iCloudDrive\ETF decomposition'
os.chdir(wd)


# dummy portfolio file
port = pd.read_excel("portfolio_allocation.xlsx") # read excel to get portfolio positions
etf_list = [x for x in port.ticker[port.asset=='etf']] # filter the etf list from portfolio
etf_holdings_dict = dict_etf_holdings(etf_list)     # dictionary of etf to constituent stocks
decomposed_stocks = etf_decomposed(port,etf_holdings_dict ) # function decomposing port into constituent stocks
decomposed_stocks.to_excel("decomposed_stock_holdings.xlsx") # export the stock holdings to excel

# Actual curated report from IBKR of current positions:
real_port = pd.read_csv("CurrentPositions_1.31.2025.csv") # read excel to get current portfolio positions
etf_list = [x for x in real_port.Symbol[real_port.SubCategory=='ETF']] # filter the etf list from portfolio
etf_metadata      = store_etf_metadata(etf_list)  # meta data for all etfs in the list
etf_holdings_dict = dict_etf_holdings(etf_list, etf_metadata) # dictionary of etf to constituent stocks
decomposed_stocks_JanEnd2025 = etf_decomposer(real_port, etf_holdings_dict) # function decomposing port into constituent stocks


decomposed_stocks_JanEnd2025['port_weight'] = decomposed_stocks_JanEnd2025.allocation/decomposed_stocks_JanEnd2025.allocation.sum()
decomposed_stocks_JanEnd2025.to_excel("decomposed_stock_holdings_JanEnd2025.xlsx") # export the stock holdings to excel

#%% Rough Work


# %% Data manipulation and calculations

def etf_decomposer(port, etf_holdings_dict):
    """
    To decompose the ETF positions into constituent stock positions
    
    inputs:
    port: dataframe of all ETFs and stocks that are held in the portfolio
    etf_holdings_dict: dictionary of dataframes with stock holdings for each ETF
    
    output:
    etf_to_stock: dataframe of all stock positions decomposed from ETF positions
    
    """
    #rename columns:
    port.rename(columns={"Symbol": "ticker", "Description": "name"}, inplace=True)  # , "positionvalue": "allocation" 
    
    # creating a list of ETFs with available holdings data
    port_etf = pd.DataFrame(etf_holdings_dict.keys(), columns=['ticker'])
    
    # separate stock and etf 
    port_stock = port[~port.ticker.isin(port_etf.ticker)]
    port_etf = pd.merge(port_etf,port, on='ticker')

    
    # Decomposing ETF into stocks:
    decomposed_etf = []
    for etf_ticker,position_value in zip(port_etf.ticker, port_etf.PositionValue):
        
        temp_df = etf_holdings_dict[etf_ticker]  # pull holdings of the etf from etf_data
        temp_df["allocation"] = temp_df.weight * position_value # allocation of each stock
        
        decomposed_etf.append(temp_df) # append the stocks in each iteration
    

    port_stock.rename(columns={"PositionValue": "allocation"}, inplace=True)
    port_stock = port_stock[["ticker", "name", "allocation"]]  #remove unnecessary columns
    
    decomposed_etf.append(port_stock) # append stocks to decomposed etf 
    merged_df = pd.concat(decomposed_etf) #concat lists into a df
    # groupby on ticker and name, then sum allocations from all etfs
    merged_df = merged_df.groupby(['ticker', 'name'], as_index= False).agg({'allocation': 'sum'})
    
    return merged_df


def dict_etf_holdings(etf_list, meta_data):
    """
    inputs:
        etf_list (str): list of all ETFs that are held in the portfolio
        
    output:
        etf_to_stock: dictionary with key of etf tickers from the input list
                      and values are the etf holdings (ticker, name, allocation)
    """
    etf_to_stock = {}
    for etf_ticker in etf_list:
        temp_etfdata = meta_data[etf_ticker]
        temp_holdings = etf_holdings_alpha_vantage(etf_ticker,temp_etfdata) ### Needs to change to accept inputs
        
        if temp_holdings is not None:
            etf_to_stock[etf_ticker] = temp_holdings
        
        else:
            print("warning: etf holdings not found for ",etf_ticker)

    return etf_to_stock

 
def etf_holdings_alpha_vantage(etf_ticker, etfdata):
    """
    Retrieve the constituent stocks of an ETF using Alpha Vantage and calculate the investment amount in each.

    Parameters:
    etf_ticker (str): The ticker symbol of the ETF.
    allocation (float): The total amount allocated to the ETF.
    api_key (str): Alpha Vantage API key.

    Returns:
    DataFrame: A Pandas DataFrame containing the holdings' tickers, names, weights, and investment amounts.
    """
    data = etfdata
    
    if "holdings" not in data or not data["holdings"]:
        print(f"No holdings data available for {etf_ticker}.")
        return None

    # Convert JSON holdings data to DataFrame
    holdings_list = data["holdings"]
    df = pd.DataFrame(holdings_list)

    # Convert weight from string to decimal
    df["weight"] = df["weight"].astype(float)
    
    # if the sum of percent constituent is not 100%
    # normalize the weights to ultimately be equal to 100
    ###
    ### need to update and check the issue with non 100% weights
    if sum(df.weight) != 1:
        print("portfolio weights did not add up to 100% for ",etf_ticker,". Total weight is: ", sum(df.weight)*100)
        df.weight = df.weight/sum(df.weight)
    
    # Rename columns for clarity
    df.rename(columns={"symbol": "ticker", "description": "name"}, inplace=True)

    return df[["ticker", "name", "weight"]] # excluding- , "allocation"


#%% MARKET DATA

META_FILE = "etf_metadata.json"

def load_meta():
    """Load ETF metadata from a file (if exists) to prevent redundant API calls."""
    if os.path.exists(META_FILE):
        with open(META_FILE, "r") as file:
            return json.load(file)
    return {}

def save_meta(meta_data):
    """Save ETF metadata to a file for later use."""
    with open(META_FILE, "w") as file:
        json.dump(meta_data, file, indent=4)

def get_etfdata__alpha_vantage(etf_ticker, api_key='KZDZF6D34D3E50IG'):
    """
    Retrieve the information of ETF using Alpha Vantage

    Parameters:
    etf_ticker (str): The ticker symbol of the ETF.
    allocation (float): The total amount allocated to the ETF.
    api_key (str): Alpha Vantage API key.

    Returns:
    Data: A dictionary/object containing the ETF info such as holdings, sectors, etc.
    """
    url = f"https://www.alphavantage.co/query"
    params = {
        "function": "ETF_PROFILE",
        "symbol": etf_ticker,
        "apikey": api_key
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"Failed to fetch holdings for {etf_ticker}. HTTP Status Code: {response.status_code}")
        return None
    
    etfdata = response.json()
    
    return etfdata


# Meta data function to store all the etf info from API pull
def store_etf_metadata(etf_list, api_key='KZDZF6D34D3E50IG'):
    """
    Fetch and store ETF data for multiple ETFs in a metadata dictionary.

    Parameters:
    etf_list (list): List of ETF ticker symbols.
    api_key (str): Alpha Vantage API key.

    Returns:
    dict: Updated meta_data dictionary containing ETF data.
    """
    # Load existing metadata
    meta_data = load_meta()

    for etf_ticker in etf_list:
        if etf_ticker in meta_data:
            print(f"{etf_ticker} already exists in metadata. Skipping API call.")
            continue  # Skip already stored ETFs

        # Fetch ETF data
        etf_data = get_etfdata__alpha_vantage(etf_ticker, api_key)
        
        if etf_data:
            meta_data[etf_ticker] = etf_data  # Store ETF data in the dictionary
            print(f"Stored metadata for {etf_ticker}.")
        else:
            print(f"Failed to retrieve data for {etf_ticker}. Skipping storage.")

    # Save updated metadata to file
    save_meta(meta_data)

    return meta_data