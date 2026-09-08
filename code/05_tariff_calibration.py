"""
05_tariff_calibration.py
--------------------------
Method 3: Regulatory Tariff Calibration based on official ASEP electric tariffs
(2023-2026), grounding budgetary projections in real regulatory pricing rather
than unconstrained statistical extrapolation.

Methodological steps:
  1. Utilizes the ENSA-MTD tariff (Medium Voltage Demand) of the Victor Levi Sasso
     Main Campus, which accounts for ~94% of institutional peak demand and ~70-80%
     of total university electricity consumption.
  2. Computes the historical theoretical monthly cost:
         Theoretical Amount = Consumption * Energy_Charge
                            + Peak_Demand * Demand_Charge
                            + Meter_Count * Fixed_Charge
  3. Evaluates theoretical vs. billed amounts across regulatory transitions:
     - Detects the judicial freeze (Supreme Court ruling reverting to 2018 rates,
       Resolution AN No. 19632-Elec, Oct 2024 - Jun 2025).
     - Identifies the subsequent tariff increase (+32% energy, +40% demand,
       Resolution AN No. 19850-Elec, effective Jul 2025).
  4. Calibrates an empirical adjustment factor (actual / theoretical) over the
     active regulatory regime (Jul 2025 to May 2026, 11 months):
     factor = 0.8356 (CV = 3.0%). This reflects that regional campus tariffs
     (BTD/BTS) modulate the pure MTD rate.
  5. Multiplies projected consumption and demand (Methods 1 & 2) by active rates
     and this empirical factor to compute realistic budget forecasts.

Usage:  python code/05_tariff_calibration.py
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

TARIFF_SHEET_PATH = _ROOT / "data" / "tarifas_asep_utp_2023_2026.xlsx"

# Active ENSA-MTD tariff charges (Resolution AN No. 19990-Elec, Jan-Aug 2026).
ACTIVE_ENERGY_CHARGE = 0.19244  # $/kWh
ACTIVE_DEMAND_CHARGE = 17.79    # $/kW
ACTIVE_FIXED_CHARGE = 9.89      # $/meter-month

CALIBRATION_FACTOR = 0.8356194911895635  # Actual / Theoretical (Jul 2025 - May 2026)


def load_ensa_mtd_tariffs(path=TARIFF_SHEET_PATH):
    """Loads and filters the ENSA-MTD tariff schedule from the ASEP master sheet."""
    tariffs = pd.read_excel(path, sheet_name="Base Maestra Tarifas", header=0)
    ensa_mtd = tariffs[(tariffs["Distribuidora"] == "ENSA") & (tariffs["Tarifa Código"] == "MTD")].copy()
    ensa_mtd[["ini", "fin"]] = ensa_mtd["Vigencia"].str.split(" - ", expand=True)
    ensa_mtd["ini"] = pd.to_datetime(ensa_mtd["ini"], dayfirst=True)
    ensa_mtd["fin"] = pd.to_datetime(ensa_mtd["fin"], dayfirst=True)
    return ensa_mtd


def theoretical_mtd_cost(consumption_kwh, demand_kw, meter_count, energy_charge, demand_charge, fixed_charge):
    """Evaluates the standard ASEP billing formula for MTD service."""
    return consumption_kwh * energy_charge + demand_kw * demand_charge + meter_count * fixed_charge


def validate_historical_tariffs(monthly, ensa_mtd):
    """Computes theoretical monthly billing matching active tariffs in each month."""
    monthly = monthly.copy()
    monthly["cargo_energia"] = np.nan
    monthly["cargo_demanda"] = np.nan
    monthly["cargo_fijo"] = np.nan
    for i, row in monthly.iterrows():
        match = ensa_mtd[(ensa_mtd["ini"] <= row["fecha"]) & (ensa_mtd["fin"] >= row["fecha"])]
        if len(match):
            r = match.iloc[0]
            monthly.loc[i, "cargo_energia"] = r["Cargo Energía ($/kWh)"]
            monthly.loc[i, "cargo_demanda"] = r["Cargo Demanda ($/kW)"]
            monthly.loc[i, "cargo_fijo"] = r["Cargo Fijo (B/.)"]

    monthly["importe_pred_mtd"] = theoretical_mtd_cost(
        monthly["consumo_kwh"],
        monthly["demanda_kw"],
        monthly["n_medidores"],
        monthly["cargo_energia"],
        monthly["cargo_demanda"],
        monthly["cargo_fijo"],
    )
    return monthly


def project_calibrated_cost(consumption_kwh, demand_kw, meter_count):
    """Forecasts energy expenditure applying the calibrated empirical scaling factor."""
    pred = theoretical_mtd_cost(
        consumption_kwh,
        demand_kw,
        meter_count,
        ACTIVE_ENERGY_CHARGE,
        ACTIVE_DEMAND_CHARGE,
        ACTIVE_FIXED_CHARGE,
    )
    return pred * CALIBRATION_FACTOR


if __name__ == "__main__":
    monthly = pd.read_csv("data/monthly.csv", parse_dates=["fecha"])
    ensa_mtd = load_ensa_mtd_tariffs()
    val = validate_historical_tariffs(monthly, ensa_mtd)
    sub = val.dropna(subset=["cargo_energia"]).copy()
    sub["ratio"] = sub["importe"] / sub["importe_pred_mtd"]

    post = sub[sub["fecha"] >= "2025-07-01"]
    print("Method 3 - Active Regulatory Regime Calibration (Jul 2025 to May 2026):")
    print(f"  Calibration Factor (mean) = {post['ratio'].mean():.4f}")
    print(f"  Standard Deviation        = {post['ratio'].std():.4f}")
    print(f"  Coefficient of Variation  = {(post['ratio'].std() / post['ratio'].mean()) * 100:.2f}%")
    print(f"  Observations (n)          = {len(post)}")

