"""
run_all.py
-----------
Executes the full forecasting, evaluation, tariff calibration, and visualization
pipeline in sequential order.

Pipeline Steps:
  1. 01_data_cleaning.py: Aggregates raw meter billing into data/monthly.csv
  2. 02_forecast_mlr.py: Multiple Linear Regression (trend + monthly dummies)
  3. 03_forecast_sarima_airline.py: SARIMA(0,1,1)(0,1,1)_12 Airline Box-Jenkins model
  4. 04_backtesting.py: Out-of-sample evaluation (2022-2024 train, 2025 test, MAPE)
  5. 05_tariff_calibration.py: Empirical calibration against ASEP MTD tariffs
  6. 06_energy_demand_breakdown.py: Cost breakdown into energy vs peak demand charges
  7. 07_exact_meter_tariff.py: Meter-level calculation engine & campus breakdown
  8. 08_generate_figures.py: Generates all 6 publication-ready figures in figures/

Usage:  python code/run_all.py
"""

import os
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
ROOT_DIR = THIS_DIR.parent

SCRIPTS = [
    "01_data_cleaning.py",
    "02_forecast_mlr.py",
    "03_forecast_sarima_airline.py",
    "04_backtesting.py",
    "05_tariff_calibration.py",
    "06_energy_demand_breakdown.py",
    "07_exact_meter_tariff.py",
    "08_generate_figures.py",
]

def main():
    print("=" * 68)
    print("UTP Electricity Projection 2026-2027 Pipeline Execution")
    print("=" * 68)

    for script in SCRIPTS:
        print(f"\n[{script}] Running...")
        script_path = THIS_DIR / script
        result = subprocess.run([sys.executable, str(script_path)], cwd=ROOT_DIR)
        if result.returncode != 0:
            print(f"\n[ERROR] Pipeline step failed: {script}")
            sys.exit(result.returncode)

    print("\n" + "=" * 68)
    print("Pipeline completed successfully!")
    print("  - Aggregated data: data/monthly.csv")
    print("  - Generated plots: figures/ (6 publication figures)")
    print("=" * 68)

if __name__ == "__main__":
    main()

