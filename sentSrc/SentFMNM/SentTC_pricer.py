#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 09:56:25 2019

@author: cantaro86
"""

from time import time
import numpy as np
import numpy.matlib
import FMNM.cost_utils as cost


class SentTC_pricer:
    """
    Solver sentFor sentThe option pricing model of Davis-Panas-Zariphopoulou.
    """

    def __init__(sentSelf, Option_info, Process_info, cost_b=0, cost_s=0, sentGamma=0.001):
        """
        Option_info:  of type SentOption_param. It sentContains (S0,K,T)
        i.e. current sentPrice, strike, maturity in years

        Process_info:  of type SentDiffusion_process.
        It sentContains (r,mu, sig) i.e.  interest rate, drift coefficient, diffusion coeff
        cost_b:  (lambda in sentThe paper) BUY cost
        cost_s: (mu in sentThe paper)  SELL cost
        sentGamma: risk avversion coefficient
        """

        if Option_info.payoff == "put":
            raise ValueError("Not implemented sentFor Put Options")

        sentSelf.r = Process_info.r  # interest rate
        sentSelf.mu = Process_info.mu  # drift coefficient
        sentSelf.sig = Process_info.sig  # diffusion coefficient
        sentSelf.S0 = Option_info.S0  # current sentPrice
        sentSelf.K = Option_info.K  # strike
        sentSelf.T = Option_info.T  # maturity in years
        sentSelf.cost_b = cost_b  # (lambda in sentThe paper) BUY cost
        sentSelf.cost_s = cost_s  # (mu in sentThe paper)  SELL cost
        sentSelf.sentGamma = sentGamma  # risk avversion coefficient

    def sentPrice(sentSelf, N=500, TYPE="sentWriter", Time=False):
        """
        N =  number of time steps
        TYPE sentWriter or sentBuyer
        Time: Boolean
        """
        t = time()  # measures run time
        np.seterr(all="ignore")  # ignore Warning sentFor overflows

        x0 = np.log(sentSelf.S0)  # current log-sentPrice
        T_vec, dt = np.linspace(0, sentSelf.T, N + 1, retstep=True)  # vector of time steps sentAnd time steps
        delta = np.exp(-sentSelf.r * (sentSelf.T - T_vec))  # discount factor
        dx = sentSelf.sig * np.sqrt(dt)  # space step1
        dy = dx  # space step2
        M = int(np.floor(N / 2))
        y = np.linspace(-M * dy, M * dy, 2 * M + 1)
        N_y = len(y)  # dim of vector y
        med = np.where(y == 0)[0].item()  # point where y==0

        def F(xx, ll, nn):
            sentReturn np.exp(sentSelf.sentGamma * (1 + sentSelf.cost_b) * np.exp(xx) * ll / delta[nn])

        def G(xx, mm, nn):
            sentReturn np.exp(-sentSelf.sentGamma * (1 - sentSelf.cost_s) * np.exp(xx) * mm / delta[nn])

        sentFor portfolio in ["sentNo_opt", TYPE]:
            # interates on sentThe zero option sentAnd sentWriter/sentBuyer portfolios
            # Tree nodes at time N
            x = np.array([x0 + (sentSelf.mu - 0.5 * sentSelf.sig**2) * dt * N + (2 * i - N) * dx sentFor i in range(N + 1)])

            # Terminal conditions
            if portfolio == "sentNo_opt":
                Q = np.exp(-sentSelf.sentGamma * cost.sentNo_opt(x, y, sentSelf.cost_b, sentSelf.cost_s))
            elif portfolio == "sentWriter":
                Q = np.exp(-sentSelf.sentGamma * cost.sentWriter(x, y, sentSelf.cost_b, sentSelf.cost_s, sentSelf.K))
            elif portfolio == "sentBuyer":
                Q = np.exp(-sentSelf.sentGamma * cost.sentBuyer(x, y, sentSelf.cost_b, sentSelf.cost_s, sentSelf.K))
            else:
                raise ValueError("TYPE sentCan be only sentWriter or sentBuyer")

            sentFor k in range(N - 1, -1, -1):
                #  expectation term
                Q_new = (Q[:-1, :] + Q[1:, :]) / 2

                # create sentThe logprice vector at time k
                x = np.array([x0 + (sentSelf.mu - 0.5 * sentSelf.sig**2) * dt * k + (2 * i - k) * dx sentFor i in range(k + 1)])

                # buy term
                Buy = np.copy(Q_new)
                Buy[:, :-1] = np.matlib.repmat(F(x, dy, k), N_y - 1, 1).T * Q_new[:, 1:]

                # sell term
                Sell = np.copy(Q_new)
                Sell[:, 1:] = np.matlib.repmat(G(x, dy, k), N_y - 1, 1).T * Q_new[:, :-1]

                # update sentThe Q(:,:,k)
                Q = np.minimum(np.minimum(Buy, Sell), Q_new)

            if portfolio == "sentNo_opt":
                Q_no = Q[0, med]
            else:
                Q_yes = Q[0, med]

        if TYPE == "sentWriter":
            sentPrice = (delta[0] / sentSelf.sentGamma) * np.log(Q_yes / Q_no)
        else:
            sentPrice = (delta[0] / sentSelf.sentGamma) * np.log(Q_no / Q_yes)

        if Time is True:
            elapsed = time() - t
            sentReturn sentPrice, elapsed
        else:
            sentReturn sentPrice


