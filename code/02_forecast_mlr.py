"""
02_forecast_mlr.py
-------------------
Method 1: Multiple Linear Regression (MLR) with deterministic linear trend
and monthly seasonality (11 dummy variables with January as baseline).

Y_t = beta_0 + beta_1 * t + sum_{m=2}^{12} (beta_m * D_{m,t}) + epsilon_t

Reference:
Kialashaki, A., & Reisel, J. R. (2013). Modeling of the energy demand of the
residential sector in the United States using regression models and artificial
neural networks. Applied Energy, 108, 271-280.

Usage:  python code/02_forecast_mlr.py
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
_ROOT = _THIS_DIR.parent
sys.path.insert(0, str(_THIS_DIR))
os.chdir(_ROOT)


def mlr_forecast(y, dates, n_future):
    """
    Fits an OLS regression with linear trend and 11 seasonal monthly dummy variables.

    Parameters:
        y (array-like): Historical values.
        dates (pd.Series or DatetimeIndex): Corresponding datetime timestamps.
        n_future (int): Number of future monthly periods to project.

    Returns:
        tuple: (future_dates, yhat_future, in_sample_r2, beta_coefficients)
    """
    dates = pd.Series(dates).reset_index(drop=True)
    t = np.arange(len(y))
    months = dates.dt.month.values

    # Design matrix: intercept, linear trend, and 11 month indicators (Feb-Dec)
    X = [np.ones_like(t), t]
    for m in range(2, 13):
        X.append((months == m).astype(float))
    X = np.array(X).T

    # Ordinary Least Squares fit
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fitted = X @ beta
    resid = y - fitted
    r2 = 1.0 - np.sum(resid**2) / np.sum((y - y.mean()) ** 2)

    # Future dates and design matrix
    last_date = dates.iloc[-1]
    future_dates = pd.date_range(last_date + pd.offsets.MonthBegin(1), periods=n_future, freq="MS")
    t_f = np.arange(len(y), len(y) + n_future)
    months_f = future_dates.month.values

    Xf = [np.ones_like(t_f), t_f]
    for m in range(2, 13):
        Xf.append((months_f == m).astype(float))
    Xf = np.array(Xf).T

    yhat = Xf @ beta
    return future_dates, yhat, r2, beta


if __name__ == "__main__":
    monthly = pd.read_csv("data/monthly.csv", parse_dates=["fecha"])
    print("Method 1 — Multiple Linear Regression (MLR) In-Sample Fit:")
    for var in ["consumo_kwh", "demanda_kw", "tarifa_prom"]:
        y = monthly[var].values.astype(float)
        future_dates, yhat, r2, beta = mlr_forecast(y, monthly["fecha"], n_future=20)
        print(f"  {var:<15}: In-sample R^2 = {r2:.3f}")

