#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 14:56:38 2025

@author: arjundeshpande
"""

import os

system = 'mac'
#system = 'windows'

if system=='mac':
    wd = '/Users/arjundeshpande/Library/Mobile Documents/com~apple~CloudDocs/ETF decomposition/App'
else:
    wd = 'C:\ArjunDesktop\iCloudDrive\ETF decomposition\App'

os.chdir(wd)

data_dir = os.path.join(wd, "data")

class_dir = os.path.join(wd, "classes")

script_dir = os.path.join(wd, "scripts")

os.chdir(script_dir)