"""
01_data_cleaning.py
--------------------
Carga el CSV crudo de facturación eléctrica (2021-2026, todos los medidores
de la UTP), lo agrega a nivel mensual institucional y guarda el resultado
en data/monthly.csv para que los demás scripts lo consuman.

Entrada:  data/Data_Energía_2021-2026.csv
Salida:   data/monthly.csv

Ejecutar desde cualquier directorio:  python3 code/01_data_cleaning.py
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS_DIR)
sys.path.insert(0, _THIS_DIR)
os.chdir(_ROOT)  # las rutas relativas (data/...) se resuelven desde la raíz del repo

import pandas as pd

RUTA_CRUDA = "data/Data_Energía_2021-2026.csv"
RUTA_SALIDA = "data/monthly.csv"


def cargar_y_limpiar(ruta=RUTA_CRUDA):
    df = pd.read_csv(ruta, encoding="utf-8-sig")

    # Excluir junio 2026: mes incompleto (solo ~10 de ~54 medidores facturados
    # al momento del corte de datos, 31-ago-2026).
    df = df[~((df["año"] == 2026) & (df["mes"] == 6))]

    df["fecha"] = pd.to_datetime(dict(year=df["año"], month=df["mes"], day=1))

    monthly = (
        df.groupby("fecha")
        .agg(
            consumo_kwh=("consumo (kwh)", "sum"),
            demanda_kw=("demanda (kw)", "sum"),
            importe=("importe ($)", "sum"),
            n_medidores=("MEDIDOR", "count"),
        )
        .reset_index()
        .sort_values("fecha")
    )
    monthly["tarifa_prom"] = monthly["importe"] / monthly["consumo_kwh"]
    return monthly


if __name__ == "__main__":
    monthly = cargar_y_limpiar()
    monthly.to_csv(RUTA_SALIDA, index=False)
    print(f"OK: {len(monthly)} meses agregados -> {RUTA_SALIDA}")
    print(monthly.tail())
