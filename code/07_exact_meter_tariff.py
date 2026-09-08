"""
07_exact_meter_tariff.py
--------------------------
Granular meter-by-meter electricity billing calculation engine:
Integrates the official university meter registry (data/meters_utp.csv:
campus location, power distributor, assigned tariff schedule) with the
detailed multi-tier regulatory rate schedules published by ASEP.

For each meter and monthly billing period:
  1. Identifies distribution utility (ENSA, EDEMET, or EDECHI) and base
     tariff code (BTS, BTD, or MTD).
  2. For BTD customers, resolves volumetric consumption sub-tier for the cycle
     (0-10k, 10k-30k, 30k-50k, or >50k kWh).
  3. Matches the exact energy charge ($/kWh), peak demand charge ($/kW),
     and fixed customer charge ($/month) active for that effective date.
  4. Sums theoretical charges across all institutional meters and evaluates
     against actual billed amounts.
  5. Computes historical electricity consumption and cost breakdown by campus.

Usage:  python code/07_exact_meter_tariff.py
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

CANDIDATE_BILLING_PATHS = [
    _ROOT / "data" / "Data 2022-2026.csv",
    _ROOT / "data" / "Data_Energía_2021-2026.csv",
]
METERS_PATH = _ROOT / "data" / "meters_utp.csv"
TARIFFS_PATH = _ROOT / "data" / "tarifas_asep_utp_2023_2026.xlsx"


def get_billing_path():
    for p in CANDIDATE_BILLING_PATHS:
        if p.exists():
            return p
    for p in (_ROOT / "data").glob("*.csv"):
        if "data" in p.name.lower() and "monthly" not in p.name.lower():
            return p
    raise FileNotFoundError("Billing dataset not found in data/ directory.")


def _subtier_btd(kwh):
    if kwh <= 10000:
        return "BTD 0-10k"
    elif kwh <= 30000:
        return "BTD 10k-30k"
    elif kwh <= 50000:
        return "BTD 30k-50k"
    return "BTD >50k"


def build_exact_meter_engine():
    billing_path = get_billing_path()
    billing = pd.read_csv(billing_path, encoding="utf-8-sig")
    meters = pd.read_csv(METERS_PATH)
    tariffs = pd.read_excel(TARIFFS_PATH, sheet_name="Base Maestra Tarifas", header=0)

    # Standardize billing column names
    col_map = {}
    for c in billing.columns:
        norm = c.strip().lower()
        if "medidor" in norm:
            col_map[c] = "meter_id"
        elif "mes" in norm:
            col_map[c] = "month"
        elif "dia" in norm:
            col_map[c] = "day"
        elif "a" in norm and ("o" in norm or "ñ" in norm):
            col_map[c] = "year"
        elif "importe" in norm:
            col_map[c] = "amount_usd"
        elif "demanda" in norm:
            col_map[c] = "demand_kw"
        elif "consumo" in norm:
            col_map[c] = "consumption_kwh"

    billing = billing.rename(columns=col_map)
    billing = billing[~((billing["year"] == 2026) & (billing["month"] == 6))]
    billing["fecha"] = pd.to_datetime(dict(year=billing["year"], month=billing["month"], day=1))

    # Parse tariff schedule validity dates
    tariffs[["ini", "fin"]] = tariffs["Vigencia"].str.split(" - ", expand=True)
    tariffs["ini"] = pd.to_datetime(tariffs["ini"], dayfirst=True)
    tariffs["fin"] = pd.to_datetime(tariffs["fin"], dayfirst=True)

    # Merge meter metadata
    merged = billing.merge(
        meters[["meter_id", "center", "province", "distributor", "tariff"]],
        on="meter_id",
        how="left",
    )

    def resolve_tariff_code(row):
        t = row["tariff"]
        if t == "BTD":
            return _subtier_btd(row["consumption_kwh"])
        elif t == "BTS":
            return "BTS 2"  # standard BTS subcategory (~1.2% total consumption)
        return t  # MTD

    merged["tarifa_codigo"] = merged.apply(resolve_tariff_code, axis=1)

    def match_tariff_charges(row):
        if pd.isna(row["distributor"]):
            return pd.Series([np.nan, np.nan, np.nan])
        m = tariffs[
            (tariffs["Distribuidora"] == row["distributor"])
            & (tariffs["Tarifa Código"] == row["tarifa_codigo"])
            & (tariffs["ini"] <= row["fecha"])
            & (tariffs["fin"] >= row["fecha"])
        ]
        if len(m) == 0:
            return pd.Series([np.nan, np.nan, np.nan])
        r = m.iloc[0]
        return pd.Series([r["Cargo Energía ($/kWh)"], r["Cargo Demanda ($/kW)"], r["Cargo Fijo (B/.)"]])

    merged[["cargo_e", "cargo_d", "cargo_f"]] = merged.apply(match_tariff_charges, axis=1)
    merged.loc[merged["tariff"] == "BTS", "cargo_d"] = 0.0  # BTS carries no demand charge

    merged["theoretical_cost"] = (
        merged["consumption_kwh"] * merged["cargo_e"].fillna(0)
        + merged["demand_kw"] * merged["cargo_d"].fillna(0)
        + merged["cargo_f"].fillna(0)
    )
    return merged


def validate_meter_engine(merged):
    sub = merged[merged["fecha"] >= "2023-01-01"].copy()
    monthly = sub.groupby("fecha").agg(
        actual_billed=("amount_usd", "sum"),
        theoretical_cost=("theoretical_cost", "sum"),
    )
    monthly["mape"] = (monthly["theoretical_cost"] - monthly["actual_billed"]).abs() / monthly["actual_billed"] * 100.0
    pre = monthly[monthly.index < "2025-07-01"]["mape"].mean()
    post = monthly[monthly.index >= "2025-07-01"]
    factor = post["actual_billed"] / post["theoretical_cost"]
    return pre, factor.mean(), factor.std()


def consumption_by_campus(merged):
    tot = merged.groupby("center").agg(
        total_consumption_kwh=("consumption_kwh", "sum"),
        total_billed_usd=("amount_usd", "sum"),
        meter_count=("meter_id", "nunique"),
    )
    tot["pct_consumption"] = tot["total_consumption_kwh"] / tot["total_consumption_kwh"].sum() * 100.0
    return tot.sort_values("total_consumption_kwh", ascending=False)


if __name__ == "__main__":
    merged = build_exact_meter_engine()
    mape_pre, factor, factor_std = validate_meter_engine(merged)
    print(f"MAPE 2023-Jun 2025 (Meter-Level Engine): {mape_pre:.2f}%")
    print(f"Calibration Factor (Jul 2025 - May 2026): {factor:.4f} (std: {factor_std:.4f})")
    print("\nCumulative Electricity Consumption by Campus (2022 - May 2026):")
    campus_df = consumption_by_campus(merged)
    print(campus_df.round(1).to_string())

