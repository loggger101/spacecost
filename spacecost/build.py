# -*- coding: utf-8 -*-
"""The pipeline: load the tables, fold in live prices, validate, write CSVs.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

import os
from datetime import datetime
from typing import Dict, Optional

import pandas as pd

from ._log import say
from .config import CONFIG, SpacecostConfig as TransportConfig
from .prices import fetch_yfinance_fuel_prices, merge_propellant_prices
from .tables import (build_transportation_summary, load_delta_v,
                     load_launch_vehicles, load_operational_costs,
                     load_propellants, load_storage)
from .validate import validate

# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def build_catalog(
    config:       TransportConfig = CONFIG,
    catalog_date: Optional[str]   = None,
) -> Dict[str, pd.DataFrame]:
    """
    Build every reference table and write the six CSVs.

    `catalog_date` pins the `catalog_date` stamp, "YYYY-MM-DD", instead of
    taking today. Pass it when you are comparing two builds: the stamp is a
    PROVENANCE column, not a model value, and midnight falling between two
    runs otherwise reads exactly like a defect. That mistake cost the parent
    project a release once -- it dropped `pipeline_version` before hashing
    and not this, got a clean MATCH on two cells and a DIFFER on the other
    two, and the whole difference was the date.

    Returns a dict of frames:
        {
          "launch_vehicles":   DataFrame,
          "propellants":       DataFrame,
          "delta_v_segments":  DataFrame,
          "operational_costs": DataFrame,
          "summary":           DataFrame,  # vehicle × segment × propellant
        }
    """
    t0 = datetime.now()

    say("=" * 75)
    say("     SPACECOST - TRANSPORTATION COST TABLES")
    say(f"      {t0.strftime('%Y-%m-%d %H:%M:%S')}  |  v{config.pipeline_version}")
    say("=" * 75)

    # ── Step 1, Reference tables (always-on) ────────────────────────────────
    launch_df = load_launch_vehicles()
    prop_ref  = load_propellants()
    dv_df     = load_delta_v()
    ops_df    = load_operational_costs()
    store_df  = load_storage()

    # ── Step 2, Live commodity proxies ──────────────────────────────────────
    live_prop = (
        fetch_yfinance_fuel_prices(config) if config.use_yfinance else pd.DataFrame()
    )

    # ── Step 3, Merge live into propellant reference ────────────────────────
    prop_df = merge_propellant_prices(prop_ref, live_prop)

    # ── Step 4: Validation ──────────────────────────────────────────────────
    validate(launch_df, prop_df, dv_df, ops_df)

    # ── Step 5: Composite summary ───────────────────────────────────────────
    summary_df = build_transportation_summary(launch_df, prop_df, dv_df, config)

    # ── Step 6, Metadata + export ───────────────────────────────────────────
    out_dir = config.table_dir()
    os.makedirs(out_dir, exist_ok=True)
    stamp   = catalog_date or t0.strftime("%Y-%m-%d")
    for df in (launch_df, prop_df, dv_df, ops_df, store_df, summary_df):
        df["catalog_date"]     = stamp
        df["pipeline_version"] = config.pipeline_version

    files = {
        "launch_vehicles.csv":          launch_df,
        "propellants.csv":              prop_df,
        "delta_v_segments.csv":         dv_df,
        "operational_costs.csv":        ops_df,
        "storage_systems.csv":          store_df,
        "transportation_summary.csv":   summary_df,
    }
    for fname, df in files.items():
        path = os.path.join(out_dir, fname)
        # lineterminator is pinned because pandas defaults it to os.linesep,
        # which makes a catalog written on Linux differ from the same catalog
        # written on Windows in every line, for no model reason.  CRLF is the
        # existing Windows output, so pinning it changes nothing here.
        df.to_csv(path, index=False, lineterminator="\r\n")
        say(f"       {fname:32s} -> {path}  ({len(df):,} rows)")

    elapsed = (datetime.now() - t0).total_seconds()
    say("\n" + "=" * 75)
    say("  OK  TRANSPORTATION CATALOG COMPLETE")
    say(f"      Tables   : {len(files)}")
    say(f"      Elapsed  : {elapsed:.1f}s")
    say("=" * 75)

    return {
        "launch_vehicles":   launch_df,
        "propellants":       prop_df,
        "delta_v_segments":  dv_df,
        "operational_costs": ops_df,
        "storage_systems":   store_df,
        "summary":           summary_df,
    }


# The name this function had as Module 3 of economicspace. Kept so a caller
# migrating from that module does not have to change the call site.
build_transportation_catalog = build_catalog
