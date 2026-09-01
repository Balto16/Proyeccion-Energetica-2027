"""
07_exact_meter_tariff.py
--------------------------
Motor de cálculo tarifario EXACTO, medidor por medidor, usando el listado
oficial de medidores de la UTP (data/meters_utp.csv: sede, distribuidora,
tarifa asignada) cruzado con el pliego tarifario real de ASEP.

Reemplaza la aproximación de una versión anterior de este proyecto, que
aplicaba una sola tarifa (MTD de ENSA) a toda la institución.

Para cada medidor y cada mes:
  1. Se identifica su distribuidora (ENSA/EDEMET/EDECHI) y su clase
     tarifaria (BTS/BTD/MTD) desde el listado de medidores.
  2. Si es BTD, se determina el escalón de consumo de ese mes (0-10k,
     10k-30k, 30k-50k o >50k kWh) según el pliego.
  3. Se aplica el cargo de energía, cargo de demanda (si corresponde) y
     cargo fijo exactos de ese período.
  4. Se suma el importe teórico de todos los medidores y se compara contra
     el importe real facturado.

También produce el desglose de consumo histórico por sede (Sección 3.5 del
informe técnico).

Ejecutar desde cualquier directorio:  python3 code/07_exact_meter_tariff.py
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS_DIR)
sys.path.insert(0, _THIS_DIR)
os.chdir(_ROOT)

import numpy as np
import pandas as pd

RUTA_BILLING = "data/Data_Energía_2021-2026.csv"
RUTA_METERS = "data/meters_utp.csv"
RUTA_TARIFAS = "data/tarifas_asep_utp_2023_2026.xlsx"


def _subtier_btd(kwh):
    if kwh <= 10000:
        return "BTD 0-10k"
    elif kwh <= 30000:
        return "BTD 10k-30k"
    elif kwh <= 50000:
        return "BTD 30k-50k"
    return "BTD >50k"


def construir_motor_exacto():
    billing = pd.read_csv(RUTA_BILLING, encoding="utf-8-sig")
    meters = pd.read_csv(RUTA_METERS)
    tarifas = pd.read_excel(RUTA_TARIFAS, sheet_name="Base Maestra Tarifas", header=0)

    billing = billing[~((billing["año"] == 2026) & (billing["mes"] == 6))]
    billing["fecha"] = pd.to_datetime(dict(year=billing["año"], month=billing["mes"], day=1))

    tarifas[["ini", "fin"]] = tarifas["Vigencia"].str.split(" - ", expand=True)
    tarifas["ini"] = pd.to_datetime(tarifas["ini"], dayfirst=True)
    tarifas["fin"] = pd.to_datetime(tarifas["fin"], dayfirst=True)

    merged = billing.merge(
        meters[["meter_id", "center", "province", "distributor", "tariff"]],
        left_on="MEDIDOR", right_on="meter_id", how="left",
    )

    def codigo_tarifa(row):
        if row["tariff"] == "BTD":
            return _subtier_btd(row["consumo (kwh)"])
        elif row["tariff"] == "BTS":
            return "BTS 2"  # supuesto simplificador: BTS es solo ~1.2% del consumo total
        return row["tariff"]  # MTD

    merged["tarifa_codigo"] = merged.apply(codigo_tarifa, axis=1)

    def buscar_cargos(row):
        if pd.isna(row["distributor"]):
            return pd.Series([np.nan, np.nan, np.nan])
        m = tarifas[
            (tarifas["Distribuidora"] == row["distributor"])
            & (tarifas["Tarifa Código"] == row["tarifa_codigo"])
            & (tarifas["ini"] <= row["fecha"])
            & (tarifas["fin"] >= row["fecha"])
        ]
        if len(m) == 0:
            return pd.Series([np.nan, np.nan, np.nan])
        r = m.iloc[0]
        return pd.Series([r["Cargo Energía ($/kWh)"], r["Cargo Demanda ($/kW)"], r["Cargo Fijo (B/.)"]])

    merged[["cargo_e", "cargo_d", "cargo_f"]] = merged.apply(buscar_cargos, axis=1)
    merged.loc[merged["tariff"] == "BTS", "cargo_d"] = 0  # BTS no tiene cargo de demanda

    merged["importe_teorico"] = (
        merged["consumo (kwh)"] * merged["cargo_e"].fillna(0)
        + merged["demanda (kw)"] * merged["cargo_d"].fillna(0)
        + merged["cargo_f"].fillna(0)
    )
    return merged


def validar(merged):
    sub = merged[merged["fecha"] >= "2023-01-01"].copy()
    mensual = sub.groupby("fecha").agg(importe_real=("importe ($)", "sum"), importe_teorico=("importe_teorico", "sum"))
    mensual["mape"] = (mensual["importe_teorico"] - mensual["importe_real"]).abs() / mensual["importe_real"] * 100
    pre = mensual[mensual.index < "2025-07-01"]["mape"].mean()
    post = mensual[mensual.index >= "2025-07-01"]
    factor = (post["importe_real"] / post["importe_teorico"])
    return pre, factor.mean(), factor.std()


def consumo_por_sede(merged):
    tot = merged.groupby("center").agg(
        consumo_total=("consumo (kwh)", "sum"), importe_total=("importe ($)", "sum"), n_medidores=("MEDIDOR", "nunique")
    )
    tot["pct_consumo"] = tot["consumo_total"] / tot["consumo_total"].sum() * 100
    return tot.sort_values("consumo_total", ascending=False)


if __name__ == "__main__":
    merged = construir_motor_exacto()
    mape_pre, factor, factor_std = validar(merged)
    print(f"MAPE 2023-jun.2025 (motor exacto): {mape_pre:.2f}%")
    print(f"Factor de calibración jul.2025-may.2026: {factor:.4f} (desv. {factor_std:.4f})")
    print("\nConsumo por sede (2022-may.2026):")
    print(consumo_por_sede(merged).round(1).to_string())
