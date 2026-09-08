"""
04_backtesting.py
-------------------
Out-of-sample model validation: trains both forecasting methods exclusively on
2022-2024 historical data (36 months) and evaluates the 12-month forward forecast
against actual billing data observed across 2025.

Performance is assessed using Mean Absolute Percentage Error (MAPE):
    MAPE = (1 / n) * sum(|y_true - y_pred| / y_true) * 100

Usage:  python code/04_backtesting.py
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from importlib import import_module

_THIS_DIR = Path(__file__).resolve().parent
_ROOT = _THIS_DIR.parent
sys.path.insert(0, str(_THIS_DIR))
os.chdir(_ROOT)

mlr_mod = import_module("02_forecast_mlr")
air_mod = import_module("03_forecast_sarima_airline")


def mape(y_true, y_pred):
    """Calculates Mean Absolute Percentage Error (MAPE)."""
    return float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100.0)


if __name__ == "__main__":
    monthly = pd.read_csv("data/monthly.csv", parse_dates=["fecha"])

    train = monthly[monthly["fecha"] < "2025-01-01"].reset_index(drop=True)
    test = monthly[(monthly["fecha"] >= "2025-01-01") & (monthly["fecha"] < "2026-01-01")].reset_index(drop=True)

    print("Out-of-Sample Backtesting Performance (Train: 2022-2024 | Test: 2025):")
    print(f"{'Target Variable':<25}{'MAPE (MLR)':>15}{'MAPE (SARIMA)':>18}")
    print("-" * 58)

    labels = {
        "consumo_kwh": "Consumption (kWh)",
        "demanda_kw": "Peak Demand (kW)",
        "tarifa_prom": "Avg Tariff ($/kWh)",
    }

    for var in ["consumo_kwh", "demanda_kw", "tarifa_prom"]:
        y_train = train[var].values.astype(float)
        y_test = test[var].values.astype(float)

        _, yhat_mlr, _, _ = mlr_mod.mlr_forecast(y_train, train["fecha"], 12)
        yhat_air, _, _, _ = air_mod.airline_forecast(y_train, 12)

        lbl = labels.get(var, var)
        print(f"{lbl:<25}{mape(y_test, yhat_mlr):>14.2f}%{mape(y_test, yhat_air):>17.2f}%")

