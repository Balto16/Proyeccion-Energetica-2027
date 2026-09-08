"""
06_energy_demand_breakdown.py
-------------------------------
Decomposes total electricity expenditure into energy charges ($/kWh * consumption)
and peak demand charges ($/kW * monthly maximum demand peak), based on the official
ASEP regulatory tariff structure.

Key regulatory distinction for MTD/BTD tariffs:
  - There is NO contracted capacity charge.
  - The electric utility meters power demand in 10-15 minute rolling intervals.
    The single highest peak recorded during the entire billing cycle is multiplied
    by the demand tariff ($/kW).
  - Concurrently, accumulated energy consumption is multiplied by the volumetric
    energy tariff ($/kWh).
  - Both components are distinct and independent. Historically, energy accounts
    for ~75% of total billed costs, while peak demand accounts for ~24% (fixed
    customer charges account for the remaining <1%).

Usage:  python code/06_energy_demand_breakdown.py
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

tariff_mod = import_module("05_tariff_calibration")


def historical_cost_breakdown(monthly, ensa_mtd):
    """
    Separates annual billed costs into volumetric energy charges and peak demand charges,
    scaled proportionally to the actual billed amount.
    """
    val = tariff_mod.validate_historical_tariffs(monthly, ensa_mtd)
    sub = val.dropna(subset=["cargo_energia"]).copy()
    sub["e_theor"] = sub["consumo_kwh"] * sub["cargo_energia"]
    sub["d_theor"] = sub["demanda_kw"] * sub["cargo_demanda"]
    sub["f_theor"] = sub["n_medidores"] * sub["cargo_fijo"]

    annual = sub.groupby(sub["fecha"].dt.year).agg(
        energy_theor=("e_theor", "sum"),
        demand_theor=("d_theor", "sum"),
        fixed_theor=("f_theor", "sum"),
        actual_billed=("importe", "sum"),
    )
    total_theor = annual["energy_theor"] + annual["demand_theor"] + annual["fixed_theor"]
    annual["pct_energy"] = annual["energy_theor"] / total_theor
    annual["pct_demand"] = annual["demand_theor"] / total_theor
    annual["energy_cost_usd"] = annual["actual_billed"] * annual["pct_energy"]
    annual["demand_cost_usd"] = annual["actual_billed"] * annual["pct_demand"]

    return annual[["energy_cost_usd", "demand_cost_usd", "actual_billed", "pct_energy", "pct_demand"]]


if __name__ == "__main__":
    monthly = pd.read_csv("data/monthly.csv", parse_dates=["fecha"])
    ensa_mtd = tariff_mod.load_ensa_mtd_tariffs()
    breakdown = historical_cost_breakdown(monthly, ensa_mtd)
    breakdown["pct_energy"] = (breakdown["pct_energy"] * 100).round(1)
    breakdown["pct_demand"] = (breakdown["pct_demand"] * 100).round(1)

    print("Annual Electricity Cost Breakdown (Energy Charge vs. Peak Demand Charge):")
    print(breakdown.round(0).to_string())

