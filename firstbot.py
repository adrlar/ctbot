import time
import sys
import argparse
import datetime
import numpy as np
from poloniex import poloniex
from keys import adrlar_key, adrlar_secret


def main():
    numpy_prices = None
    prices = list()
    active_trade = False
    type_of_trade = None
    current_mov_avg = 0
    current_bollinger = None
    current_trade_details = list()
    total_gains = list()
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
    while True:
        if args.history and history_data:
            history_this = history_data.pop(0)
            last_price = history_this['weightedAverage']
            t_now = datetime.datetime.fromtimestamp(int(history_this['date'])).strftime('%Y-%m-%d %H:%M:%S')
        elif args.history:

            print "History run complete. We made {} in total".format(sum(total_gains))
            exit(0)
        else:
            current_value = polo.api_query("returnTicker")
            #print current_value
            last_price = current_value[args.pair]["last"]
            t_now = datetime.datetime.now()

        if len(prices)>0:
            
            current_mov_avg = np.mean(numpy_prices) #sum(prices)/float(len(prices))
            current_bollinger = 2*np.std(numpy_prices)
            if not current_bollinger: #no current bollinger yet
                prev_bollinger = current_bollinger
            
            prev_price = prices[-1]
            
            #active_trade, type_of_trade, total_gains, current_trade_details = model_moving_avg(
            #        args, last_price, prev_price, current_mov_avg, active_trade, type_of_trade, total_gains, current_trade_details)
            active_trade, type_of_trade, total_gains, current_trade_details = model_bollinger_long(
                    args, last_price, prev_price, current_mov_avg, current_bollinger, prev_bollinger, active_trade, type_of_trade, total_gains, current_trade_details)
        else:
            prev_price = 0
        
        prev_price = last_price
        prev_bollinger = current_bollinger

        prices.append(float(last_price))
        prices = prices[-args.m_avg_points:]
        numpy_prices = np.array(prices)
        if args.verbose:
            print "{} Period: {}s {}: {} mavg: {}".format(t_now, args.period, args.pair, last_price, current_mov_avg)
        if not args.history:
            try:
                time.sleep(args.period)
            except KeyboardInterrupt as e:

                if type_of_trade == "short":
                    if args.verbose:
                        print "Exiting trade! We were {}. We made {}".format(current_trade_details[0], current_trade_details[1]-last_price)
                elif type_of_trade == "long":
                    if args.verbose:
                        print "Exiting trade! We were {}. We made {}".format(current_trade_details[0], last_price-current_trade_details[1])
                print "Exiting, profits: {}".format(sum(total_gains))


def model_bollinger_long(args, last_price, prev_price, current_mov_avg, current_bollinger, prev_bollinger, active_trade, type_of_trade, total_gains, current_trade_details):
    if not active_trade:
        if current_bollinger > prev_bollinger and last_price - (current_mov_avg-current_bollinger) < last_price*0.01 and prev_price - (current_mov_avg-current_bollinger) < prev_price*0.01:
            if args.verbose:
                print "Buy order, GOING LONG! Last: {} Prev: {} Avg: {} bollinger:".format(last_price, prev_price, current_mov_avg, current_bollinger)
            active_trade = True
            type_of_trade = "long"
            current_trade_details = [type_of_trade, last_price]
        elif current_bollinger < prev_bollinger:
            pass
#            if args.verbose:
#            print "Sell order, SHORTING! Last: {} Prev: {} Avg: {}".format(last_price, prev_price, current_mov_avg)
#            active_trade = True
#            type_of_trade = "short"
#            current_trade_details = [type_of_trade, last_price]
    elif type_of_trade == "short":
        if last_price < current_mov_avg:
            if args.verbose:
                print "Exiting trade! We were {}. We made {}".format(current_trade_details[0], current_trade_details[1]-last_price)
            total_gains.append(current_trade_details[1] - last_price)
            active_trade = False
            type_of_trade = None
    elif type_of_trade == "long":
        if last_price > (current_mov_avg+current_bollinger):
            if args.verbose:
                print "Exiting trade! We were {}. We made {}".format(current_trade_details[0], last_price-current_trade_details[1])
            total_gains.append(last_price - current_trade_details[1])
            active_trade = False
            type_of_trade = None
    return active_trade, type_of_trade, total_gains, current_trade_details



def model_moving_avg(args, last_price, prev_price, current_mov_avg, active_trade, type_of_trade, total_gains, current_trade_details):
    if not active_trade:
        if last_price > current_mov_avg and last_price < prev_price:
            #SELLING because price is higher than mov_avg but going down
            if args.verbose:
                print "Sell order, SHORTING! Last: {} Prev: {} Avg: {}".format(last_price, prev_price, current_mov_avg)
            active_trade = True
            type_of_trade = "short"
            current_trade_details = [type_of_trade, last_price]
        elif last_price < current_mov_avg and last_price > prev_price:
            #BYUING because price is lower than mov_avg but going up
            if args.verbose:
                print "Buy order, GOING LONG! Last: {} Prev: {} Avg: {}".format(last_price, prev_price, current_mov_avg)
            active_trade = True
            type_of_trade = "long"
            current_trade_details = [type_of_trade, last_price]
    elif type_of_trade == "short":
        if last_price < current_mov_avg:
            if args.verbose:
                print "Exiting trade! We were {}. We made {}".format(current_trade_details[0], current_trade_details[1]-last_price)
            total_gains.append(current_trade_details[1] - last_price)
            active_trade = False
            type_of_trade = None
    elif type_of_trade == "long":
        if last_price > current_mov_avg:
            if args.verbose:
                print "Exiting trade! We were {}. We made {}".format(current_trade_details[0], last_price-current_trade_details[1])
            total_gains.append(last_price - current_trade_details[1])
            active_trade = False
            type_of_trade = None
    return active_trade, type_of_trade, total_gains, current_trade_details

if __name__ == "__main__":
    main()
