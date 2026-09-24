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
    purchasable_only: bool = False,
) -> pd.DataFrame:
    """Rank launch vehicles by $/kg to a given destination.

    `purchasable_only` (v0.4.0) keeps only rows whose `availability` is
    `open`.  Off by default so the ranking is unchanged for existing callers,
    but read what it removes before leaving it off: `status` says whether a
    vehicle FLIES, and 28 of the 48 operational rows fly for somebody else --
    sanctioned, export-controlled, sold out or government-only.  The cheapest
    LEO price in an unfiltered ranking is not always one a Western mission can
    book.

    ⚠️  v1.15.0 BEHAVIOUR CHANGE: a vehicle that does not REACH the destination
    is now dropped rather than ranked last.

    Electron, Vega C and Alpha carry nothing beyond LEO, so their
    `payload_gto_kg` is 0 and their `usd_per_kg_to_gto` is NaN.  The old filter
    was `payload >= min_payload_kg`, and with the default `min_payload_kg=0`
    that is `0 >= 0`, so all three were included in a ranking of the cheapest
    way to GTO -- sorted to the bottom, because pandas puts NaN last, and so
    invisible right up until somebody asked for more rows than there were real
    answers.  A price of "not at any price" is not a large price, and the two
    must not sort against each other.
    """
    col = {"leo":    "usd_per_kg_to_leo",
           "gto":    "usd_per_kg_to_gto",
           "escape": "usd_per_kg_to_escape"}[destination.lower()]
    pay = {"leo":    "payload_leo_kg",
           "gto":    "payload_gto_kg",
           "escape": "payload_escape_kg"}[destination.lower()]

    df = catalog["launch_vehicles"].copy()
    if operational_only:
        df = df[df["status"] == "operational"]
    if purchasable_only:
        df = df[df["availability"] == "open"]
    df = df[df[pay] >= min_payload_kg]
    # Reachability, checked on BOTH columns: a missing price and a zero payload
    # are two different ways for the table to say the vehicle does not go there,
    # and a row is only ranked if it says neither.
    reaches = (np.isfinite(pd.to_numeric(df[col], errors="coerce"))
               & (pd.to_numeric(df[pay], errors="coerce") > 0))
    df = df[reaches]
    return df.sort_values(col).reset_index(drop=True)


def cheapest_propellant_for(
    catalog: Dict[str, pd.DataFrame],
    delta_v_m_per_s: float,
    include_propellantless: bool = False,
    apply_dv_penalty: bool = True,
) -> pd.DataFrame:
    """Rank propellants by USD-per-kg-payload to apply this Δv (rocket eq.).

    ⚠️  v1.15.0 BEHAVIOUR CHANGE, and it moves the top of the ranking.  The
    propellant table carries two columns whose entire purpose is to stop the
    rocket equation being read literally, and this helper read it literally.

    **Propellantless rows are excluded by default.**  A sail carries no
    propellant, so its Isp is infinite by construction, so the mass ratio is 1,
    so the cost of any Δv is exactly $0.00 -- and the three sail and tether rows
    swept the top three places of every ranking this function has ever
    returned.  They are not free; their characteristic acceleration is around
    0.1 mm/s², which is fine for a 6 kg cubesat and meaningless for a hold full
    of ore, and sizing one properly needs a thrust-limited trajectory model this
    package does not have.  PROPELLANTS_REFERENCE says exactly this at the
    `propellantless` flag, and `validate` already excludes them from its bands
    for the same reason.  Pass `include_propellantless=True` to see them, and
    read the $0.00 as "the rocket equation does not apply here".

    **The low-thrust Δv penalty is applied by default.**  `dv_penalty_factor`
    is 1.5 on every electric row because a milli-newton stage cannot fly the
    impulsive burns the Δv table assumes -- it spirals, and a spiral costs
    strictly more Δv than the equivalent impulse.  Ranking electric propulsion
    on an impulsive budget is the specific error the column exists to prevent,
    and it is worth real places rather than a rounding: it moves 17 of the 38
    ranked rows at 6,500 m/s and 25 of them at the main-belt 10,500, where it
    costs VASIMR first place outright.

    The penalised Δv is RETURNED, in `effective_dv_m_per_s`, rather than being
    applied out of sight.  Silently moving the number the caller asked about
    would be its own quiet defect.

    ⚠️  `build_transportation_summary` deliberately does NOT do either of these
    things, and must not start.  That table is a raw cross-join, and
    economicspace's Stage 4 applies the penalty itself when it reads it;
    applying it in both places would charge it twice.  This helper has no
    Stage 4 behind it, so if it does not apply the penalty, nothing does.
    """
    df = catalog["propellants"].copy()

    if not include_propellantless and "propellantless" in df.columns:
        # `.ne(True)` for the reason validate.py sets out at length: a row that
        # omits the key makes the column `object`, and `.astype(bool)` reads
        # NaN as True, which would silently DROP a real propellant here.
        df = df[df["propellantless"].ne(True)]

    if apply_dv_penalty and "dv_penalty_factor" in df.columns:
        penalty = pd.to_numeric(df["dv_penalty_factor"],
                                errors="coerce").fillna(1.0)
    else:
        penalty = pd.Series(1.0, index=df.index)
    df["dv_penalty_factor"] = penalty
    df["effective_dv_m_per_s"] = float(delta_v_m_per_s) * penalty

    df["usd_per_kg_payload_for_dv"] = df.apply(
        lambda r: cost_per_dv_usd_per_kg(
            r["cost_usd_per_kg"], r["isp_vac_s"], r["effective_dv_m_per_s"],
        ),
        axis=1,
    )
    return df[["name", "isp_vac_s", "cost_usd_per_kg", "dv_penalty_factor",
               "effective_dv_m_per_s",
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
    apply_dv_penalty:   bool = True,
) -> dict:
    """
    Full end-to-end USD breakdown for one mission scenario.

    Returns dict with: launch_usd, outbound_prop_usd, return_prop_usd,
    hardware_usd, ops_usd, contingency_usd, total_usd, usd_per_kg_returned,
    the three mass figures, and (v1.15.0) `dv_penalty_factor` with the two
    effective Δv values it produced.

    ⚠️  v1.15.0 BEHAVIOUR CHANGE: the low-thrust Δv penalty is applied, so
    costing a mission on an ELECTRIC propellant now returns larger numbers.
    Same reason as `cheapest_propellant_for`: `dv_penalty_factor` is 1.5 on
    every electric row because a milli-newton stage spirals rather than burns,
    and a spiral costs strictly more Δv.  Chemical rows carry 1.0 and are
    unaffected, which is every default this function ships with.

    The factor and both effective Δv values are returned rather than applied
    out of sight, so a caller can see that the number it asked about was not
    the number that was flown.

    ⚠️  IF YOUR CALLER ALREADY APPLIES THE PENALTY, pass
    `apply_dv_penalty=False` or you will charge it twice.  economicspace's
    Stage 4 does apply it, on the SUMMARY -- which is a different path, and
    `build_transportation_summary` is deliberately left raw for exactly that
    reason.  This helper has no Stage 4 behind it, so if it does not apply the
    penalty, nothing does.

    ⚠️  WHAT IS STILL NOT MODELLED, and it all pushes the same way (optimistic):
    tankage mass (`tank_kg_per_L` is in the table and nothing here charges it
    to the launcher), boil-off over `mission_duration_yr` (`boiloff_pct_per_day`
    is in the table too, and over a three-year hold it is not small for a
    cryogen), and the power plant an electric stage needs.  Treat the total as
    a floor.
    """
    lv  = catalog["launch_vehicles"].set_index("name").loc[launch_vehicle]
    p   = catalog["propellants"].set_index("name").loc[propellant]
    ops = catalog["operational_costs"].set_index("category")

    isp = p["isp_vac_s"]

    # Low-thrust penalty, read from the propellant row.  `or 1.0` catches both
    # a missing column and a NaN: a propellant that does not say otherwise
    # flies impulsively, which is true of every chemical row.
    penalty = 1.0
    if apply_dv_penalty:
        stated = p.get("dv_penalty_factor", 1.0)
        penalty = float(stated) if pd.notna(stated) else 1.0
    delta_v_outbound = float(delta_v_outbound) * penalty
    delta_v_return   = float(delta_v_return) * penalty

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
        # The Δv actually flown, which is not the Δv that was asked for on an
        # electric row.  Returned so the difference is visible in the output
        # rather than only in this function.
        "dv_penalty_factor":     penalty,
        "effective_dv_outbound": delta_v_outbound,
        "effective_dv_return":   delta_v_return,
    }
