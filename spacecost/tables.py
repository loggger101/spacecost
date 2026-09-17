# -*- coding: utf-8 -*-
"""Reference-table loaders, and the (vehicle x segment x propellant) summary.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

import pandas as pd

from ._log import say
from .config import CONFIG, SpacecostConfig as TransportConfig
from .deltav import DELTA_V_REFERENCE
from .environments import ENVIRONMENTS_REFERENCE
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

    ⚠️  ADD IT BY MIRRORING, NOT BY TYPING IT TWICE. Three figures obeyed the
    instruction above by existing as a literal value AND a literal range in
    both files, agreeing only because nobody had edited one of them yet. Since
    v1.15.0 the copy in storage.py reads the ops row through `_mirrors_ops`,
    and `tests/test_schema.py` fails on a fourth undeclared duplicate.
    """
    say("\n   Loading storage-systems reference ...")
    df = pd.DataFrame(STORAGE_REFERENCE)
    say(f"     OK  {len(df)} storage systems")
    return df

def load_environments() -> pd.DataFrame:
    """`ENVIRONMENTS_REFERENCE` as a frame: where a kilogram is being priced.

    The one table here that is not inherited from economicspace Module 3, and
    the one that carries no money.  It exists because three rows of
    `operational_costs` -- power-system specific mass, energy storage, and the
    autonomy NRE -- are functions of heliocentric distance, and nothing in this
    dataset knew the distance.  See environments.py for the derivations.
    """
    say("\n  Loading environments reference ...")
    df = pd.DataFrame(ENVIRONMENTS_REFERENCE)
    say(f"     OK  {len(df)} destination environments")
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

    # ⚠️  The two inner frames are unpacked ONCE, not re-walked per vehicle.
    # `iterrows()` rebuilds a Series per row per call, and nested three deep
    # that was 36 x 32 rebuilds of all 41 propellant rows -- 47,232 Series
    # constructed to do 39,852 multiplications, which is where roughly 90% of a
    # build's wall time went.
    #
    # ⚠️  WHAT IS DELIBERATELY *NOT* DONE HERE IS VECTORISING THE ARITHMETIC.
    # (This module imports no numpy at all, which is the shortest way to say
    # so: the only array library in reach is the one behind the scalar call
    # below, and nothing here should reach for it directly.)
    # It would be one numpy call and it would be faster still, and it would
    # also change the output bytes: `propellant_mass_for_dv` reaches `np.exp`,
    # and numpy dispatches a SIMD kernel for an array that is not the scalar
    # path, so the two disagree in the last bit or two. The committed summary
    # hash is a scalar-path hash. The cost is real and the hash is the point,
    # so the loop stays a loop and only the row access is hoisted. Same
    # operations, same order, same bytes -- verified against the pre-change
    # build before this was committed.
    segments = [(str(r["segment"]), float(r["dv_m_per_s"]), r["duration_yr"])
                for _, r in in_space.iterrows()]
    propellants = [(r["name"], float(r["cost_usd_per_kg"]), float(r["isp_vac_s"]))
                   for _, r in propellant_df.iterrows()]

    rows = []
    for _, lv in launch_df.iterrows():
        # Use the LEO price as the baseline cost to "lift" the payload to
        # the start of every in-space segment.  Module 4 can switch this
        # to escape-class numbers for deep-space-direct injections.
        leo_cost_per_kg = lv["usd_per_kg_to_leo"]
        vehicle_name    = lv["name"]
        vehicle_status  = lv["status"]

        for segment_name, dv, duration_yr in segments:
            for prop_name, cost_per_kg, isp in propellants:
                prop_per_payload = float(propellant_mass_for_dv(1.0, dv, isp))
                in_space_cost    = prop_per_payload * cost_per_kg

                rows.append({
                    "vehicle":                                vehicle_name,
                    "vehicle_status":                         vehicle_status,
                    "segment":                                segment_name,
                    "segment_dv_m_per_s":                     dv,
                    "segment_duration_yr":                    duration_yr,
                    "propellant":                             prop_name,
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
