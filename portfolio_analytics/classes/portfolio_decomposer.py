#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 12:04:16 2025

@author: arjundeshpande
"""
import pandas as pd

class PortfolioDecomposer:
    """
    Decomposes ETF and stock positions into sector allocations.
    """

    def __init__(self, port, market_data):
        self.port = port.copy()
#        self.stock_universe = stock_universe
        #self.market_data  = market_data
        self.etf_sectors_dict  = market_data.get_etf_sectors() 
        self.etf_holdings_dict = market_data.get_etf_holdings()

    def decompose_stocks(self):
#    port_decomp_stocks(port, etf_holdings_dict):
        """
        To decompose the ETF positions into constituent stock positions
        
        inputs:
        port: dataframe of all ETFs and stocks that are held in the portfolio
        etf_holdings_dict: dictionary of dataframes with stock holdings for each ETF
        
        output:
        etf_to_stock: dataframe of all stock positions decomposed from ETF positions
        
        """
        #port = port.copy()
        
        #rename columns:
        self.port = self.port.rename(columns={"Symbol": "ticker", "Description": "name"})  # , "positionvalue": "allocation" 
        
        # creating a list of ETFs with available holdings data
        port_etf = pd.DataFrame(self.etf_holdings_dict.keys(), columns=['ticker'])
        
        # separate stock and etf 
        port_stock = self.port[~self.port.ticker.isin(port_etf["ticker"])]
        port_etf = pd.merge(port_etf,self.port, on='ticker')
    
        
        # Decomposing ETF into stocks:
        decomposed_etf = []
        for etf_ticker, position_value in zip(port_etf.ticker, port_etf.PositionValue):
            
            temp_df = self.etf_holdings_dict[etf_ticker].copy()  # pull holdings of the etf from etf_data
            temp_df["allocation"] = temp_df["weight"] * position_value # allocation of each stock
            
            decomposed_etf.append(temp_df) # append the stocks in each iteration
        
    
        port_stock = port_stock.rename(columns={"PositionValue": "allocation"})
        port_stock = port_stock[["ticker", "name", "allocation"]]  #remove unnecessary columns
        
        decomposed_etf.append(port_stock) # append stocks to decomposed etf 
        merged_df = pd.concat(decomposed_etf) #concat lists into a df
        # groupby on ticker and name, then sum allocations from all etfs
        merged_df = merged_df.groupby(['ticker', 'name'], as_index= False).agg({'allocation': 'sum'})
        merged_df['port_weight'] = merged_df["allocation"]/merged_df["allocation"].sum()
        
        return merged_df
    
    def decompose_sectors(self,stock_universe):
        """Convert ETF positions into sector allocations."""
        self.port = self.port.rename(columns={"Symbol": "ticker", "Description": "name"})

        port_etf = pd.DataFrame(self.etf_sectors_dict.keys(), columns=['ticker'])
        port_stock = self.port[~self.port["ticker"].isin(port_etf["ticker"])].copy()
        port_etf = pd.merge(port_etf, self.port, on="ticker").copy()

        decomposed_etf = []
        for etf_ticker, position_value in zip(port_etf["ticker"], port_etf["PositionValue"]):
            temp_df = self.etf_sectors_dict[etf_ticker].copy()
            temp_df["allocation"] = temp_df["weight"] * position_value
            decomposed_etf.append(temp_df)

        port_stock = port_stock.rename(columns={"PositionValue": "allocation"}).copy()
        port_stock = pd.merge(port_stock, stock_universe, on="ticker", how="inner").copy()
        port_stock = port_stock[["sector", "allocation"]]

        decomposed_etf.append(port_stock)
        merged_df = pd.concat(decomposed_etf, ignore_index=True)
        merged_df = merged_df.groupby(["sector"], as_index=False).agg({"allocation": "sum"})
        merged_df["port_weight"] = merged_df["allocation"] / merged_df["allocation"].sum()
        return merged_df