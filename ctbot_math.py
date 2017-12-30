'''
Math functions for ctbot
'''
from __future__ import division
import numpy as np
#import time

def calc_ema(prices, n):
    if len(prices) < 2 * n:
        raise ValueError("Price list is too short")
    if len(prices) > 500:
        prices = prices[-500:]
    c = 2.0 / (n + 1)

    current_ema = prices[0] #testing with using all values to calc ema and mma

    for value in prices[1:]:
        current_ema = (c * value) + ((1 - c) * current_ema)
    return current_ema

def calc_mma(prices, n):
    if len(prices) < 2 * n:
        raise ValueError("Price list is too short")
    if len(prices) > 500:
        prices = prices[-500:]
    c = 1 / n
    current_mma = prices[0]
    for value in prices[1:]:
        current_mma = (c * value) + ((1 - c) * current_mma)
    return current_mma


def calc_macd(variables):
    macd_12 = calc_ema(variables['all_close_prices'], 12)
    macd_26 = calc_ema(variables['all_close_prices'], 26)
    macd = macd_12 - macd_26
    
    variables['all_macd'].append(macd)

    #can only calc signal if there are more than 9 macd values
    macd_signal = 0
    macd_hist = 0
    if len(variables['all_macd']) > 18:
        macd_signal = calc_ema(variables['all_macd'], 9)
        macd_hist = macd - macd_signal
    
    variables['all_macd_signal'].append(macd_signal)
    variables['all_macd_hist'].append(macd_hist)

    return variables

def calc_rsi(variables, n=14):
    if variables['all_close_prices'][-1] > variables['all_close_prices'][-2]:
        rsi_u = variables['all_close_prices'][-1] - variables['all_close_prices'][-2]
        rsi_d = 0
    elif variables['all_close_prices'][-1] < variables['all_close_prices'][-2]:
        rsi_u = 0
        rsi_d = variables['all_close_prices'][-2] - variables['all_close_prices'][-1]
    else:
        rsi_u = 0
        rsi_d = 0
    
    variables['all_rsi_d'].append(rsi_d)
    variables['all_rsi_u'].append(rsi_u)
   
    if len(variables['all_rsi_d']) > n*2:
        rsi_d_mov_avg = calc_mma(variables['all_rsi_d'], n)
        rsi_u_mov_avg = calc_mma(variables['all_rsi_u'], n)
    else:
        rsi_d_mov_avg = 0
        rsi_u_mov_avg = 0

    if rsi_d_mov_avg != 0:
        rs = rsi_u_mov_avg/rsi_d_mov_avg
    else:
        rs = 10000 #large number 
    rsi = 100 - (100/(1+rs))

    variables['all_rsi'].append(rsi)
    
    return variables

def calc_bollinger(variables, k=20, n=2):
    numpy_prices = np.array(variables['all_close_prices'][-k:])

    ema = calc_ema(variables['all_close_prices'], k)
    current_bollinger = n*np.std(numpy_prices)
    variables['all_bollinger'].append([current_bollinger, ema])

    return variables

def list_scalar_multiplication(l, n):
    new_l = list()
    for i in l:
        if i != None:
            new_l.append(i*n)
        else:
            new_l.append(None)
    return new_l
