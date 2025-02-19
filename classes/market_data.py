#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 12:01:54 2025

@author: arjundeshpande
"""

import sqlite3
import requests
import yfinance as yf
import json
import os
from datetime import datetime
import pandas as pd

class MarketData:
    """
    Manages database creation, updates, and refresh policies for stock universe & ETF data.
    Also fetches data from Alpha Vantage, Yahoo Finance, and other APIs.
    """

    def __init__(self, db_name="stocks.db", meta_file="etf_metadata.json", av_api_key="KZDZF6D34D3E50IG"):
        self.db_name = db_name
        self.meta_file = meta_file
        self.api_key = av_api_key
        self.meta_data = self.load_meta()

    # 🔹 Load ETF Metadata from File
    def load_meta(self):
        """Load ETF metadata from a file."""
        if os.path.exists(self.meta_file):
            with open(self.meta_file, "r") as file:
                return json.load(file)
        return {}

    # 🔹 Save ETF Metadata to File
    def save_meta(self):
        """Save ETF metadata to a file."""
        with open(self.meta_file, "w") as file:
            json.dump(self.meta_data, file, indent=4)

    # 🔹 Fetch Stock Data from Yahoo Finance
    def _fetch_yfinance_stock_info(self, ticker):
        """Fetch stock details from Yahoo Finance."""
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "currency": info.get("currency", "N/A"),
            "exchange": info.get("exchange", "N/A"),
            "dividend_yield": info.get("dividendYield", 0),
            "pe_ratio": info.get("trailingPE", None),
            "beta": info.get("beta", None),
            "high_52_week": info.get("fiftyTwoWeekHigh", None),
            "low_52_week": info.get("fiftyTwoWeekLow", None),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    # 🔹 Fetch ETF Data from Alpha Vantage
    def _fetch_alphavantage_etf_data(self, etf_ticker):
        """Retrieve ETF holdings from Alpha Vantage."""
        url = "https://www.alphavantage.co/query"
        params = {"function": "ETF_PROFILE", "symbol": etf_ticker, "apikey": self.api_key}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        return None
    
    # 🔹 Store Stock Universe Database
    def store_stock_info(self, tickers, refresh_days=30):
        """Create or update the stock universe database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS stock_universe (
            ticker TEXT PRIMARY KEY, name TEXT, sector TEXT, last_updated TEXT)''')

        cursor.execute("SELECT ticker, last_updated FROM stock_universe")
        existing_data = {row[0]: row[1] for row in cursor.fetchall()}
        outdated_tickers = [t for t, last_updated in existing_data.items() 
                            if (datetime.now() - datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S")).days >= refresh_days]

        tickers_to_fetch = [t for t in tickers if t not in existing_data or t in outdated_tickers]

        for ticker in tickers_to_fetch:
            stock_data = self._fetch_yfinance_stock_info(ticker)
            cursor.execute('''INSERT INTO stock_universe (ticker, name, sector, last_updated)
                              VALUES (?, ?, ?, ?) ON CONFLICT(ticker) DO UPDATE SET 
                              name=excluded.name, sector=excluded.sector, last_updated=excluded.last_updated''',
                           (ticker, stock_data["name"], stock_data["sector"], stock_data["last_updated"]))

        conn.commit()
        conn.close()



    # 🔹 Store ETF Metadata in File
    def store_etf_data(self, etf_list):
        """Fetch multiple ETF data from Alpha Vantage and store ETF metadata."""
        for etf_ticker in etf_list:
            if etf_ticker in self.meta_data:
                print(f"{etf_ticker} already exists in metadata. Skipping API call.")
                continue  

            etf_data = self._fetch_alphavantage_etf_data(etf_ticker)
            if etf_data:
                self.meta_data[etf_ticker] = etf_data  
                print(f"Stored metadata for {etf_ticker}.")
            else:
                print(f"Failed to retrieve data for {etf_ticker}.")

        self.save_meta()
        
    def _process_etf_data(self, parameter):
        etf_metadata_dict = self.get_etf_metadata()
        etf_tickers = list(etf_metadata_dict.keys())
        etf_dict = {}
        for ticker in etf_tickers:
            data = etf_metadata_dict[ticker].get(parameter, [])
            
            df = pd.DataFrame(data)
            # Convert numeric columns to float
            df = df.apply(pd.to_numeric, errors='ignore')

            if not df.empty:
                etf_dict[ticker] = df
            else:
                print(parameter," data not available for ",ticker)
        
        return etf_dict
    
    def get_etf_holdings(self, parameter = "holdings"):
        etf_dict = self._process_etf_data(parameter)
        etf_dict = {
            key: df.rename(columns={"symbol": "ticker", "description": "name"})
            for key, df in etf_dict.items()
            }

        return etf_dict
    
    
    def get_etf_sectors(self, parameter = "sectors"):
        return self._process_etf_data(parameter)
    
    
    def get_etf_metadata(self):
        """get etf meta data from meta data"""
        etf_metadata = self.meta_data
        
        etf_list = list(etf_metadata.keys())
        etf_metadata_dict = {}
        for ticker in etf_list:
            df = etf_metadata[ticker]
            
            if not df:
                print("etf not in the data base",{ticker})
            else:
                etf_metadata_dict[ticker] =df
        
        return etf_metadata_dict
    
    def get_stock_data(self, stock_list):
        """get stock data from database"""
        conn = sqlite3.connect(self.db_name)  # Connect to the database
    
        # Convert stock_list into a format for SQL IN clause
        placeholders = ','.join(['?'] * len(stock_list))
        query = f"SELECT * FROM stock_universe WHERE ticker IN ({placeholders})"
    
        # Fetch data as a Pandas DataFrame
        df = pd.read_sql_query(query, conn, params=stock_list)
    
        conn.close()  # Close the database connection
    
        return df



# =============================================================================
#     def get_etf_metadata(self, etf_list):
#         """get etf meta data from data base"""
#         conn = sqlite3.connect(self.meta_data)
#         #cursor = conn.cursor() # not used here, can be used instead of pd.read_sql
# 
#         etf_metadata_dict = {}
#         query = "SELECT * FROM meta_data WHERE ticker=?" #similar to sql query ? will be replace by a variable ticker
#         
#         for ticker in etf_list:
#             # Query database for the ETF's metadata
#             df = pd.read_sql(query,conn, params=(ticker,))
#             # Store the result in dictionary (only if data exists)
#             if not df.empty:
#                 etf_metadata[ticker] = df
# 
#         conn.close()
#         return etf_metadata_dict
# =============================================================================
# =============================================================================
#         stock_universe = self.db_name
#         stock_data = stock_universe[stock_universe["ticker"].isin(stock_list)]
#         #for ticker in stock_list:
#         return stock_data
#             
# =============================================================================
