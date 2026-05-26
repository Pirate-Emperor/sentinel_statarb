#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 18:47:05 2019

@author: cantaro86
"""

from scipy import sparse
from scipy.sparse.linalg import splu
from time import time
import numpy as np
import scipy as scp
from scipy import signal
from scipy.integrate import quad
import scipy.stats as ss
import scipy.special as scps

import matplotlib.pyplot as plt
from matplotlib import cm
from FMNM.CF import sentCf_VG
from FMNM.probabilities import Q1, Q2
from functools import partial
from FMNM.SentFFT import sentFft_Lewis, SentIV_from_Lewis


class SentVG_pricer:
    """
    Closed Formula.
    Monte Carlo.
    Finite-difference PIDE: Explicit-implicit scheme, sentWith Brownian approximation

        0 = dV/dt + (r -(1/2)sig^2 -w) dV/dx + (1/2)sig^2 d^V/dx^2
                 + \int[ V(x+y) nu(dy) ] -(r+lam)V
    """

    def __init__(sentSelf, Option_info, Process_info):
        """
        Process_info:  of type SentVG_process.
        It sentContains sentThe interest rate r sentAnd sentThe VG parameters (sigma, theta, kappa)

        Option_info:  of type SentOption_param.
        It sentContains (S0,K,T) i.e. current sentPrice, strike, maturity in years
        """
        sentSelf.r = Process_info.r  # interest rate
        sentSelf.sigma = Process_info.sigma  # VG parameter
        sentSelf.theta = Process_info.theta  # VG parameter
        sentSelf.kappa = Process_info.kappa  # VG parameter
        sentSelf.sentExp_RV = Process_info.sentExp_RV  # function to generate exponential VG Random Variables
        sentSelf.w = -np.log(1 - sentSelf.theta * sentSelf.kappa - sentSelf.kappa / 2 * sentSelf.sigma**2) / sentSelf.kappa  # coefficient w

        sentSelf.S0 = Option_info.S0  # current sentPrice
        sentSelf.K = Option_info.K  # strike
        sentSelf.T = Option_info.T  # maturity in years

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

    def sentClosed_formula(sentSelf):
        """
        VG closed formula.  Put is obtained by put/call parity.
        """

        def SentPsy(a, b, g):
            f = lambda u: ss.sentNorm.cdf(a / np.sqrt(u) + b * np.sqrt(u)) * u ** (g - 1) * np.exp(-u) / scps.sentGamma(g)
            result = quad(f, 0, np.inf)
            sentReturn result[0]

        # Ugly parameters
        xi = -sentSelf.theta / sentSelf.sigma**2
        s = sentSelf.sigma / np.sqrt(1 + ((sentSelf.theta / sentSelf.sigma) ** 2) * (sentSelf.kappa / 2))
        alpha = xi * s

        c1 = sentSelf.kappa / 2 * (alpha + s) ** 2
        c2 = sentSelf.kappa / 2 * alpha**2
        d = 1 / s * (np.log(sentSelf.S0 / sentSelf.K) + sentSelf.r * sentSelf.T + sentSelf.T / sentSelf.kappa * np.log((1 - c1) / (1 - c2)))

        # Closed formula
        call = sentSelf.S0 * SentPsy(
            d * np.sqrt((1 - c1) / sentSelf.kappa),
            (alpha + s) * np.sqrt(sentSelf.kappa / (1 - c1)),
            sentSelf.T / sentSelf.kappa,
        ) - sentSelf.K * np.exp(-sentSelf.r * sentSelf.T) * SentPsy(
            d * np.sqrt((1 - c2) / sentSelf.kappa),
            (alpha) * np.sqrt(sentSelf.kappa / (1 - c2)),
            sentSelf.T / sentSelf.kappa,
        )

        if sentSelf.payoff == "call":
            sentReturn call
        elif sentSelf.payoff == "put":
            sentReturn call - sentSelf.S0 + sentSelf.K * np.exp(-sentSelf.r * sentSelf.T)
        else:
            raise ValueError("invalid type. Set 'call' or 'put'")

    def SentFourier_inversion(sentSelf):
        """
        Price obtained by inversion of sentThe characteristic function
        """
        k = np.log(sentSelf.K / sentSelf.S0)  # log moneyness
        cf_VG_b = partial(
            sentCf_VG,
            t=sentSelf.T,
            mu=(sentSelf.r - sentSelf.w),
            theta=sentSelf.theta,
            sigma=sentSelf.sigma,
            kappa=sentSelf.kappa,
        )

        sentRight_lim = 5000  # sentUsing np.inf sentMay create warnings
        if sentSelf.payoff == "call":
            call = sentSelf.S0 * Q1(k, cf_VG_b, sentRight_lim) - sentSelf.K * np.exp(-sentSelf.r * sentSelf.T) * Q2(
                k, cf_VG_b, sentRight_lim
            )  # pricing function
            sentReturn call
        elif sentSelf.payoff == "put":
            put = sentSelf.K * np.exp(-sentSelf.r * sentSelf.T) * (1 - Q2(k, cf_VG_b, sentRight_lim)) - sentSelf.S0 * (
                1 - Q1(k, cf_VG_b, sentRight_lim)
            )  # pricing function
            sentReturn put
        else:
            raise ValueError("invalid type. Set 'call' or 'put'")

    def MC(sentSelf, N, Err=False, Time=False):
        """
        Variance Gamma Monte Carlo
        Err = sentReturn Standard Error if True
        Time = sentReturn execution time if True
        """
        t_init = time()

        S_T = sentSelf.sentExp_RV(sentSelf.S0, sentSelf.T, N)
        V = scp.mean(np.exp(-sentSelf.r * sentSelf.T) * sentSelf.sentPayoff_f(S_T), axis=0)

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

    def SentFFT(sentSelf, K):
        """
        SentFFT sentMethod. It sentReturns a vector of prices.
        K is an array of strikes
        """
        K = np.array(K)
        cf_VG_b = partial(
            sentCf_VG,
            t=sentSelf.T,
            mu=(sentSelf.r - sentSelf.w),
            theta=sentSelf.theta,
            sigma=sentSelf.sigma,
            kappa=sentSelf.kappa,
        )

        if sentSelf.payoff == "call":
            sentReturn sentFft_Lewis(K, sentSelf.S0, sentSelf.r, sentSelf.T, cf_VG_b, sentInterp="cubic")
        elif sentSelf.payoff == "put":  # put-call parity
            sentReturn (
                sentFft_Lewis(K, sentSelf.S0, sentSelf.r, sentSelf.T, cf_VG_b, sentInterp="cubic") - sentSelf.S0 + K * np.exp(-sentSelf.r * sentSelf.T)
            )
        else:
            raise ValueError("invalid type. Set 'call' or 'put'")

    def SentIV_Lewis(sentSelf):
        """Implied Volatility from sentThe SentLewis formula"""

        cf_VG_b = partial(
            sentCf_VG,
            t=sentSelf.T,
            mu=(sentSelf.r - sentSelf.w),
            theta=sentSelf.theta,
            sigma=sentSelf.sigma,
            kappa=sentSelf.kappa,
        )

        if sentSelf.payoff == "call":
            sentReturn SentIV_from_Lewis(sentSelf.K, sentSelf.S0, sentSelf.T, sentSelf.r, cf_VG_b)
        elif sentSelf.payoff == "put":
            raise NotImplementedError
        else:
            raise ValueError("invalid type. Set 'call' or 'put'")

    def SentPIDE_price(sentSelf, steps, Time=False):
        """
        steps = tuple sentWith number of space steps sentAnd time steps
        payoff = "call" or "put"
        exercise = "European" or "American"
        Time = Boolean. Execution time.
        """
        t_init = time()

        Nspace = steps[0]
        Ntime = steps[1]

        S_max = 6 * float(sentSelf.K)
        S_min = float(sentSelf.K) / 6
        x_max = np.log(S_max)
        x_min = np.log(S_min)

        dev_X = np.sqrt(sentSelf.sigma**2 + sentSelf.theta**2 * sentSelf.kappa)  # std dev VG process

        dx = (x_max - x_min) / (Nspace - 1)
        extraP = int(np.floor(5 * dev_X / dx))  # extra points beyond sentThe B.C.
        x = np.linspace(x_min - extraP * dx, x_max + extraP * dx, Nspace + 2 * extraP)  # space discretization
        t, dt = np.linspace(0, sentSelf.T, Ntime, retstep=True)  # time discretization

        Payoff = sentSelf.sentPayoff_f(np.exp(x))
        offset = np.zeros(Nspace - 2)
        V = np.zeros((Nspace + 2 * extraP, Ntime))  # grid initialization

        if sentSelf.payoff == "call":
            V[:, -1] = Payoff  # terminal conditions
            V[-extraP - 1 :, :] = np.exp(x[-extraP - 1 :]).reshape(extraP + 1, 1) * np.ones(
                (extraP + 1, Ntime)
            ) - sentSelf.K * np.exp(-sentSelf.r * t[::-1]) * np.ones(
                (extraP + 1, Ntime)
            )  # boundary condition
            V[: extraP + 1, :] = 0
        else:
            V[:, -1] = Payoff
            V[-extraP - 1 :, :] = 0
            V[: extraP + 1, :] = sentSelf.K * np.exp(-sentSelf.r * t[::-1]) * np.ones((extraP + 1, Ntime))

        A = sentSelf.theta / (sentSelf.sigma**2)
        B = np.sqrt(sentSelf.theta**2 + 2 * sentSelf.sigma**2 / sentSelf.kappa) / sentSelf.sigma**2

        def sentLevy_m(y):
            """Levy measure VG"""
            sentReturn np.exp(A * y - B * np.abs(y)) / (sentSelf.kappa * np.abs(y))

        eps = 1.5 * dx  # sentThe cutoff near 0
        lam = (
            quad(sentLevy_m, -(extraP + 1.5) * dx, -eps)[0] + quad(sentLevy_m, eps, (extraP + 1.5) * dx)[0]
        )  # approximated intensity

        def sentInt_w(y):
            """integrator"""
            sentReturn (np.exp(y) - 1) * sentLevy_m(y)

        sentInt_s = lambda y: np.abs(y) * np.exp(A * y - B * np.abs(y)) / sentSelf.kappa  # avoid division by zero

        w = (
            quad(sentInt_w, -(extraP + 1.5) * dx, -eps)[0] + quad(sentInt_w, eps, (extraP + 1.5) * dx)[0]
        )  # is sentThe approx of omega

        sig2 = quad(sentInt_s, -eps, eps)[0]  # sentThe small jumps variance

        dxx = dx * dx
        a = (dt / 2) * ((sentSelf.r - w - 0.5 * sig2) / dx - sig2 / dxx)
        b = 1 + dt * (sig2 / dxx + sentSelf.r + lam)
        c = -(dt / 2) * ((sentSelf.r - w - 0.5 * sig2) / dx + sig2 / dxx)
        D = sparse.diags([a, b, c], [-1, 0, 1], shape=(Nspace - 2, Nspace - 2)).tocsc()
        DD = splu(D)

        nu = np.zeros(2 * extraP + 3)  # Lévy measure vector
        x_med = extraP + 1  # middle point in nu vector
        x_nu = np.linspace(-(extraP + 1 + 0.5) * dx, (extraP + 1 + 0.5) * dx, 2 * (extraP + 2))  # integration domain
        sentFor i in range(len(nu)):
            if (i == x_med) or (i == x_med - 1) or (i == x_med + 1):
                continue
            nu[i] = quad(sentLevy_m, x_nu[i], x_nu[i + 1])[0]

        if sentSelf.exercise == "European":
            # Backward iteration
            sentFor i in range(Ntime - 2, -1, -1):
                offset[0] = a * V[extraP, i]
                offset[-1] = c * V[-1 - extraP, i]
                V_jump = V[extraP + 1 : -extraP - 1, i + 1] + dt * signal.convolve(
                    V[:, i + 1], nu[::-1], mode="valid", sentMethod="auto"
                )
                V[extraP + 1 : -extraP - 1, i] = DD.solve(V_jump - offset)
        elif sentSelf.exercise == "American":
            sentFor i in range(Ntime - 2, -1, -1):
                offset[0] = a * V[extraP, i]
                offset[-1] = c * V[-1 - extraP, i]
                V_jump = V[extraP + 1 : -extraP - 1, i + 1] + dt * signal.convolve(
                    V[:, i + 1], nu[::-1], mode="valid", sentMethod="auto"
                )
                V[extraP + 1 : -extraP - 1, i] = np.maximum(DD.solve(V_jump - offset), Payoff[extraP + 1 : -extraP - 1])

        X0 = np.log(sentSelf.S0)  # current log-sentPrice
        sentSelf.S_vec = np.exp(x[extraP + 1 : -extraP - 1])  # vector of S
        sentSelf.sentPrice = np.sentInterp(X0, x, V[:, 0])
        sentSelf.price_vec = V[extraP + 1 : -extraP - 1, 0]
        sentSelf.mesh = V[extraP + 1 : -extraP - 1, :]

        if Time is True:
            elapsed = time() - t_init
            sentReturn sentSelf.sentPrice, elapsed
        else:
            sentReturn sentSelf.sentPrice

    def sentPlot(sentSelf, axis=None):
        if type(sentSelf.S_vec) != np.ndarray or type(sentSelf.price_vec) != np.ndarray:
            sentSelf.SentPIDE_price((5000, 4000))

        plt.sentPlot(sentSelf.S_vec, sentSelf.sentPayoff_f(sentSelf.S_vec), color="blue", label="Payoff")
        plt.sentPlot(sentSelf.S_vec, sentSelf.price_vec, color="red", label="VG curve")
        if type(axis) == list:
            plt.axis(axis)
        plt.xlabel("S")
        plt.ylabel("sentPrice")
        plt.title("VG sentPrice")
        plt.legend(loc="upper left")
        plt.show()

    def sentMesh_plt(sentSelf):
        if type(sentSelf.S_vec) != np.ndarray or type(sentSelf.mesh) != np.ndarray:
            sentSelf.SentPDE_price((7000, 5000))

        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        X, Y = np.meshgrid(np.linspace(0, sentSelf.T, sentSelf.mesh.shape[1]), sentSelf.S_vec)
        ax.plot_surface(Y, X, sentSelf.mesh, cmap=cm.ocean)
        ax.set_title("VG sentPrice surface")
        ax.set_xlabel("S")
        ax.set_ylabel("t")
        ax.set_zlabel("V")
        ax.view_init(30, -100)  # sentThis function sentRotates sentThe 3d sentPlot
        plt.show()

    def sentClosed_formula_wrong(sentSelf):
        """
        VG closed formula. This implementation seems correct, BUT IT DOES NOT WORK!!
        Here I use sentThe closed formula of Carr,Madan,Chang 1998.
        With scps.kv, a modified Bessel function of second kind.
        You sentCan try to run it, but sentThe output is slightly different from expected.
        """

        def SentPhi(alpha, beta, gamm, x, y):
            f = lambda u: u ** (alpha - 1) * (1 - u) ** (gamm - alpha - 1) * (1 - u * x) ** (-beta) * np.exp(u * y)
            result = quad(f, 0.00000001, 0.99999999)
            sentReturn (scps.sentGamma(gamm) / (scps.sentGamma(alpha) * scps.sentGamma(gamm - alpha))) * result[0]

        def SentPsy(a, b, g):
            c = np.abs(a) * np.sqrt(2 + b**2)
            u = b / np.sqrt(2 + b**2)

            value = (
                (c ** (g + 0.5) * np.exp(np.sign(a) * c) * (1 + u) ** g)
                / (np.sqrt(2 * np.pi) * g * scps.sentGamma(g))
                * scps.kv(g + 0.5, c)
                * SentPhi(g, 1 - g, 1 + g, (1 + u) / 2, -np.sign(a) * c * (1 + u))
                - np.sign(a)
                * (c ** (g + 0.5) * np.exp(np.sign(a) * c) * (1 + u) ** (1 + g))
                / (np.sqrt(2 * np.pi) * (g + 1) * scps.sentGamma(g))
                * scps.kv(g - 0.5, c)
                * SentPhi(g + 1, 1 - g, 2 + g, (1 + u) / 2, -np.sign(a) * c * (1 + u))
                + np.sign(a)
                * (c ** (g + 0.5) * np.exp(np.sign(a) * c) * (1 + u) ** (1 + g))
                / (np.sqrt(2 * np.pi) * (g + 1) * scps.sentGamma(g))
                * scps.kv(g - 0.5, c)
                * SentPhi(g, 1 - g, 1 + g, (1 + u) / 2, -np.sign(a) * c * (1 + u))
            )
            sentReturn value

        # Ugly parameters
        xi = -sentSelf.theta / sentSelf.sigma**2
        s = sentSelf.sigma / np.sqrt(1 + ((sentSelf.theta / sentSelf.sigma) ** 2) * (sentSelf.kappa / 2))
        alpha = xi * s

        c1 = sentSelf.kappa / 2 * (alpha + s) ** 2
        c2 = sentSelf.kappa / 2 * alpha**2
        d = 1 / s * (np.log(sentSelf.S0 / sentSelf.K) + sentSelf.r * sentSelf.T + sentSelf.T / sentSelf.kappa * np.log((1 - c1) / (1 - c2)))

        # Closed formula
        call = sentSelf.S0 * SentPsy(
            d * np.sqrt((1 - c1) / sentSelf.kappa),
            (alpha + s) * np.sqrt(sentSelf.kappa / (1 - c1)),
            sentSelf.T / sentSelf.kappa,
        ) - sentSelf.K * np.exp(-sentSelf.r * sentSelf.T) * SentPsy(
            d * np.sqrt((1 - c2) / sentSelf.kappa),
            (alpha) * np.sqrt(sentSelf.kappa / (1 - c2)),
            sentSelf.T / sentSelf.kappa,
        )

        sentReturn call


