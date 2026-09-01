"""
04_backtesting.py
-------------------
Validación fuera de muestra: entrena ambos métodos solo con 2022-2024 y
compara el pronóstico de 12 meses contra los valores reales de 2025
(Error Porcentual Absoluto Medio, MAPE).

Reproduce las cifras reportadas en la sección 3.3 del informe técnico.

Ejecutar desde cualquier directorio:  python3 code/04_backtesting.py
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS_DIR)
sys.path.insert(0, _THIS_DIR)
os.chdir(_ROOT)

import numpy as np
import pandas as pd
from importlib import import_module

mlr_mod = import_module("02_forecast_mlr")
air_mod = import_module("03_forecast_sarima_airline")


def mape(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


if __name__ == "__main__":
    monthly = pd.read_csv("data/monthly.csv", parse_dates=["fecha"])

    train = monthly[monthly["fecha"] < "2025-01-01"].reset_index(drop=True)
    test = monthly[(monthly["fecha"] >= "2025-01-01") & (monthly["fecha"] < "2026-01-01")].reset_index(drop=True)

    print(f"{'Variable':<15}{'MAPE MLR':>12}{'MAPE SARIMA':>15}")
    for var in ["consumo_kwh", "demanda_kw", "tarifa_prom"]:
        y_train = train[var].values.astype(float)
        y_test = test[var].values.astype(float)

        _, yhat_mlr, _, _ = mlr_mod.mlr_forecast(y_train, train["fecha"], 12)
        yhat_air, _, _, _ = air_mod.airline_forecast(y_train, 12)

        print(f"{var:<15}{mape(y_test, yhat_mlr):>11.2f}%{mape(y_test, yhat_air):>14.2f}%")
