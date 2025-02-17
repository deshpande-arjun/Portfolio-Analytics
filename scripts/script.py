#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 12:06:22 2025

@author: arjundeshpande
"""



#%% Rough Work
from config import class_dir, data_dir, wd
import pandas as pd
import os
import sys
# import requests
# import json

# Add `classes/` directory to Python's module search path
sys.path.append(class_dir)

# Import necessary classes
from market_data import MarketData
from portfolio_calculations import PortfolioCalculations
from portfolio_decomposer import PortfolioDecomposer

# Actual curated report from IBKR of current positions:
port_file = os.path.join(data_dir, "CurrentPositions_1.31.2025.csv")
real_port = pd.read_csv(port_file) # read excel to get current portfolio positions
etf_list = [x for x in real_port.Symbol[real_port.SubCategory=='ETF']] # filter the etf list from portfolio
#stock_list = [x for x in real_port.Symbol[real_port.SubCategory=='COMMON']] # filter the etf list from portfolio

db_name=os.path.join(data_dir, "stocks.db")
meta_file=os.path.join(data_dir, "etf_metadata.json")
market_data = MarketData(db_name,meta_file)

#etf_sectors_dict = market_data.get_etf_sectors()
#etf_holdings_dict = market_data.get_etf_holdings()

port_decomposer = PortfolioDecomposer(real_port, market_data)

port_to_stocks = port_decomposer.decompose_stocks()

