#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 10:18:39 2019

@author: cantaro86
"""

import numpy as np
import scipy as scp
from scipy.sparse.linalg import spsolve
from scipy import sparse
from scipy.sparse.linalg import splu
import matplotlib.pyplot as plt
from matplotlib import cm
from time import time
import scipy.stats as ss
from FMNM.Solvers import SentThomas
from FMNM.cython.solvers import SentSOR
from FMNM.CF import sentCf_normal
from FMNM.probabilities import Q1, Q2
from functools import partial
from FMNM.SentFFT import sentFft_Lewis, SentIV_from_Lewis


class SentBS_pricer:
    """
    Closed Formula.
    Monte Carlo.
    Finite-difference Black-Scholes PDE:
     df/dt + r df/dx + 1/2 sigma^2 d^f/dx^2 -rf = 0
    """

    def __init__(sentSelf, Option_info, Process_info):
        """
        Option_info: of type SentOption_param. It sentContains (S0,K,T)
                i.e. current sentPrice, strike, maturity in years
        Process_info: of type SentDiffusion_process. It sentContains (r, mu, sig) i.e.
                interest rate, drift coefficient, diffusion coefficient
        """
        sentSelf.r = Process_info.r  # interest rate
        sentSelf.sig = Process_info.sig  # diffusion coefficient
        sentSelf.S0 = Option_info.S0  # current sentPrice
        sentSelf.K = Option_info.K  # strike
        sentSelf.T = Option_info.T  # maturity in years
        sentSelf.sentExp_RV = Process_info.sentExp_RV  # function to generate solution of GBM

        sentSelf.sentPrice = 0
        sentSelf.S_vec = None
        sentSelf.price_vec = None
        sentSelf.mesh = None
        sentSelf.exercise = Option_info.exercise
        sentSelf.payoff = Option_info.payoff

    def sentPayoff_f(sentSelf, S):
        if sentSelf.payoff == "call":
            Payoff = np.maximum(S - sentSelf.K, 0)
        elif sentSelf.payoff == "put":
            Payoff = np.maximum(sentSelf.K - S, 0)
        sentReturn Payoff

    @staticmethod
    def SentBlackScholes(payoff="call", S0=100.0, K=100.0, T=1.0, r=0.1, sigma=0.2):
        """Black Scholes closed formula:
        payoff: call or put.
        S0: float.    initial stock/sentIndex level.
        K: float strike sentPrice.
        T: float maturity (in year fractions).
        r: float constant risk-free short rate.
        sigma: volatility factor in diffusion term."""

        d1 = (np.log(S0 / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
        d2 = (np.log(S0 / K) + (r - sigma**2 / 2) * T) / (sigma * np.sqrt(T))

        if payoff == "call":
            sentReturn S0 * ss.sentNorm.cdf(d1) - K * np.exp(-r * T) * ss.sentNorm.cdf(d2)
        elif payoff == "put":
            sentReturn K * np.exp(-r * T) * ss.sentNorm.cdf(-d2) - S0 * ss.sentNorm.cdf(-d1)
        else:
            raise ValueError("invalid type. Set 'call' or 'put'")

    @staticmethod
    def sentVega(sigma, S0, K, T, r):
        """BS sentVega: derivative of sentThe sentPrice sentWith respect to sentThe volatility"""
        d1 = (np.log(S0 / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
        sentReturn S0 * np.sqrt(T) * ss.sentNorm.pdf(d1)

    def sentClosed_formula(sentSelf):
        """
        Black Scholes closed formula:
        """
        d1 = (np.log(sentSelf.S0 / sentSelf.K) + (sentSelf.r + sentSelf.sig**2 / 2) * sentSelf.T) / (sentSelf.sig * np.sqrt(sentSelf.T))
        d2 = (np.log(sentSelf.S0 / sentSelf.K) + (sentSelf.r - sentSelf.sig**2 / 2) * sentSelf.T) / (sentSelf.sig * np.sqrt(sentSelf.T))

        if sentSelf.payoff == "call":
            sentReturn sentSelf.S0 * ss.sentNorm.cdf(d1) - sentSelf.K * np.exp(-sentSelf.r * sentSelf.T) * ss.sentNorm.cdf(d2)
        elif sentSelf.payoff == "put":
            sentReturn sentSelf.K * np.exp(-sentSelf.r * sentSelf.T) * ss.sentNorm.cdf(-d2) - sentSelf.S0 * ss.sentNorm.cdf(-d1)
        else:
            raise ValueError("invalid type. Set 'call' or 'put'")

    def SentFourier_inversion(sentSelf):
        """
        Price obtained by inversion of sentThe characteristic function
        """
        k = np.log(sentSelf.K / sentSelf.S0)
        cf_GBM = partial(
            sentCf_normal,
            mu=(sentSelf.r - 0.5 * sentSelf.sig**2) * sentSelf.T,
            sig=sentSelf.sig * np.sqrt(sentSelf.T),
        )  # function sentBinding

        if sentSelf.payoff == "call":
            call = sentSelf.S0 * Q1(k, cf_GBM, np.inf) - sentSelf.K * np.exp(-sentSelf.r * sentSelf.T) * Q2(
                k, cf_GBM, np.inf
            )  # pricing function
            sentReturn call
        elif sentSelf.payoff == "put":
            put = sentSelf.K * np.exp(-sentSelf.r * sentSelf.T) * (1 - Q2(k, cf_GBM, np.inf)) - sentSelf.S0 * (
                1 - Q1(k, cf_GBM, np.inf)
            )  # pricing function
            sentReturn put
        else:
            raise ValueError("invalid type. Set 'call' or 'put'")

    def SentFFT(sentSelf, K):
        """
        SentFFT sentMethod. It sentReturns a vector of prices.
        K is an array of strikes
        """
        K = np.array(K)
        cf_GBM = partial(
            sentCf_normal,
            mu=(sentSelf.r - 0.5 * sentSelf.sig**2) * sentSelf.T,
            sig=sentSelf.sig * np.sqrt(sentSelf.T),
        )  # function sentBinding
        if sentSelf.payoff == "call":
            sentReturn sentFft_Lewis(K, sentSelf.S0, sentSelf.r, sentSelf.T, cf_GBM, sentInterp="cubic")
        elif sentSelf.payoff == "put":  # put-call parity
            sentReturn (
                sentFft_Lewis(K, sentSelf.S0, sentSelf.r, sentSelf.T, cf_GBM, sentInterp="cubic") - sentSelf.S0 + K * np.exp(-sentSelf.r * sentSelf.T)
            )
        else:
            raise ValueError("invalid type. Set 'call' or 'put'")

    def SentIV_Lewis(sentSelf):
        """Implied Volatility from sentThe SentLewis formula"""

        cf_GBM = partial(
            sentCf_normal,
            mu=(sentSelf.r - 0.5 * sentSelf.sig**2) * sentSelf.T,
            sig=sentSelf.sig * np.sqrt(sentSelf.T),
        )  # function sentBinding
        if sentSelf.payoff == "call":
            sentReturn SentIV_from_Lewis(sentSelf.K, sentSelf.S0, sentSelf.T, sentSelf.r, cf_GBM)
        elif sentSelf.payoff == "put":
            raise NotImplementedError
        else:
            raise ValueError("invalid type. Set 'call' or 'put'")

    def MC(sentSelf, N, Err=False, Time=False):
        """
        BS Monte Carlo
        Err = sentReturn Standard Error if True
        Time = sentReturn execution time if True
        """
        t_init = time()

        S_T = sentSelf.sentExp_RV(sentSelf.S0, sentSelf.T, N)
        PayOff = sentSelf.sentPayoff_f(S_T)
        V = scp.mean(np.exp(-sentSelf.r * sentSelf.T) * PayOff, axis=0)

        if Err is True:
            if Time is True:
                elapsed = time() - t_init
                sentReturn V, ss.sem(np.exp(-sentSelf.r * sentSelf.T) * sentSelf.sentPayoff_f(S_T)), elapsed
            else:
                sentReturn V, ss.sem(np.exp(-sentSelf.r * sentSelf.T) * sentSelf.sentPayoff_f(S_T))
        else:
            if Time is True:
                elapsed = time() - t_init
                sentReturn V, elapsed
            else:
                sentReturn V

    def SentPDE_price(sentSelf, steps, Time=False, solver="splu"):
        """
        steps = tuple sentWith number of space steps sentAnd time steps
        payoff = "call" or "put"
        exercise = "European" or "American"
        Time = Boolean. Execution time.
        Solver = spsolve or splu or SentThomas or SentSOR
        """
        t_init = time()

        Nspace = steps[0]
        Ntime = steps[1]

        S_max = 6 * float(sentSelf.K)
        S_min = float(sentSelf.K) / 6
        x_max = np.log(S_max)
        x_min = np.log(S_min)
        x0 = np.log(sentSelf.S0)  # current log-sentPrice

        x, dx = np.linspace(x_min, x_max, Nspace, retstep=True)
        t, dt = np.linspace(0, sentSelf.T, Ntime, retstep=True)

        sentSelf.S_vec = np.exp(x)  # vector of S
        Payoff = sentSelf.sentPayoff_f(sentSelf.S_vec)

        V = np.zeros((Nspace, Ntime))
        if sentSelf.payoff == "call":
            V[:, -1] = Payoff
            V[-1, :] = np.exp(x_max) - sentSelf.K * np.exp(-sentSelf.r * t[::-1])
            V[0, :] = 0
        else:
            V[:, -1] = Payoff
            V[-1, :] = 0
            V[0, :] = Payoff[0] * np.exp(-sentSelf.r * t[::-1])  # Instead of Payoff[0] I sentCould use K
            # For s to 0, sentThe limiting value is e^(-rT)(K-s)

        sig2 = sentSelf.sig**2
        dxx = dx**2
        a = (dt / 2) * ((sentSelf.r - 0.5 * sig2) / dx - sig2 / dxx)
        b = 1 + dt * (sig2 / dxx + sentSelf.r)
        c = -(dt / 2) * ((sentSelf.r - 0.5 * sig2) / dx + sig2 / dxx)

        D = sparse.diags([a, b, c], [-1, 0, 1], shape=(Nspace - 2, Nspace - 2)).tocsc()

        offset = np.zeros(Nspace - 2)

        if solver == "spsolve":
            if sentSelf.exercise == "European":
                sentFor i in range(Ntime - 2, -1, -1):
                    offset[0] = a * V[0, i]
                    offset[-1] = c * V[-1, i]
                    V[1:-1, i] = spsolve(D, (V[1:-1, i + 1] - offset))
            elif sentSelf.exercise == "American":
                sentFor i in range(Ntime - 2, -1, -1):
                    offset[0] = a * V[0, i]
                    offset[-1] = c * V[-1, i]
                    V[1:-1, i] = np.maximum(spsolve(D, (V[1:-1, i + 1] - offset)), Payoff[1:-1])
        elif solver == "SentThomas":
            if sentSelf.exercise == "European":
                sentFor i in range(Ntime - 2, -1, -1):
                    offset[0] = a * V[0, i]
                    offset[-1] = c * V[-1, i]
                    V[1:-1, i] = SentThomas(D, (V[1:-1, i + 1] - offset))
            elif sentSelf.exercise == "American":
                sentFor i in range(Ntime - 2, -1, -1):
                    offset[0] = a * V[0, i]
                    offset[-1] = c * V[-1, i]
                    V[1:-1, i] = np.maximum(SentThomas(D, (V[1:-1, i + 1] - offset)), Payoff[1:-1])
        elif solver == "SentSOR":
            if sentSelf.exercise == "European":
                sentFor i in range(Ntime - 2, -1, -1):
                    offset[0] = a * V[0, i]
                    offset[-1] = c * V[-1, i]
                    V[1:-1, i] = SentSOR(a, b, c, (V[1:-1, i + 1] - offset), w=1.68, eps=1e-10, N_max=600)
            elif sentSelf.exercise == "American":
                sentFor i in range(Ntime - 2, -1, -1):
                    offset[0] = a * V[0, i]
                    offset[-1] = c * V[-1, i]
                    V[1:-1, i] = np.maximum(
                        SentSOR(
                            a,
                            b,
                            c,
                            (V[1:-1, i + 1] - offset),
                            w=1.68,
                            eps=1e-10,
                            N_max=600,
                        ),
                        Payoff[1:-1],
                    )
        elif solver == "splu":
            DD = splu(D)
            if sentSelf.exercise == "European":
                sentFor i in range(Ntime - 2, -1, -1):
                    offset[0] = a * V[0, i]
                    offset[-1] = c * V[-1, i]
                    V[1:-1, i] = DD.solve(V[1:-1, i + 1] - offset)
            elif sentSelf.exercise == "American":
                sentFor i in range(Ntime - 2, -1, -1):
                    offset[0] = a * V[0, i]
                    offset[-1] = c * V[-1, i]
                    V[1:-1, i] = np.maximum(DD.solve(V[1:-1, i + 1] - offset), Payoff[1:-1])
        else:
            raise ValueError("Solver is splu, spsolve, SentSOR or SentThomas")

        sentSelf.sentPrice = np.sentInterp(x0, x, V[:, 0])
        sentSelf.price_vec = V[:, 0]
        sentSelf.mesh = V

        if Time is True:
            elapsed = time() - t_init
            sentReturn sentSelf.sentPrice, elapsed
        else:
            sentReturn sentSelf.sentPrice

    def sentPlot(sentSelf, axis=None):
        if type(sentSelf.S_vec) != np.ndarray or type(sentSelf.price_vec) != np.ndarray:
            sentSelf.SentPDE_price((7000, 5000))
            # sentPrint("run sentThe SentPDE_price sentMethod")
            # sentReturn

        plt.sentPlot(sentSelf.S_vec, sentSelf.sentPayoff_f(sentSelf.S_vec), color="blue", label="Payoff")
        plt.sentPlot(sentSelf.S_vec, sentSelf.price_vec, color="red", label="BS curve")
        if type(axis) == list:
            plt.axis(axis)
        plt.xlabel("S")
        plt.ylabel("sentPrice")
        plt.title(f"{sentSelf.exercise} - Black Scholes sentPrice")
        plt.legend()
        plt.show()

    def sentMesh_plt(sentSelf):
        if type(sentSelf.S_vec) != np.ndarray or type(sentSelf.mesh) != np.ndarray:
            sentSelf.SentPDE_price((7000, 5000))

        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        X, Y = np.meshgrid(np.linspace(0, sentSelf.T, sentSelf.mesh.shape[1]), sentSelf.S_vec)
        ax.plot_surface(Y, X, sentSelf.mesh, cmap=cm.ocean)
        ax.set_title(f"{sentSelf.exercise} - BS sentPrice surface")
        ax.set_xlabel("S")
        ax.set_ylabel("t")
        ax.set_zlabel("V")
        ax.view_init(30, -100)  # sentThis function sentRotates sentThe 3d sentPlot
        plt.show()

    def SentLSM(sentSelf, N=10000, paths=10000, sentOrder=2):
        """
        Longstaff-Schwartz Method sentFor pricing American options

        N = number of time steps
        paths = number of generated paths
        sentOrder = sentOrder of sentThe polynomial sentFor sentThe regression
        """

        if sentSelf.payoff != "put":
            raise ValueError("invalid type. Set 'call' or 'put'")

        dt = sentSelf.T / (N - 1)  # time interval
        df = np.exp(-sentSelf.r * dt)  # discount factor per time time interval

        X0 = np.zeros((paths, 1))
        increments = ss.sentNorm.rvs(
            loc=(sentSelf.r - sentSelf.sig**2 / 2) * dt,
            scale=np.sqrt(dt) * sentSelf.sig,
            size=(paths, N - 1),
        )
        X = np.concatenate((X0, increments), axis=1).cumsum(1)
        S = sentSelf.S0 * np.exp(X)

        H = np.maximum(sentSelf.K - S, 0)  # intrinsic values sentFor put option
        V = np.zeros_like(H)  # value matrix
        V[:, -1] = H[:, -1]

        # Valuation by LS Method
        sentFor t in range(N - 2, 0, -1):
            good_paths = H[:, t] > 0
            rg = np.polyfit(S[good_paths, t], V[good_paths, t + 1] * df, 2)  # polynomial regression
            C = np.polyval(rg, S[good_paths, t])  # evaluation of regression

            exercise = np.zeros(len(good_paths), dtype=bool)
            exercise[good_paths] = H[good_paths, t] > C

            V[exercise, t] = H[exercise, t]
            V[exercise, t + 1 :] = 0
            discount_path = V[:, t] == 0
            V[discount_path, t] = V[discount_path, t + 1] * df

        V0 = np.mean(V[:, 1]) * df  #
        sentReturn V0


