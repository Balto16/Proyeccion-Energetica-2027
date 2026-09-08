"""
01_data_cleaning.py
--------------------
Loads the raw electricity billing CSV (all UTP university meters, 2022-2026),
aggregates metrics to the institutional monthly level, and saves the cleaned
time series to data/monthly.csv for consumption by downstream forecasting models.

Inputs:   data/Data 2022-2026.csv (or data/Data_Energía_2021-2026.csv)
Outputs:  data/monthly.csv

Usage:    python code/01_data_cleaning.py
"""

import os
import sys
from pathlib import Path
import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
_ROOT = _THIS_DIR.parent
sys.path.insert(0, str(_THIS_DIR))
os.chdir(_ROOT)

CANDIDATE_RAW_PATHS = [
    _ROOT / "data" / "Data 2022-2026.csv",
    _ROOT / "data" / "Data_Energía_2021-2026.csv",
]
OUTPUT_PATH = _ROOT / "data" / "monthly.csv"


def get_raw_path():
    for p in CANDIDATE_RAW_PATHS:
        if p.exists():
            return p
    for p in (_ROOT / "data").glob("*.csv"):
        if "data" in p.name.lower() and "monthly" not in p.name.lower():
            return p
    raise FileNotFoundError("Raw billing dataset not found in data/ directory.")


def load_and_clean(raw_path=None):
    if raw_path is None:
        raw_path = get_raw_path()

    df = pd.read_csv(raw_path, encoding="utf-8-sig")

    # Standardize column mapping to robust internal keys
    col_map = {}
    for c in df.columns:
        norm = c.strip().lower()
        if "medidor" in norm:
            col_map[c] = "meter_id"
        elif "mes" in norm:
            col_map[c] = "month"
        elif "dia" in norm:
            col_map[c] = "day"
        elif "a" in norm and ("o" in norm or "ñ" in norm):  # handles año / corrupted encoding
            col_map[c] = "year"
        elif "importe" in norm:
            col_map[c] = "amount_usd"
        elif "demanda" in norm:
            col_map[c] = "demand_kw"
        elif "consumo" in norm:
            col_map[c] = "consumption_kwh"

    df = df.rename(columns=col_map)

    # Exclude June 2026: incomplete reporting period at cutoff date
    # (only ~10 of ~54 meters were billed by the data extraction date).
    df = df[~((df["year"] == 2026) & (df["month"] == 6))]

    # Build monthly timestamp
    df["fecha"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))

    # Institutional monthly aggregation
    monthly = (
        df.groupby("fecha")
        .agg(
            consumo_kwh=("consumption_kwh", "sum"),
            demanda_kw=("demand_kw", "sum"),
            importe=("amount_usd", "sum"),
            n_medidores=("meter_id", "count"),
        )
        .reset_index()
        .sort_values("fecha")
    )

    # Effective institutional average tariff ($/kWh)
    monthly["tarifa_prom"] = monthly["importe"] / monthly["consumo_kwh"]
    return monthly


if __name__ == "__main__":
    monthly = load_and_clean()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(OUTPUT_PATH, index=False)
    print(f"SUCCESS: {len(monthly)} monthly records aggregated -> {OUTPUT_PATH.relative_to(_ROOT)}")
    print(monthly.tail())
