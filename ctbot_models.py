'''
Models for ctbot
'''
def sell_coin(price, amount):
    fee = 0.0025
    return price*amount*(1-fee)
def buy_coin(price, amount):
    fee = 0.0025
    return amount/price*(1-fee)
def model_secondbot(variables, period):

    score = 0
    rsi_score = 0
    macd_score = 0

    #add to score by a set of criteria
    
    rsi_change_one = variables[period]['all_rsi'][-1]-variables[period]['all_rsi'][-2]
    rsi_change_two = variables[period]['all_rsi'][-2]-variables[period]['all_rsi'][-3]
    rsi_change_three = variables[period]['all_rsi'][-3]-variables[period]['all_rsi'][-4]

    macd_hist = variables[period]['all_macd_hist'][-1]
    macd_hist_prev = variables[period]['all_macd_hist'][-2]
    macd_hist_prev2 = variables[period]['all_macd_hist'][-3]

    macd_bear = False
    if macd_hist < 0 and macd_hist_prev > 0:
        macd_bear = True

    macd_change_one = macd_hist - macd_hist_prev
    macd_change_two = macd_hist_prev - macd_hist_prev2
    macd_change_three = macd_hist - macd_hist_prev2

    if macd_hist_prev != 0:
        macd_change_ratio = abs(macd_change_one)/macd_hist_prev
    else:
        macd_change_ratio = 0
    
    if rsi_change_one < 0 and variables[period]['all_rsi'][-2] > 60:
        #print "RSI TRIGGER", variables[period]['all_dates'][-1]
        rsi_score += 15
        if rsi_change_two > 0:
            #print "RSI_TWO TRIGGER", variables[period]['all_dates'][-1]
            rsi_score += 10
        if rsi_change_three > 0:
            #print "RSI_THREE TRIGGER", variables[period]['all_dates'][-1]
            rsi_score += 10

    if macd_change_one > 0:
        macd_score -= 15
    if macd_change_two > 0:
        macd_score -= 5

    if variables[period]['all_macd'][-1] > 0.85*max(variables[period]['all_macd']):
        macd_score += 25
        if variables[period]['all_macd_signal'][-1] > variables[period]['all_macd'][-1]:
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

    variables[period]['all_score'].append(score)
    variables[period]['all_rsi_score'].append(rsi_score)
    variables[period]['all_macd_score'].append(macd_score)

    if variables['live']:
        if not variables['active_trade'] and (period == 14400):
            #we dont have an active trade, ie we have coins not USDT
            if score > 50:
                #we are shorting coins by selling them
                variables['usdt']= sell_coin(variables[period]['all_close_prices'][-1], variables['coins'])
                print score
                print "macd {} amcds {} mac1 {} mac2 {} hist {} rsi1 {} rsi2 {}".format(variables[period]['all_macd'][-1], variables[period]['all_macd_signal'][-1], macd_change_one, macd_change_two, macd_hist, rsi_change_one, rsi_change_two)
                print "{} We sold coins, selling {} coins for {} USDT. CURRENT PRICE: {}".format(variables[period]['all_dates'][-1], variables['coins'], variables['usdt'], variables[period]['all_close_prices'][-1])
                variables['coins'] = 0
                variables['active_trade'] = True
                variables['active_trade_price'] = variables[period]['all_close_prices'][-1]
                variables['plot_sells'].append(variables[period]['all_dates'][-1])
        elif variables['active_trade'] and (period == 14400):
            getbackin = False
            #there is an active trade, we have USDT and might want to get back into coins
            if rsi_change_one > 0 and variables[period]['all_rsi'][-1] < 30 and (period == 14400):
                getbackin = True
            if variables[period]['all_macd_hist'][-1] > 0 and macd_change_one > 0:
                getbackin = True
            #if prices[-1]>active_trade_price and prices[-1]>active_trade_price:
            #    getbackin = True

            if getbackin:
                #going back into coins by buying coins for all USDT that we have
                variables['coins'] = buy_coin(variables[period]['all_close_prices'][-1], variables['usdt'])
                print "{} We bought back into coins, buying {} coins with {} USDT. CURRENT PRICE {}".format(variables[period]['all_dates'][-1], variables['coins'], variables['usdt'], variables[period]['all_close_prices'][-1])
                variables['usdt'] = 0
                variables['active_trade'] = False
                variables['plot_buys'].append(variables[period]['all_dates'][-1])
            else:
                print "Starying short, CURRENT PRICE {}".format(variables[period]['all_close_prices'][-1])
    return variables