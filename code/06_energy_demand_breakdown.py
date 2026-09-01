"""
06_energy_demand_breakdown.py
-------------------------------
Desglosa el costo total (histórico y proyectado) entre cargo por energía
($/kWh x consumo) y cargo por demanda ($/kW x demanda máxima registrada del
mes), usando el pliego tarifario real de ASEP.

Importante sobre la tarifa MTD/BTD: no existe "capacidad contratada". La
distribuidora mide la potencia en intervalos de 10-15 minutos durante todo
el mes; el intervalo de mayor valor se multiplica por el cargo de demanda.
De forma independiente, el consumo acumulado del mes se multiplica por el
cargo de energía. Ambos cargos son estructuralmente distintos y se calculan
por separado (ver sección 4.5 del informe técnico).

Ejecutar desde cualquier directorio:  python3 code/06_energy_demand_breakdown.py
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS_DIR)
sys.path.insert(0, _THIS_DIR)
os.chdir(_ROOT)

import numpy as np
import pandas as pd
from importlib import import_module

tariff_mod = import_module("05_tariff_calibration")


def desglose_historico(monthly, ensa_mtd):
    """Separa el importe real anual en cargo de energía y cargo de demanda,
    escalando proporcionalmente al importe real facturado (elimina el
    residuo del factor de calibración)."""
    val = tariff_mod.validar_historico(monthly, ensa_mtd)
    sub = val.dropna(subset=["cargo_energia"]).copy()
    sub["e_teor"] = sub["consumo_kwh"] * sub["cargo_energia"]
    sub["d_teor"] = sub["demanda_kw"] * sub["cargo_demanda"]
    sub["f_teor"] = sub["n_medidores"] * sub["cargo_fijo"]

    anual = sub.groupby(sub["fecha"].dt.year).agg(
        e_teor=("e_teor", "sum"), d_teor=("d_teor", "sum"), f_teor=("f_teor", "sum"),
        importe_real=("importe", "sum"),
    )
    tot_teor = anual["e_teor"] + anual["d_teor"] + anual["f_teor"]
    anual["pct_energia"] = anual["e_teor"] / tot_teor
    anual["pct_demanda"] = anual["d_teor"] / tot_teor
    anual["energia_final"] = anual["importe_real"] * anual["pct_energia"]
    anual["demanda_final"] = anual["importe_real"] * anual["pct_demanda"]
    return anual[["energia_final", "demanda_final", "importe_real", "pct_energia", "pct_demanda"]]


if __name__ == "__main__":
    monthly = pd.read_csv("data/monthly.csv", parse_dates=["fecha"])
    ensa_mtd = tariff_mod.cargar_tarifa_ensa_mtd()
    resultado = desglose_historico(monthly, ensa_mtd)
    resultado["pct_energia"] = (resultado["pct_energia"] * 100).round(1)
    resultado["pct_demanda"] = (resultado["pct_demanda"] * 100).round(1)
    print(resultado.round(0).to_string())
