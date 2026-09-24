# -*- coding: utf-8 -*-
"""Structural guardrails: the checks that catch a QUIET wrong row.

`test_invariants.py` asks whether a value is plausible. This file asks whether
a row is even shaped like the other rows, and whether the constants two modules
share still agree. Every check here exists because the failure it catches
produces no error and no warning -- it produces a column of NaN, a lookup that
returns the wrong object, or a live price that silently never applies.

The pattern is the one validate.py names at the `propellantless` band: the
wrong behaviour is the quiet one. A table of dicts has no schema, so a key
typed `isp_vac_S` on one row of forty-one does not raise; it adds a column that
is NaN everywhere else, and every band that reads the real column skips the row
it was most needed on.
"""

import math

import numpy as np

import pytest

import spacecost

# (module attribute, the column that is its unique key)
TABLES = [
    ("LAUNCH_VEHICLES_REFERENCE",   "name"),
    ("PROPELLANTS_REFERENCE",       "name"),
    ("DELTA_V_REFERENCE",           "segment"),
    ("OPERATIONAL_COSTS_REFERENCE", "category"),
    ("STORAGE_REFERENCE",           "name"),
    ("ENVIRONMENTS_REFERENCE",      "name"),
]


# ------------------------------------------------------------------ shape
@pytest.mark.parametrize("table,key", TABLES)
def test_every_row_has_the_same_keys(table, key):
    """One typo'd key name adds a column of NaN and removes a row from a band.

    `pd.DataFrame(list_of_dicts)` takes the UNION of the keys, so a row that
    spells a column differently gets NaN in the real column and a new column
    nobody reads. Nothing raises. The row then falls out of every check that
    filters on the real column -- and the row most likely to carry a typo is
    the row somebody just added, which is the one least likely to be right.
    """
    rows = getattr(spacecost, table)
    keysets = {frozenset(r) for r in rows}
    if len(keysets) > 1:
        common = frozenset.intersection(*keysets)
        odd = {r[key]: sorted(set(r) - common) for r in rows
               if set(r) - common}
        raise AssertionError(
            "%s rows do not agree on their keys; these rows carry keys the "
            "others do not: %s" % (table, odd))


@pytest.mark.parametrize("table,key", TABLES)
def test_the_key_column_is_unique(table, key):
    """A duplicated key turns `.set_index(key).loc[value]` into a FRAME.

    `mission_cost_breakdown` does exactly that lookup for the vehicle and the
    propellant. With two rows of one name the arithmetic that follows
    broadcasts instead of raising, so the mission cost comes back as a frame of
    numbers rather than a number -- and which of the two rows was meant is
    unknowable from the output.
    """
    rows = getattr(spacecost, table)
    seen, dupes = set(), []
    for r in rows:
        if r[key] in seen:
            dupes.append(r[key])
        seen.add(r[key])
    assert not dupes, "%s has duplicate %s values: %s" % (table, key, dupes)


@pytest.mark.parametrize("table,key", TABLES)
def test_no_key_is_blank_or_padded(table, key):
    """A key with a trailing space looks identical in a printed table.

    It is not identical to `.loc`, and the failure reads as a missing row.
    """
    for r in getattr(spacecost, table):
        value = r[key]
        assert isinstance(value, str) and value.strip(), \
            "%s has a row with an empty %s" % (table, key)
        assert value == value.strip(), \
            "%s: %r has leading or trailing whitespace" % (table, value)


# ------------------------------------------------- closed vocabularies
def test_environment_kind_values_are_closed():
    """`kind` is a filter column, so a typo silently empties a filtered search.

    Same rule `status` gets on the launch and propellant tables.
    """
    allowed = {"earth_orbit", "libration_point", "cislunar", "moon_surface",
               "planet_orbit", "planet_surface", "neo", "main_belt", "trojan"}
    got = {e["kind"] for e in spacecost.ENVIRONMENTS_REFERENCE}
    assert got <= allowed, "unknown environment kind: " + str(got - allowed)


def test_propellant_storage_classes_all_resolve():
    """Every `storage_class` in the table has a tankage multiplier.

    `_tank_kg_per_L` raises on an unknown class, which is the right behaviour,
    but the rows store `tank_kg_per_L` as a VALUE -- so a row could declare a
    class that nothing can resolve and never call the function that objects.
    This calls it for every row.
    """
    from spacecost.propellants import _tank_kg_per_L
    for p in spacecost.PROPELLANTS_REFERENCE:
        _tank_kg_per_L(p["storage_class"])


def test_tankage_is_positive_except_where_there_is_no_tank():
    """Only a propellantless row may carry zero tankage."""
    for p in spacecost.PROPELLANTS_REFERENCE:
        tank = p["tank_kg_per_L"]
        if p["propellantless"]:
            assert tank == 0, p["name"] + " is propellantless with a tank"
        else:
            assert tank > 0, p["name"] + " has non-positive tankage"


# ------------------------------------------- constants two modules share
def test_live_price_blends_name_real_propellants():
    """`_LIVE_BLENDS` is keyed by exact row name, and a stale key is silent.

    prices.py weights a live commodity quote by the mixture ratio so that a
    kerosene price moves only the kerosene half of kerolox. It looks the row up
    by name. Rename the row and the lookup misses, the `else` branch takes the
    quote as the price of the WHOLE mixture, and a `--live` build prices
    kerolox as if it were pure RP-1 -- roughly three times its real cost, with
    nothing in the output saying anything happened.
    """
    from spacecost.prices import _LIVE_BLENDS, _LIVE_OXIDISER
    from spacecost.propellants import _COMPONENTS, _OF_RATIOS
    names = {p["name"] for p in spacecost.PROPELLANTS_REFERENCE}
    for row_name, blend in _LIVE_BLENDS.items():
        assert row_name in names, \
            "_LIVE_BLENDS names %r, which is not a propellant row" % row_name
        assert blend in _OF_RATIOS, \
            "_LIVE_BLENDS maps to %r, which has no mixture ratio" % blend
        assert _LIVE_OXIDISER[blend] in _COMPONENTS, \
            "%s has no oxidiser component" % blend


def test_yfinance_proxies_are_fetchable_keys():
    """A `yfinance_proxy` no fetcher produces is a row that never goes live.

    The merge skips a proxy key that is not in the fetched dict, so a typo here
    means `--live` quietly resolves that row to its reference price. The only
    visible symptom is `price_basis` reading "reference" on a row the caller
    asked to be live, which is exactly what an offline build looks like.
    """
    from spacecost.prices import _YFINANCE_TICKERS
    from spacecost.units import COMMODITY_DENSITY_KG_PER_L
    fetchable = {fluid for _, _, fluid in _YFINANCE_TICKERS.values()}
    for p in spacecost.PROPELLANTS_REFERENCE:
        proxy = p.get("yfinance_proxy")
        if not proxy:
            continue
        assert proxy in fetchable, \
            "%s proxies %r, which no ticker produces" % (p["name"], proxy)
        assert proxy in COMMODITY_DENSITY_KG_PER_L, \
            "%s proxies %r, which has no density" % (p["name"], proxy)


def test_thruster_entries_name_real_propellants():
    """A `_THRUSTER_SYSTEMS` key that matches no row is a dead entry.

    The reverse direction already raises at load time: an electric row with no
    entry is a `KeyError`, deliberately, because that is the failure that flew
    a micronewton thruster as a cargo tug. This is the other direction, which
    is silent -- a renamed row leaves its device data stranded under the old
    name, and the row itself then raises at load. Catching it here says WHICH
    name went stale.
    """
    from spacecost.propellants import _THRUSTER_SYSTEMS
    names = {p["name"] for p in spacecost.PROPELLANTS_REFERENCE}
    stale = sorted(k for k in _THRUSTER_SYSTEMS if k not in names)
    assert not stale, "_THRUSTER_SYSTEMS entries name no propellant: %s" % stale


# ------------------------------------------------------- the environments
def test_environment_derived_columns_agree_with_their_inputs():
    """Every derived column recomputes from the row's own asserted values.

    The point of deriving them in `_env` is that a row cannot disagree with
    itself. This is the test that somebody has not since written a literal into
    one of these columns, which would re-open exactly that gap.
    """
    from spacecost.environments import (blackbody_temp_k,
                                        one_way_light_time_min,
                                        solar_array_mass_factor,
                                        solar_flux_w_per_m2)
    from spacecost.units import NEWTON_G_M3_PER_KG_S2
    for e in spacecost.ENVIRONMENTS_REFERENCE:
        au = e["au_mean"]
        assert e["solar_flux_w_per_m2"] == solar_flux_w_per_m2(au), e["name"]
        assert e["solar_array_mass_factor"] == solar_array_mass_factor(au), e["name"]
        assert e["blackbody_temp_k"] == blackbody_temp_k(au), e["name"]
        assert e["one_way_light_time_min"] == one_way_light_time_min(
            e["max_earth_range_au"]), e["name"]
        if e["mass_kg"] is not None:
            gm = NEWTON_G_M3_PER_KG_S2 * e["mass_kg"]
            r = e["mean_radius_m"]
            assert e["surface_gravity_m_per_s2"] == gm / (r * r), e["name"]
            assert e["escape_velocity_m_per_s"] == math.sqrt(2.0 * gm / r), e["name"]
        else:
            assert e["surface_gravity_m_per_s2"] is None, e["name"]
            assert e["escape_velocity_m_per_s"] is None, e["name"]


def test_environment_distances_are_ordered():
    """Perihelion <= semi-major axis <= aphelion, on every row."""
    for e in spacecost.ENVIRONMENTS_REFERENCE:
        assert e["au_min"] <= e["au_mean"] <= e["au_max"], e["name"]
        assert e["au_min"] > 0, e["name"]


def test_heliocentric_rows_state_the_conjunction_range():
    """`max_earth_range_au` follows a stated convention; hold it to it.

    On a heliocentric row it is the body's aphelion plus Earth's, the two on
    opposite sides of the Sun. Earth-bound rows state an orbital radius
    instead, and are exempt by `kind` rather than by being small enough not to
    notice.
    """
    from spacecost.environments import _EARTH_APHELION_AU
    earthbound = {"earth_orbit", "cislunar", "moon_surface", "libration_point"}
    for e in spacecost.ENVIRONMENTS_REFERENCE:
        if e["kind"] in earthbound:
            continue
        want = e["au_max"] + _EARTH_APHELION_AU
        assert abs(e["max_earth_range_au"] - want) < 0.01, (
            "%s states a conjunction range of %.4f AU, convention gives %.4f"
            % (e["name"], e["max_earth_range_au"], want))


def test_environment_derivations_avoid_transcendentals():
    """The byte-portability contract, as a test of the source rather than prose.

    environments.csv is promised byte-identical on every platform, and that
    promise rests on the derivations using only multiplication, division and
    `sqrt` -- the operations IEEE 754 requires to be correctly rounded.
    `exp`, `pow` and `**` are not, which is precisely why the SUMMARY is
    promised values and not bytes. A `**0.5` added here would move this table
    from the strong contract to the weak one, and the CSV would still look
    fine on the machine it was written on.
    """
    import ast
    import os
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "spacecost", "environments.py"),
        encoding="utf-8").read()
    banned_calls = {"exp", "pow", "log", "sin", "cos", "cbrt", "hypot"}
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            raise AssertionError(
                "environments.py uses ** at line %d; `pow` is not required to "
                "be correctly rounded and the byte contract rests on that"
                % node.lineno)
        if isinstance(node, ast.Call):
            fn = node.func
            name = (fn.attr if isinstance(fn, ast.Attribute)
                    else getattr(fn, "id", ""))
            assert name not in banned_calls, (
                "environments.py calls %s() at line %d; see the byte contract "
                "in its docstring" % (name, node.lineno))


# ------------------------------------- columns that restate other columns
# CITATIONS.md states the rule these three enforce: "two copies of one
# measurement is a defect waiting to happen: one of them gets updated." Where
# this dataset keeps two copies anyway -- because a reader wants the answer in
# both forms -- the arithmetic between them is the only thing holding the
# second honest, and nothing was checking it.


def test_launch_price_per_kg_is_its_own_price_over_its_own_payload():
    """`usd_per_kg_to_leo` restates `list_price_usd / payload_leo_kg`.

    All three sit on one very long row, twelve columns apart, which is what
    makes raising a price and forgetting the $/kg beside it the single most
    likely way this table goes wrong.

    1% rather than exact: every stated $/kg is rounded to whole dollars.
    """
    bad = []
    for v in spacecost.LAUNCH_VEHICLES_REFERENCE:
        payload = v["payload_leo_kg"]
        if not payload:
            continue
        implied = v["list_price_usd"] / payload
        quoted = v["usd_per_kg_to_leo"]
        if abs(quoted - implied) > 0.01 * implied:
            bad.append("%s: quoted %.0f, implied %.0f"
                       % (v["name"], quoted, implied))
    assert not bad, "; ".join(bad)


def test_exhaust_velocity_restates_isp():
    """`exhaust_vel_m_per_s` is `isp_vac_s * g0`, and both are columns.

    ⚠️  The mass driver is stated the other way round: its primary figure is
    the 3,000 m/s muzzle velocity, and its Isp is that divided by g0 and
    rounded to a whole second. So the tolerance is a rounding rather than a
    float epsilon, and it must stay loose enough to hold a row that was
    measured in the other unit.
    """
    from spacecost.units import G0_M_S2
    bad = []
    for p in spacecost.PROPELLANTS_REFERENCE:
        isp = p["isp_vac_s"]
        if not math.isfinite(isp):
            assert not math.isfinite(p["exhaust_vel_m_per_s"]), \
                p["name"] + " has infinite Isp and a finite exhaust velocity"
            continue
        want = isp * G0_M_S2
        if abs(p["exhaust_vel_m_per_s"] - want) > 1e-3 * want:
            bad.append("%s: %s m/s against Isp %s (%.1f m/s)"
                       % (p["name"], p["exhaust_vel_m_per_s"], isp, want))
    assert not bad, "; ".join(bad)


def test_cost_per_litre_restates_cost_per_kg_and_density():
    """`ref_cost_usd_per_L` is `ref_cost_usd_per_kg * density_kg_per_L`.

    Exact here, not a tolerance: unlike the two above, this column is computed
    in the source rather than typed, so any drift at all means somebody has
    replaced the expression with a literal.

    ⚠️  Propellantless rows are exempt and are checked the other way instead. A
    sail has no density because it has no propellant, so `density_kg_per_L` is
    NaN there and the product is NaN rather than the 0.0 the row correctly
    carries. That is the row being right, not the row disagreeing with itself,
    and asserting the multiplication on it would be asserting arithmetic about
    a thing that does not exist.
    """
    for p in spacecost.PROPELLANTS_REFERENCE:
        if p["propellantless"]:
            assert math.isnan(p["density_kg_per_L"]), \
                p["name"] + " is propellantless with a density"
            assert p["ref_cost_usd_per_kg"] == 0.0, p["name"]
            assert p["ref_cost_usd_per_L"] == 0.0, p["name"]
            continue
        want = p["ref_cost_usd_per_kg"] * p["density_kg_per_L"]
        assert p["ref_cost_usd_per_L"] == want, p["name"]


@pytest.mark.parametrize("table,key", [
    ("OPERATIONAL_COSTS_REFERENCE", "category"),
    ("STORAGE_REFERENCE", "name"),
])
def test_a_value_sits_inside_its_own_range(table, key):
    """A point estimate outside its own uncertainty band is a typo, not width.

    Both tables carry `value`, `range_low` and `range_high`, and until v1.15.0
    nothing checked the three against each other. The failure it catches is
    revising the anchor and leaving the bracket, or swapping low for high --
    and a swapped bracket still prints as a perfectly ordinary row.
    """
    bad = []
    for r in getattr(spacecost, table):
        v, lo, hi = r["value"], r["range_low"], r["range_high"]
        if lo is None or hi is None:
            continue
        if lo > hi:
            bad.append("%s: range [%s, %s] is inverted" % (r[key], lo, hi))
        elif not lo <= v <= hi:
            bad.append("%s: %s not in [%s, %s]" % (r[key], v, lo, hi))
    assert not bad, "; ".join(bad)


def test_the_reference_tables_do_not_read_the_config_singleton():
    """A reference row must be a constant, not a view of a mutable dial.

    "Contingency reserve" was `CONFIG.contingency_fraction * 100`, evaluated at
    import against a module-level dataclass instance. Two consequences, neither
    of which raised: a build with `SpacecostConfig(contingency_fraction=0.45)`
    charged 45% in `mission_cost_breakdown` and wrote 20.0 into the CSV beside
    it, so the catalog reported a contingency the build had not used; and
    assigning to `spacecost.CONFIG` after import moved the dial without moving
    the table.

    Checked at the SOURCE rather than by value, because the value is 20.0
    either way -- which is precisely why nothing noticed.
    """
    import ast
    import os

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    offenders = []
    for module in ("vehicles.py", "propellants.py", "deltav.py",
                   "operations.py", "storage.py", "environments.py"):
        src = open(os.path.join(here, "spacecost", module),
                   encoding="utf-8").read()
        for node in ast.walk(ast.parse(src)):
            if (isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "CONFIG"):
                offenders.append("%s:%d reads CONFIG.%s"
                                 % (module, node.lineno, node.attr))
    assert not offenders, (
        "a reference table is reading the config singleton: "
        + "; ".join(offenders)
        + ".  A row is a cited constant; a config field is a dial on one "
          "mission's arithmetic.  They may agree at the default, and they are "
          "not the same thing.")


def test_a_custom_contingency_does_not_silently_disagree_with_the_table():
    """The guard that replaced the coupling: validate says when they differ."""
    import pandas as pd

    from spacecost.prices import merge_propellant_prices

    def findings(fraction):
        return spacecost.validate_tables(
            spacecost.load_launch_vehicles(),
            merge_propellant_prices(spacecost.load_propellants(),
                                    pd.DataFrame()),
            spacecost.load_delta_v(),
            spacecost.load_operational_costs(),
            config=spacecost.SpacecostConfig(contingency_fraction=fraction),
        )

    checks = {f["check"] for f in findings(0.45)}
    assert "contingency_matches_config" in checks

    checks = {f["check"] for f in findings(0.20)}
    assert "contingency_matches_config" not in checks, \
        "the default must not warn about itself"

    # And it is a NOTE: a first-of-kind mission at 45% is legitimate, so this
    # must not fail a gate.
    note = [f for f in findings(0.45)
            if f["check"] == "contingency_matches_config"][0]
    assert note["level"] == "NOTE"


def test_the_blend_helper_and_the_live_path_agree_on_a_mixture():
    """`_blend` and `fuel_mass_fraction` both compute 1/(1+O/F).

    Two implementations of one formula over one shared `_OF_RATIOS` table. The
    data cannot drift, but an inline ratio passed to `_blend` could, so this
    holds the two answers together for every blend that has both.
    """
    from spacecost.propellants import (_kerolox, _methalox, _hydrolox,
                                       fuel_mass_fraction)
    for blend, built in (("kerolox", _kerolox), ("methalox", _methalox),
                         ("hydrolox", _hydrolox)):
        assert fuel_mass_fraction(blend) == built["fuel_mass_fraction"], blend
        assert built["fuel_mass_fraction"] + built["ox_mass_fraction"] == \
            pytest.approx(1.0), blend


def test_no_undeclared_figure_is_restated_in_both_tables():
    """A figure in BOTH `operational_costs` and `storage_systems` must say so.

    The two tables overlap by design: `storage_systems` is the taxonomy and the
    citations, `operational_costs` is what economicspace's Stage 4 actually
    reads, and `load_storage` tells you to add a figure to both. Three figures
    were obeying that instruction by being typed twice -- RTG specific power,
    the eclipse fraction, the volatile containment mass -- each a literal value
    AND a literal range in two files, agreeing only because nobody had edited
    one yet. They are now mirrored through `_mirrors_ops`.

    This is the half that is not tautological. It catches the FOURTH one: a row
    copy-pasted between the files in a future edit, which would restore exactly
    the drift the mirroring removed.

    Matching on value AND both range bounds, because a bare value collision is
    ordinary -- several unrelated rows happen to be 5, or 0.5, or 100 -- while
    three numbers agreeing is a copy.
    """
    from spacecost.storage import (_ECLIPSE_FRAC, _RTG_W_PER_KG,
                                   _VOLATILE_HOLDUP)
    declared = {_ECLIPSE_FRAC, _RTG_W_PER_KG, _VOLATILE_HOLDUP}

    undeclared = []
    for o in spacecost.OPERATIONAL_COSTS_REFERENCE:
        triple = (o["value"], o["range_low"], o["range_high"])
        if None in triple or triple in declared:
            continue
        for st in spacecost.STORAGE_REFERENCE:
            if (st["value"], st["range_low"], st["range_high"]) == triple:
                undeclared.append(
                    "%r and %r both state %s in [%s, %s]"
                    % (o["category"], st["name"], triple[0], triple[1],
                       triple[2]))
    assert not undeclared, (
        "these figures are restated in both tables without being mirrored: "
        + "; ".join(undeclared)
        + ".  Read one from the other through storage.py's `_mirrors_ops`, or "
          "say here why the collision is a coincidence.")


# ------------------------------------------------ the launch table's bands
# v1.16.0.  The launch table carries a low / high band beside every price and
# payload, and derives every $/kg from them.  These hold the contract the
# README states: the headline is the geometric CENTRE of its band, and nothing
# that can be derived is typed.


def test_launch_vocabularies_are_closed():
    """Filter columns, so a typo silently empties a filtered search."""
    from spacecost.vehicles import _LAUNCH_VOCAB
    for key, allowed in _LAUNCH_VOCAB.items():
        got = {v[key] for v in spacecost.LAUNCH_VEHICLES_REFERENCE}
        assert got <= allowed, "unknown %s: %s" % (key, got - allowed)


def test_the_launch_headline_is_the_centre_of_its_band():
    """The stated rule, asserted: geometric centre, 3 significant figures.

    A wide range lands in the middle rather than at whichever end was to hand.
    If a row ever needs its headline somewhere else in its band, that is a
    decision to write down here, not an edit to make quietly.
    """
    from spacecost.vehicles import band_centre
    bad = []
    for v in spacecost.LAUNCH_VEHICLES_REFERENCE:
        for mid in ("list_price_usd", "payload_leo_kg", "payload_gto_kg",
                    "payload_escape_kg"):
            want = band_centre(v[mid + "_low"], v[mid + "_high"])
            got = v[mid]
            if not (got == want or (math.isnan(got) and math.isnan(want))):
                bad.append("%s: %s is %s, band centre is %s"
                           % (v["name"], mid, got, want))
    assert not bad, "; ".join(bad)


def test_band_centre_is_geometric_rounded_and_clamped():
    from spacecost.vehicles import band_centre
    assert band_centre(450_000_000, 2_100_000_000) == 972_000_000
    assert band_centre(17_400, 17_400) == 17_400
    # 18,832 rounds to 18,800, which is outside [18,814, 18,850]: clamped.
    assert band_centre(18_814, 18_850) == 18_814
    assert math.isnan(band_centre(np.nan, np.nan))
    # Narrow bands barely move; wide ones move a lot.  That is the point.
    assert band_centre(100, 110) == 105
    assert band_centre(100, 10_000) == 1_000


def test_every_launch_band_is_ordered():
    for v in spacecost.LAUNCH_VEHICLES_REFERENCE:
        for mid in ("list_price_usd", "payload_leo_kg", "payload_gto_kg",
                    "payload_escape_kg"):
            lo, m, hi = v[mid + "_low"], v[mid], v[mid + "_high"]
            if math.isfinite(m):
                assert lo <= m <= hi, "%s: %s band" % (v["name"], mid)
            else:
                assert not math.isfinite(lo) and not math.isfinite(hi),                     "%s: %s is unpublished but its band is not" % (v["name"], mid)


def test_launch_price_per_kg_bands_are_derived_from_the_ends():
    """Low $/kg is low price over HIGH payload, and the reverse.

    Swapping the pairing is the natural typo, and it produces a band that looks
    plausible and is too narrow.
    """
    for v in spacecost.LAUNCH_VEHICLES_REFERENCE:
        for dest in ("leo", "gto", "escape"):
            col = "usd_per_kg_to_" + dest
            pay = "payload_%s_kg" % dest
            if not (math.isfinite(v[pay]) and v[pay] > 0):
                for suffix in ("", "_low", "_high"):
                    assert math.isnan(v[col + suffix]),                         "%s: %s priced where it does not go" % (v["name"], col)
                continue
            assert v[col + "_low"] == round(v["list_price_usd_low"]
                                            / v[pay + "_high"]), v["name"]
            assert v[col + "_high"] == round(v["list_price_usd_high"]
                                             / v[pay + "_low"]), v["name"]
            assert v[col + "_low"] <= v[col] <= v[col + "_high"], v["name"]


def _launch_row(**over):
    row = {"name": "Test rocket", "operator": "x", "country": "x",
           "status": "operational", "availability": "open",
           "core_propellant": "kerolox", "first_flight_year": 2020,
           "payload_leo_kg": 1_000, "payload_gto_kg": 0,
           "payload_escape_kg": 0, "fairing_volume_m3": 1.0,
           "list_price_usd": 10_000_000, "price_basis": "published",
           "reference_year": 2026, "notes": "x"}
    row.update(over)
    return row


@pytest.mark.parametrize("over,message", [
    ({"usd_per_kg_to_leo": 10_000}, "derived"),
    ({"list_price_usd_high": 12_000_000}, "AND a band"),
    ({"payload_leo_kg_low": 900}, "AND a band"),
    ({"availability": "for sale"}, "availability"),
    ({"core_propellant": "RP-1"}, "core_propellant"),
    ({"payload_leo_kg_hi": 1_200}, "unknown keys"),
])
def test_a_bad_launch_row_raises_at_import(over, message):
    """The failures that would otherwise be quiet: a typed $/kg that drifts
    from its price, a band that excludes its own headline, a vocabulary typo,
    and a band key spelled wrong -- which would otherwise just never apply."""
    from spacecost.vehicles import _apply_launch_defaults
    with pytest.raises(ValueError, match=message):
        _apply_launch_defaults([_launch_row(**over)])


def test_a_launch_band_must_be_whole_and_ordered():
    from spacecost.vehicles import _apply_launch_defaults
    row = _launch_row()
    del row["list_price_usd"]
    row["list_price_usd_low"] = 12_000_000
    with pytest.raises(ValueError, match="nor both"):
        _apply_launch_defaults([dict(row)])
    row["list_price_usd_high"] = 10_000_000
    with pytest.raises(ValueError, match="is above"):
        _apply_launch_defaults([dict(row)])
    row["list_price_usd_high"] = 14_000_000
    _apply_launch_defaults([row])
    assert row["list_price_usd"] == 13_000_000      # sqrt(12 x 14) = 12.96


def test_a_launch_row_must_state_where_it_can_be_bought():
    from spacecost.vehicles import _apply_launch_defaults
    row = _launch_row()
    del row["availability"]
    with pytest.raises(ValueError, match="does not state"):
        _apply_launch_defaults([row])


def test_first_flight_year_is_an_integer_or_blank_in_the_csv():
    """Plain pandas writes a year beside a None as "2010.0"."""
    df = spacecost.load_launch_vehicles()
    assert str(df["first_flight_year"].dtype) == "Int64"
    text = df[["name", "first_flight_year"]].to_csv(index=False)
    assert ".0" not in text


# --------------------------------------------------------- validation gate
def test_the_shipped_tables_produce_no_warnings():
    """The tables pass their own sanity bands. Asserted, not assumed.

    Until v1.15.0 `validate` printed through `say()`, which is silent by
    default, so "the shipped tables are clean" was true by inspection and by
    nothing else. A band that fires on a committed row would have been visible
    only to somebody who ran a verbose build and read the log.

    NOTEs are allowed and expected -- three launchers really do exceed 50 g.
    """
    import pandas as pd

    from spacecost.prices import merge_propellant_prices
    findings = spacecost.validate_tables(
        spacecost.load_launch_vehicles(),
        merge_propellant_prices(spacecost.load_propellants(), pd.DataFrame()),
        spacecost.load_delta_v(),
        spacecost.load_operational_costs(),
        spacecost.load_environments(),
        spacecost.load_storage(),
    )
    warnings = [f for f in findings if f["level"] == "WARN"]
    assert not warnings, "the committed tables trip their own bands: " + "; ".join(
        f["table"] + "/" + f["check"] + ": " + f["message"] for f in warnings)


def test_strict_mode_raises_on_a_warning():
    """The gate itself. A band that cannot fail is not a gate.

    Feeds `validate` a deliberately broken frame and asserts that `strict=True`
    turns the finding into an exception -- because the whole value of the
    strict flag is to CI, and CI needs the process to exit non-zero.
    """
    import pandas as pd

    from spacecost.prices import merge_propellant_prices
    from spacecost.validate import ValidationError

    launch = spacecost.load_launch_vehicles().copy()
    # Cast first: the column is int64 and assigning a float into it emits a
    # pandas FutureWarning, which would make this test the thing that fails on
    # a future pandas rather than the thing that catches a bad row.
    launch["usd_per_kg_to_leo"] = launch["usd_per_kg_to_leo"].astype(float)
    launch.loc[launch.index[0], "usd_per_kg_to_leo"] = 0.01   # below any band
    frames = (launch,
              merge_propellant_prices(spacecost.load_propellants(),
                                      pd.DataFrame()),
              spacecost.load_delta_v(),
              spacecost.load_operational_costs())

    findings = spacecost.validate_tables(*frames)            # non-strict: quiet
    assert any(f["check"] == "leo_price_band" for f in findings)

    with pytest.raises(ValidationError) as caught:
        spacecost.validate_tables(*frames, strict=True)
    assert caught.value.findings, "the exception carries the findings"


def test_notes_alone_never_fail_strict_mode():
    """A NOTE must not fail a gate, or nobody will switch the gate on.

    The g-load line fires on the committed tables every time. If that failed
    `--strict`, the only way to keep CI green would be to stop running it.
    """
    import pandas as pd

    from spacecost.prices import merge_propellant_prices
    findings = spacecost.validate_tables(
        spacecost.load_launch_vehicles(),
        merge_propellant_prices(spacecost.load_propellants(), pd.DataFrame()),
        spacecost.load_delta_v(),
        spacecost.load_operational_costs(),
        spacecost.load_environments(),
        spacecost.load_storage(),
        strict=True,
    )
    assert any(f["level"] == "NOTE" for f in findings), \
        "no NOTE fired, so this test is no longer proving anything"
