"""
run_all.py
-----------
Corre todo el pipeline en orden y muestra un resumen final.
Uso:  python3 code/run_all.py
"""

import os
import subprocess
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = [
    "01_data_cleaning.py",
    "02_forecast_mlr.py",
    "03_forecast_sarima_airline.py",
    "04_backtesting.py",
    "05_tariff_calibration.py",
    "06_energy_demand_breakdown.py",
    "07_exact_meter_tariff.py",
]

for script in SCRIPTS:
    print(f"\n{'='*60}\n{script}\n{'='*60}")
    ruta = os.path.join(THIS_DIR, script)
    result = subprocess.run([sys.executable, ruta])
    if result.returncode != 0:
        print(f"FALLÓ: {script}")
        sys.exit(1)

print("\nPipeline completo. Ver data/monthly.csv y la salida de cada paso arriba.")
