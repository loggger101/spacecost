# -*- coding: utf-8 -*-
"""Commodity fuel prices, live or recorded, and the merge into the reference table.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

from typing import Dict

import numpy as np
import pandas as pd

from ._log import say
from .config import SpacecostConfig
from .propellants import (_COMPONENTS, PROPELLANTS_REFERENCE,
                          fuel_mass_fraction)
from .quotes import (Quote, closes_by_ticker, fetch_closes, load_snapshot,
                     missing)
from .units import (_per_bbl_to_per_kg, _per_gal_to_per_kg,
                    _per_mmbtu_to_per_kg_ng)

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

# Which propellant ROWS are blends whose live quote prices only the fuel half,
# and what the other half is.  Keyed by the row's exact `name`, because
# `startswith` matched by prefix and would have silently caught a future
# "methalox (subcooled)" row with the wrong mixture ratio.
#
# ⚠️  A row named here that no longer exists, or a blend key absent from
# `_OF_RATIOS`, is a live price quietly applied as if the propellant were pure
# fuel.  tests/test_schema.py holds both to the tables.
_LIVE_BLENDS = {
    "kerolox  (RP-1 / LOX)":   "kerolox",
    "methalox  (LCH4 / LOX)":  "methalox",
}
_LIVE_OXIDISER = {
    "kerolox":  "LOX",
    "methalox": "LOX",
}


# The tickers whose fluid prices a propellant row.  CL=F is a cross-check on
# HO=F and prices nothing, so a snapshot may leave it out; one missing either
# of these would leave a row the caller asked for at its reference price.
def required_fuel_tickers() -> Dict[str, str]:
    """Ticker -> quote unit, for every ticker some propellant's price reads."""
    proxies = {p.get("yfinance_proxy") for p in PROPELLANTS_REFERENCE}
    return {t: unit for t, (_label, unit, fluid) in _YFINANCE_TICKERS.items()
            if fluid in proxies}


# Ticker -> quote unit, for all three.  What `fetch_closes` is asked for.
FUEL_TICKERS: Dict[str, str] = {t: unit for t, (_label, unit, _fluid)
                                in _YFINANCE_TICKERS.items()}


def fetch_yfinance_fuel_prices(
    config: SpacecostConfig,
) -> pd.DataFrame:
    """
    Live commodity quotes for the liquid-propellant proxies.

    Returns a small DataFrame with one row per propellant that has a
    `yfinance_proxy` key in PROPELLANTS_REFERENCE.  Columns:
        name, live_cost_usd_per_kg, live_cost_usd_per_L,
        live_price_date, live_price_source.
    """
    say("\n  yfinance  (Yahoo Finance) - live fuel commodity prices ...")
    rows, failed = fetch_closes(FUEL_TICKERS)
    for problem in failed:
        say(f"     FAIL  {problem}")
    return fuel_prices_from_quotes(closes_by_ticker(rows))


def snapshot_fuel_prices(
    config: SpacecostConfig,
) -> pd.DataFrame:
    """The same frame as `fetch_yfinance_fuel_prices`, from a recorded snapshot.

    Reads `config.quote_snapshot` from spacecost/quotes/, and refuses one that
    lacks a ticker some row is priced from, or quotes it in another unit: a
    silent fall-back to the reference price is the failure snapshots exist to
    end.
    """
    name = config.quote_snapshot
    say(f"\n  Recorded fuel quotes - snapshot {name} ...")
    rows = load_snapshot(name)
    bad = missing(rows, required_fuel_tickers())
    if bad:
        raise ValueError(f"snapshot {name}: " + "; ".join(bad))
    return fuel_prices_from_quotes(closes_by_ticker(rows))


def fuel_prices_from_quotes(quotes: Dict[str, Quote]) -> pd.DataFrame:
    """The live-price frame from closes, however they were obtained.

    One conversion for both paths, so a build from a snapshot is the build that
    fetching those closes live would have made.
    """
    # Step 1, convert each commodity close to $/kg
    commodity_usd_per_kg: Dict[str, dict] = {}
    for ticker, (label, unit, fluid_key) in _YFINANCE_TICKERS.items():
        q = quotes.get(ticker)
        if q is None:
            continue
        if q.unit != unit:
            say(f"     WARN  {label} ({ticker}) - quoted per {q.unit!r}, "
                f"converted per {unit!r}; skipped")
            continue

        last_close = q.close
        last_date  = q.close_date

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
            "source":       q.source,
            "raw_quote":    last_close,
            "raw_unit":     unit,
            "quote_date":   last_date,
        }
        say(f"     OK  {label:38s} ({ticker}) = "
              f"{last_close:>8,.2f} USD/{unit:6s} "
              f"-> {usd_per_kg:>7.3f} USD/kg  [{last_date}]")

    if not commodity_usd_per_kg:
        say("     WARN  no commodity quotes")
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

        # A live quote prices the FUEL.  For a bipropellant only the fuel half
        # moves, so the mixture ratio is read back out of propellants.py rather
        # than restated here -- see `fuel_mass_fraction` for why that matters.
        blend = _LIVE_BLENDS.get(prop["name"])
        if blend is not None:
            fuel_frac = fuel_mass_fraction(blend)
            ox_cost   = _COMPONENTS[_LIVE_OXIDISER[blend]]["cost_usd_per_kg"]
            live_cost = fuel_frac * proxy["usd_per_kg"] + (1 - fuel_frac) * ox_cost
        else:
            live_cost = proxy["usd_per_kg"]

        rows.append({
            "name":                  prop["name"],
            "live_cost_usd_per_kg":  live_cost,
            "live_cost_usd_per_L":   live_cost * prop["density_kg_per_L"],
            "live_price_date":       proxy["quote_date"],
            "live_price_source":     f"{proxy['source']}:{proxy['ticker']}",
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
                # A live row that matches no reference row is a live price that
                # silently does not apply.  It means a propellant was renamed
                # without `_LIVE_BLENDS` and `yfinance_proxy` following it, and
                # the only visible symptom would be `price_basis` reading
                # "reference" on a row the caller asked to be live.
                say("     WARN  live quote for " + str(row["name"])
                    + " matches no reference propellant - price NOT applied")
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
