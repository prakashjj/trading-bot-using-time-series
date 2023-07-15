##################################################
##################################################

# Start code:

print()

##################################################
##################################################

print("Init code: ")
print()

##################################################
##################################################

print("Test")
print()

##################################################
##################################################

# Import modules:

import math
import time
import numpy as np
import requests
import talib
import json
import datetime
from datetime import timedelta
from decimal import Decimal
import decimal
import random
import statistics
from statistics import mean

##################################################
##################################################

# binance module imports
from binance.client import Client as BinanceClient
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.enums import *

##################################################
##################################################

# Load credentials from file
with open("credentials.txt", "r") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    api_secret = lines[1].strip()

# Instantiate Binance client
client = BinanceClient(api_key, api_secret)

##################################################
##################################################

# Define a function to get the account balance in BUSD

def get_account_balance():
    accounts = client.futures_account_balance()
    for account in accounts:
        if account['asset'] == 'BUSD':
            bUSD_balance = float(account['balance'])
            return bUSD_balance

# Get the USDT balance of the futures account
bUSD_balance = float(get_account_balance())

# Print account balance
print("BUSD Futures balance:", bUSD_balance)
print()

##################################################
##################################################

# Define Binance client reading api key and secret from local file:

def get_binance_client():
    # Read credentials from file    
    with open("credentials.txt", "r") as f:   
         lines = f.readlines()
         api_key = lines[0].strip()  
         api_secret = lines[1].strip()  
          
    # Instantiate client        
    client = BinanceClient(api_key, api_secret)
          
    return client

# Call the function to get the client  
client = get_binance_client()

##################################################
##################################################

# Initialize variables for tracking trade state:

TRADE_SYMBOL = "BTCUSDT"

##################################################
##################################################

# Define timeframes and get candles:

timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h',  '6h', '8h', '12h', '1d']

def get_candles(symbol, timeframes):
    candles = []
    for timeframe in timeframes:  
        klines = client.get_klines(
            symbol=symbol, 
            interval=timeframe,  
            limit=1000  
        )
        # Convert klines to candle dict
        for k in klines:
            candle = {
                "time": k[0] / 1000,   
                "open": float(k[1]), 
                "high": float(k[2]),   
                "low": float(k[3]),    
                "close": float(k[4]),   
                "volume": float(k[5]), 
                "timeframe": timeframe    
            }
            candles.append(candle)    
    return candles

# Get candles  
candles = get_candles(TRADE_SYMBOL, timeframes) 
#print(candles)

# Organize candles by timeframe        
candle_map = {}  
for candle in candles:
    timeframe = candle["timeframe"]  
    candle_map.setdefault(timeframe, []).append(candle)

#print(candle_map)

##################################################
##################################################

def get_close(timeframe):
    # Get candles for this specific timeframe
    candles = candle_map[timeframe]
    
    # Get close of last candle    
    close = candles[-1]['close']
    
    return close

##################################################
##################################################

# Get close price as <class 'float'> type

close = get_close('1m')
#print(close)

##################################################
##################################################

# Get entire list of close prices as <class 'list'> type

def get_closes(timeframe):
    closes = []
    candles = candle_map[timeframe]
    
    for c in candles:
        close = c['close']
        if not np.isnan(close):     
            closes.append(close)
            
    return closes

closes = get_closes('1m')
#print(type(closes))

##################################################
##################################################

# Get SMA for all timeframes and for all intervals lengths

def get_sma(timeframe, length):
   closes = get_closes(timeframe)  
    
   sma = talib.SMA(np.array(closes), timeperiod=length)

   # Filter out NaN  
   sma = sma[np.isnan(sma) == False]
      
   return sma

# Call the function
sma_lengths = [5, 12, 21, 27, 56, 72, 100, 150, 200, 250, 369]

#for timeframe in timeframes:
#    for length in sma_lengths:
#       sma = get_sma(timeframe, length)
#       print(f"SMA {length} for {timeframe}: {sma}")

print()

##################################################
##################################################

def get_sma_diff(timeframe, length):
    close = get_close(timeframe)
    sma = get_sma(timeframe, length)[-1]
    
    diff = (close - sma) / sma * 100 if sma != 0 else 0
    
    position = "CLOSE ABOVE" if close > sma else "CLOSE BELOW"
    
    return diff, position

# Call the function   
for timeframe in timeframes:
    for length in sma_lengths:
       
       # Get close price
       close = get_close(timeframe)
       
       # Get SMA 
       sma = get_sma(timeframe, length)[-1]
       
       # Calculate % diff from close  
       close_diff = (close - sma) / sma * 100  
       
       # Initialize diff arrays 
       sma_diffs = []
       sma_values = []
           
       # Get SMA value for all lengths 
       for l in sma_lengths:
           sma_value = get_sma(timeframe, l)[-1]
           sma_values.append(sma_value)
           
       # Calculate diff between all SMAs       
       for i in range(len(sma_values)-1):
           sma_diff = abs(sma_values[i] - sma_values[i+1])
           sma_diffs.append(sma_diff)
            
       # Calculate average SMA diff     
       avg_sma_diff = mean(sma_diffs)       
         
##################################################
##################################################

def get_sma_ratio(timeframe):    
    above_ratios = []    
    below_ratios = []
    
    for length in sma_lengths:
         diff, position = get_sma_diff(timeframe, length)
          
         if position == "CLOSE ABOVE":
             above_ratios.append(diff)
         else:  
             below_ratios.append(diff)
            
    if above_ratios:        
        above_avg = statistics.mean(above_ratios)
    else:
        above_avg = 0
        
    if below_ratios:                
        below_avg = statistics.mean(below_ratios)          
    else:
        below_avg = 0
            
    return above_avg, below_avg

# Call the function
for timeframe in timeframes:
    above_avg, below_avg =  get_sma_ratio(timeframe)
    
    if below_avg > above_avg:
        print(f"{timeframe} Close is below SMAs at a local dip")        
    elif above_avg > below_avg:
        print(f"{timeframe} Close is above SMAs at a local top")

print()

##################################################
##################################################

# Scale close prices to sine wave       
def scale_to_sine(timeframe):
    
    # Get close prices    
    close_prices = np.array(get_closes(timeframe))  
        
    # Set sine limits
    sin_min = 0  
    sin_max = 360
        
    # Calculate sine wave    
    sine_wave, _ = talib.HT_SINE(close_prices)   
      
    # Filter NaN     
    sine_wave = np.nan_to_num(sine_wave)
      
    # Invert sine wave        
    sine_wave = -sine_wave  
      
    # Get min/max sine     
    min_sine = np.min(sine_wave)       
    max_sine = np.max(sine_wave)
      
    for i in range(len(close_prices)):
      
        # Get close price      
        close = close_prices[i]  
                
        # Calculate sine value from 0-360               
        sine = sin_min + (sin_max - sin_min)*(sine_wave[i] + 1)/2  
                
        # Determine quadrant   
        quadrant = 1 if sine < 90 else 2 if sine < 180 else 3 if sine < 270 else 4 
                
        # Calculate % distance from min/max based on sine    
        dist_to_min = ((sine_wave[i] - min_sine)/(max_sine - min_sine))*100
   
        # Calculate % distance from max sine       
        dist_to_max = ((max_sine - sine_wave[i])/(max_sine - min_sine))*100
        
        print(f"Close: {close} Sine: {sine} "   
              f"Quadrant: {quadrant} " 
              f"Dist. to min: {dist_to_min:.2f}% "  
              f"Dist. to max: {dist_to_max:.2f}%")  
          
# Call function           
for timeframe in timeframes:         
    scale_to_sine(timeframe)
        
for timeframe in timeframes:
    scale_to_sine(timeframe)
