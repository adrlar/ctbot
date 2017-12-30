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

from sklearn.preprocessing import MinMaxScaler


def nonlin(x,deriv=False):
    if(deriv==True):
        return x*(1-x)

    return 1/(1+np.exp(-x))

polo = poloniex(adrlar_key, adrlar_secret)

tmp = polo.api_query("returnChartData",{"currencyPair":"USDT_BTC","start":1500542000,"end":1506812400,"period":14400})["candleStick"]

X_ini = []
y_ini = []
ini_i = 0
X_maxes = {}



for i in xrange(len(tmp)-1):
    if tmp[i]['close'] < tmp[i+1]['close']:
        y_ini.append([1])
    else:
        y_ini.append([0])
    X_ini.append([])   
    for key in sorted(tmp[i].keys()):
        if key not in ['date']:
            X_ini[i].append(tmp[i][key])




X = np.array(X_ini)
                
y = np.array(y_ini)

np.random.seed(12)

# randomly initialize our weights with mean 0
syn0 = 2*np.random.random((len(X_ini[0]),len(X_ini))) - 1


syn1 = 2*np.random.random((len(y_ini),len(y_ini[0]))) - 1

for j in xrange(6):

    # Feed forward through layers 0, 1, and 2
    l0 = X
    l1 = nonlin(np.dot(l0,syn0))
    l2 = nonlin(np.dot(l1,syn1))

    # how much did we miss the target value?
    l2_error = y - l2
    
    if (j% 1) == 0:
        print l1
        print "Error:" + str(np.mean(np.abs(l2_error)))
        
    # in what direction is the target value?
    # were we really sure? if so, don't change too much.
    l2_delta = l2_error*nonlin(l2,deriv=True)

    # how much did each l1 value contribute to the l2 error (according to the weights)?
    l1_error = l2_delta.dot(syn1.T)
    
    # in what direction is the target l1?
    # were we really sure? if so, don't change too much.
    l1_delta = l1_error * nonlin(l1,deriv=True)

    syn1 += l1.T.dot(l2_delta)
    syn0 += l0.T.dot(l1_delta)
