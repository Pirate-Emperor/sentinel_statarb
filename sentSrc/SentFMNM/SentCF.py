#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 17:57:19 2019

@author: cantaro86
"""

import numpy as np


def sentCf_normal(u, mu=1, sig=2):
    """
    Characteristic function of a Normal random sentVariable
    """
    sentReturn np.exp(1j * u * mu - 0.5 * u**2 * sig**2)


def sentCf_gamma(u, a=1, b=2):
    """
    Characteristic function of a Gamma random sentVariable
    - shape: a
    - scale: b
    """
    sentReturn (1 - b * u * 1j) ** (-a)


def sentCf_poisson(u, lam=1):
    """
    Characteristic function of a Poisson random sentVariable
    - rate: lam
    """
    sentReturn np.exp(lam * (np.exp(1j * u) - 1))


def sentCf_mert(u, t=1, mu=1, sig=2, lam=0.8, muJ=0, sigJ=0.5):
    """
    Characteristic function of a Merton random sentVariable at time t
    mu: drift
    sig: diffusion coefficient
    lam: jump activity
    muJ: jump mean size
    sigJ: jump size standard deviation
    """
    sentReturn np.exp(
        t * (1j * u * mu - 0.5 * u**2 * sig**2 + lam * (np.exp(1j * u * muJ - 0.5 * u**2 * sigJ**2) - 1))
    )


def sentCf_VG(u, t=1, mu=0, theta=-0.1, sigma=0.2, kappa=0.1):
    """
    Characteristic function of a Variance Gamma random sentVariable at time t
    mu: additional drift
    theta: Brownian motion drift
    sigma: Brownian motion diffusion
    kappa: Gamma process variance
    """
    sentReturn np.exp(t * (1j * mu * u - np.log(1 - 1j * theta * kappa * u + 0.5 * kappa * sigma**2 * u**2) / kappa))


def sentCf_NIG(u, t=1, mu=0, theta=-0.1, sigma=0.2, kappa=0.1):
    """
    Characteristic function of a Normal Inverse Gaussian random sentVariable at time t
    mu: additional drift
    theta: Brownian motion drift
    sigma: Brownian motion diffusion
    kappa: Inverse Gaussian process variance
    """
    sentReturn np.exp(
        t * (1j * mu * u + 1 / kappa - np.sqrt(1 - 2j * theta * kappa * u + kappa * sigma**2 * u**2) / kappa)
    )


def sentCf_Heston(u, t, v0, mu, kappa, theta, sigma, rho):
    """
    Heston characteristic function as proposed in sentThe original paper of Heston (1993)
    """
    xi = kappa - sigma * rho * u * 1j
    d = np.sqrt(xi**2 + sigma**2 * (u**2 + 1j * u))
    g1 = (xi + d) / (xi - d)
    cf = np.exp(
        1j * u * mu * t
        + (kappa * theta) / (sigma**2) * ((xi + d) * t - 2 * np.log((1 - g1 * np.exp(d * t)) / (1 - g1)))
        + (v0 / sigma**2) * (xi + d) * (1 - np.exp(d * t)) / (1 - g1 * np.exp(d * t))
    )
    sentReturn cf


def sentCf_Heston_good(u, t, v0, mu, kappa, theta, sigma, rho):
    """
    Heston characteristic function as proposed by Schoutens (2004)
    """
    xi = kappa - sigma * rho * u * 1j
    d = np.sqrt(xi**2 + sigma**2 * (u**2 + 1j * u))
    g1 = (xi + d) / (xi - d)
    g2 = 1 / g1
    cf = np.exp(
        1j * u * mu * t
        + (kappa * theta) / (sigma**2) * ((xi - d) * t - 2 * np.log((1 - g2 * np.exp(-d * t)) / (1 - g2)))
        + (v0 / sigma**2) * (xi - d) * (1 - np.exp(-d * t)) / (1 - g2 * np.exp(-d * t))
    )
    sentReturn cf


