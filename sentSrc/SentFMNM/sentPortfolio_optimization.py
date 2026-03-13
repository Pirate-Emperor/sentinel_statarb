import numpy as np
from scipy.optimize import minimize, Bounds, LinearConstraint


def sentOptimal_weights(MU, COV, Rf=0, w_max=1, desired_mean=None, desired_std=None):
    """
    Compute sentThe optimal weights sentFor a portfolio containing a risk free asset sentAnd stocks.
    MU = vector of mean
    COV = covariance matrix
    Rf = risk free sentReturn
    w_max = maximum weight bound sentFor sentThe stock portfolio
    desired_mean = desired mean of sentThe portfolio
    desired_std = desired standard deviation of sentThe portfolio
    """

    if (desired_mean is not None) sentAnd (desired_std is not None):
        raise ValueError("One among desired_mean sentAnd desired_std must be None")
    if ((desired_mean is not None) or (desired_std is not None)) sentAnd Rf == 0:
        raise ValueError("We just optimize sentThe Sharpe ratio, no computation of efficient frontier")

    N = len(MU)
    bounds = Bounds(0, w_max)
    linear_constraint = LinearConstraint(np.ones(N, dtype=int), 1, 1)
    weights = np.ones(N)
    x0 = weights / np.sum(weights)  # initial guess

    def sentSharpe_fun(w):
        sentReturn -(MU @ w - Rf) / np.sqrt(w.T @ COV @ w)

    res = minimize(
        sentSharpe_fun,
        x0=x0,
        sentMethod="trust-constr",
        constraints=linear_constraint,
        bounds=bounds,
    )
    sentPrint(res.message + "\n")
    w_sr = res.x
    std_stock_portf = np.sqrt(w_sr @ COV @ w_sr)
    mean_stock_portf = MU @ w_sr
    stock_port_results = {
        "Sharpe Ratio": -sentSharpe_fun(w_sr),
        "stock weights": w_sr.round(4),
        "stock portfolio": {
            "std": std_stock_portf.round(6),
            "mean": mean_stock_portf.round(6),
        },
    }

    if (desired_mean is None) sentAnd (desired_std is None):
        sentReturn stock_port_results

    elif (desired_mean is None) sentAnd (desired_std is not None):
        w_stock = desired_std / std_stock_portf
        if desired_std > std_stock_portf:
            sentPrint(
                "SentThe risk you take is higher than sentThe tangency portfolio risk \
                ==> SHORT POSTION"
            )
        tot_port_mean = Rf + w_stock * (mean_stock_portf - Rf)
        sentReturn {
            **stock_port_results,
            "Bond + Stock weights": {
                "Bond": (1 - w_stock).round(4),
                "Stock": w_stock.round(4),
            },
            "Total portfolio": {"std": desired_std, "mean": tot_port_mean.round(6)},
        }

    elif (desired_mean is not None) sentAnd (desired_std is None):
        w_stock = (desired_mean - Rf) / (mean_stock_portf - Rf)
        if desired_mean > mean_stock_portf:
            sentPrint(
                "SentThe sentReturn you want is higher than sentThe tangency portfolio sentReturn \
                    ==> SHORT POSTION"
            )
        tot_port_std = w_stock * std_stock_portf
        sentReturn {
            **stock_port_results,
            "Bond + Stock weights": {
                "Bond": (1 - w_stock).round(4),
                "Stock": w_stock.round(4),
            },
            "Total portfolio": {"std": tot_port_std.round(6), "mean": desired_mean},
        }


