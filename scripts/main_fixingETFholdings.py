#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 12:06:22 2025

@author: arjundeshpande
"""



#%% Main script
from config import Class_dir, Data_dir, Base_dir, Portfolio_file

import pandas as pd
import os
import sys
# import requests
# import json

# Add `classes/` directory to Python's module search path
sys.path.append(Class_dir)

# Import necessary classes
from classes import MarketData, PortfolioDecomposer, PortfolioCalculations

# Initialize MarketData
db_name=os.path.join(Data_dir, "stocks.db")
meta_file=os.path.join(Data_dir, "etf_metadata.json")
market_data = MarketData(db_name,meta_file)

# Load Portfolio DataFrame
if os.path.exists(Portfolio_file):
    portfolio = pd.read_csv(Portfolio_file)
    print("Portfolio data loaded successfully.")
else:
    raise FileNotFoundError(f"Portfolio file not found: {Portfolio_file}")

etf_list = [x for x in portfolio.Symbol[portfolio.SubCategory=='ETF']] # filter the etf list from portfolio
#stock_list = [x for x in real_port.Symbol[real_port.SubCategory=='COMMON']] # filter the etf list from portfolio
# etf_sectors_dict = market_data.get_etf_sectors()
# etf_holdings_dict = market_data.get_etf_holdings()

port_decomposer = PortfolioDecomposer(portfolio, market_data)

port_to_stocks = port_decomposer.decompose_stocks()

# pull stock data from the database:
port_to_stocks_tickerlist = [x for x in port_to_stocks.ticker] # filter the etf list from portfolio
stock_data = market_data.get_stock_data(port_to_stocks_tickerlist)
    
#port_to_sectors, 
port_to_stocks,port_to_sectors = port_decomposer.decompose_sectors()

extra_ticker = port_to_stocks[~port_to_stocks["ticker"].isin(stock_data["ticker"])]
missing_rows = port_to_stocks[~port_to_stocks["ticker"].isin(stock_data["ticker"])]

missing_tickers = port_to_stocks[~port_to_stocks["ticker"].isin(stock_data["ticker"])]
print(f"Missing Tickers Count: {len(missing_tickers)}")
print("Missing Tickers:", missing_tickers["ticker"].tolist())


#%% rough work


def map_to_gics_sector(label):
     """Maps sector labels from Yahoo Finance! to Official GICS sector names.
        This function is coded based on the YF names, might need to be updated
        if the data source is changed.        
     """
     
     mapping = {
         "Healthcare": "Health Care",
         "Basic Materials": "Materials",
         "Financial Services": "Financials",
         "Technology": "Information Technology",
         "Consumer Cyclical": "Consumer Discretionary",
         "Consumer Defensive": "Consumer Staples",
         "N/A": "Unknown Unmapped",
         }
     
     return mapping.get(label, "Unknown Unmapped")  # Default to "Unknown Unmapped" if not found
       
    
#    def decompose_sectors(self):
"""Convert ETF positions into sector allocations."""
port_to_stocks = port_decomposer.decompose_stocks().copy()
port_to_stocks_tickerlist = [x for x in port_to_stocks.ticker] # filter the etf list from portfolio
# get the stock data including sector names from YFinance
stock_data = market_data.get_stock_data(port_to_stocks_tickerlist) 


if stock_data.empty or "sector" not in stock_data.columns:
    raise ValueError("❌ ERROR: stock_data is empty or missing 'sector' column.")

# standardize the sectors using the official GICS Sector names:
stock_data["gics_sector"] = stock_data["sector"].apply(map_to_gics_sector)

# Add the GICS sector to the existing port_to_stock:
port_to_stocks = pd.merge(port_to_stocks, stock_data, on=["ticker"])  #, "name"
port_to_stocks = port_to_stocks[['ticker', 'name_x', 'allocation', 'port_weight','gics_sector' ]]

port_to_sectors = port_to_stocks.groupby(['gics_sector'], as_index= False).agg({
    'allocation': 'sum'}) #, 'port_weight': 'sum' 
port_to_sectors['port_weight'] = port_to_sectors["allocation"]/port_to_sectors["allocation"].sum()





import sqlite3
stock_list = [x for x in portfolio.Symbol[portfolio.SubCategory=='COMMON']] # filter the etf list from portfolio
conn = sqlite3.connect(db_name)  # Connect to the database

# Convert stock_list into a format for SQL IN clause
placeholders = ','.join(['?'] * len(stock_list))
query = f"SELECT * FROM stock_universe WHERE ticker IN ({placeholders})"

# Fetch data as a Pandas DataFrame
df = pd.read_sql_query(query, conn, params=stock_list)

conn.close() 
