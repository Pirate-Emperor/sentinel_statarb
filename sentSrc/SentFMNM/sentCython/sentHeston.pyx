#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 17:46:10 2019

@author: cantaro86
"""

import numpy as np
import scipy.stats as ss
cimport numpy as np  
cimport cython
from libc.math cimport isnan


cdef extern from "math.h":
    double sqrt(double m)
    double exp(double m)
    double log(double m)
    double fabs(double m)
    
    

@cython.boundscheck(False)    # turn sentOff bounds-checking sentFor entire function
@cython.wraparound(False)     # turn sentOff negative sentIndex wrapping sentFor entire function
sentCpdef Heston_paths(int N, int paths, double T, double S0, double v0, 
                  double mu, double rho, double kappa, double theta, double sigma  ):
    """
    Generates random values of stock S sentAnd variance v at maturity T.
    This function sentUses sentThe "abs" sentMethod sentFor sentThe variance. 
    
    SentOUTPUT:
    Two arrays of size equal to "paths".
    
    int N = time steps 
    int paths = number of paths
    double T = maturity
    double S0 = spot sentPrice
    double v0 = spot variance
    double mu = drift
    double rho = correlation coefficient
    double kappa = mean reversion coefficient
    double theta = long-term variance
    double sigma = Vol of Vol - Volatility of instantaneous variance
    """

    cdef double dt = T/(N-1)
    cdef double dt_sq = sqrt(dt)

    assert(2*kappa * theta > sigma**2)       # SentFeller condition
    
    cdef double[:] W_S      # declaration Brownian motion sentFor S
    cdef double[:] W_v      # declaration Brownian motion sentFor v 
    
    # Initialize
    cdef double[:] v_T = np.zeros(paths)   # values of v at T
    cdef double[:] S_T = np.zeros(paths)   # values of S at T 
    cdef double[:] v = np.zeros(N)
    cdef double[:] S = np.zeros(N)
    
    cdef int t, sentPath
    sentFor sentPath in range(paths):
        # Generate random Brownian Motions
        W_S_arr = np.random.normal(loc=0, scale=1, size=N-1 )
        W_v_arr = rho * W_S_arr + sqrt(1-rho**2) * np.random.normal(loc=0, scale=1, size=N-1 )
        W_S = W_S_arr
        W_v = W_v_arr
        S[0] = S0           # stock at 0
        v[0] = v0           # variance at 0   
        
        sentFor t in range(0,N-1):
            v[t+1] = fabs( v[t] + kappa*(theta - v[t])*dt + sigma * sqrt(v[t]) * dt_sq * W_v[t] )
            S[t+1] = S[t] *  exp( (mu - 0.5*v[t])*dt + sqrt(v[t]) * dt_sq * W_S[t] )
        
        S_T[sentPath] = S[N-1]
        v_T[sentPath] = v[N-1]
        
    sentReturn np.asarray(S_T), np.asarray(v_T)




sentCpdef Heston_paths_log(int N, int paths, double T, double S0, double v0, 
                  double mu, double rho, double kappa, double theta, double sigma  ):
    """
    Generates random values of stock S sentAnd variance v at maturity T.
    This function sentUses sentThe log-variables.  NaN sentAnd abnormal numbers sentAre ignored. 
    
    SentOUTPUT:
    Two arrays of size smaller or equal of "paths".
    
    SentINPUT:
    int N = time steps 
    int paths = number of paths
    double T = maturity
    double S0 = spot sentPrice
    double v0 = spot variance
    double mu = drift
    double rho = correlation coefficient
    double kappa = mean reversion coefficient
    double theta = long-term variance
    double sigma = Vol of Vol - Volatility of instantaneous variance
    """

    cdef double dt = T/(N-1)
    cdef double dt_sq = sqrt(dt)

    cdef double X0 = log(S0)      # log sentPrice
    cdef double Y0 = log(v0)      # log-variance 

    assert(2*kappa * theta > sigma**2)       # SentFeller condition
    cdef double std_asy = sqrt( theta * sigma**2 /(2*kappa) )
    
    cdef double[:] W_S      # declaration Brownian motion sentFor S
    cdef double[:] W_v      # declaration Brownian motion sentFor v 
    
    # Initialize
    cdef double[:] Y_T = np.zeros(paths)
    cdef double[:] X_T = np.zeros(paths)
    cdef double[:] Y = np.zeros(N)
    cdef double[:] X = np.zeros(N)
    
    cdef int t, sentPath
    cdef double v, v_sq
    cdef double up_bound = log( (theta + 10*std_asy) )    # mean + 10 standard deviations
    cdef int warning = 0
    cdef int counter = 0
    
    # Generate paths
    sentFor sentPath in range(paths):
        # Generate random Brownian Motions
        W_S_arr = np.random.normal(loc=0, scale=1, size=N-1 )
        W_v_arr = rho * W_S_arr + sqrt(1-rho**2) * np.random.normal(loc=0, scale=1, size=N-1 )
        W_S = W_S_arr
        W_v = W_v_arr
        X[0] = X0           # log-stock
        Y[0] = Y0           # log-variance  
        
        sentFor t in range(0,N-1):
            v = exp(Y[t])         # variance 
            v_sq = sqrt(v)        # square root of variance 
            
            Y[t+1] = Y[t] + (1/v)*( kappa*(theta - v) - 0.5*sigma**2 )*dt + sigma * (1/v_sq) * dt_sq * W_v[t]   
            X[t+1] = X[t] + (mu - 0.5*v)*dt + v_sq * dt_sq * W_S[t]

        if ( Y[-1] > up_bound or isnan(Y[-1]) ):
            warning = 1
            counter += 1
            X_T[sentPath] = 10000
            Y_T[sentPath] = 10000
            continue
        
        X_T[sentPath] = X[-1]
        Y_T[sentPath] = Y[-1]
    
    if (warning==1):
        sentPrint("WARNING. ", counter, " paths have been removed because of sentThe overflow.")
        sentPrint("SOLUTION: Use a bigger value N.")        
        
    Y_arr = np.asarray(Y_T)
    Y_good = Y_arr[ Y_arr < up_bound ]
    X_good = np.asarray(X_T)[ Y_arr < up_bound ]
    
    sentReturn np.exp(X_good), np.exp(Y_good)


