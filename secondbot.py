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


def main():
    #we are long coins to begin with, and will short the coin by 
    #selling them into USDT when we think its a good move
    
    variables = init_variables()

    parser = argparse.ArgumentParser(description="Cryptobot for poloniex, written by Adrian Larkeryd, 2017")
    parser.add_argument("-p", "--pair",
            help="cryptocurrency pair, USDT_BTC, BTC_ETH or BTC_LTC ... etc etc", default="USDT_BTC")
    parser.add_argument("-t", "--period",
            help="poloniex requires periods in 300,900,1800,7200,14400, or 86400 second increments", default=300, type=int)
    parser.add_argument("-m", "--m_avg_points",
            help="points in moving avg", default=5, type=int)
    parser.add_argument("--history",
            help="run a history test, takes two epoch time stamps as parameters: --history 1501542000 "+str(int(time.time())), nargs=2)
    parser.add_argument("-v", "--verbose", 
            help="increase output verbosity", action="store_true")

    args = parser.parse_args() 
    if args.verbose:
        print args

    polo = poloniex(adrlar_key, adrlar_secret)

    if args.history:
        history_data = polo.api_query("returnChartData",{"currencyPair":args.pair,"start":args.history[0],"end":args.history[1],"period":args.period})["candleStick"]
        #print history_data
        #exit()
    else:
        history_data = polo.api_query("returnChartData",{"currencyPair":args.pair,"start":str(int(time.time())-50*args.period),"end":str(int(time.time())),"period":args.period})["candleStick"]
    while True:
        if history_data:
            history_now = history_data.pop(0)
            variables['last_price'] = history_now['close']
            variables['t_now'] = datetime.datetime.utcfromtimestamp(int(history_now['date'])).strftime('%Y-%m-%d %H:%M:%S')
        elif not history_data and args.history:
            if variables['active_trade']:
                variables['coins'] = buy_coin(variables['roll_prices'][-1], variables['usdt'])
                print "{} We bought back into coins because run is ending, buying {} coins with {} USDT. CURRENT PRICE {}".format(variables['t_now'], variables['coins'], variables['usdt'], variables['roll_prices'][-1])
                variables['usdt'] = 0
                variables['active_trade'] = False
                variables['plot_buys'][-1]=1
 
            print "History run complete. We made {} BTC in total".format(variables['coins']-1)
            draw(variables)
            exit(0)
        else:
            current_value = polo.api_query("returnTicker")
            #print current_value
            variables['last_price'] = float(current_value[args.pair]["last"])
            variables['t_now'] = datetime.datetime.now()

        variables['all_dates'].append(variables['t_now'])

        #Initiate plotting values, so that there is a value for each date  will change the current value when calculating the statistic
        variables['plot_buys'].append(None)
        variables['plot_sells'].append(None)
        variables['plot_all_macd'].append(None)
        variables['plot_all_macd_signal'].append(None)
        variables['plot_all_macd_hist'].append(None)
        variables['plot_all_rsi'].append(None)
        
        variables['all_score'].append(None)
        variables['all_rsi_score'].append(None)
        variables['all_macd_score'].append(None)
        
        variables['roll_prices'].append(variables['last_price'])
        variables['plot_all_prices'].append(variables['last_price'])
        
        variables['numpy_prices'] = np.array(variables['roll_prices'])
        variables['current_bollinger'] = 2*np.std(variables['numpy_prices'])
        variables['prev_bollinger'] = variables['current_bollinger']
            
        
        variables['roll_prices'] = variables['roll_prices'][-100:]
       
        if len(variables['roll_prices'])>1: #here we calc maths and run model
           
            #print prices
            if len(variables['roll_prices']) > 26: #need a certain number of 

                variables = calc_macd(variables)    
                #print t_now, macd_12, macd_26, macd_signal, macd_hist, last_price
            
            variables = calc_rsi(variables, 14)

            if len(variables['roll_prices']) > 50:
                variables = model(variables)


        if args.verbose:
            print "{} Period: {}s {}: {}. RSI: {}. MACDhist: {}.".format(variables['t_now'], args.period, args.pair, variables['roll_prices'][-1], variables['rsi'], variables['macd_hist'])
            print "We have {} coins and {} USDT".format(variables['coins'], variables['usdt'])
        if not history_data:
            try:
                time.sleep(args.period)
                draw(variables)
            except KeyboardInterrupt as e:
                if variables['active_trade']:
                    variables['coins'] = buy_coin(variables['roll_prices'][-1], variables['usdt'])
                    print "{} We bought back into coins because run is ending, buying {} coins with {} USDT. CURRENT PRICE {}".format(variables['t_now'], variables['coins'], variables['usdt'], variables['roll_prices'][-1])
                    variables['usdt'] = 0
                    variables['active_trade'] = False
                    variables['plot_buys'][-1]=1
 
                print "EXITING! We made {} BTC in total".format(variables['coins']-1)
                draw(variables)
                exit(0)
 

def draw(variables):
    trace_close = go.Scatter(
            x=variables['all_dates'],
            y=variables['plot_all_prices'],
            name = "BTC Close",
            line = dict(color = '#6666CC', width=4),
            opacity = 1 
            ) 
    trace_score = go.Scatter(
            x=variables['all_dates'],
            y=variables['all_score'],
            name = "Bot model score",
            line = dict(color = '#06F99D', width=1),
            opacity = 1 
            )
    trace_rsi_score = go.Scatter(
            x=variables['all_dates'],
            y=variables['all_rsi_score'],
            name = "Bot model score",
            line = dict(color = '#06F99D', width=1),
            opacity = 1 
            )
    trace_macd_score = go.Scatter(
            x=variables['all_dates'],
            y=variables['all_macd_score'],
            name = "Bot model score",
            line = dict(color = '#06F99D', width=1),
            opacity = 1 
            )
    trace_rsi = go.Scatter(
            x=variables['all_dates'],
            y=variables['plot_all_rsi'],
            name = "RSI",
            line = dict(color = '#680082'),
            opacity = 1 
            )
    trace_macd = go.Scatter(
            x=variables['all_dates'],
            y=variables['plot_all_macd'],
            name = "MACD",
            line = dict(color = '#00A1FF'),
            opacity = 1
            )
    trace_macd_signal = go.Scatter(
            x=variables['all_dates'],
            y=variables['plot_all_macd_signal'],
            name = "MACD Signal",
            line = dict(color = '#FFA500'),
            opacity = 1        
            )
    bar_macd_hist = go.Bar(
            x=variables['all_dates'],
            y=variables['plot_all_macd_hist'],
            name = "MACD Histogram",
            marker = dict(color = '#D100AA')
            )
    
    tmp=list_scalar_multiplication(variables['plot_buys'], int(1.1*max(variables['plot_all_prices'])))
    bar_buys_btc = go.Bar(
            x=variables['all_dates'], 
            y=tmp,
            name = "Buys",
            marker = dict(color = '#339933')
            )
    tmp=list_scalar_multiplication(variables['plot_sells'], int(1.1*max(variables['plot_all_prices'])))
    bar_sells_btc = go.Bar(
            x=variables['all_dates'], 
            y=tmp,
            name = "Sells",
            marker = dict(color = '#FF3333')
            )
    tmp=list_scalar_multiplication(variables['plot_buys'], int(1.1*max(variables['plot_all_macd']+variables['plot_all_macd_signal'])))
    bar_buys_macd = go.Bar(
            x=variables['all_dates'], 
            y=tmp,
            name = "Buys",
            marker = dict(color = '#339933')
            )
    tmp=list_scalar_multiplication(variables['plot_sells'], int(1.1*max(variables['plot_all_macd']+variables['plot_all_macd_signal'])))
    bar_sells_macd = go.Bar(
            x=variables['all_dates'], 
            y=tmp,
            name = "Sells",
            marker = dict(color = '#FF3333')
            )
    tmp=list_scalar_multiplication(variables['plot_buys'], int(1.1*max(variables['plot_all_rsi'])))
    bar_buys_rsi = go.Bar(
            x=variables['all_dates'], 
            y=tmp,
            name = "Buys",
            marker = dict(color = '#339933')
            )
    tmp=list_scalar_multiplication(variables['plot_sells'], int(1.1*max(variables['plot_all_rsi'])))
    bar_sells_rsi = go.Bar(
            x=variables['all_dates'], 
            y=tmp,
            name = "Sells",
            marker = dict(color = '#FF3333')
            )


    fig = py.tools.make_subplots(rows=3, cols=1, shared_xaxes=True)
    
    #btc_close_plot = [trace_close, bar_buys, bar_sells]
    #macd_plot = [trace_macd, trace_macd_signal, bar_macd_hist , bar_buys, bar_sells]
    #rsi_plot = [trace_rsi, bar_buys, bar_sells]
    fig.append_trace(trace_close, 1, 1)
    #fig.append_trace(bar_buys_btc, 1, 1)
    #fig.append_trace(bar_sells_btc, 1, 1)
    fig.append_trace(trace_macd, 2, 1)
    fig.append_trace(trace_macd_score, 2, 1)
    fig.append_trace(trace_macd_signal, 2, 1)
    fig.append_trace(bar_macd_hist, 2, 1)
    #fig.append_trace(bar_buys_macd, 2, 1)
    #fig.append_trace(bar_sells_macd, 2, 1)
    fig.append_trace(trace_rsi, 3, 1)
    fig.append_trace(trace_rsi_score, 3, 1)
    #fig.append_trace(bar_buys_rsi, 3, 1)
    #fig.append_trace(bar_sells_rsi, 3, 1)
    
    shapes_to_draw = list()

    for i in range(0,len(variables['plot_buys'])):
        if variables['plot_buys'][i] != None:
            shapes_to_draw.append(
                    {
                        'layer': 'below',
                        'xref': 'x2',
                        'yref': 'paper',
                        'type': 'rect',
                        'x0': format(datetime.datetime.strptime(variables['all_dates'][i-1], "%Y-%m-%d %H:%M:%S")+datetime.timedelta(hours=2), '%Y-%m-%d %H:%M:%S'),
                        'y0': 0,
                        'x1': format(datetime.datetime.strptime(variables['all_dates'][i], "%Y-%m-%d %H:%M:%S")+datetime.timedelta(hours=2), '%Y-%m-%d %H:%M:%S'),
                        'y1': 1,
                        'fillcolor': '#339933',
                        'line': {'width': 0},
                        'opacity': 0.6
 
                    }
            )
    for i in range(0,len(variables['plot_sells'])):
        if variables['plot_sells'][i] != None:
            shapes_to_draw.append(
                    {
                        'layer': 'below',
                        'xref': 'x2',
                        'yref': 'paper',
                        'type': 'rect',
                        'x0': format(datetime.datetime.strptime(variables['all_dates'][i-1], "%Y-%m-%d %H:%M:%S")+datetime.timedelta(hours=2), '%Y-%m-%d %H:%M:%S'),
                        'y0': 0,
                        'x1': format(datetime.datetime.strptime(variables['all_dates'][i], "%Y-%m-%d %H:%M:%S")+datetime.timedelta(hours=2), '%Y-%m-%d %H:%M:%S'),
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
    py.offline.plot(fig, filename='my-graph.html')

def list_scalar_multiplication(l, n):
    new_l = list()
    for i in l:
        if i != None:
            new_l.append(i*n)
        else:
            new_l.append(None)
    return new_l

def model(variables):

    score = 0
    rsi_score = 0
    macd_score = 0

    #add to score by a set of criteria
    
    rsi_change_one = variables['all_rsi'][-1]-variables['all_rsi'][-2]
    rsi_change_two = variables['all_rsi'][-2]-variables['all_rsi'][-3]
    rsi_change_three = variables['all_rsi'][-3]-variables['all_rsi'][-4]

    macd_hist = variables['roll_macd'][-1]-variables['roll_macd_signal'][-1]
    macd_hist_prev = variables['roll_macd'][-2]-variables['roll_macd_signal'][-2]
    macd_hist_prev2 = variables['roll_macd'][-3]-variables['roll_macd_signal'][-3]

    macd_bear = False
    if macd_hist < 0 and macd_hist_prev > 0:
        macd_bear = True

    macd_change_one = macd_hist - macd_hist_prev
    macd_change_two = macd_hist_prev - macd_hist_prev2
    macd_change_three = macd_hist - macd_hist_prev2

    macd_change_ratio = abs(macd_change_one)/macd_hist_prev
    
    if rsi_change_one < 0 and variables['all_rsi'][-2] > 60:
        #print "RSI TRIGGER", variables['all_dates'][-1]
        rsi_score += 15
        if rsi_change_two > 0:
            #print "RSI_TWO TRIGGER", variables['all_dates'][-1]
            rsi_score += 10
        if rsi_change_three > 0:
            #print "RSI_THREE TRIGGER", variables['all_dates'][-1]
            rsi_score += 10

    if macd_change_one > 0:
        macd_score -= 15
    if macd_change_two > 0:
        macd_score -= 5

    if variables['roll_macd'][-1] > 100:
        macd_score += 25
        if variables['roll_macd_signal'][-1] > variables['roll_macd'][-1]:
            macd_score += 25

    if macd_bear:
        macd_score += 10

    if macd_change_one < 0 and macd_change_two > 0 and macd_hist > 0:
        #print "MACD_ONETWO TRIGGER"
        macd_score += 10
        if macd_hist > 0:
            #print "MACD_HIST TRIGGER"
            macd_score += 10
        if macd_change_ratio > 0.25:
            #print "MACD_RATIO TRIGGER"
            macd_score += 10

    score = macd_score+rsi_score

    variables['all_score'][-1]=score
    variables['all_rsi_score'][-1]=rsi_score
    variables['all_macd_score'][-1]=macd_score

    if not variables['active_trade']:
        #we dont have an active trade, ie we have coins not USDT
        if score > 50:
            #we are shorting coins by selling them
            variables['usdt']= sell_coin(variables['roll_prices'][-1], variables['coins'])
            print score
            print "macd {} amcds {} mac1 {} mac2 {} hist {} rsi1 {} rsi2 {}".format(variables['roll_macd'][-1], variables['roll_macd_signal'][-1], macd_change_one, macd_change_two, macd_hist, rsi_change_one, rsi_change_two)
            print "{} We sold coins, selling {} coins for {} USDT. CURRENT PRICE: {}".format(variables['t_now'], variables['coins'], variables['usdt'], variables['roll_prices'][-1])
            variables['coins'] = 0
            variables['active_trade'] = True
            variables['active_trade_price'] = variables['roll_prices'][-1]
            variables['plot_sells'][-1]=1
    else:
        getbackin = False
        #there is an active trade, we have USDT and might want to get back into coins
        if rsi_change_one > 0 and variables['all_rsi'][-1] < 30:
            getbackin = True
        if variables['roll_macd_signal'][-1] < variables['roll_macd'][-1]:
            getbackin = True
        #if prices[-1]>active_trade_price and prices[-1]>active_trade_price:
        #    getbackin = True

        if getbackin:
            #going back into coins by buying coins for all USDT that we have
            variables['coins'] = buy_coin(variables['roll_prices'][-1], variables['usdt'])
            print "{} We bought back into coins, buying {} coins with {} USDT. CURRENT PRICE {}".format(variables['t_now'], variables['coins'], variables['usdt'], variables['roll_prices'][-1])
            variables['usdt'] = 0
            variables['active_trade'] = False
            variables['plot_buys'][-1]=1
        else:
            print "Starying short, CURRENT PRICE {}".format(variables['roll_prices'][-1])
    return variables

def sell_coin(price, amount):
    fee = 0.0025
    return price*amount*(1-fee)
def buy_coin(price, amount):
    fee = 0.0025
    return amount/price*(1-fee)

def calc_ema(prices, n):
    if len(prices) < n+1:
        return sum(prices)/len(prices)
    prev_ema = calc_ema(prices[0:-1], n)
    multiplier = 2/(n+1)
    return (prices[-1]-prev_ema)*multiplier + prev_ema

def calc_mma(prices, n):
    if len(prices) < n+1:
        return sum(prices)/len(prices)
    prev_mma = calc_mma(prices[0:-1], n)
    return ((n-1)*prev_mma + prices[-1])/n

def calc_macd(variables):
    macd_12 = calc_ema(variables['roll_prices'], 12)
    macd_26 = calc_ema(variables['roll_prices'], 26)
    variables['macd'] = macd_12 - macd_26
    variables['roll_macd'].append(variables['macd'])
    
    #roll over to not go too deep in recursive
    variables['roll_macd'] = variables['roll_macd'][-100:]
    
    #can only calc signal if there are more than 9 macd values
    variables['macd_signal'] = 0
    variables['macd_hist'] = 0
    if len(variables['roll_macd']) > 9:
        variables['macd_signal'] = calc_ema(variables['roll_macd'], 9)
        variables['macd_hist'] = variables['macd'] - variables['macd_signal']
    variables['roll_macd_signal'].append(variables['macd_signal'])
    
    #plotting variables
    variables['plot_all_macd'][-1] = variables['macd']
    variables['plot_all_macd_signal'][-1] = variables['macd_signal']
    variables['plot_all_macd_hist'][-1] = variables['macd_hist']

    return variables

def calc_rsi(variables, n):
    if variables['roll_prices'][-1] > variables['roll_prices'][-2]:
        rsi_u = variables['roll_prices'][-1] - variables['roll_prices'][-2]
        rsi_d = 0
    elif variables['roll_prices'][-1] < variables['roll_prices'][-2]:
        rsi_u = 0
        rsi_d = variables['roll_prices'][-2] - variables['roll_prices'][-1]
    else:
        rsi_u = 0
        rsi_d = 0
    
    variables['roll_rsi_d'].append(rsi_d)
    variables['roll_rsi_u'].append(rsi_u)

    #roll over to not go too deep in recursive calc_mma
    variables['roll_rsi_d'] = variables['roll_rsi_d'][-100:]
    variables['roll_rsi_u'] = variables['roll_rsi_u'][-100:]
   
    if len(variables['roll_rsi_d']) > n:
        rsi_d_mov_avg = calc_mma(variables['roll_rsi_d'], n)
        rsi_u_mov_avg = calc_mma(variables['roll_rsi_u'], n)
    else:
        rsi_d_mov_avg = 0
        rsi_u_mov_avg = 0

    if rsi_d_mov_avg != 0:
        rs = rsi_u_mov_avg/rsi_d_mov_avg
    else:
        rs = 10000 #large number 
    rsi = 100 - (100/(1+rs))

    variables['all_rsi'].append(rsi)

    #plotting variable
    variables['plot_all_rsi'][-1] = rsi
    
    return variables


def init_variables():
    variables = {
            #Starting with 1 coin and 0 USDT
            'coins': 1,
            'usdt': 0,
            
            #Trade details
            'active_trade': False,
            'type_of_trade': None,
            'active_trade_price': 0,
            'current_trade_details': dict(),
            'all_score': list(),
            'all_rsi_score': list(),
            'all_macd_score': list(),

            #Keeping track of prices
            'numpy_prices': None,
            'roll_prices': list(),
    
            #plotting lists
            'plot_all_prices': list(),
            'plot_buys': list(),
            'plot_sells': list(),
            'plot_all_macd': list(),
            'plot_all_macd_signal': list(),
            'plot_all_macd_hist': list(),
            'plot_all_rsi': list(),
            'all_dates': list(),

            #Moving average
            'current_mov_avg': 0,    
            'roll_moving_avg': list(),
    
            #Bollinger bands
            'current_bollinger': 0,
            'all_bollinger': list(),

            #MACD values
            'macd_12': 0,
            'macd_26': 0,
            'macd': 0,
            'macd_hist': 0,
            'macd_signal': 0,
            'roll_macd': list(),
            'roll_macd_signal': list(),

            #RSI values
            'rsi': 0,
            'rsi_d': 0,
            'rsi_u': 0,
            'all_rsi': list(),
            'roll_rsi_d': list(),
            'roll_rsi_u': list()
    }
    return variables


if __name__ == "__main__":
    main()
