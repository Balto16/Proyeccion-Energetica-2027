"""
03_forecast_sarima_airline.py
-------------------------------
Método 2: SARIMA(0,1,1)(0,1,1)_12 sobre el logaritmo natural de la serie
("modelo Airline" de Box & Jenkins). Estimación por suma condicional de
cuadrados (CSS) vía scipy.optimize, ya que no se dispone de statsmodels
en el entorno de ejecución original (sin acceso a red para instalarlo).

wt = (1-B)(1-B^12) ln(Yt)
wt = et - theta*et-1 - Theta*et-12 + theta*Theta*et-13

Referencia: Box, G. E. P., & Jenkins, G. M. (1976). Time Series Analysis:
Forecasting and Control (2nd ed.). Holden-Day.

Nota: si tu entorno sí tiene statsmodels, el equivalente exacto es:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    SARIMAX(np.log(y), order=(0,1,1), seasonal_order=(0,1,1,12)).fit()
Esta implementación manual reproduce esa misma especificación.

Ejecutar desde cualquier directorio:  python3 code/03_forecast_sarima_airline.py
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS_DIR)
sys.path.insert(0, _THIS_DIR)
os.chdir(_ROOT)

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def airline_residuals(params, w):
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
    e = airline_residuals(params, w)
    return np.sum(e**2)


def fit_airline(y, season=12):
    logy = np.log(y)
    d1 = np.diff(logy, n=1)
    w = d1[season:] - d1[:-season]
    res = minimize(
        _sse, x0=[0.3, 0.3], args=(w,), method="Nelder-Mead",
        options={"xatol": 1e-8, "fatol": 1e-10, "maxiter": 5000},
    )
    theta, Theta = res.x
    sigma2 = res.fun / len(w)
    resid = airline_residuals([theta, Theta], w)
    return theta, Theta, sigma2, logy, d1, w, resid


def airline_forecast(y, n_future, season=12):
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

    # Corrección de sesgo lognormal: E[exp(X)] = exp(mu + sigma^2/2)
    y_full = np.exp(logy_full) * np.exp(sigma2 / 2)
    forecast = y_full[len(y):]
    return forecast, theta, Theta, sigma2


if __name__ == "__main__":
    monthly = pd.read_csv("data/monthly.csv", parse_dates=["fecha"])
    for var in ["consumo_kwh", "demanda_kw", "tarifa_prom"]:
        y = monthly[var].values.astype(float)
        fc, theta, Theta, sigma2 = airline_forecast(y, n_future=20)
        print(f"{var}: theta={theta:.3f} Theta={Theta:.3f}  primeros forecasts={np.round(fc[:3], 4)}")
