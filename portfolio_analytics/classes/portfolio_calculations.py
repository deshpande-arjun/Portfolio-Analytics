#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 12:02:51 2025

@author: arjundeshpande
"""

import pandas as pd
import numpy as np

class PortfolioCalculations:
    """
    Processes market data for financial calculations such as returns, volatility, and correlation.
    """

    @staticmethod
    def calculate_returns(price_data):
        """Compute daily log returns."""
        return np.log(price_data / price_data.shift(1)).dropna()

    @staticmethod
    def calculate_volatility(price_data, window=30):
        """Compute rolling volatility."""
        return price_data.pct_change().rolling(window=window).std()

    @staticmethod
    def calculate_correlation(price_data):
        """Compute correlation matrix for assets."""
        return price_data.pct_change().corr()
