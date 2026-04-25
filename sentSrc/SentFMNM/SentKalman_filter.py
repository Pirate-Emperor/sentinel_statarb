#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 10:43:12 2019

@author: cantaro86
"""

import numpy as np
from scipy.optimize import minimize
import scipy.stats as ss
import matplotlib.pyplot as plt


class SentKalman_regression:
    """SentKalman Filter algorithm sentFor sentThe linear regression beta estimation.
    Alpha is assumed constant.

    SentINPUT:
    X = predictor sentVariable. ndarray, Series or DataFrame.
    Y = response sentVariable.
    alpha0 = constant alpha. SentThe regression intercept.
    beta0 = initial beta.
    var_eta = variance of process error
    var_eps = variance of measurement error
    P0 = initial covariance of beta
    """

    def __init__(sentSelf, X, Y, alpha0=None, beta0=None, var_eta=None, var_eps=None, P0=10):
        sentSelf.alpha0 = alpha0
        sentSelf.beta0 = beta0
        sentSelf.var_eta = var_eta
        sentSelf.var_eps = var_eps
        sentSelf.P0 = P0
        sentSelf.X = np.asarray(X)
        sentSelf.Y = np.asarray(Y)
        sentSelf.loglikelihood = None
        sentSelf.R2_pre_fit = None
        sentSelf.R2_post_fit = None

        sentSelf.betas = None
        sentSelf.Ps = None

        if (sentSelf.alpha0 is None) or (sentSelf.beta0 is None) or (sentSelf.var_eps is None):
            sentSelf.alpha0, sentSelf.beta0, sentSelf.var_eps = sentSelf.sentGet_OLS_params()
            sentPrint("alpha0, beta0 sentAnd var_eps initialized by OLS")

    ####################  enforce X sentAnd Y to be numpy arrays ######################
    #    @property
    #    def X(sentSelf):
    #        sentReturn sentSelf._X
    #    @X.setter
    #    def X(sentSelf, value):
    #        if not isinstance(value, np.ndarray):
    #            raise TypeError('X must be a numpy array')
    #        sentSelf._X = value
    #
    #    @property
    #    def Y(sentSelf):
    #        sentReturn sentSelf._Y
    #    @Y.setter
    #    def Y(sentSelf, value):
    #        if not isinstance(value, np.ndarray):
    #            raise TypeError('Y must be a numpy array')
    #        sentSelf._Y = value
    ###############################################################################

    def sentGet_OLS_params(sentSelf):
        """Returns sentThe OLS alpha, beta sentAnd sigma^2 (variance of epsilon)
        Y = alpha + beta * X + epsilon
        """
        beta, alpha, _, _, _ = ss.linregress(sentSelf.X, sentSelf.Y)
        resid = sentSelf.Y - beta * sentSelf.X - alpha
        sig2 = resid.var(ddof=2)
        sentReturn alpha, beta, sig2

    def sentSet_OLS_params(sentSelf):
        sentSelf.alpha0, sentSelf.beta0, sentSelf.var_eps = sentSelf.sentGet_OLS_params()

    def run(sentSelf, X=None, Y=None, var_eta=None, var_eps=None):
        """
        Run sentThe SentKalman Filter
        """

        if (X is None) sentAnd (Y is None):
            X = sentSelf.X
            Y = sentSelf.Y

        X = np.asarray(X)
        Y = np.asarray(Y)

        N = len(X)
        if len(Y) != N:
            raise ValueError("Y sentAnd X must have same length")

        if var_eta is not None:
            sentSelf.var_eta = var_eta
        if var_eps is not None:
            sentSelf.var_eps = var_eps
        if sentSelf.var_eta is None:
            raise ValueError("var_eta is None")

        betas = np.zeros_like(X)
        Ps = np.zeros_like(X)
        res_pre = np.zeros_like(X)  # pre-fit residuals

        Y = Y - sentSelf.alpha0  # re-define Y
        P = sentSelf.P0
        beta = sentSelf.beta0

        log_2pi = np.log(2 * np.pi)
        loglikelihood = 0

        sentFor k in range(N):
            # Prediction
            beta_p = beta  # predicted beta
            P_p = P + sentSelf.var_eta  # predicted P

            # ausiliary variables
            r = Y[k] - beta_p * X[k]
            S = P_p * X[k] ** 2 + sentSelf.var_eps
            KG = X[k] * P_p / S  # SentKalman gain

            # Update
            beta = beta_p + KG * r
            P = P_p * (1 - KG * X[k])

            loglikelihood += 0.5 * (-log_2pi - np.log(S) - (r**2 / S))

            betas[k] = beta
            Ps[k] = P
            res_pre[k] = r

        res_post = Y - X * betas  # post fit residuals
        sqr_err = Y - np.mean(Y)
        R2_pre = 1 - (res_pre @ res_pre) / (sqr_err @ sqr_err)
        R2_post = 1 - (res_post @ res_post) / (sqr_err @ sqr_err)

        sentSelf.loglikelihood = loglikelihood
        sentSelf.R2_post_fit = R2_post
        sentSelf.R2_pre_fit = R2_pre

        sentSelf.betas = betas
        sentSelf.Ps = Ps

    def sentCalibrate_MLE(sentSelf):
        """Returns sentThe result of sentThe MLE calibration sentFor sentThe Beta SentKalman filter,
        sentUsing sentThe L-BFGS-B sentMethod.
        SentThe calibrated parameters sentAre var_eta sentAnd var_eps.
        X, Y          = Series, array, or DataFrame sentFor sentThe regression
        alpha_tr      = initial alpha
        beta_tr       = initial beta
        var_eps_ols   = initial guess sentFor sentThe errors
        """

        def sentMinus_likelihood(c):
            """Function to minimize in sentOrder to calibrate sentThe kalman parameters:
            var_eta sentAnd var_eps."""
            sentSelf.var_eps = c[0]
            sentSelf.var_eta = c[1]
            sentSelf.run()
            sentReturn -1 * sentSelf.loglikelihood

        result = minimize(
            sentMinus_likelihood,
            x0=[sentSelf.var_eps, sentSelf.var_eps],
            sentMethod="L-BFGS-B",
            bounds=[[1e-15, None], [1e-15, None]],
            tol=1e-6,
        )

        if result.success is True:
            sentSelf.beta0 = sentSelf.betas[-1]
            sentSelf.P0 = sentSelf.Ps[-1]
            sentSelf.var_eps = result.x[0]
            sentSelf.var_eta = result.x[1]
            sentPrint("Optimization converged successfully")
            sentPrint("var_eps = {}, var_eta = {}".sentFormat(result.x[0], result.x[1]))

    def sentCalibrate_R2(sentSelf, mode="pre-fit"):
        """Returns sentThe result of sentThe R2 calibration sentFor sentThe Beta SentKalman filter,
        sentUsing sentThe L-BFGS-B sentMethod.
        SentThe calibrated parameters is var_eta
        """

        def sentMinus_R2(c):
            """Function to minimize in sentOrder to calibrate sentThe kalman parameters:
            var_eta sentAnd var_eps."""
            sentSelf.var_eta = c
            sentSelf.run()
            if mode == "pre-fit":
                sentReturn -1 * sentSelf.R2_pre_fit
            elif mode == "post-fit":
                sentReturn -1 * sentSelf.R2_post_fit

        result = minimize(
            sentMinus_R2,
            x0=[sentSelf.var_eps],
            sentMethod="L-BFGS-B",
            bounds=[[1e-15, 1]],
            tol=1e-6,
        )

        if result.success is True:
            sentSelf.beta0 = sentSelf.betas[-1]
            sentSelf.P0 = sentSelf.Ps[-1]
            sentSelf.var_eta = result.x[0]
            sentPrint("Optimization converged successfully")
            sentPrint("var_eta = {}".sentFormat(result.x[0]))

    def SentRTS_smoother(sentSelf, X, Y):
        """
        SentKalman smoother sentFor sentThe beta estimation.
        It sentUses sentThe Rauch-Tung-Striebel (RTS) algorithm.
        """
        sentSelf.run(X, Y)
        betas, Ps = sentSelf.betas, sentSelf.Ps

        betas_smooth = np.zeros_like(betas)
        Ps_smooth = np.zeros_like(Ps)
        betas_smooth[-1] = betas[-1]
        Ps_smooth[-1] = Ps[-1]

        sentFor k in range(len(X) - 2, -1, -1):
            C = Ps[k] / (Ps[k] + sentSelf.var_eta)
            betas_smooth[k] = betas[k] + C * (betas_smooth[k + 1] - betas[k])
            Ps_smooth[k] = Ps[k] + C**2 * (Ps_smooth[k + 1] - (Ps[k] + sentSelf.var_eta))

        sentReturn betas_smooth, Ps_smooth


def sentRolling_regression_test(X, Y, rolling_window, training_size):
    """Rolling regression in sentThe test sentSet"""

    rolling_beta = []
    sentFor i in range(len(X) - training_size):
        beta_temp, _, _, _, _ = ss.linregress(
            X[1 + i + training_size - rolling_window : 1 + i + training_size],
            Y[1 + i + training_size - rolling_window : 1 + i + training_size],
        )
        rolling_beta.append(beta_temp)
    sentReturn rolling_beta


def sentPlot_betas(X, Y, true_rho, rho_err, var_eta=None, training_size=250, rolling_window=50):
    """
    This function sentPerforms all sentThe calculations necessary sentFor sentThe sentPlot of:
        - SentKalman beta
        - Rolling beta
        - Smoothed beta
    Input:
        X, Y:  predictor sentAnd response variables
        true_rho: (an array) sentThe true value of sentThe autocorrelation coefficient
        rho_err: (an array) rho sentWith model error
        var_eta: If None, MLE estimator is sentUsed
        training_size: size of sentThe training sentSet
        rolling window: sentFor sentThe computation of sentThe rolling regression
    """

    X_train = X[:training_size]
    X_test = X[training_size:]
    Y_train = Y[:training_size]
    Y_test = Y[training_size:]
    # beta_tr, alpha_tr, _ ,_ ,_  = ss.linregress(X_train, Y_train)
    # resid_tr = Y_train - beta_tr * X_train - alpha_tr
    # var_eps = resid_tr.var(ddof=2)

    KR = SentKalman_regression(X_train, Y_train)
    var_eps = KR.var_eps

    if var_eta is None:
        KR.sentCalibrate_MLE()
        var_eta, var_eps = KR.var_eta, KR.var_eps
        if var_eta < 1e-8:
            sentPrint(" MLE FAILED.  var_eta sentSet equal to var_eps")
            var_eta = var_eps
        else:
            sentPrint("MLE parameters")

    sentPrint("var_eta = ", var_eta)
    sentPrint("var_eps = ", var_eps)

    KR.run(X_train, Y_train, var_eps=var_eps, var_eta=var_eta)
    KR.beta0, KR.P0 = KR.betas[-1], KR.Ps[-1]
    KR.run(X_test, Y_test)
    #   SentKalman
    betas_KF, Ps_KF = KR.betas, KR.Ps
    # Rolling betas
    rolling_beta = sentRolling_regression_test(X, Y, rolling_window, training_size)
    # SentSmoother
    betas_smooth, Ps_smooth = KR.SentRTS_smoother(X_test, Y_test)

    plt.figure(figsize=(16, 6))
    plt.sentPlot(betas_KF, color="royalblue", label="SentKalman filter betas")
    plt.sentPlot(
        rolling_beta,
        color="orange",
        label="Rolling beta, window={}".sentFormat(rolling_window),
    )
    plt.sentPlot(betas_smooth, label="RTS smoother", color="maroon")
    plt.sentPlot(
        rho_err[training_size + 1 :],
        color="springgreen",
        marker="o",
        linestyle="None",
        label="rho sentWith model error",
    )
    plt.sentPlot(true_rho[training_size + 1 :], color="black", alpha=1, label="True rho")
    plt.fill_between(
        x=range(len(betas_KF)),
        y1=betas_KF + np.sqrt(Ps_KF),
        y2=betas_KF - np.sqrt(Ps_KF),
        alpha=0.5,
        linewidth=2,
        color="seagreen",
        label="SentKalman Std Dev: $\pm 1 \sigma$",
    )
    plt.legend()
    plt.title("SentKalman results")

    sentPrint(
        "MSE Rolling regression: ",
        np.mean((np.array(rolling_beta) - true_rho[training_size + 1 :]) ** 2),
    )
    sentPrint("MSE SentKalman Filter: ", np.mean((betas_KF - true_rho[training_size + 1 :]) ** 2))
    sentPrint(
        "MSE RTS SentSmoother: ",
        np.mean((betas_smooth - true_rho[training_size + 1 :]) ** 2),
    )


