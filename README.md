# Proyección de Consumo, Demanda, Tarifa y Costo de Energía Eléctrica — UTP 2026-2027

Investigación de soporte para la proyección presupuestaria de energía eléctrica de la
Universidad Tecnológica de Panamá (todas las sedes), usando dos métodos estadísticos
independientes y validación cruzada con el pliego tarifario real de ASEP (2023-2026).

## Nota sobre la tarifa de demanda

La tarifa MTD/BTD de ASEP **no cobra por capacidad contratada**. La distribuidora
mide la potencia en intervalos durante todo el mes; el intervalo
de mayor valor se multiplica por el cargo de demanda ($/kW). El consumo acumulado
del mes se multiplica, por separado, por el cargo de energía ($/kWh). El desglose
histórico (`06_energy_demand_breakdown.py`) muestra que ~75% del costo corresponde
a energía y ~24% a demanda, proporción estable desde 2023 (ver sección 4.5 del
informe técnico).

## Resultado principal (2027, recomendado)

| Indicador | Valor |
|---|---|
| Consumo | 17,438 MWh |
| Demanda pico | 5,225 kW |
| Costo de energía | US$3,676,433 (rango: $3.67M–$3.86M según método) |

## Estructura del repositorio

```
.
├── data/
│   ├── Data_Energía_2021-2026.csv           # Facturación mensual por medidor (fuente primaria)
│   ├── meters_utp.csv                       # Listado oficial de medidores: sede, distribuidora, tarifa
│   ├── tarifas_asep_utp_2023_2026.xlsx      # Pliego tarifario ASEP, resumido y estructurado
│   ├── Tarifario_ASEP_2023_-_2026__OCT_.pdf # Pliego tarifario ASEP, documento oficial original
│   └── monthly.csv                          # (generado) serie mensual agregada institucional
├── code/
│   ├── 01_data_cleaning.py                  # Limpieza y agregación mensual
│   ├── 02_forecast_mlr.py                   # Método 1: Regresión Lineal Múltiple
│   ├── 03_forecast_sarima_airline.py        # Método 2: SARIMA(0,1,1)(0,1,1)_12 (Box-Jenkins)
│   ├── 04_backtesting.py                    # Validación fuera de muestra (MAPE, 2025)
│   ├── 05_tariff_calibration.py             # Método 3 (v1): calibración con tarifa MTD única
│   ├── 06_energy_demand_breakdown.py        # Desglose costo: cargo energía vs. cargo demanda
│   ├── 07_exact_meter_tariff.py             # Método 3 (v2): motor exacto por medidor + consumo por sede
│   ├── run_all.py                           # Corre el pipeline completo en orden
│   ├── build_informe_tecnico.js             # Genera docs/informe_proyeccion_energia_UTP.docx
│   └── build_resumen_ejecutivo.js           # Genera docs/resumen_ejecutivo_UTP.docx
├── figures/                                 # Gráficos + assets del sistema visual (paleta DINAGEA)
│   ├── fig_consumo.png, fig_demanda.png, fig_tarifa.png, fig_costo_anual.png
│   ├── portada_diagonal.png                 # Fondo de portada (diagonal, spec 2F)
│   └── banner_diagonal.png                  # Banda de encabezado delgada (spec 2B)
├── docs/                                    # Informes finales (Word)
├── requirements.txt
└── README.md
```

## Cómo reproducir

```bash
pip install -r requirements.txt
python3 code/run_all.py
```

Esto regenera `data/monthly.csv` y reproduce en consola las cifras de R², MAPE y el
factor de calibración tarifaria reportados en el informe técnico (sección 3.3 y 3.4).

## Metodología (resumen)

**Método 1 — Regresión Lineal Múltiple (MLR):** tendencia lineal + 11 variables dummy
mensuales. Referencia: Kialashaki & Reisel (2013), *Applied Energy*.

**Método 2 — SARIMA(0,1,1)(0,1,1)₁₂ ("modelo Airline"):** estimado por suma condicional
de cuadrados sobre el logaritmo de la serie. Referencia: Box & Jenkins (1976).
*Nota: se implementó manualmente con scipy porque el entorno de desarrollo original no
tenía acceso a red para instalar `statsmodels`. Si tu entorno sí lo tiene, el
equivalente exacto es `SARIMAX(np.log(y), order=(0,1,1), seasonal_order=(0,1,1,12))`.*

**Método 3 — Validación con tarifa real ASEP:** aplica el pliego tarifario oficial
(ENSA-MTD, tarifa de la Sede Principal) a las proyecciones de consumo/demanda, calibrado
con un factor empírico (0.836, derivado de 11 observaciones reales, CV=3%) que corrige
por el hecho de que la UTP no factura el 100% de su energía bajo esa tarifa única.

Se evaluó y **descartó** un tercer método (Holt-Winters) por sobreajuste en series
cortas (R² negativo en tarifa). Ver sección 3.3 del informe técnico para el detalle.


## Licencia / uso

Material de trabajo interno de la Universidad Tecnológica de Panamá. Los datos de
facturación son propiedad institucional; el pliego tarifario ASEP es información pública.
