# -*- coding: utf-8 -*-
"""Sanity bands over the loaded tables.

Extracted from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).  The BANDS are
that extraction verbatim.  What v1.15.0 added is a way to hear them.

⚠️  UNTIL v1.15.0 THIS FUNCTION COULD NOT FAIL AND USUALLY COULD NOT BE HEARD.
Every finding went to `say()`, `say()` is silent unless somebody called
`set_verbose(True)`, and `build_catalog` calls this on every build.  So the
default path — a library import, a quiet CLI build, a consumer's pipeline
stage — ran every check here and discarded the result.  A check whose output is
dropped is not a guardrail; it is a comment that costs CPU.

Three things changed, and none of them moved a band:

  * every finding is also RETURNED, as a list of dicts, so a caller can act on
    what it says without parsing stdout,
  * `strict=True` raises `ValidationError` on a WARN, which is what makes this
    usable as a CI gate (`spacecost validate --strict`),
  * findings carry a LEVEL.  `WARN` means a row looks wrong.  `NOTE` means a
    row is unusual and the reader should know — the g-load line has always been
    a NOTE in all but name, and strict mode must not fail on it, or nobody will
    turn strict mode on.

The printed output keeps its shape deliberately: it is what a verbose build has
looked like since 1.9.0, and there is no reason for a log to move.
"""

import datetime
from typing import List, Optional

import numpy as np
import pandas as pd

from ._log import say


class ValidationError(AssertionError):
    """Raised by `validate(..., strict=True)` when any WARN-level finding fires.

    An `AssertionError` subclass so that a caller who wraps a build in a bare
    `except AssertionError` — which is what a notebook harness tends to do —
    keeps catching it.
    """

    def __init__(self, findings: List[dict]):
        self.findings = findings
        super().__init__(
            "%d validation warning(s): %s"
            % (len(findings), "; ".join(x["message"] for x in findings)))


# How far behind the current year a `reference_year` may fall before the table
# says so.  NOTE-level and never fatal: a 2026 launch price read in 2030 is
# stale, not wrong, and the whole reason every row carries the year is that
# staleness should be VISIBLE rather than assumed away.  Failing a build on the
# calendar would make the passage of time a release blocker, which is the wrong
# trade for a reference dataset.
_STALE_AFTER_YEARS = 3


def _detail(df: pd.DataFrame, label_col: str, value_col: str, fmt: str = "{}"):
    """`name: value` lines for a finding's detail block."""
    return ["%s: %s" % (r[label_col], fmt.format(r[value_col]))
            for _, r in df.iterrows()]


class _Findings(object):
    """Collects findings, and prints them in the shape a verbose build had."""

    def __init__(self):
        self.items: List[dict] = []

    def add(self, level, table, check, message, detail=None):
        detail = detail or []
        self.items.append({"level": level, "table": table, "check": check,
                           "message": message, "detail": detail})
        say("     %-5s %s" % (level, message))
        for line in detail:
            say("          " + line)

    def warn(self, *a, **kw):
        self.add("WARN", *a, **kw)

    def note(self, *a, **kw):
        self.add("NOTE", *a, **kw)


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def validate(
    launch_df:       pd.DataFrame,
    propellant_df:   pd.DataFrame,
    delta_v_df:      pd.DataFrame,
    ops_df:          pd.DataFrame,
    environments_df: Optional[pd.DataFrame] = None,
    storage_df:      Optional[pd.DataFrame] = None,
    *,
    config=None,
    strict:          bool = False,
) -> List[dict]:
    """Check the loaded tables against their sanity bands.

    Returns the findings in the order they fired, each a dict with `level`
    (`"WARN"` or `"NOTE"`), `table`, `check`, `message` and `detail`.

    `strict=True` raises `ValidationError` if any finding is a WARN.  It
    defaults False because `build_catalog` calls this, and a build that died on
    a band would make every speculative row in the table a release blocker.
    Keyword-only, so that a frame can be appended to the positional list later
    without turning somebody's `True` into a DataFrame argument.

    The last two frames are optional so that the four-frame call economicspace
    makes keeps working unchanged; pass them and their bands run too.
    """
    say("\n  Validating catalog ...")
    f = _Findings()

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
        f.warn("launch_vehicles", "leo_price_band",
               "%d flying launch rows outside $100-$100 000 / kg-to-LEO "
               "sanity band:" % len(bad_launch),
               _detail(bad_launch, "name", "usd_per_kg_to_leo", "{:,.0f}"))

    concepts = launch_df[launch_df["status"] == "concept"]
    bad_concept = concepts[
        (concepts["usd_per_kg_to_leo"] < 1)
        | (concepts["usd_per_kg_to_leo"] > 100_000)
    ]
    if not bad_concept.empty:
        f.warn("launch_vehicles", "concept_price_band",
               "%d concept launch rows outside $1-$100 000 / kg-to-LEO:"
               % len(bad_concept),
               _detail(bad_concept, "name", "usd_per_kg_to_leo", "{:,.0f}"))

    # ── Payload g-load  (v1.9.0) ─────────────────────────────────────────────
    # Not a sanity check on the data, a capability check on the fleet.  Above
    # ~50 g a launcher can carry consumables and not machinery, which changes
    # what it is FOR rather than how much it costs.
    rough = launch_df[launch_df["max_accel_g"] > 50]
    if not rough.empty:
        f.note("launch_vehicles", "payload_g_load",
               "%d launchers exceed 50 g and can lift bulk material only, not "
               "mining hardware:" % len(rough),
               _detail(rough, "name", "max_accel_g", "{:,.0f} g"))

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
    # Python bools, so that case cannot arise here, but do not copy this line
    # onto a frame that came off disk.
    #
    # Resolved once and read twice: the expression was written out at both
    # sanity bands, which is one more place for the two to drift apart.
    has_mass_ratio = propellant_df["propellantless"].ne(True)

    finite_isp = propellant_df[has_mass_ratio]
    bad_isp = finite_isp[
        (finite_isp["isp_vac_s"] < 40) | (finite_isp["isp_vac_s"] > 200_000)
    ]
    if not bad_isp.empty:
        f.warn("propellants", "isp_band",
               "%d propellant rows with implausible Isp:" % len(bad_isp),
               _detail(bad_isp, "name", "isp_vac_s", "{} s"))

    # ── Propellant $/kg sanity band ──────────────────────────────────────────
    # Also widened: iodine at $60/kg and antimatter at $1e15/kg are both real
    # entries.  The band now only catches a missing or negative price.
    priced = propellant_df[has_mass_ratio]
    bad_prop_cost = priced[
        (priced["cost_usd_per_kg"] <= 0)
        | (~np.isfinite(pd.to_numeric(priced["cost_usd_per_kg"], errors="coerce")))
    ]
    if not bad_prop_cost.empty:
        f.warn("propellants", "price_present",
               "%d propellant rows with a missing or non-positive price:"
               % len(bad_prop_cost),
               _detail(bad_prop_cost, "name", "cost_usd_per_kg"))

    # ── Tankage sanity  (v1.9.0) ─────────────────────────────────────────────
    # tank_kg_per_L / density is the fraction of its own mass a propellant pays
    # in tankage.  Above ~1.0 the tank outweighs its contents, which is real for
    # nothing in this table and would signal a density or storage-class error.
    tank_frac = (pd.to_numeric(propellant_df["tank_kg_per_L"], errors="coerce")
                 / pd.to_numeric(propellant_df["density_kg_per_L"], errors="coerce"))
    bad_tank = propellant_df[tank_frac > 1.0]
    if not bad_tank.empty:
        f.warn("propellants", "tank_outweighs_propellant",
               "%d propellant rows whose tank outweighs the propellant:"
               % len(bad_tank),
               ["%s: %.2f kg tank / kg propellant" % (r["name"], tank_frac[i])
                for i, r in bad_tank.iterrows()])

    # ── Maturity gate is populated ───────────────────────────────────────────
    _VALID_STATUS = {"operational", "development", "concept", "retired"}
    bad_status = propellant_df[~propellant_df["status"].isin(_VALID_STATUS)]
    if not bad_status.empty:
        f.warn("propellants", "status_vocabulary",
               "%d propellant rows with an unrecognised status (Module 4 gates "
               "on this):" % len(bad_status),
               ["%s: %r" % (r["name"], r["status"])
                for _, r in bad_status.iterrows()])

    # ── Δv sanity band ───────────────────────────────────────────────────────
    bad_dv = delta_v_df[
        (delta_v_df["dv_m_per_s"] < 50) | (delta_v_df["dv_m_per_s"] > 20_000)
    ]
    if not bad_dv.empty:
        f.warn("delta_v_segments", "dv_band",
               "%d dv rows outside 50-20 000 m/s sanity band:" % len(bad_dv),
               _detail(bad_dv, "segment", "dv_m_per_s", "{} m/s"))

    # ── A quoted price is its own price and payload  (v1.15.0) ───────────────
    # `usd_per_kg_to_leo` is `list_price_usd / payload_leo_kg`, and the table
    # carries all three.  Three copies of two measurements, in other words, and
    # the arithmetic between them is the only thing keeping the third honest.
    # Since v1.16.0 `vehicles.py` DERIVES the $/kg at import rather than
    # letting a row type it, so the committed table cannot fail this.  It stays
    # for the frame a caller edits after loading -- raise a price in a notebook
    # and forget the $/kg beside it, twelve columns apart on one very long row,
    # and this is what says so.
    #
    # 1% rather than exact: every stated $/kg in the table is rounded to whole
    # dollars, and on Electron at $23,438/kg a single dollar is 0.004%.
    price = pd.to_numeric(launch_df["list_price_usd"], errors="coerce")
    payload = pd.to_numeric(launch_df["payload_leo_kg"], errors="coerce")
    quoted = pd.to_numeric(launch_df["usd_per_kg_to_leo"], errors="coerce")
    implied = price / payload.where(payload > 0)
    off_by = (quoted - implied).abs() / implied.abs()
    inconsistent = launch_df[off_by > 0.01]
    if not inconsistent.empty:
        f.warn("launch_vehicles", "price_matches_payload",
               "%d launch rows quote a $/kg that is not their own price over "
               "their own payload:" % len(inconsistent),
               ["%s: quoted %.0f, price/payload gives %.0f"
                % (r["name"], quoted[i], implied[i])
                for i, r in inconsistent.iterrows()])

    # ── A launch headline sits inside its own band  (v1.16.0) ────────────────
    # The same rule `value_within_range` applies to the two tables below, for
    # the launch table's price and payload bands.  `vehicles.py` raises on
    # this at import, so again it is the caller's edited frame being checked.
    for mid in ("list_price_usd", "payload_leo_kg", "payload_gto_kg",
                "payload_escape_kg"):
        if mid + "_low" not in launch_df.columns:
            continue
        v = pd.to_numeric(launch_df[mid], errors="coerce")
        lo = pd.to_numeric(launch_df[mid + "_low"], errors="coerce")
        hi = pd.to_numeric(launch_df[mid + "_high"], errors="coerce")
        outside = launch_df[v.notna() & ((v < lo) | (v > hi))]
        if not outside.empty:
            f.warn("launch_vehicles", "value_within_range",
                   "%d launch rows hold a %s outside their own band:"
                   % (len(outside), mid),
                   ["%s: %s not in [%s, %s]" % (r["name"], v[i], lo[i], hi[i])
                    for i, r in outside.iterrows()])

    # ── A value sits inside its own stated range  (v1.15.0) ──────────────────
    # `operational_costs` and `storage_systems` both carry `value`,
    # `range_low` and `range_high`, and nothing has ever checked that the first
    # is between the other two.  A point estimate outside its own uncertainty
    # band is not a wide estimate, it is a typo or a stale edit: somebody
    # revised the anchor and left the bracket, or swapped low and high.  Both
    # tables are clean today, which is exactly when to write the check down.
    for label, df, key in (("operational_costs", ops_df,     "category"),
                           ("storage_systems",   storage_df, "name")):
        if df is None or df.empty or "range_low" not in df.columns:
            continue
        v = pd.to_numeric(df["value"], errors="coerce")
        lo = pd.to_numeric(df["range_low"], errors="coerce")
        hi = pd.to_numeric(df["range_high"], errors="coerce")
        bracketed = lo.notna() & hi.notna()

        inverted = df[bracketed & (lo > hi)]
        if not inverted.empty:
            f.warn(label, "range_is_ordered",
                   "%d %s rows have range_low above range_high:"
                   % (len(inverted), label),
                   ["%s: [%s, %s]" % (r[key], lo[i], hi[i])
                    for i, r in inverted.iterrows()])

        outside = df[bracketed & ((v < lo) | (v > hi))]
        if not outside.empty:
            f.warn(label, "value_within_range",
                   "%d %s rows hold a value outside their own stated range:"
                   % (len(outside), label),
                   ["%s: %s not in [%s, %s]" % (r[key], v[i], lo[i], hi[i])
                    for i, r in outside.iterrows()])

    # ── Keys are unique  (v1.15.0) ───────────────────────────────────────────
    # `mission_cost_breakdown` does `.set_index("name").loc[propellant]`, and a
    # duplicated name turns that lookup from a Series into a DataFrame.  The
    # arithmetic downstream then broadcasts instead of raising, so a mission
    # cost comes back as a frame of numbers rather than a number, and which of
    # the two rows was meant is unknowable.  Cheap to check, silent to hit.
    for label, df, key in (("launch_vehicles",   launch_df,     "name"),
                           ("propellants",       propellant_df, "name"),
                           ("delta_v_segments",  delta_v_df,    "segment"),
                           ("operational_costs", ops_df,        "category")):
        dupes = df[key][df[key].duplicated(keep=False)].unique().tolist()
        if dupes:
            f.warn(label, "unique_key",
                   "%d duplicated %s value(s) in %s: a keyed lookup returns a "
                   "frame rather than a row" % (len(dupes), key, label),
                   [str(d) for d in dupes])

    # ── Environment bands  (v1.15.0) ─────────────────────────────────────────
    if environments_df is not None and not environments_df.empty:
        from .environments import solar_flux_w_per_m2

        env = environments_df
        bad_au = env[(env["au_mean"] <= 0) | (env["au_mean"] > 60)]
        if not bad_au.empty:
            f.warn("environments", "heliocentric_distance_band",
                   "%d environment rows outside 0-60 AU:" % len(bad_au),
                   _detail(bad_au, "name", "au_mean"))

        # The flux column is DERIVED from au_mean, so a mismatch means a row
        # was edited past the derivation rather than through it — which is the
        # one way this table can hold a number that no longer means what its
        # column name says.
        want = env["au_mean"].map(solar_flux_w_per_m2)
        got = pd.to_numeric(env["solar_flux_w_per_m2"], errors="coerce")
        off = env[(got - want).abs() > 1e-9 * want.abs()]
        if not off.empty:
            f.warn("environments", "flux_matches_distance",
                   "%d environment rows whose solar flux does not match their "
                   "heliocentric distance:" % len(off),
                   _detail(off, "name", "solar_flux_w_per_m2", "{:,.1f} W/m2"))

        bad_ecl = env[(env["eclipse_fraction"] < 0)
                      | (env["eclipse_fraction"] > 1)]
        if not bad_ecl.empty:
            f.warn("environments", "eclipse_fraction_band",
                   "%d environment rows with an eclipse fraction outside 0-1:"
                   % len(bad_ecl),
                   _detail(bad_ecl, "name", "eclipse_fraction"))

    # ── The dial agrees with the table  (v1.15.0) ────────────────────────────
    # `contingency_fraction` is a dial on one mission's arithmetic and
    # "Contingency reserve" is a cited reference row, and they are two
    # statements of one number.  Until v1.15.0 the row was literally
    # `CONFIG.contingency_fraction * 100`, read at import from a mutable
    # singleton, so a build with a custom config charged one figure in
    # `mission_cost_breakdown` and wrote the OTHER into the CSV beside it.
    # Decoupling them was the fix; this is what stops them drifting apart
    # unnoticed now that they can.
    #
    # NOTE, not WARN: a caller is entitled to run a first-of-kind mission at
    # 45% while the table states the 20% industry standard.  They are just not
    # entitled to be surprised by it later.
    if config is not None and "category" in ops_df.columns:
        stated = ops_df.loc[ops_df["category"] == "Contingency reserve", "value"]
        if not stated.empty:
            table_pct = float(stated.iloc[0])
            config_pct = float(config.contingency_fraction) * 100.0
            if abs(table_pct - config_pct) > 1e-9:
                f.note("operational_costs", "contingency_matches_config",
                       "the build charges %.1f%% contingency and the table "
                       "states %.1f%%: the CSV will not describe the run that "
                       "produced it" % (config_pct, table_pct))

    # ── Staleness  (v1.15.0) ─────────────────────────────────────────────────
    # NOTE, never WARN.  See _STALE_AFTER_YEARS for why the calendar is not
    # allowed to fail a build.
    this_year = datetime.date.today().year
    for label, df in (("launch_vehicles",   launch_df),
                      ("propellants",       propellant_df),
                      ("operational_costs", ops_df)):
        if "reference_year" not in df.columns:
            continue
        years = pd.to_numeric(df["reference_year"], errors="coerce")
        stale = df[years < this_year - _STALE_AFTER_YEARS]
        if not stale.empty:
            f.note(label, "reference_year_staleness",
                   "%d %s rows carry a reference_year more than %d years old "
                   "(oldest %d, now %d)"
                   % (len(stale), label, _STALE_AFTER_YEARS,
                      int(years.min()), this_year))

    say("     OK  Unit invariants: launch USD/kg | propellant USD/kg + USD/L | "
        "dv m/s | ops USD per unit")

    warnings = [x for x in f.items if x["level"] == "WARN"]
    if strict and warnings:
        raise ValidationError(warnings)
    return f.items


# `validate` is a name Module 2 of economicspace also defines, and that repo's
# single-file build resolves the collision with a whole-word regex over the
# source text.  A consumer writing `from spacecost import validate as _v` gets
# that import rewritten and then an ImportError -- which happened, and was
# caught by a docs check rather than by anything looking at Stage 3.
#
# So the function has a second, collision-proof name.  Prefer it in any code
# that might be concatenated, vendored, or rewritten by a build step.
validate_tables = validate
