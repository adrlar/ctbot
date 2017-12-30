from __future__ import division
import time
import sys
import argparse
import datetime

import numpy as np
import plotly as py
import plotly.graph_objs as go

from poloniex import poloniex
from keys import adrlar_key, adrlar_secret
from ctbot_helpers import init_variables, send_email
from ctbot_math import *

def update_math(variables, period):
    variables[period] = calc_macd(variables[period])
    variables[period] = calc_rsi(variables[period], 14)
    variables[period] = calc_bollinger(variables[period], 20, 2)
    return variables

def live_setup(polo, variables, periods, pair):
    # Get initial candles
    for period in sorted(periods, reverse=True):
        print "Getting data for {}s period for {}...".format(period, pair)
        t_now = int(time.time())
        tmp = polo.api_query("returnChartData",{"currencyPair":pair,"start":t_now-period*205,"end":t_now,"period":period})["candleStick"][-201:-1]
        # Grabbing the 100 last candles (not the very last, it is still being "worked on")
        variables[period]['all_candles'] = tmp
        #variables[period]['roll_candles'] = variables[period]['roll_candles'][-100:]
        variables[period]['len_candles'] = len(variables[period]['all_candles'])
        # Fill in all the temporary values so that there is something to plot and to start calculations with
        for i in range(len(tmp)):
            variables[period]['all_dates'].append(datetime.datetime.utcfromtimestamp(int(tmp[i]['date'])).strftime('%Y-%m-%d %H:%M:%S'))
            variables[period]['all_close_prices'].append(tmp[i]['close'])
            if i > 56:
                variables = update_math(variables, period)
                #variables = model(variables, period)
            else:
                for j in ['all_macd', 'all_macd_signal', 'all_macd_hist', 'all_rsi', 'all_rsi_d', 'all_rsi_u', 'all_score', 'all_rsi_score', 'all_macd_score']:
                    variables[period][j].append(0)
                variables[period]['all_bollinger'].append([0,0])
    return variables


pairs = [
        "USDT_BTC",
        "USDT_ETH",
        "USDT_ZEC",
        "USDT_LTC",
        "USDT_ETC",
        "USDT_XRP",
        "USDT_BCH",
        "USDT_XMR",
        "USDT_DASH",
        "USDT_NXT",
        "USDT_STR"
]
#"USDT_REP"

pair_data = dict()
polo = poloniex(adrlar_key, adrlar_secret)
periods = [300, 900, 1800]


for pair in pairs:
    variables = init_variables()
    variables = live_setup(polo, variables, periods, pair)
    variables['live'] = True
    pair_data[pair] = variables
    time.sleep(3)
time.sleep(10)
while True:
    for pair in pairs:
        current_tick = polo.api_query("returnTicker")
        current_time_str = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        t_now = int(time.time())

        for period in periods:
            #print variables[period]['all_candles'][-1]
            if t_now > pair_data[pair][period]['all_candles'][-1]['date'] + 2*period: # Checking if its time to get a new candle
                # Get new candle
                # Getting the second to last candle, cause the last one is still being "worked on"
                #print pair, period
                for tries in xrange(5):
                    try:
                        tmp = polo.api_query("returnChartData",{"currencyPair":pair,"start":t_now-period*5-1,"end":t_now,"period":period})["candleStick"][-2]
                        break
                    except IndexError:
                        print polo.api_query("returnChartData",{"currencyPair":pair,"start":t_now-period*5-1,"end":t_now,"period":period})["candleStick"]
                        print "ERROR", pair, period, t_now-period*5-1, t_now, tries
                    time.sleep(3)
                if pair_data[pair][period]['all_candles'][-1] != tmp: # This would mean the newest candle is the same we have if they were equal
                    pair_data[pair][period]['all_dates'].append(datetime.datetime.utcfromtimestamp(int(tmp['date'])).strftime('%Y-%m-%d %H:%M:%S'))
                    pair_data[pair][period]['all_candles'].append(tmp)
                    pair_data[pair][period]['all_close_prices'].append(tmp['close'])
        
        # Want to get all information before running model
        new_tick = False
        for period in periods:
            if len(pair_data[pair][period]['all_candles']) > pair_data[pair][period]['len_candles']:
                new_tick = True
                pair_data[pair] = update_math(pair_data[pair], period)
                #pair_data[pair] = model(pair_data[pair], period)
                pair_data[pair][period]['len_candles'] = len(pair_data[pair][period]['all_candles'])
                #draw(pair_data[pair], period)
        if new_tick:
            if pair_data[pair][300]['all_rsi'][-1] < 30 and pair_data[pair][900]['all_rsi'][-1] < 30 and pair_data[pair][1800]['all_rsi'][-1] < 30:
                print pair, pair_data[pair][300]['all_rsi'][-1], pair_data[pair][900]['all_rsi'][-1], pair_data[pair][1800]['all_rsi'][-1]
                #alerts(pair_data[pair])

        checker_time = min([pair_data[pair][period]['all_candles'][-1]['date'] - int(time.time()) + period*2 + 1 for p in periods])
        sleep_time = max(checker_time, 10) # To never sleep less than 10s
        #print "{} Sleeping {}s. Current price {} USD".format(current_time_str, sleep_time, round(float(current_tick[pair]['last']), 2))
        #print t_now
        time.sleep(5)

    #print "sleeping 30"
    #time.sleep()
'''
for pair in pairs:
    
    history_data = {}
    for period in periods:
        tmp = polo.api_query("returnChartData",{"currencyPair":pair,"start":1500542000-period*200,"end":1506720000,"period":period})["candleStick"]
        history_data[period] = tmp

    t_now_hist = int(history_data[1800][0]['date'])
    t_last = int(history_data[300][-1]['date'])
    variables['live'] = False

    print t_now_hist, t_last

    flag =True
    saved_candles = []
    totals = []
    top_totals = []
    sum_neg = 0
    sum_pos = 0
    sum_totals = []

    while t_now_hist <= t_last:
        for period in periods:
            if history_data[period] and t_now_hist >= int(history_data[period][0]['date']):
                variables[period]['all_dates'].append(datetime.datetime.utcfromtimestamp(int(history_data[period][0]['date'])).strftime('%Y-%m-%d %H:%M:%S'))
                variables[period]['all_candles'].append(history_data[period][0])
                variables[period]['all_close_prices'].append(history_data[period][0]['close'])
                if len(variables[period]['all_dates']) > 56:
                    variables = update_math(variables, period)
                    #variables = model(variables, period)
                else:
                    for j in ['all_macd', 'all_macd_signal', 'all_macd_hist', 'all_rsi', 'all_rsi_d', 'all_rsi_u', 'all_score', 'all_rsi_score', 'all_macd_score']:
                        variables[period][j].append(0)
                    variables[period]['all_bollinger'].append([0,0])
                history_data[period].pop(0)
        if len(variables[300]['all_candles'])> 200:
            variables['live'] = True
        t_now_hist += 300

        if variables['live']:
            if flag:
                if variables[300]['all_rsi'][-1] < 30 and variables[900]['all_rsi'][-1] < 30 and variables[1800]['all_rsi'][-1] < 30:
                    flag = False
                    count = 0
                    saved_price = float(variables[300]['all_close_prices'][-1])
                    #print "\nLONG TIME??", variables[300]['all_rsi'][-1], variables[900]['all_rsi'][-1], variables[1800]['all_rsi'][-1], t_now_hist, variables[300]['all_close_prices'][-1]
            else:
                saved_candles.append(variables[300]['all_close_prices'][-1])
                count +=1
                if count > 9:
                    #print saved_candles, max(saved_candles)-saved_price, sum(saved_candles)/5-saved_price, min(saved_candles)-saved_price, saved_price
                    totals.append((sum(saved_candles)/10-saved_price)/saved_price)
                    for i in saved_candles:
                        if i-saved_price > 0:
                            sum_pos +=1
                        else:
                            sum_neg +=1
                    #print max(saved_candles)-saved_price, saved_price
                    top_totals.append((max(saved_candles)-saved_price)/saved_price)
                    sum_totals.append([sum_pos, sum_neg])
                    count = 0
                    saved_candles = []
                    flag = True
                    sum_pos = 0
                    sum_neg = 0
        
    print pair
    print sum_totals
    print sum(totals)
    #print top_totals
    print sum(top_totals)
'''




















