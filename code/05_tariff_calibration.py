"""
05_tariff_calibration.py
--------------------------
Método 3: proyección de costo fundamentada en el pliego tarifario real
de ASEP (2023-2026), en vez de extrapolación puramente estadística.

Pasos:
  1. Toma la tarifa ENSA-MTD (Media Tensión Demanda), correspondiente al
     Campus Metropolitano / Sede Principal de la UTP, que según el mapeo
     oficial de sedes concentra ~94% de la demanda pico institucional y
     entre 70-80% del consumo total.
  2. Calcula el importe teórico mensual histórico:
         Importe = Consumo*CargoEnergia + Demanda*CargoDemanda
                   + N_medidores*CargoFijo
  3. Compara contra el importe real facturado -> identifica el quiebre
     estructural de oct-2024 a jun-2025 (Fallo CSJ, Res. AN 19632-Elec)
     y el alza posterior (Res. AN 19850-Elec).
  4. Calibra un factor único (real/teórico) usando el régimen tarifario
     vigente más reciente (jul-2025 a may-2026, 11 observaciones).
  5. Aplica el factor calibrado a las proyecciones de consumo/demanda de
     los métodos 1 y 2 para obtener una tercera estimación de costo.

Nota importante (documentada y NO oculta en el informe): se probó un
modelo de dos componentes (MTD + resto, ponderado 70-80%/94%) y el
resultado no fue sostenible: la tarifa implícita del componente
restante resultó por debajo de cualquier tarifa BTD/BTS real publicada.
Esto sugiere un tratamiento tarifario institucional/gubernamental no
documentado en el pliego comercial general. Por eso se usa el factor de
calibración único, no el modelo de dos componentes.

Ejecutar desde cualquier directorio:  python3 code/05_tariff_calibration.py
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS_DIR)
sys.path.insert(0, _THIS_DIR)
os.chdir(_ROOT)

import numpy as np
import pandas as pd

RUTA_TARIFAS = "data/tarifas_asep_utp_2023_2026.xlsx"

# Tarifa ENSA-MTD vigente más reciente en los datos (Res. AN No. 19990-Elec,
# 01/01/2026-31/08/2026). Actualizar si ASEP publica un nuevo pliego.
CARGO_ENERGIA_VIGENTE = 0.19244   # $/kWh
CARGO_DEMANDA_VIGENTE = 17.79     # $/kW
CARGO_FIJO_VIGENTE = 9.89         # $/medidor-mes

FACTOR_CALIBRACION = 0.8356194911895635  # real/teórico, régimen jul-2025 a may-2026


def cargar_tarifa_ensa_mtd(ruta=RUTA_TARIFAS):
    tarifas = pd.read_excel(ruta, sheet_name="Base Maestra Tarifas", header=0)
    ensa_mtd = tarifas[(tarifas["Distribuidora"] == "ENSA") & (tarifas["Tarifa Código"] == "MTD")].copy()
    ensa_mtd[["ini", "fin"]] = ensa_mtd["Vigencia"].str.split(" - ", expand=True)
    ensa_mtd["ini"] = pd.to_datetime(ensa_mtd["ini"], dayfirst=True)
    ensa_mtd["fin"] = pd.to_datetime(ensa_mtd["fin"], dayfirst=True)
    return ensa_mtd


def importe_teorico_mtd(consumo_kwh, demanda_kw, n_medidores, cargo_energia, cargo_demanda, cargo_fijo):
    return consumo_kwh * cargo_energia + demanda_kw * cargo_demanda + n_medidores * cargo_fijo


def validar_historico(monthly, ensa_mtd):
    """Aplica la tarifa vigente en cada mes histórico y compara contra el importe real."""
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

    monthly["importe_pred_mtd"] = importe_teorico_mtd(
        monthly["consumo_kwh"], monthly["demanda_kw"], monthly["n_medidores"],
        monthly["cargo_energia"], monthly["cargo_demanda"], monthly["cargo_fijo"],
    )
    return monthly


def proyectar_costo_calibrado(consumo_kwh, demanda_kw, n_medidores):
    """Proyecta el costo usando la tarifa vigente + factor de calibración empírico."""
    pred = importe_teorico_mtd(
        consumo_kwh, demanda_kw, n_medidores,
        CARGO_ENERGIA_VIGENTE, CARGO_DEMANDA_VIGENTE, CARGO_FIJO_VIGENTE,
    )
    return pred * FACTOR_CALIBRACION


if __name__ == "__main__":
    monthly = pd.read_csv("data/monthly.csv", parse_dates=["fecha"])
    ensa_mtd = cargar_tarifa_ensa_mtd()
    val = validar_historico(monthly, ensa_mtd)
    sub = val.dropna(subset=["cargo_energia"]).copy()
    sub["ratio"] = sub["importe"] / sub["importe_pred_mtd"]

    post = sub[sub["fecha"] >= "2025-07-01"]
    print("Régimen tarifario vigente (jul-2025 a may-2026):")
    print(f"  factor calibración (media) = {post['ratio'].mean():.4f}")
    print(f"  desviación estándar        = {post['ratio'].std():.4f}")
    print(f"  n observaciones            = {len(post)}")
