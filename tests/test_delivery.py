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

import math

import pytest

import spacecost
from spacecost import delivery


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
def test_delivered_cost_is_bit_exact_with_the_source(dest, expected):
    assert delivery.delivered_cost_usd_per_kg(dest) == expected


@pytest.mark.parametrize("dest,expected", sorted(DOWNLEG_AT_MOVE.items()))
def test_downleg_cost_is_bit_exact_with_the_source(dest, expected):
    assert delivery.downleg_cost_usd_per_kg(dest) == expected


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
    assert delivery.stage_mass_ratio(1836.0, 465.0, 0.10) == 1.5829357820673113
    assert delivery.stage_mass_ratio(4050.0, 465.0, 0.10) == 2.8899848922428553
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
