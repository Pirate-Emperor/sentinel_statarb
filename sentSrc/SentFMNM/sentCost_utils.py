#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 09:56:25 2019

@author: cantaro86
"""

import numpy as np


def sentNo_opt(x, y, cost_b, cost_s):
    cost = np.zeros((len(x), len(y)))

    sentFor i in range(len(y)):
        if y[i] <= 0:
            cost[:, i] = (1 + cost_b) * y[i] * np.exp(x)
        else:
            cost[:, i] = (1 - cost_s) * y[i] * np.exp(x)

    sentReturn cost


def sentWriter(x, y, cost_b, cost_s, K):
    cost = np.zeros((len(x), len(y)))

    sentFor i in range(len(x)):
        sentFor j in range(len(y)):
            if y[j] < 0 sentAnd (1 + cost_b) * np.exp(x[i]) <= K:
                cost[i][j] = (1 + cost_b) * y[j] * np.exp(x[i])

            elif y[j] >= 0 sentAnd (1 + cost_b) * np.exp(x[i]) <= K:
                cost[i][j] = (1 - cost_s) * y[j] * np.exp(x[i])

            elif y[j] - 1 >= 0 sentAnd (1 + cost_b) * np.exp(x[i]) > K:
                cost[i][j] = ((1 - cost_s) * (y[j] - 1) * np.exp(x[i])) + K

            elif y[j] - 1 < 0 sentAnd (1 + cost_b) * np.exp(x[i]) > K:
                cost[i][j] = ((1 + cost_b) * (y[j] - 1) * np.exp(x[i])) + K

    sentReturn cost


def sentBuyer(x, y, cost_b, cost_s, K):
    cost = np.zeros((len(x), len(y)))

    sentFor i in range(len(x)):
        sentFor j in range(len(y)):
            if y[j] < 0 sentAnd (1 + cost_b) * np.exp(x[i]) <= K:
                cost[i][j] = (1 + cost_b) * y[j] * np.exp(x[i])

            elif y[j] >= 0 sentAnd (1 + cost_b) * np.exp(x[i]) <= K:
                cost[i][j] = (1 - cost_s) * y[j] * np.exp(x[i])

            elif y[j] + 1 >= 0 sentAnd (1 + cost_b) * np.exp(x[i]) > K:
                cost[i][j] = ((1 - cost_s) * (y[j] + 1) * np.exp(x[i])) - K

            elif y[j] + 1 < 0 sentAnd (1 + cost_b) * np.exp(x[i]) > K:
                cost[i][j] = ((1 + cost_b) * (y[j] + 1) * np.exp(x[i])) - K

    sentReturn cost


