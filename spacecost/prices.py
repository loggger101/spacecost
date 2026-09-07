# -*- coding: utf-8 -*-
"""Live commodity fuel prices (yfinance) and the merge into the reference table.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

from typing import Dict

import numpy as np
import pandas as pd

from ._log import say
from .config import SpacecostConfig as TransportConfig
from .propellants import _COMPONENTS, PROPELLANTS_REFERENCE
from .units import (COMMODITY_DENSITY_KG_PER_L, _per_bbl_to_per_kg,
                    _per_gal_to_per_kg, _per_mmbtu_to_per_kg_ng)

# ─────────────────────────────────────────────────────────────────────────────
# YFINANCE FETCHER  (live commodity proxies for liquid propellants)
# ─────────────────────────────────────────────────────────────────────────────
# yfinance gives us:
#   • HO=F  NY heating oil  → No. 2 distillate, the standard RP-1 proxy
#                              (kerosene chemistry is essentially No. 1 / No. 2)
#                              Quote: USD per US gallon.
#   • NG=F  Henry-Hub natural gas → methane (LCH4) proxy
#                              Quote: USD per MMBtu.
#   • CL=F  WTI crude oil   → upstream cross-check on HO=F
#                              Quote: USD per barrel.
# Each updates the matching propellant's `live_cost_usd_per_kg` column.

_YFINANCE_TICKERS = {
    # ticker  : (commodity_name_for_print, quote_unit, fluid_density_key)
    "HO=F":   ("Heating oil (kerosene/RP-1 proxy)", "gallon",  "heating_oil"),
    "NG=F":   ("Natural gas (CH4/LCH4 proxy)",     "MMBtu",   "natural_gas"),
    "CL=F":   ("WTI crude (cross-check)",          "barrel",  "crude_oil"),
}

def fetch_yfinance_fuel_prices(
    config: TransportConfig,
) -> pd.DataFrame:
    """
    Live commodity quotes for the liquid-propellant proxies.

    Returns a small DataFrame with one row per propellant that has a
    `yfinance_proxy` key in PROPELLANTS_REFERENCE.  Columns:
        name, live_cost_usd_per_kg, live_cost_usd_per_L,
        live_price_date, live_price_source.
    """
    say("\n  yfinance  (Yahoo Finance) - live fuel commodity prices ...")

    try:
        import yfinance as yf
    except ImportError:
        say("     FAIL  yfinance not importable - skipped")
        return pd.DataFrame()

    # Step 1, pull commodity quotes
    commodity_usd_per_kg: Dict[str, dict] = {}
    for ticker, (label, unit, fluid_key) in _YFINANCE_TICKERS.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d", auto_adjust=False)
            closes = hist["Close"].dropna() if "Close" in hist else pd.Series(dtype=float)
            if closes.empty:
                say(f"     WARN  {label} ({ticker}) - no close data")
                continue

            last_close = float(closes.iloc[-1])
            last_date  = closes.index[-1].strftime("%Y-%m-%d")

            if unit == "gallon":
                usd_per_kg = _per_gal_to_per_kg(last_close, fluid_key)
            elif unit == "MMBtu":
                usd_per_kg = _per_mmbtu_to_per_kg_ng(last_close)
            elif unit == "barrel":
                usd_per_kg = _per_bbl_to_per_kg(last_close, fluid_key)
            else:
                say(f"     WARN  {label} - unrecognised unit {unit!r}")
                continue

            commodity_usd_per_kg[fluid_key] = {
                "usd_per_kg":   usd_per_kg,
                "ticker":       ticker,
                "raw_quote":    last_close,
                "raw_unit":     unit,
                "quote_date":   last_date,
            }
            say(f"     OK  {label:38s} ({ticker}) = "
                  f"{last_close:>8,.2f} USD/{unit:6s} "
                  f"-> {usd_per_kg:>7.3f} USD/kg  [{last_date}]")

        except Exception as exc:
            say(f"     FAIL  {label} ({ticker}) - {type(exc).__name__}: {exc}")

    if not commodity_usd_per_kg:
        say("     WARN  yfinance returned no commodity quotes")
        return pd.DataFrame()

    # Step 2, map onto propellants via `yfinance_proxy`.  Bipropellants
    # have a fuel proxy only; the LOX/N2O4 oxidiser cost stays at reference.
    # We blend the live fuel cost back in using the stored mass fractions.
    rows = []
    for prop in PROPELLANTS_REFERENCE:
        proxy_key = prop.get("yfinance_proxy")
        if not proxy_key or proxy_key not in commodity_usd_per_kg:
            continue
        proxy = commodity_usd_per_kg[proxy_key]

        if prop["name"].startswith("kerolox"):
            # RP-1 fraction was 1/(1+2.30) of the combined mass
            fuel_frac = 1.0 / (1.0 + 2.30)
            ox_cost   = _COMPONENTS["LOX"]["cost_usd_per_kg"]
            live_cost = fuel_frac * proxy["usd_per_kg"] + (1 - fuel_frac) * ox_cost
        elif prop["name"].startswith("methalox"):
            fuel_frac = 1.0 / (1.0 + 3.60)
            ox_cost   = _COMPONENTS["LOX"]["cost_usd_per_kg"]
            live_cost = fuel_frac * proxy["usd_per_kg"] + (1 - fuel_frac) * ox_cost
        else:
            live_cost = proxy["usd_per_kg"]

        rows.append({
            "name":                  prop["name"],
            "live_cost_usd_per_kg":  live_cost,
            "live_cost_usd_per_L":   live_cost * prop["density_kg_per_L"],
            "live_price_date":       proxy["quote_date"],
            "live_price_source":     f"yfinance:{proxy['ticker']}",
        })

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
# MERGE LIVE INTO REFERENCE
# ─────────────────────────────────────────────────────────────────────────────
def merge_propellant_prices(
    reference: pd.DataFrame, live: pd.DataFrame,
) -> pd.DataFrame:
    """
    Fold live yfinance prices into the propellant reference table.  Output
    `cost_usd_per_kg` and `cost_usd_per_L` resolve to live where available,
    reference where not, same pattern as Module 2.
    """
    say("\n  Merging live + reference propellant prices ...")

    out = reference.copy()
    out["live_cost_usd_per_kg"] = pd.NA
    out["live_cost_usd_per_L"]  = pd.NA
    out["live_price_date"]      = pd.NA
    out["live_price_source"]    = pd.NA

    if not live.empty:
        for _, row in live.iterrows():
            mask = out["name"] == row["name"]
            if not mask.any():
                continue
            idx = out.index[mask]
            out.loc[idx, "live_cost_usd_per_kg"] = row["live_cost_usd_per_kg"]
            out.loc[idx, "live_cost_usd_per_L"]  = row["live_cost_usd_per_L"]
            out.loc[idx, "live_price_date"]     = row["live_price_date"]
            out.loc[idx, "live_price_source"]   = row["live_price_source"]

    live_kg = pd.to_numeric(out["live_cost_usd_per_kg"], errors="coerce")
    ref_kg  = pd.to_numeric(out["ref_cost_usd_per_kg"],  errors="coerce")
    out["cost_usd_per_kg"] = live_kg.fillna(ref_kg)

    live_L = pd.to_numeric(out["live_cost_usd_per_L"], errors="coerce")
    ref_L  = pd.to_numeric(out["ref_cost_usd_per_L"],  errors="coerce")
    out["cost_usd_per_L"]  = live_L.fillna(ref_L)

    out["price_basis"] = np.where(
        live_kg.notna(), "live",
        np.where(ref_kg.notna(), "reference", "unpriced"),
    )

    n_live = int((out["price_basis"] == "live").sum())
    n_ref  = int((out["price_basis"] == "reference").sum())
    say(f"     Live  : {n_live} | Reference : {n_ref}")
    return out
