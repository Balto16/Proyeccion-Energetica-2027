"""
08_generate_figures.py
-----------------------
Generates high-resolution publication-ready visualizations in English for the
UTP electricity projection study (2026-2027).

Figures produced in figures/:
  1. fig_consumo.png: Monthly Electricity Consumption (Historical & Forecast 2026-2027)
  2. fig_demanda.png: Monthly Peak Electricity Demand (Historical & Forecast 2026-2027)
  3. fig_tarifa.png: Effective Monthly Electricity Tariff (Historical & Forecast)
  4. fig_costo_anual.png: Annual Electricity Cost: Actual vs. Forecast by Method
  5. fig_consumo_por_sede.png: Cumulative Electricity Consumption by Campus (2022-May 2026)
  6. fig_desglose_energia_demanda.png: Annual Cost Breakdown: Energy Charge vs. Peak Demand Charge

Usage:  python code/08_generate_figures.py
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from importlib import import_module

_THIS_DIR = Path(__file__).resolve().parent
_ROOT = _THIS_DIR.parent
sys.path.insert(0, str(_THIS_DIR))
os.chdir(_ROOT)

mlr_mod = import_module("02_forecast_mlr")
air_mod = import_module("03_forecast_sarima_airline")
tariff_mod = import_module("05_tariff_calibration")
break_mod = import_module("06_energy_demand_breakdown")
exact_mod = import_module("07_exact_meter_tariff")

FIGURES_DIR = _ROOT / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Color Palette (DINAGEA / UTP design system)
COLOR_DARK_GREEN = "#244E38"  # Historical series / Main campus
COLOR_TEAL       = "#4D8270"  # SARIMA / Energy charge
COLOR_PURPLE     = "#4C2E6A"  # MLR / Accent
COLOR_AMBER      = "#B87B08"  # Demand charge / Tariff method
GRID_COLOR       = "#F0F0F0"

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.edgecolor"] = "#333333"
plt.rcParams["axes.linewidth"] = 0.8


def _apply_clean_layout(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, linestyle="-", alpha=0.5, color=GRID_COLOR, zorder=0)


def plot_time_series(monthly, future_dates, var, yhat_mlr, yhat_sarima, title, ylabel, out_name, divisor=1.0):
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=200)
    _apply_clean_layout(ax)

    hist_dates = pd.to_datetime(monthly["fecha"])
    hist_vals = monthly[var].values.astype(float) / divisor
    mlr_vals = np.array(yhat_mlr) / divisor
    sarima_vals = np.array(yhat_sarima) / divisor

    # Historical curve
    ax.plot(hist_dates, hist_vals, color=COLOR_DARK_GREEN, linewidth=2.0, label="Historical (actual)", zorder=3)

    # Forecast transition line
    transition_date = future_dates[0]
    ax.axvline(x=transition_date, color="#888888", linestyle=":", linewidth=1.2, alpha=0.85, zorder=2)

    # Method 1 (MLR)
    ax.plot(
        future_dates,
        mlr_vals,
        color=COLOR_PURPLE,
        linestyle="--",
        linewidth=1.8,
        marker="o",
        markersize=3.8,
        label="Forecast Method 1: MLR",
        zorder=4,
    )

    # Method 2 (SARIMA Airline)
    ax.plot(
        future_dates,
        sarima_vals,
        color=COLOR_TEAL,
        linestyle="--",
        linewidth=1.8,
        marker="^",
        markersize=4.2,
        label="Forecast Method 2: SARIMA (Airline)",
        zorder=4,
    )

    ax.set_title(title, fontsize=13, color=COLOR_DARK_GREEN, pad=12)
    ax.set_ylabel(ylabel, fontsize=10.5, color="#111111", labelpad=8)

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%y"))
    plt.xticks(rotation=45, ha="right", fontsize=9.5)
    plt.yticks(fontsize=9.5)

    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    plt.tight_layout()

    out_path = FIGURES_DIR / out_name
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Saved: {out_path.name}")


def plot_annual_cost(monthly, dates_f, c_mlr, t_mlr, c_air, t_air, d_air):
    fig, ax = plt.subplots(figsize=(10.5, 5.0), dpi=200)
    _apply_clean_layout(ax)

    # Historical totals
    hist_totals = monthly.groupby(monthly["fecha"].dt.year)["importe"].sum()
    hist_2022 = hist_totals.loc[2022] / 1e6
    hist_2023 = hist_totals.loc[2023] / 1e6
    hist_2024 = hist_totals.loc[2024] / 1e6
    hist_2025 = hist_totals.loc[2025] / 1e6

    # 2026: Jan-May actuals + Jun-Dec projections
    act_2026 = monthly[monthly["fecha"].dt.year == 2026]["importe"].sum()
    mlr_2026 = (act_2026 + np.sum(c_mlr[:7] * t_mlr[:7])) / 1e6
    air_2026 = (act_2026 + np.sum(c_air[:7] * t_air[:7])) / 1e6
    tar_2026 = (act_2026 + np.sum(tariff_mod.project_calibrated_cost(c_air[:7], d_air[:7], 54))) / 1e6

    # 2027: Full year projections
    mlr_2027 = np.sum(c_mlr[7:] * t_mlr[7:]) / 1e6
    air_2027 = np.sum(c_air[7:] * t_air[7:]) / 1e6
    tar_2027 = np.sum(tariff_mod.project_calibrated_cost(c_air[7:], d_air[7:], 54)) / 1e6

    labels = [
        "2022\n(actual)",
        "2023\n(actual)",
        "2024\n(actual)",
        "2025\n(actual)",
        "2026\nMLR",
        "2026\nSARIMA",
        "2026\nASEP Tariff",
        "2027\nMLR",
        "2027\nSARIMA",
        "2027\nASEP Tariff",
    ]
    values = [
        hist_2022,
        hist_2023,
        hist_2024,
        hist_2025,
        mlr_2026,
        air_2026,
        tar_2026,
        mlr_2027,
        air_2027,
        tar_2027,
    ]
    colors = [
        COLOR_DARK_GREEN,
        COLOR_DARK_GREEN,
        COLOR_DARK_GREEN,
        COLOR_DARK_GREEN,
        COLOR_PURPLE,
        COLOR_TEAL,
        COLOR_AMBER,
        COLOR_PURPLE,
        COLOR_TEAL,
        COLOR_AMBER,
    ]

    bars = ax.bar(range(len(values)), values, color=colors, width=0.75, zorder=3)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + 0.04,
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color="#222222",
        )

    ax.set_title("UTP – Annual Electricity Cost: Actual (2022–2025) vs. Forecast (2026–2027)", fontsize=13, color=COLOR_DARK_GREEN, pad=12)
    ax.set_ylabel("Annual Energy Cost (Million $)", fontsize=10.5, color="#111111", labelpad=8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8.8)
    ax.set_ylim(0, 4.15)
    plt.yticks(fontsize=9.5)
    plt.tight_layout()

    out_path = FIGURES_DIR / "fig_costo_anual.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Saved: {out_path.name}")


def plot_campus_consumption():
    merged = exact_mod.build_exact_meter_engine()
    campus_df = exact_mod.consumption_by_campus(merged).reset_index()

    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=200)
    _apply_clean_layout(ax)

    # Sort descending so highest is on top
    campus_df = campus_df.sort_values("total_consumption_kwh", ascending=True)

    y_pos = range(len(campus_df))
    mwh_vals = campus_df["total_consumption_kwh"] / 1000.0
    colors = [COLOR_DARK_GREEN if "victor levi sasso" in c.lower() else COLOR_TEAL for c in campus_df["center"]]

    bars = ax.barh(y_pos, mwh_vals, color=colors, height=0.72, zorder=3)

    for bar, (_, row) in zip(bars, campus_df.iterrows()):
        mwh = row["total_consumption_kwh"] / 1000.0
        pct = row["pct_consumption"]
        ax.text(
            bar.get_width() + 450,
            bar.get_y() + bar.get_height() / 2.0,
            f"{mwh:,.0f} MWh ({pct:.1f}%)",
            ha="left",
            va="center",
            fontsize=8.5,
            color="#222222",
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(campus_df["center"], fontsize=9.5)
    ax.set_xlabel("Cumulative Electricity Consumption 2022–May 2026 (MWh)", fontsize=10.5, labelpad=8)
    ax.set_title("UTP – Cumulative Electricity Consumption by Campus (2022–May 2026)", fontsize=13, color=COLOR_DARK_GREEN, pad=12)
    ax.set_xlim(0, 57000)
    plt.xticks(fontsize=9.5)
    plt.tight_layout()

    out_path = FIGURES_DIR / "fig_consumo_por_sede.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Saved: {out_path.name}")


def plot_energy_demand_breakdown(monthly, c_air, d_air):
    ensa_mtd = tariff_mod.load_ensa_mtd_tariffs()
    hist = break_mod.historical_cost_breakdown(monthly, ensa_mtd)

    years = [2023, 2024, 2025, 2026, 2027]
    labels = ["2023\n(actual)", "2024\n(actual)", "2025\n(actual)", "2026\n(projected)", "2027\n(projected)"]

    # Historical values
    e_vals = [hist.loc[y, "energy_cost_usd"] / 1e6 for y in [2023, 2024, 2025]]
    d_vals = [hist.loc[y, "demand_cost_usd"] / 1e6 for y in [2023, 2024, 2025]]

    # 2026 Projection
    e_2026 = (hist.loc[2026, "energy_cost_usd"] + np.sum(c_air[:7] * tariff_mod.ACTIVE_ENERGY_CHARGE * tariff_mod.CALIBRATION_FACTOR)) / 1e6
    d_2026 = (hist.loc[2026, "demand_cost_usd"] + np.sum(d_air[:7] * tariff_mod.ACTIVE_DEMAND_CHARGE * tariff_mod.CALIBRATION_FACTOR)) / 1e6
    e_vals.append(e_2026)
    d_vals.append(d_2026)

    # 2027 Projection
    e_2027 = np.sum(c_air[7:] * tariff_mod.ACTIVE_ENERGY_CHARGE * tariff_mod.CALIBRATION_FACTOR) / 1e6
    d_2027 = np.sum(d_air[7:] * tariff_mod.ACTIVE_DEMAND_CHARGE * tariff_mod.CALIBRATION_FACTOR) / 1e6
    e_vals.append(e_2027)
    d_vals.append(d_2027)

    fig, ax = plt.subplots(figsize=(9.2, 4.8), dpi=200)
    _apply_clean_layout(ax)

    x = np.arange(len(years))
    width = 0.65

    bars_e = ax.bar(x, e_vals, width, label="Energy charge ($/kWh)", color=COLOR_TEAL, zorder=3)
    bars_d = ax.bar(x, d_vals, width, bottom=e_vals, label="Peak demand charge ($/kW)", color=COLOR_AMBER, zorder=3)

    for i in range(len(years)):
        tot = e_vals[i] + d_vals[i]
        pct_e = round(e_vals[i] / tot * 100)
        pct_d = round(d_vals[i] / tot * 100)

        # Labels inside bars
        ax.text(x[i], e_vals[i] / 2.0, f"{pct_e}%", ha="center", va="center", color="white", fontweight="bold", fontsize=9.5)
        ax.text(x[i], e_vals[i] + d_vals[i] / 2.0, f"{pct_d}%", ha="center", va="center", color="white", fontweight="bold", fontsize=9.5)

        # Total on top of bar
        ax.text(x[i], tot + 0.07, f"${tot:.2f}M", ha="center", va="bottom", color=COLOR_DARK_GREEN, fontweight="bold", fontsize=9.5)

    ax.set_title("UTP – Electricity Cost Breakdown: Energy Charge vs. Peak Demand Charge", fontsize=13, color=COLOR_DARK_GREEN, pad=14)
    ax.set_ylabel("Annual Cost (Million $)", fontsize=10.5, color="#111111", labelpad=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylim(0, 4.1)
    ax.legend(frameon=False, loc="upper left", fontsize=9.5)
    plt.tight_layout()

    out_path = FIGURES_DIR / "fig_desglose_energia_demanda.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Saved: {out_path.name}")


def main():
    print("Generating all project figures in English...")
    monthly = pd.read_csv("data/monthly.csv", parse_dates=["fecha"])

    c_y = monthly["consumo_kwh"].values.astype(float)
    d_y = monthly["demanda_kw"].values.astype(float)
    t_y = monthly["tarifa_prom"].values.astype(float)

    future_dates, c_mlr, _, _ = mlr_mod.mlr_forecast(c_y, monthly["fecha"], 19)
    _, d_mlr, _, _ = mlr_mod.mlr_forecast(d_y, monthly["fecha"], 19)
    _, t_mlr, _, _ = mlr_mod.mlr_forecast(t_y, monthly["fecha"], 19)

    c_air, _, _, _ = air_mod.airline_forecast(c_y, 19)
    d_air, _, _, _ = air_mod.airline_forecast(d_y, 19)
    t_air, _, _, _ = air_mod.airline_forecast(t_y, 19)

    # 1. Monthly Consumption
    plot_time_series(
        monthly,
        future_dates,
        "consumo_kwh",
        c_mlr,
        c_air,
        title="UTP – Monthly Electricity Consumption: Historical and Forecast 2026–2027",
        ylabel="Monthly Consumption (MWh)",
        out_name="fig_consumo.png",
        divisor=1000.0,
    )

    # 2. Monthly Demand
    plot_time_series(
        monthly,
        future_dates,
        "demanda_kw",
        d_mlr,
        d_air,
        title="UTP – Monthly Peak Electricity Demand: Historical and Forecast 2026–2027",
        ylabel="Billed Peak Demand (kW)",
        out_name="fig_demanda.png",
        divisor=1.0,
    )

    # 3. Monthly Tariff
    plot_time_series(
        monthly,
        future_dates,
        "tarifa_prom",
        t_mlr,
        t_air,
        title="UTP – Monthly Effective Electricity Tariff: Historical and Forecast",
        ylabel="Average Tariff ($/kWh)",
        out_name="fig_tarifa.png",
        divisor=1.0,
    )

    # 4. Annual Cost
    plot_annual_cost(monthly, future_dates, c_mlr, t_mlr, c_air, t_air, d_air)

    # 5. Campus breakdown
    plot_campus_consumption()

    # 6. Energy vs Demand breakdown
    plot_energy_demand_breakdown(monthly, c_air, d_air)

    print("All 6 figures regenerated successfully in figures/.")


if __name__ == "__main__":
    main()
