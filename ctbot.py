#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import time
import sys
import argparse
import datetime
import numpy as np

import plotly as py
import plotly.graph_objs as go

# Local files 
# poloniex API and API keys for account
# helper_functions random functions moved for readability
# math all the math functions
from poloniex import poloniex
from ctbot_helpers import init_variables, send_email
from ctbot_math import *
from ctbot_models import *
from keys import adrlar_key, adrlar_secret


def main():
    '''
    Main function. Parses command line args and starts a history run or live ticker. 
    '''
    
    variables = init_variables()

    parser = argparse.ArgumentParser(description="Cryptobot for poloniex, written by Adrian Larkeryd, 2017")
    parser.add_argument("-p", "--pair",
            help="cryptocurrency pair, USDT_BTC, BTC_ETH or BTC_LTC ... etc etc", default="USDT_BTC")
    parser.add_argument("--history",
            help="run a history test, takes two epoch time stamps as parameters: --history 1501542000 "+str(int(time.time())), nargs=2, type=int)
    parser.add_argument("-v", "--verbose", 
            help="increase output verbosity", action="store_true")

    args = parser.parse_args() 
    if args.verbose:
        print args

    variables['pair'] = args.pair

    polo = poloniex(adrlar_key, adrlar_secret)

    if args.history:
        history_run(args.history[0], args.history[1], polo, variables, model_secondbot)
    else:
        print "Setting up with 200 data points in all timeframes..."
        t_tmp = time.time()
        variables = live_setup(polo, variables, model_secondbot)
        print "It took {}s to gather the historical data and crunch the numbers".format(round(time.time()-t_tmp, 2))
        print "\nGOING LIVE!"
        # Start ticker
        variables['live'] = True
        #print len(variables[300]['all_dates']), len(variables[300]['all_score']), len(variables[300]['all_candles']), len(variables[300]['all_close_prices']), len(variables[300]['all_rsi'])
        ticker(polo, variables, model_secondbot)

def live_setup(polo, variables, model):
    # Get initial candles
    for period in sorted(variables['periods'], reverse=True):
        print "Getting data for {}s period...".format(period)
        t_now = int(time.time())
        tmp = polo.api_query("returnChartData",{"currencyPair":variables['pair'],"start":t_now-period*205,"end":t_now,"period":period})["candleStick"][-201:-1]
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
                variables = model(variables, period)
            else:
                for j in ['all_macd', 'all_macd_signal', 'all_macd_hist', 'all_rsi', 'all_rsi_d', 'all_rsi_u', 'all_score', 'all_rsi_score', 'all_macd_score']:
                    variables[period][j].append(0)
                variables[period]['all_bollinger'].append([0,0])
    return variables

def history_run(start_time, end_time, polo, variables, model):
    '''
        Outputs
            None
    '''
    history_data = {}
    for period in variables['periods']:
        tmp = polo.api_query("returnChartData",{"currencyPair":variables['pair'],"start":start_time-period*200,"end":end_time,"period":period})["candleStick"]
        history_data[period] = tmp

    t_now_hist = int(history_data[14400][0]['date'])
    t_last = int(history_data[300][-1]['date'])
    variables['live'] = False

    print t_now_hist, t_last

    while t_now_hist <= t_last:
        for period in variables['periods']:
            if history_data[period] and t_now_hist >= int(history_data[period][0]['date']):
                variables[period]['all_dates'].append(datetime.datetime.utcfromtimestamp(int(history_data[period][0]['date'])).strftime('%Y-%m-%d %H:%M:%S'))
                variables[period]['all_candles'].append(history_data[period][0])
                variables[period]['all_close_prices'].append(history_data[period][0]['close'])
                if len(variables[period]['all_dates']) > 56:
                    variables = update_math(variables, period)
                    variables = model(variables, period)
                else:
                    for j in ['all_macd', 'all_macd_signal', 'all_macd_hist', 'all_rsi', 'all_rsi_d', 'all_rsi_u', 'all_score', 'all_rsi_score', 'all_macd_score']:
                        variables[period][j].append(0)
                    variables[period]['all_bollinger'].append([0,0])
                history_data[period].pop(0)
        if len(variables[300]['all_candles'])> 200:
            variables['live'] = True
        t_now_hist += 300
        
    #print len(variables[300]['all_candles']), len(variables[900]['all_candles']), len(variables[1800]['all_candles']), len(variables[7200]['all_candles']), len(variables[14400]['all_candles'])

    draw(variables, 7200)
    draw(variables, 14400)


def ticker(polo, variables, model):
    '''
        Function that runs the ticker loop. 

        Inputs
            polo: the poloniex API connection
            variables: dictionary with all the variables relevant to execution
            model: the model function to use

        Outputs
            None
    '''
    while True:
        current_tick = polo.api_query("returnTicker")
        current_time_str = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        t_now = int(time.time())

        for period in variables['periods']:
            #print variables[period]['all_candles'][-1]
            if t_now > variables[period]['all_candles'][-1]['date'] + 2*period: # Checking if its time to get a new candle
                # Get new candle
                # Getting the second to last candle, cause the last one is still being "worked on"
                tmp = polo.api_query("returnChartData",{"currencyPair":variables['pair'],"start":t_now-period*3-1,"end":t_now,"period":period})["candleStick"][-2]
                if variables[period]['all_candles'][-1] != tmp: # This would mean the newest candle is the same we have if they were equal
                    variables[period]['all_dates'].append(datetime.datetime.utcfromtimestamp(int(tmp['date'])).strftime('%Y-%m-%d %H:%M:%S'))
                    variables[period]['all_candles'].append(tmp)
                    variables[period]['all_close_prices'].append(tmp['close'])
        
        # Want to get all information before running model
        for period in variables['periods']:
            if len(variables[period]['all_candles']) > variables[period]['len_candles']:
                variables = update_math(variables, period)
                variables = model(variables, period)
                variables[period]['len_candles'] = len(variables[period]['all_candles'])
                draw(variables, period)
                alerts(variables)

        checker_time = min([variables[period]['all_candles'][-1]['date'] - int(time.time()) + period*2 + 1 for period in variables['periods']])
        sleep_time = max(checker_time, 10) # To never sleep less than 10s
        print "{} Sleeping {}s. Current price {} USD".format(current_time_str, sleep_time, round(float(current_tick[variables['pair']]['last']), 2))

        #print t_now
        time.sleep(sleep_time)

def alerts(variables):
    alert = False
    if variables[300]['all_rsi'][-1] < 30 and variables[900]['all_rsi'][-1] < 30 and variables[1800]['all_rsi'][-1] < 30:
        alert = True
        subject = "RSI low"
        message = "5min RSI: {}\n 15min RSI: {}\n 30min RSI: {}".format(variables[300]['all_rsi'][-1], variables[900]['all_rsi'][-1], variables[1800]['all_rsi'][-1])
    if alert:
        send_email(subject, message)

def update_math(variables, period):
    variables[period] = calc_macd(variables[period])
    variables[period] = calc_rsi(variables[period], 14)
    variables[period] = calc_bollinger(variables[period], 20, 2)
    return variables

def draw(variables, period):
    trace_close = go.Scatter(
            x=variables[period]['all_dates'],
            y=variables[period]['all_close_prices'],
            name = "BTC Close",
            line = dict(color = '#6666CC', width=4),
            opacity = 1 
            ) 
    trace_score = go.Scatter(
            x=variables[period]['all_dates'],
            y=variables[period]['all_score'],
            name = "Bot model score",
            line = dict(color = '#06F99D', width=1),
            opacity = 1 
            )
    trace_rsi_score = go.Scatter(
            x=variables[period]['all_dates'],
            y=variables[period]['all_rsi_score'],
            name = "Bot model score",
            line = dict(color = '#06F99D', width=1),
            opacity = 1 
            )
    trace_macd_score = go.Scatter(
            x=variables[period]['all_dates'],
            y=variables[period]['all_macd_score'],
            name = "Bot model score",
            line = dict(color = '#06F99D', width=1),
            opacity = 1 
            )
    trace_rsi = go.Scatter(
            x=variables[period]['all_dates'],
            y=variables[period]['all_rsi'],
            name = "RSI",
            line = dict(color = '#680082'),
            opacity = 1 
            )
    trace_macd = go.Scatter(
            x=variables[period]['all_dates'],
            y=variables[period]['all_macd'],
            name = "MACD",
            line = dict(color = '#00A1FF'),
            opacity = 1
            )
    trace_macd_signal = go.Scatter(
            x=variables[period]['all_dates'],
            y=variables[period]['all_macd_signal'],
            name = "MACD Signal",
            line = dict(color = '#FFA500'),
            opacity = 1        
            )
    bar_macd_hist = go.Bar(
            x=variables[period]['all_dates'],
            y=variables[period]['all_macd_hist'],
            name = "MACD Histogram",
            marker = dict(color = '#D100AA')
            )

    fig = py.tools.make_subplots(rows=3, cols=1, shared_xaxes=True)

    fig.append_trace(trace_close, 1, 1)
    fig.append_trace(trace_macd, 2, 1)
    fig.append_trace(trace_macd_score, 2, 1)
    fig.append_trace(trace_macd_signal, 2, 1)
    fig.append_trace(bar_macd_hist, 2, 1)
    fig.append_trace(trace_rsi, 3, 1)
    fig.append_trace(trace_rsi_score, 3, 1)
    
    shapes_to_draw = list()

    # Buy and sell shapes
    for buy_timestamp in variables['plot_buys']:
        shapes_to_draw.append(
                {
                    'layer': 'below',
                    'xref': 'x2',
                    'yref': 'paper',
                    'type': 'rect',
                    'x0': format(datetime.datetime.strptime(buy_timestamp, "%Y-%m-%d %H:%M:%S")-datetime.timedelta(hours=2), '%Y-%m-%d %H:%M:%S'),
                    'y0': 0,
                    'x1': format(datetime.datetime.strptime(buy_timestamp, "%Y-%m-%d %H:%M:%S")+datetime.timedelta(hours=2), '%Y-%m-%d %H:%M:%S'),
                    'y1': 1,
                    'fillcolor': '#339933',
                    'line': {'width': 0},
                    'opacity': 0.6

                }
        )
    for sell_timestamp in variables['plot_sells']:
        shapes_to_draw.append(
                {
                    'layer': 'below',
                    'xref': 'x2',
                    'yref': 'paper',
                    'type': 'rect',
                    'x0': format(datetime.datetime.strptime(sell_timestamp, "%Y-%m-%d %H:%M:%S")-datetime.timedelta(hours=2), '%Y-%m-%d %H:%M:%S'),
                    'y0': 0,
                    'x1': format(datetime.datetime.strptime(sell_timestamp, "%Y-%m-%d %H:%M:%S")+datetime.timedelta(hours=2), '%Y-%m-%d %H:%M:%S'),
                    'y1': 1,
                    'fillcolor': '#FF3333',
                    'line': {'width': 0},
                    'opacity': 0.6

                }
        )
     
    #RSI 30-70 interval shape
    shapes_to_draw.append(
            {
            'xref': 'paper',
            'yref': 'y3',
            'type': 'rect',
            'x0': 0,
            'y0': 30,
            'x1': 1,
            'y1': 70,
            'line': {
                'color': 'rgba(128, 0, 128, 1)',
                'width': 0
            },
            'fillcolor': 'rgba(128, 0, 128, 0.2)'
            }    
    )
    
    fig['layout'].update(title='BTC Trading Bot')
    fig['layout'].update(yaxis=dict(title='BTC Closing price', domain=[0.5,1]), yaxis2=dict(title='MACD', domain=[0.3,0.5]), yaxis3=dict(title='RSI', domain=[0.2,0.3], range=[0,100]))
    fig['layout'].update(bargap=0, barmode='stack')
    fig['layout'].update(shapes=shapes_to_draw)
    fig['layout'].update(xaxis1=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                        label='1m',
                        step='month',
                        stepmode='backward'),
                    dict(count=1,
                        label='1w',
                        step='week',
                        stepmode='backward'),
                    dict(step='all')
                ])
            ),
            rangeslider=dict(),
            type='date'
        )
    )

    plot_name = "ctbot_plots/{}_{}s_ctbot_plot.html".format(variables[period]['all_dates'][-1].replace(" ", "_").replace(":", "_"), period)

    py.offline.plot(fig, filename=plot_name)

if __name__ == "__main__":
    main()