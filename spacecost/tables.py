# -*- coding: utf-8 -*-
"""Reference-table loaders, and the (vehicle x segment x propellant) summary.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

import numpy as np
import pandas as pd

from ._log import say
from .config import CONFIG, SpacecostConfig as TransportConfig
from .deltav import DELTA_V_REFERENCE
from .operations import OPERATIONAL_COSTS_REFERENCE
from .propellants import PROPELLANTS_REFERENCE, _apply_thruster_data
from .rocket import propellant_mass_for_dv
from .storage import STORAGE_REFERENCE
from .vehicles import LAUNCH_VEHICLES_REFERENCE

# ─────────────────────────────────────────────────────────────────────────────
# REFERENCE-TABLE LOADERS  (always-on)
# ─────────────────────────────────────────────────────────────────────────────
def load_launch_vehicles() -> pd.DataFrame:
    """`LAUNCH_VEHICLES_REFERENCE` as a frame. Always on; nothing is fetched."""
    say("\n  Loading launch-vehicles reference ...")
    df = pd.DataFrame(LAUNCH_VEHICLES_REFERENCE)
    say(f"     OK  {len(df)} vehicles")
    return df


def load_propellants() -> pd.DataFrame:
    """`PROPELLANTS_REFERENCE` as a frame, with the thruster columns filled in.

    The only loader here that does more than wrap a list: `_apply_thruster_data`
    attaches `thruster_kg_per_n`, `thruster_efficiency` and `thrust_scaling` per
    technology, and RAISES on an electric row with no entry rather than
    defaulting, because a missing per-newton figure is what let Stage 4 size
    micronewton devices as ten-newton cargo tugs.
    """
    say("\n  Loading propellants reference ...")
    df = pd.DataFrame(PROPELLANTS_REFERENCE)
    _apply_thruster_data(df)
    n_rep = int((df["thrust_scaling"] == "replicated").sum())
    say(f"     OK  {len(df)} propellant systems "
          f"({n_rep} thrust by replication - see _THRUSTER_SYSTEMS)")
    return df


def load_delta_v() -> pd.DataFrame:
    """`DELTA_V_REFERENCE` as a frame: the trajectory segments, in m/s."""
    say("\n  Loading mission dv reference ...")
    df = pd.DataFrame(DELTA_V_REFERENCE)
    say(f"     OK  {len(df)} trajectory segments")
    return df


def load_operational_costs() -> pd.DataFrame:
    """`OPERATIONAL_COSTS_REFERENCE` as a frame.

    The one Stage 4 leans on hardest, and the one it checks by ROW as well as
    by column (`schema_check`), because the table is keyed by category so a
    missing figure is invisible to a column test.
    """
    say("\n  Loading operational-costs reference ...")
    df = pd.DataFrame(OPERATIONAL_COSTS_REFERENCE)
    say(f"     OK  {len(df)} cost categories")
    return df


def load_storage() -> pd.DataFrame:
    """`STORAGE_REFERENCE` as a frame, written to storage_systems.csv.

    ⚠️  Stage 4 does NOT load that CSV. Everything in here it needs was moved
    into `OPERATIONAL_COSTS_REFERENCE` in v1.11.0, after this table had spent
    two releases being quoted as a model while being documentation. If you add
    a figure here that Stage 4 should read, add it there too.
    """
    say("\n   Loading storage-systems reference ...")
    df = pd.DataFrame(STORAGE_REFERENCE)
    say(f"     OK  {len(df)} storage systems")
    return df

def build_transportation_summary(
    launch_df:      pd.DataFrame,
    propellant_df:  pd.DataFrame,
    delta_v_df:     pd.DataFrame,
    config:         TransportConfig = CONFIG,
) -> pd.DataFrame:
    """
    Cross-join (vehicle × in-space-segment × propellant) into a long-form
    table of normalised costs.  This is what Module 4 reads to pick the
    cheapest viable combination for any asteroid.

    Output rows:  (vehicle, segment, propellant) tuples with the columns
        launch_usd_per_kg
        in_space_prop_usd_per_kg_payload     ← rocket-equation cost
        total_usd_per_kg_payload_to_segment_end
        propellant_mass_per_kg_payload
        segment_duration_yr
    """
    say("\n  Building (vehicle x segment x propellant) cost summary ...")

    # Only price IN-SPACE Δv with the propellant table; surface ascent is
    # already baked into the launch vehicle's $/kg-to-LEO.
    in_space = delta_v_df[
        ~delta_v_df["segment"].str.contains("surface", case=False)
    ].copy()

    rows = []
    for _, lv in launch_df.iterrows():
        # Use the LEO price as the baseline cost to "lift" the payload to
        # the start of every in-space segment.  Module 4 can switch this
        # to escape-class numbers for deep-space-direct injections.
        leo_cost_per_kg = lv["usd_per_kg_to_leo"]

        for _, seg in in_space.iterrows():
            for _, p in propellant_df.iterrows():
                cost_per_kg = float(p["cost_usd_per_kg"])
                isp         = float(p["isp_vac_s"])
                dv          = float(seg["dv_m_per_s"])

                prop_per_payload = float(propellant_mass_for_dv(1.0, dv, isp))
                in_space_cost    = prop_per_payload * cost_per_kg

                rows.append({
                    "vehicle":                                lv["name"],
                    "vehicle_status":                         lv["status"],
                    "segment":                                seg["segment"],
                    "segment_dv_m_per_s":                     dv,
                    "segment_duration_yr":                    seg["duration_yr"],
                    "propellant":                             p["name"],
                    "propellant_isp_s":                       isp,
                    "propellant_cost_usd_per_kg":             cost_per_kg,
                    "launch_usd_per_kg_to_leo":               leo_cost_per_kg,
                    "propellant_mass_per_kg_payload":         prop_per_payload,
                    "in_space_prop_usd_per_kg_payload":       in_space_cost,
                    "total_usd_per_kg_payload_to_segment_end":
                        leo_cost_per_kg + in_space_cost,
                })

    summary = pd.DataFrame(rows)
    say(f"     OK  {len(summary):,} (vehicle x segment x propellant) rows")
    return summary
