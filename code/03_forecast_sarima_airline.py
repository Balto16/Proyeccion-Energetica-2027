"""
03_forecast_sarima_airline.py
-------------------------------
Method 2: SARIMA(0,1,1)(0,1,1)_12 on the natural log of the series
(the canonical Box-Jenkins "Airline Model"). Estimated via Conditional Sum of
Squares (CSS) optimization with scipy.optimize, providing a self-contained
implementation independent of statsmodels.

w_t = (1 - B)(1 - B^12) ln(Y_t)
w_t = e_t - theta * e_{t-1} - Theta * e_{t-12} + theta * Theta * e_{t-13}

Reference:
Box, G. E. P., & Jenkins, G. M. (1976). Time Series Analysis:
Forecasting and Control (2nd ed.). Holden-Day.

Note: In environments where statsmodels is available, the exact equivalent is:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    SARIMAX(np.log(y), order=(0,1,1), seasonal_order=(0,1,1,12)).fit()
This native scipy implementation reproduces this specification directly.

Usage:  python code/03_forecast_sarima_airline.py
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize

_THIS_DIR = Path(__file__).resolve().parent
_ROOT = _THIS_DIR.parent
sys.path.insert(0, str(_THIS_DIR))
os.chdir(_ROOT)


def airline_residuals(params, w):
    """
    Computes moving average residuals recursively for the multiplicative Airline model.
    """
    theta, Theta = params
    n = len(w)
    e = np.zeros(n)
    for t in range(n):
        et1 = e[t - 1] if t - 1 >= 0 else 0.0
        et12 = e[t - 12] if t - 12 >= 0 else 0.0
        et13 = e[t - 13] if t - 13 >= 0 else 0.0
        e[t] = w[t] + theta * et1 + Theta * et12 - theta * Theta * et13
    return e


def _sse(params, w):
    """Sum of squared residuals (CSS objective function)."""
    e = airline_residuals(params, w)
    return np.sum(e**2)


def fit_airline(y, season=12):
    """
    Fits the SARIMA(0,1,1)(0,1,1)_s Airline model to series y.

    Returns:
        tuple: (theta, Theta, sigma2, logy, d1, w, residuals)
    """
    logy = np.log(y)
    d1 = np.diff(logy, n=1)
    w = d1[season:] - d1[:-season]
    res = minimize(
        _sse,
        x0=[0.3, 0.3],
        args=(w,),
        method="Nelder-Mead",
        options={"xatol": 1e-8, "fatol": 1e-10, "maxiter": 5000},
    )
    theta, Theta = res.x
    sigma2 = res.fun / len(w)
    resid = airline_residuals([theta, Theta], w)
    return theta, Theta, sigma2, logy, d1, w, resid


def airline_forecast(y, n_future, season=12):
    """
    Generates multi-step ahead out-of-sample forecasts from the fitted Airline model.
    Includes log-normal bias adjustment: E[exp(X)] = exp(mu + sigma^2 / 2).

    Parameters:
        y (array-like): Historical values.
        n_future (int): Horizon of forecast periods.
        season (int): Seasonal period (default 12 for monthly data).

    Returns:
        tuple: (forecast_array, theta, Theta, sigma2)
    """
    theta, Theta, sigma2, logy, d1, w, e = fit_airline(y, season)

    e_ext = np.concatenate([e, np.zeros(n_future)])
    w_ext = list(w)
    n_w = len(w)
    for h in range(n_future):
        t = n_w + h
        et1 = e_ext[t - 1] if t - 1 >= 0 else 0.0
        et12 = e_ext[t - 12] if t - 12 >= 0 else 0.0
        et13 = e_ext[t - 13] if t - 13 >= 0 else 0.0
        w_ext.append(-theta * et1 - Theta * et12 + theta * Theta * et13)
    w_ext = np.array(w_ext)

    d1_full = list(d1)
    for h in range(n_future):
        idx = len(d1_full)
        d1_full.append(d1_full[idx - season] + w_ext[idx - season])
    d1_full = np.array(d1_full)

    logy_full = list(logy)
    for h in range(n_future):
        idx = len(logy_full)
        logy_full.append(logy_full[idx - 1] + d1_full[idx - 1])
    logy_full = np.array(logy_full)

    # Lognormal bias correction: E[exp(X)] = exp(mu + sigma^2 / 2)
    y_full = np.exp(logy_full) * np.exp(sigma2 / 2.0)
    forecast = y_full[len(y):]
    return forecast, theta, Theta, sigma2


if __name__ == "__main__":
    monthly = pd.read_csv("data/monthly.csv", parse_dates=["fecha"])
    print("Method 2 — SARIMA Airline Model Parameters & Initial Forecasts:")
    for var in ["consumo_kwh", "demanda_kw", "tarifa_prom"]:
        y = monthly[var].values.astype(float)
        fc, theta, Theta, sigma2 = airline_forecast(y, n_future=20)
        print(f"  {var:<15}: theta={theta:.3f}, Theta={Theta:.3f} | First 3 forecasts: {np.round(fc[:3], 4)}")
