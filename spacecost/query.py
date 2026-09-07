# -*- coding: utf-8 -*-
"""Convenience queries over a built catalog, and a worked mission breakdown.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

import numpy as np
from typing import Dict

import pandas as pd

from .config import CONFIG, SpacecostConfig as TransportConfig
from .rocket import cost_per_dv_usd_per_kg, propellant_mass_for_dv

# ─────────────────────────────────────────────────────────────────────────────
# QUERY UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
def cheapest_launch_to(
    catalog: Dict[str, pd.DataFrame],
    destination: str = "leo",       # "leo" | "gto" | "escape"
    min_payload_kg: float = 0.0,
    operational_only: bool = True,
) -> pd.DataFrame:
    """Rank launch vehicles by $/kg to a given destination."""
    col = {"leo":    "usd_per_kg_to_leo",
           "gto":    "usd_per_kg_to_gto",
           "escape": "usd_per_kg_to_escape"}[destination.lower()]
    pay = {"leo":    "payload_leo_kg",
           "gto":    "payload_gto_kg",
           "escape": "payload_escape_kg"}[destination.lower()]

    df = catalog["launch_vehicles"].copy()
    if operational_only:
        df = df[df["status"] == "operational"]
    df = df[df[pay] >= min_payload_kg]
    return df.sort_values(col).reset_index(drop=True)


def cheapest_propellant_for(
    catalog: Dict[str, pd.DataFrame],
    delta_v_m_per_s: float,
) -> pd.DataFrame:
    """Rank propellants by USD-per-kg-payload to apply this Δv (rocket eq.)."""
    df = catalog["propellants"].copy()
    df["usd_per_kg_payload_for_dv"] = df.apply(
        lambda r: cost_per_dv_usd_per_kg(
            r["cost_usd_per_kg"], r["isp_vac_s"], delta_v_m_per_s,
        ),
        axis=1,
    )
    return df[["name", "isp_vac_s", "cost_usd_per_kg",
               "usd_per_kg_payload_for_dv"]].sort_values(
        "usd_per_kg_payload_for_dv",
    ).reset_index(drop=True)


def mission_cost_breakdown(
    catalog: Dict[str, pd.DataFrame],
    payload_kg:         float,
    delta_v_outbound:   float,
    delta_v_return:     float,
    launch_vehicle:     str,
    propellant:         str,
    mission_duration_yr: float,
    hardware_kg:        float = 0.0,
    config:             TransportConfig = CONFIG,
) -> dict:
    """
    Full end-to-end USD breakdown for one mission scenario.

    Returns dict with: launch_usd, outbound_prop_usd, return_prop_usd,
    hardware_usd, ops_usd, contingency_usd, total_usd, usd_per_kg_returned.
    """
    lv  = catalog["launch_vehicles"].set_index("name").loc[launch_vehicle]
    p   = catalog["propellants"].set_index("name").loc[propellant]
    ops = catalog["operational_costs"].set_index("category")

    isp = p["isp_vac_s"]

    # ── Return-leg propellant; solved first because it sits on the outbound
    # leg as dead mass (unless ISRU manufactures it at the asteroid).
    #
    #   m_prop_return = m_payload × (exp(Δv_ret / (Isp·g₀)) − 1)
    return_prop_kg = float(propellant_mass_for_dv(
        payload_kg, delta_v_return, isp,
    ))
    return_prop_cost_kg = (
        config.isru_processing_usd_per_kg
        if config.isru_return_propellant
        else p["cost_usd_per_kg"]
    )
    return_prop_usd = return_prop_kg * return_prop_cost_kg

    # ── Outbound-leg propellant, must push (payload + hardware + return_prop)
    # through Δv_outbound.  This is the bug-fix vs naive `propellant_mass_for_dv
    # (payload + hardware)`: omitting return_prop_kg understates outbound mass
    # and gives optimistic launch + propellant numbers.
    #
    # If ISRU is enabled, return prop is made at the asteroid, so it does NOT
    # sit on the outbound leg; outbound_dry collapses to (payload + hardware).
    outbound_dry = (
        payload_kg + hardware_kg
        if config.isru_return_propellant
        else payload_kg + hardware_kg + return_prop_kg
    )
    outbound_prop_kg = float(propellant_mass_for_dv(
        outbound_dry, delta_v_outbound, isp,
    ))

    # Launch lifts (outbound_dry + outbound_prop_kg) to LEO
    launch_mass    = outbound_dry + outbound_prop_kg
    launch_usd     = launch_mass * lv["usd_per_kg_to_leo"]
    outbound_prop_usd = outbound_prop_kg * p["cost_usd_per_kg"]

    # Hardware recurring + dev amortised
    hw_recurring_per_kg = ops.loc["Mining payload recurring cost", "value"]
    hardware_usd = hardware_kg * hw_recurring_per_kg

    # Mission ops, per-year × duration
    ops_per_year = ops.loc["Mission operations", "value"]
    ops_usd = ops_per_year * mission_duration_yr

    subtotal = launch_usd + outbound_prop_usd + return_prop_usd + hardware_usd + ops_usd
    contingency_usd = subtotal * config.contingency_fraction
    total_usd       = subtotal + contingency_usd

    return {
        "launch_usd":            launch_usd,
        "outbound_prop_usd":     outbound_prop_usd,
        "return_prop_usd":       return_prop_usd,
        "hardware_usd":          hardware_usd,
        "ops_usd":               ops_usd,
        "contingency_usd":       contingency_usd,
        "total_usd":             total_usd,
        "usd_per_kg_returned":   total_usd / payload_kg if payload_kg > 0 else np.nan,
        "outbound_prop_kg":      outbound_prop_kg,
        "return_prop_kg":        return_prop_kg,
        "launched_mass_kg":      launch_mass,
    }
