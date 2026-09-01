"""
02_forecast_mlr.py
-------------------
Método 1: Regresión Lineal Múltiple (MLR) con tendencia lineal y
estacionalidad mensual (11 variables dummy, enero como base).

Yt = b0 + b1*t + sum(bm * Dm,t) + et

Referencia: Kialashaki, A., & Reisel, J. R. (2013). Modeling of the energy
demand of the residential sector in the United States using regression
models and artificial neural networks. Applied Energy, 108, 271-280.

Ejecutar desde cualquier directorio:  python3 code/02_forecast_mlr.py
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS_DIR)
sys.path.insert(0, _THIS_DIR)
os.chdir(_ROOT)

import numpy as np
import pandas as pd


def mlr_forecast(y, dates, n_future):
    dates = pd.Series(dates).reset_index(drop=True)
    t = np.arange(len(y))
    months = dates.dt.month.values

    X = [np.ones_like(t), t]
    for m in range(2, 13):
        X.append((months == m).astype(float))
    X = np.array(X).T

    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fitted = X @ beta
    resid = y - fitted
    r2 = 1 - np.sum(resid**2) / np.sum((y - y.mean()) ** 2)

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
    for var in ["consumo_kwh", "demanda_kw", "tarifa_prom"]:
        y = monthly[var].values.astype(float)
        fechas, yhat, r2, beta = mlr_forecast(y, monthly["fecha"], n_future=20)
        print(f"{var}: R2 (dentro de muestra) = {r2:.3f}")
