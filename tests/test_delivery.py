# -*- coding: utf-8 -*-
"""The delivery chains, pinned BIT-EXACT to the implementation they moved from.

WHY THE VALUES ARE HARDCODED.  `spacecost/delivery.py` was moved out of
economicspace's `modules/mineral_value.py` at its pipeline_version 1.9.0, and
that project argues its releases from bit-identity: every in-space commodity
price in its Stage 2 catalog is this arithmetic, and every Stage 4 result is
downstream of that.  A move that changed the last bit of one of these would be
a silent re-pricing of the whole model.

So these are not "reasonable values" or a regression net taken after the fact.
They were captured by running the ORIGINAL implementation before a line was
edited, at full `repr` precision, and they are what that code returned.  An
exact `==` is the right comparison and a tolerance would defeat the purpose.

⚠️  A FAILURE HERE IS NOT A ROUNDING QUESTION.  It means either the arithmetic
moved or a `DELTA_V_REFERENCE` row underneath it moved.  `delivery.py`'s own
`_CHAIN_DV_AT_MOVE` assertion fires at import for the second case, so if that
passed and this failed, look at the arithmetic.  Either way the answer is to
tell economicspace before releasing, not to update the constant here.
"""

import json
import math
import os
import platform

import pytest

import spacecost
from spacecost import delivery


# ─────────────────────────────────────────────────────────────────────────────
# 🚨  EXACT ON THE RECORDED PLATFORM, TOLERANT EVERYWHERE ELSE
# ─────────────────────────────────────────────────────────────────────────────
# The first version of this file asserted `==` on every platform and CI went
# red on the first push, on `lunar_surface` and nothing else: Linux returned
# 21209.958393766807 where Windows returns 21209.9583937668.  One ULP.
#
# That was not a defect in the module, it was the wrong CONTRACT.  This package
# already says so in its README and enforces it in `test_parity.py`: the six
# reference tables are byte identical on every platform BECAUSE they pass
# values through, and the composite summary is promised only "the same values
# to a few ULP" BECAUSE it runs through `exp()`, which is the platform libm and
# is not required by IEEE 754 to be correctly rounded.  Every number in this
# file is a mass ratio, so every number in this file is `exp()`.
#
# ⚠️  AND `lunar_surface` FAILING ALONE IS THE TELL.  It is the only chain with
# two burns at different dry-mass fractions, so it compounds the most rounding;
# the single-burn chains happened to land on the same float.  A cross-platform
# claim that holds for six of seven cases is a claim that has not been tested,
# not a claim that is true.
#
# So the split below, which is `test_parity.py`'s own pattern rather than a new
# one: **exact on the platform the reference was recorded on, and a tolerance
# tight enough to catch any real change everywhere else.**  The smallest change
# this module could plausibly suffer is a delta-v row moving or `TUG_ISP_S`
# being derived, and the latter is the SMALLEST at 2.96%; 1e-12 is nine orders
# of magnitude below that and eleven above the ULP noise.
_TOLERANCE = 1e-12


def _reference_platform():
    """The platform `reference/summary_meta.json` was recorded on."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "reference", "summary_meta.json"),
              encoding="utf-8") as fh:
        return json.load(fh)["reference_platform"]


def _on_reference_platform():
    ref = _reference_platform()
    return (platform.system() == ref["system"]
            and platform.machine() == ref["machine"])


def assert_reproduces(got, want, what):
    """`==` on the recorded platform, a tight relative tolerance elsewhere.

    Not a relaxation: on the platform the numbers were captured on this is the
    exact comparison it always was, and the tolerance only ever applies where
    an exact one would be asserting something `exp()` cannot deliver.
    """
    if _on_reference_platform():
        assert got == want, (
            "%s: %r != %r on the reference platform, where this file's "
            "figures were captured.  That is a real change, not rounding."
            % (what, got, want))
    elif want == 0.0:
        assert got == 0.0, "%s: %r is not zero" % (what, got)
    else:
        rel = abs(got - want) / abs(want)
        assert rel < _TOLERANCE, (
            "%s: %r vs %r is %.3g relative, past the %g this platform is "
            "allowed for an exp()-derived value.  A libm difference is ~1e-16; "
            "anything this large is the model." % (what, got, want, rel, _TOLERANCE))


# Captured from economicspace modules/mineral_value.py @ pipeline_version
# 1.9.0, before the move.  Full precision, not rounded.
DELIVERED_AT_MOVE = {
    "earth_surface": 0.0,
    "leo":           4253.0,
    "geo":           12526.338533584149,
    "cislunar":      10809.933771428967,
    "lunar_surface": 21209.9583937668,
    "mars_orbit":    13495.708351816706,
    "mars_surface":  45105.39127487685,
}

DOWNLEG_AT_MOVE = {
    "earth_surface": 0.0,
    "leo":           25409.947878851424,
    "geo":           34314.68047480949,
    "cislunar":      27316.958591940387,
    "lunar_surface": 44938.93868240678,
    "mars_orbit":    30150.150574294374,
    "mars_surface":  96394.30338160615,
}


@pytest.mark.parametrize("dest,expected", sorted(DELIVERED_AT_MOVE.items()))
def test_delivered_cost_reproduces_the_source(dest, expected):
    assert_reproduces(delivery.delivered_cost_usd_per_kg(dest), expected,
                      "delivered_cost_usd_per_kg(%r)" % dest)


@pytest.mark.parametrize("dest,expected", sorted(DOWNLEG_AT_MOVE.items()))
def test_downleg_cost_reproduces_the_source(dest, expected):
    assert_reproduces(delivery.downleg_cost_usd_per_kg(dest), expected,
                      "downleg_cost_usd_per_kg(%r)" % dest)


def test_the_launch_price_comes_off_the_vehicle_table():
    """Not a literal: the whole point of the move."""
    assert delivery.LEO_LAUNCH_USD_PER_KG == 4253.0
    row = [r for r in spacecost.LAUNCH_VEHICLES_REFERENCE
           if r["name"] == "Falcon 9 (reusable)"]
    assert row and float(row[0]["usd_per_kg_to_leo"]) == delivery.LEO_LAUNCH_USD_PER_KG


def test_the_downleg_cost_lines_come_off_the_operations_table():
    ops = {r["category"]: float(r["value"]) for r in spacecost.OPERATIONAL_COSTS_REFERENCE}
    assert delivery.DOWNLEG_CAPSULE_USD_PER_KG == ops["Return capsule recurring cost"]
    assert delivery.DOWNLEG_TPS_USD_PER_KG == ops["Heat shield / TPS for Earth return"]
    assert delivery.DOWNLEG_RECOVERY_USD == ops["Sample recovery operations"]


def test_every_chain_delta_v_is_a_row_of_the_delta_v_table():
    """The de-duplication, stated as a test rather than as a comment.

    Every burn in every chain must be a `DELTA_V_REFERENCE` value or the sum of
    two of them.  A literal creeping back into a chain fails here.
    """
    rows = {float(r["dv_m_per_s"]) for r in spacecost.DELTA_V_REFERENCE}
    sums = {a + b for a in rows for b in rows}
    for dest, legs in delivery.DELIVERY_CHAINS.items():
        for leg in (legs or []):
            if leg[0] != "burn":
                continue
            assert leg[1] in rows or leg[1] in sums, (
                "%s burns %s, which is neither a delta-v row nor the sum of "
                "two.  Chains derive from the table; do not type a value in."
                % (dest, leg[1]))


def test_none_and_empty_chain_are_not_the_same_thing():
    """The defect this distinction already caused once, as a test.

    `earth_surface` has NO chain and avoids no launch; `leo` has an EMPTY
    chain and avoids the whole LEO launch price.  A truthiness test reads them
    as equal and prices LEO at zero.
    """
    assert delivery.DELIVERY_CHAINS["earth_surface"] is None
    assert delivery.DELIVERY_CHAINS["leo"] == []
    assert delivery.delivered_cost_usd_per_kg("earth_surface") == 0.0
    assert delivery.delivered_cost_usd_per_kg("leo") == delivery.LEO_LAUNCH_USD_PER_KG
    assert delivery.delivery_mass_ratio("earth_surface") == 0.0
    assert delivery.delivery_mass_ratio("leo") == 1.0


def test_staging_beats_a_single_burn_to_the_lunar_surface():
    """The reason the chains are chains: 4.99 kg in LEO, not 10.96.

    A single stage burning the table's own composite "LEO -> lunar surface"
    5,920 m/s costs roughly twice the two-stage chain.  If this ever stops
    being true the leg-by-leg model has lost its argument.
    """
    staged = delivery.delivery_mass_ratio("lunar_surface")
    composite = [r for r in spacecost.DELTA_V_REFERENCE
                 if r["segment"].endswith("lunar surface")
                 and r["segment"].startswith("LEO")]
    assert composite, "the composite LEO -> lunar surface row has gone"
    single = delivery.stage_mass_ratio(
        float(composite[0]["dv_m_per_s"]),
        delivery.TUG_ISP_S, delivery.LANDER_DRY_MASS_FRAC)
    assert round(staged, 2) == 4.99
    assert round(single, 2) == 10.96
    assert single > 2.0 * staged * 0.99


def test_the_tank_can_fail_to_close():
    """`inf` is a feasibility statement, not an expensive answer."""
    assert delivery.stage_mass_ratio(0.0, 465.0, 0.10) == 1.0
    assert delivery.stage_mass_ratio(-50.0, 465.0, 0.10) == 1.0
    assert_reproduces(delivery.stage_mass_ratio(1836.0, 465.0, 0.10),
                      1.5829357820673113, "stage_mass_ratio(1836)")
    assert_reproduces(delivery.stage_mass_ratio(4050.0, 465.0, 0.10),
                      2.8899848922428553, "stage_mass_ratio(4050)")
    assert math.isinf(delivery.stage_mass_ratio(12000.0, 465.0, 0.20))
    assert math.isinf(delivery.stage_mass_ratio(20000.0, 465.0, 0.20))


@pytest.mark.parametrize("bad", ["", "   ", "nonsense", None, "Mars"])
def test_an_unknown_destination_is_free_rather_than_fatal(bad):
    """The consumer's long-standing behaviour: no chain, no launch avoided."""
    assert delivery.delivered_cost_usd_per_kg(bad) == 0.0
    assert delivery.downleg_cost_usd_per_kg(bad) == 0.0


@pytest.mark.parametrize("dest", sorted(DELIVERED_AT_MOVE))
def test_case_and_whitespace_are_tolerated(dest):
    assert (delivery.delivered_cost_usd_per_kg("  %s  " % dest.upper())
            == delivery.delivered_cost_usd_per_kg(dest))
    assert (delivery.downleg_cost_usd_per_kg("  %s  " % dest.upper())
            == delivery.downleg_cost_usd_per_kg(dest))


def test_the_launch_price_argument_still_scales_linearly():
    """`leo_usd_per_kg` is public, so it is part of the contract."""
    for dest in DELIVERED_AT_MOVE:
        assert delivery.delivered_cost_usd_per_kg(dest, 0.0) == 0.0
        at_one = delivery.delivered_cost_usd_per_kg(dest, 1.0)
        assert at_one == delivery.delivery_mass_ratio(dest)


def test_adding_this_module_did_not_move_the_data_contract():
    """A derivation over the tables is not a table.

    If this fails somebody made `delivery` a seventh CSV.  That is allowed, but
    it restamps every output and obliges economicspace to re-run a stage that
    re-fetches live prices, so it is a deliberate release rather than a tidy-up.
    """
    assert spacecost.DATA_VERSION == "1.15.0"


# ─────────────────────────────────────────────────────────────────────────────
# THE REGISTER: every number in this module that is TYPED rather than derived
# ─────────────────────────────────────────────────────────────────────────────
# The module's claim is that it derives its values from the reference tables.
# A claim like that decays one literal at a time, and no test of the OUTPUTS
# can see it happen: a hardcoded 3,600 and a looked-up 3,600 produce identical
# numbers and identical hashes, right up until the row moves and only one of
# them follows.
#
# So this reads the SOURCE.  Every numeric literal in delivery.py must either
# be algebra (0 and 1, the identities the rocket equation is written with) or
# carry a row here saying why it cannot come from a table.
#
# ⚠️  BOTH HALVES ARE FINDINGS.  A literal with no row is a value that stopped
# being derived; a row with no literal is a permission still being granted for
# a number somebody has since removed.  That is the same rule this package's
# consumer applies to its own `TYPED_OK` and `BORROWED` registers, and the
# reason is the same: an allowlist nobody prunes quietly stops being a
# decision and becomes a way past the check.

TYPED = {
    465.0:    "TUG_ISP_S, an upper-stage figure; the table's row is 452 s",
    452.0:    "_ISP_AT_MOVE, the table value that discrepancy is asserted against",
    0.1:      "TUG_DRY_MASS_FRAC and DOWNLEG_CAPSULE_DRY_FRAC; no structural-fraction table",
    0.2:      "LANDER_DRY_MASS_FRAC, Apollo LM descent stage",
    0.3:      "MARS_LANDED_MASS_FRACTION, MSL 27.6% / Perseverance 29.8%",
    0.15:     "DOWNLEG_TPS_FRAC, mirrors economicspace's heat_shield_frac_of_payload",
    10000.0:  "DOWNLEG_BATCH_KG, the batch the recovery campaign is spread over",
    120.0:    "_LEO_DEORBIT_DV_M_S; a LEO deorbit burn has no row",
    850.0:    "_LLO_TEI_DV_M_S; TEI out of low lunar orbit has no row",
    1490.0:   "_GEO_DEORBIT_DV_M_S, a hand figure predating the 1,488 row",
    1488.0:   "_GEO_DEORBIT_ROW_AT_MOVE, the row that is asserted against",
    # The two *_AT_MOVE registers restate every derived delta-v on purpose:
    # they are what turns "a row moved" from a silent re-pricing into an
    # import error.  They are typed BECAUSE deriving them would defeat them.
    2455.0: "_CHAIN_DV_AT_MOVE", 1836.0: "_CHAIN_DV_AT_MOVE",
    3600.0: "_CHAIN_DV_AT_MOVE", 4050.0: "_CHAIN_DV_AT_MOVE",
    1870.0: "_CHAIN_DV_AT_MOVE", 800.0: "_CHAIN_DV_AT_MOVE",
    900.0:  "_CHAIN_DV_AT_MOVE / _DOWNLEG_DV_AT_MOVE",
    450.0:  "_DOWNLEG_DV_AT_MOVE", 2720.0: "_DOWNLEG_DV_AT_MOVE",
    6200.0: "_DOWNLEG_DV_AT_MOVE",
}

ALGEBRA = {0, 1, 0.0, 1.0}


def _literals():
    """Every numeric literal in delivery.py, as {value: [line, ...]}."""
    import ast
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "spacecost", "delivery.py")
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    found = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant)
                and isinstance(node.value, (int, float))
                and not isinstance(node.value, bool)):
            found.setdefault(float(node.value), []).append(node.lineno)
    return found


def test_no_number_is_typed_without_a_reason():
    """A literal with no register row is a value that stopped being derived."""
    undeclared = {v: ls for v, ls in _literals().items()
                  if v not in ALGEBRA and v not in TYPED}
    assert not undeclared, (
        "delivery.py types these and the register does not explain them: "
        + "; ".join("%s at line(s) %s" % (v, ls)
                    for v, ls in sorted(undeclared.items()))
        + ".  Derive it from a reference table, or add a row to TYPED saying "
          "which table cannot supply it.")


def test_the_register_has_nothing_stale_in_it():
    """A row with no literal is a permission granted for a number that has gone."""
    present = set(_literals())
    stale = sorted(v for v in TYPED if v not in present)
    assert not stale, (
        "TYPED still allows %s, and delivery.py no longer contains them.  "
        "Drop the row: an allowlist nobody prunes stops being a decision."
        % (stale,))
