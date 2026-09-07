# -*- coding: utf-8 -*-
"""Sanity bands over the loaded tables. Prints warnings; never raises.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

import numpy as np
import pandas as pd

from ._log import say


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def validate(
    launch_df:      pd.DataFrame,
    propellant_df:  pd.DataFrame,
    delta_v_df:     pd.DataFrame,
    ops_df:         pd.DataFrame,
) -> None:
    """Print sanity warnings.  Never raises."""
    say("\n  Validating catalog ...")

    # ── Launch $/kg sanity band ──────────────────────────────────────────────
    # The band applies to things that FLY.  v1.9.0 added non-rocket concepts
    # quoting $10-100/kg, which would trip a $100 floor built around Starship, 
    # and tripping it would be meaningless, because those figures are
    # infrastructure amortisations rather than launch prices.  Concepts are
    # checked against a wider band of their own; only the flying fleet is held
    # to $100-$100,000.
    flying = launch_df[launch_df["status"].isin(["operational", "development",
                                                 "retired"])]
    bad_launch = flying[
        (flying["usd_per_kg_to_leo"] < 100)
        | (flying["usd_per_kg_to_leo"] > 100_000)
    ]
    if not bad_launch.empty:
        say(f"     WARN  {len(bad_launch)} flying launch rows outside "
              f"$100-$100 000 / kg-to-LEO sanity band:")
        for _, r in bad_launch.iterrows():
            say(f"          {r['name']}: {r['usd_per_kg_to_leo']:,.0f}")

    concepts = launch_df[launch_df["status"] == "concept"]
    bad_concept = concepts[
        (concepts["usd_per_kg_to_leo"] < 1)
        | (concepts["usd_per_kg_to_leo"] > 100_000)
    ]
    if not bad_concept.empty:
        say(f"     WARN  {len(bad_concept)} concept launch rows outside "
              f"$1-$100 000 / kg-to-LEO:")
        for _, r in bad_concept.iterrows():
            say(f"          {r['name']}: {r['usd_per_kg_to_leo']:,.0f}")

    # ── Payload g-load  (v1.9.0) ─────────────────────────────────────────────
    # Not a sanity check on the data, a capability check on the fleet.  Above
    # ~50 g a launcher can carry consumables and not machinery, which changes
    # what it is FOR rather than how much it costs.
    rough = launch_df[launch_df["max_accel_g"] > 50]
    if not rough.empty:
        say(f"     NOTE   {len(rough)} launchers exceed 50 g and can lift bulk "
              f"material only, not mining hardware:")
        for _, r in rough.iterrows():
            say(f"          {r['name']}: {r['max_accel_g']:,.0f} g")

    # ── Propellant Isp sanity band ───────────────────────────────────────────
    # v1.9.0 widened this from 150-5,000 s, which was the range of the seven
    # propellants the table used to hold.  The floor is now cold gas (70 s) and
    # the ceiling nuclear pulse (10,000 s); anything outside 40-200,000 s is a
    # typo rather than a technology.  Propellantless rows carry Isp = inf by
    # construction and are excluded, not warned about.
    #
    # ⚠️  v1.12.1: `.ne(True)` rather than `~(...).astype(bool)`.  Every row of
    # PROPELLANTS_REFERENCE states `propellantless` today, so pandas infers
    # dtype `bool` and the old expression was correct, but add ONE row that
    # omits the key and the column comes back `object` with a NaN in it, and
    # `.astype(bool)` reads NaN as **True**.  A propellant that forgot to say it
    # has a mass ratio would be silently classed as a sail and dropped from both
    # sanity bands below, so the two checks would quietly stop covering the row
    # most likely to be new and wrong.  That is the trap CLAUDE.md names under
    # "Correctness invariants that were expensive to find"; the wrong behaviour
    # is the quiet one.
    #
    # `.ne(True)` says the intended thing directly ("not flagged propellantless")
    # and is total: it returns dtype `bool` from a `bool` column and from an
    # `object` column alike, so a missing value reads as "has a mass ratio",
    # which is true of every real propellant.
    #
    # ⚠️  NOT `.fillna(False).astype(bool)`, which was tried first and is worse
    # in the one case this exists for: on an object column pandas raises
    # `FutureWarning: Downcasting object dtype arrays on .fillna is deprecated`,
    # so the fix would emit a deprecation warning exactly when it fires, and
    # change behaviour again on a future pandas.
    #
    # ⚠️  A CSV-loaded frame would still need `_truthy`-style parsing, because
    # the STRING "True" is not `True`.  This frame is built in-module from
    # Python bools and `validate()` has no other caller, so that case cannot
    # arise here, but do not copy this line onto a frame that came off disk.
    #
    # Resolved once and read twice: the expression was written out at both
    # sanity bands, which is one more place for the two to drift apart.
    has_mass_ratio = propellant_df["propellantless"].ne(True)

    finite_isp = propellant_df[has_mass_ratio]
    bad_isp = finite_isp[
        (finite_isp["isp_vac_s"] < 40) | (finite_isp["isp_vac_s"] > 200_000)
    ]
    if not bad_isp.empty:
        say(f"     WARN  {len(bad_isp)} propellant rows with implausible Isp:")
        for _, r in bad_isp.iterrows():
            say(f"          {r['name']}: {r['isp_vac_s']} s")

    # ── Propellant $/kg sanity band ──────────────────────────────────────────
    # Also widened: iodine at $60/kg and antimatter at $1e15/kg are both real
    # entries.  The band now only catches a missing or negative price.
    priced = propellant_df[has_mass_ratio]
    bad_prop_cost = priced[
        (priced["cost_usd_per_kg"] <= 0)
        | (~np.isfinite(pd.to_numeric(priced["cost_usd_per_kg"], errors="coerce")))
    ]
    if not bad_prop_cost.empty:
        say(f"     WARN  {len(bad_prop_cost)} propellant rows with a missing or "
              f"non-positive price:")
        for _, r in bad_prop_cost.iterrows():
            say(f"          {r['name']}: {r['cost_usd_per_kg']}")

    # ── Tankage sanity  (v1.9.0) ─────────────────────────────────────────────
    # tank_kg_per_L / density is the fraction of its own mass a propellant pays
    # in tankage.  Above ~1.0 the tank outweighs its contents, which is real for
    # nothing in this table and would signal a density or storage-class error.
    tank_frac = (pd.to_numeric(propellant_df["tank_kg_per_L"], errors="coerce")
                 / pd.to_numeric(propellant_df["density_kg_per_L"], errors="coerce"))
    bad_tank = propellant_df[tank_frac > 1.0]
    if not bad_tank.empty:
        say(f"     WARN  {len(bad_tank)} propellant rows whose tank outweighs "
              f"the propellant:")
        for i, r in bad_tank.iterrows():
            say(f"          {r['name']}: {tank_frac[i]:.2f} kg tank / kg propellant")

    # ── Maturity gate is populated ───────────────────────────────────────────
    _VALID_STATUS = {"operational", "development", "concept", "retired"}
    bad_status = propellant_df[~propellant_df["status"].isin(_VALID_STATUS)]
    if not bad_status.empty:
        say(f"     WARN  {len(bad_status)} propellant rows with an unrecognised "
              f"status (Module 4 gates on this):")
        for _, r in bad_status.iterrows():
            say(f"          {r['name']}: {r['status']!r}")

    # ── Δv sanity band ───────────────────────────────────────────────────────
    bad_dv = delta_v_df[
        (delta_v_df["dv_m_per_s"] < 50) | (delta_v_df["dv_m_per_s"] > 20_000)
    ]
    if not bad_dv.empty:
        say(f"     WARN  {len(bad_dv)} dv rows outside 50-20 000 m/s sanity band:")
        for _, r in bad_dv.iterrows():
            say(f"          {r['segment']}: {r['dv_m_per_s']} m/s")

    say(f"     OK  Unit invariants: launch USD/kg | propellant USD/kg + USD/L | "
          f"dv m/s | ops USD per unit")
