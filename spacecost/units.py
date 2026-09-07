# -*- coding: utf-8 -*-
"""Unit conversions and the physical constants the tables are quoted in.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""



# ─────────────────────────────────────────────────────────────────────────────
# UNIT CONVERSION HELPERS
# ─────────────────────────────────────────────────────────────────────────────
# yfinance commodity quotes arrive in legacy units (USD/bbl, USD/MMBtu,
# USD/gallon).  Everything funnels through these helpers so output columns
# carry the explicit `_usd_per_kg` / `_usd_per_L` suffix.

G0_M_S2          = 9.806_65          # standard gravity, used in rocket equation
LITRES_PER_GAL   = 3.785_411_784     # US gallon → litre
LITRES_PER_BBL   = 158.987_294_928   # oil barrel → litre

# Approximate mass densities of liquid commodities at storage conditions.
# Used to map yfinance per-volume quotes onto per-mass propellant prices.
COMMODITY_DENSITY_KG_PER_L = {
    "crude_oil":       0.870,   # WTI ~32° API
    "heating_oil":     0.845,   # No. 2 distillate; kerosene/RP-1 proxy
    "rbob_gasoline":   0.740,
    "natural_gas":     0.422,   # methane LIQUID at boiling point (LNG/LCH4)
}


def _per_bbl_to_per_kg(usd_per_bbl: float, fluid: str) -> float:
    """Convert a $/barrel oil quote to $/kg using the named fluid's density."""
    rho = COMMODITY_DENSITY_KG_PER_L[fluid]
    return float(usd_per_bbl) / (LITRES_PER_BBL * rho)


def _per_gal_to_per_kg(usd_per_gal: float, fluid: str) -> float:
    """Convert a $/gallon quote to $/kg."""
    rho = COMMODITY_DENSITY_KG_PER_L[fluid]
    return float(usd_per_gal) / (LITRES_PER_GAL * rho)


def _per_mmbtu_to_per_kg_ng(usd_per_mmbtu: float) -> float:
    """
    Henry-Hub natural gas trades in $/MMBtu (1 MMBtu = 10⁶ BTU).
    1 kg LNG ≈ 50 MJ ≈ 0.04739 MMBtu.  So $/kg = $/MMBtu × 0.04739.
    """
    return float(usd_per_mmbtu) * 0.047_39
