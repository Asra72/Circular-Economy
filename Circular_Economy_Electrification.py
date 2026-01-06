#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd

years = np.arange(2025, 2051)

scenarios = {
    "Vienna_Base": {
        "electrification_growth": 0.015,
        "renewables_start_2025": 0.45,
        "renewables_target_2050": 0.75,
        "battery_share_of_load": 0.08,
        "recycling_start_2025": 0.15,
        "recycling_rate_2050": 0.60,
    },
    "Vienna_FastElectrification": {
        "electrification_growth": 0.025,
        "renewables_start_2025": 0.45,
        "renewables_target_2050": 0.85,
        "battery_share_of_load": 0.12,
        "recycling_start_2025": 0.15,
        "recycling_rate_2050": 0.75,
    },
    "Vienna_CircularPush": {
        "electrification_growth": 0.020,
        "renewables_start_2025": 0.45,
        "renewables_target_2050": 0.80,
        "battery_share_of_load": 0.10,
        "recycling_start_2025": 0.20,
        "recycling_rate_2050": 0.85,
    },
}

base_demand_twh_2025 = 19.0

grid_emissions_t_per_mwh_2025 = 0.18
grid_emissions_t_per_mwh_2050 = 0.03

pv_cf = 0.14
wind_cf = 0.27

pv_capex_eur_per_kw = 650
wind_capex_eur_per_kw = 1200
battery_capex_eur_per_kwh = 180

battery_lifetime_years = 12

kwh_per_twh = 1e9
hours_per_year = 8760

materials_kg_per_kwh = {
    "Li": 0.10,
    "Ni": 0.60,
    "Co": 0.12,
}

primary_material_co2_kg_per_kg = {
    "Li": 8.0,
    "Ni": 12.0,
    "Co": 18.0,
}

recycled_material_co2_factor = 0.35


def ramp(a, b, x):
    return a + (b - a) * x


def share_path(start, target, y0, y1, y):
    x = (y - y0) / (y1 - y0)
    x = float(np.clip(x, 0.0, 1.0))
    return ramp(start, target, x)


def grid_emissions_path(y):
    return share_path(
        grid_emissions_t_per_mwh_2025,
        grid_emissions_t_per_mwh_2050,
        years[0],
        years[-1],
        y,
    )


def capacity_needed_gw(energy_twh, cf):
    mwh = energy_twh * 1e6
    return mwh / (hours_per_year * cf) / 1e3


def run_scenario(name, p):
    demand = []
    re_share = []
    grid_em = []
    rec_rate = []

    for y in years:
        t = y - years[0]
        d = base_demand_twh_2025 * ((1 + p["electrification_growth"]) ** t)
        demand.append(d)
        re_share.append(
            share_path(
                p["renewables_start_2025"],
                p["renewables_target_2050"],
                years[0],
                years[-1],
                y,
            )
        )
        grid_em.append(grid_emissions_path(y))
        rec_rate.append(
            share_path(
                p["recycling_start_2025"],
                p["recycling_rate_2050"],
                years[0],
                years[-1],
                y,
            )
        )

    demand = np.array(demand, dtype=float)
    re_share = np.array(re_share, dtype=float)
    grid_em = np.array(grid_em, dtype=float)
    rec_rate = np.array(rec_rate, dtype=float)

    re_energy = demand * re_share
    nonre_energy = demand - re_energy

    pv_energy = 0.5 * re_energy
    wind_energy = 0.5 * re_energy

    pv_gw = np.array([capacity_needed_gw(e, pv_cf) for e in pv_energy], dtype=float)
    wind_gw = np.array([capacity_needed_gw(e, wind_cf) for e in wind_energy], dtype=float)

    pv_new_gw = np.maximum(0, np.diff(pv_gw, prepend=pv_gw[0]))
    wind_new_gw = np.maximum(0, np.diff(wind_gw, prepend=wind_gw[0]))

    battery_energy_twh = demand * p["battery_share_of_load"]
    battery_kwh = battery_energy_twh * kwh_per_twh

    batt_inflow_kwh = np.maximum(0, np.diff(battery_kwh, prepend=battery_kwh[0]))

    batt_outflow_kwh = np.zeros_like(batt_inflow_kwh, dtype=float)
    for i, y in enumerate(years):
        old_year = y - battery_lifetime_years
        if old_year >= years[0]:
            j = int(old_year - years[0])
            batt_outflow_kwh[i] = batt_inflow_kwh[j]

    recycled_kwh = batt_outflow_kwh * rec_rate
    landfill_kwh = batt_outflow_kwh * (1 - rec_rate)

    co2_imports_t = nonre_energy * 1e6 * grid_em

    co2_materials_t = np.zeros_like(years, dtype=float)
    for m, kgpkwh in materials_kg_per_kwh.items():
        primary = batt_inflow_kwh * kgpkwh
        recycled = batt_outflow_kwh * kgpkwh * rec_rate
        co2_materials_t += (
            primary * primary_material_co2_kg_per_kg[m]
            + recycled * primary_material_co2_kg_per_kg[m] * recycled_material_co2_factor
        ) / 1000.0

    pv_cost = pv_new_gw * 1e6 * pv_capex_eur_per_kw
    wind_cost = wind_new_gw * 1e6 * wind_capex_eur_per_kw
    batt_cost = batt_inflow_kwh * battery_capex_eur_per_kwh

    return pd.DataFrame({
        "year": years,
        "scenario": name,
        "demand_twh": demand,
        "renewables_share": re_share,
        "battery_stock_gwh": battery_kwh / 1e6,
        "battery_recycled_gwh": recycled_kwh / 1e6,
        "battery_landfill_gwh": landfill_kwh / 1e6,
        "co2_total_t": co2_imports_t + co2_materials_t,
        "capex_total_eur": pv_cost + wind_cost + batt_cost,
    })


frames = []
for name, params in scenarios.items():
    frames.append(run_scenario(name, params))

df = pd.concat(frames, ignore_index=True)

print(
    df[df["year"].isin([2025, 2030, 2040, 2050])]
    .round(3)
    .to_string(index=False)
)

df.to_csv("vienna_circular_electrification_results.csv", index=False)
print("\nSaved: vienna_circular_electrification_results.csv")


# In[ ]:




