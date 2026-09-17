# -*- coding: utf-8 -*-
"""The query helpers answer with the table's own caveats applied.

Every test here pins a rule that the rocket equation, read literally, gets
wrong. The propellant table carries a column for each of them -- `propellantless`
and `dv_penalty_factor` -- and until v1.15.0 these helpers read neither, so the
CLI's headline answer to "what is the cheapest way to move a kilogram through
6,500 m/s" was three sails at $0.00.

⚠️  THE ASYMMETRY WITH `build_transportation_summary` IS DELIBERATE AND TESTED
BOTH WAYS.  The summary is a raw cross-join that economicspace's Stage 4 reads
and applies the penalty to itself; applying it there as well would charge it
twice. These helpers have no Stage 4 behind them. So the summary must stay raw
and these must not, and a change that "makes them consistent" in either
direction is a bug.
"""

import numpy as np
import pandas as pd
import pytest

import spacecost
from spacecost.prices import merge_propellant_prices


@pytest.fixture(scope="module")
def catalog():
    """The offline catalog the CLI builds, shared across this file."""
    return {
        "launch_vehicles": spacecost.load_launch_vehicles(),
        "propellants": merge_propellant_prices(spacecost.load_propellants(),
                                               pd.DataFrame()),
        "operational_costs": spacecost.load_operational_costs(),
    }


# ------------------------------------------------- cheapest_propellant_for
def test_sails_do_not_win_by_carrying_no_propellant(catalog):
    """A mass ratio of 1 is not a price of zero.

    A propellantless row has infinite Isp by construction, so the rocket
    equation returns exactly $0.00 for any Δv and the three sail and tether
    rows swept the top three places of every ranking. Their characteristic
    acceleration is ~0.1 mm/s²; "free" is the one thing they are not.
    """
    ranked = spacecost.cheapest_propellant_for(catalog, 6_500)
    assert (ranked["usd_per_kg_payload_for_dv"] > 0).all(), \
        "something still ranks at zero cost"

    names = set(ranked["name"])
    propellantless = {p["name"] for p in spacecost.PROPELLANTS_REFERENCE
                      if p["propellantless"]}
    assert propellantless, "no propellantless rows; this test proves nothing"
    assert not (names & propellantless), "a sail is still in the ranking"


def test_sails_come_back_when_asked_for(catalog):
    """Excluded by default, not deleted. The rows are real and are documented."""
    ranked = spacecost.cheapest_propellant_for(
        catalog, 6_500, include_propellantless=True)
    zero = ranked[ranked["usd_per_kg_payload_for_dv"] == 0]
    assert len(zero) == 3, "the three propellantless rows should be back"


def test_the_low_thrust_penalty_is_applied_and_shown(catalog):
    """1.5x on electric rows, 1.0x on chemical, and the factor is returned.

    Applying it out of sight would be its own quiet defect: the caller asked
    about 6,500 m/s and an electric row is being costed at 9,750.
    """
    ranked = spacecost.cheapest_propellant_for(catalog, 6_500).set_index("name")
    assert ranked.loc["VASIMR  (argon, variable Isp)",
                      "dv_penalty_factor"] == 1.5
    assert ranked.loc["VASIMR  (argon, variable Isp)",
                      "effective_dv_m_per_s"] == 9_750.0
    assert ranked.loc["methalox  (LCH4 / LOX)", "dv_penalty_factor"] == 1.0
    assert ranked.loc["methalox  (LCH4 / LOX)",
                      "effective_dv_m_per_s"] == 6_500.0


def test_the_penalty_changes_the_answer_not_just_the_numbers(catalog):
    """If it reordered nothing it would not be worth the behaviour change.

    It moves 17 of 38 rows at 6,500 m/s and costs VASIMR first place at the
    main-belt 10,500 -- which is the figure the docstring quotes, so it is
    asserted rather than left as prose.
    """
    for dv, want_moved in ((6_500, 10), (10_500, 20)):
        raw = spacecost.cheapest_propellant_for(
            catalog, dv, apply_dv_penalty=False)["name"].tolist()
        adj = spacecost.cheapest_propellant_for(
            catalog, dv)["name"].tolist()
        moved = sum(1 for n in raw if raw.index(n) != adj.index(n))
        assert moved >= want_moved, (
            "the penalty moved only %d rows at %d m/s" % (moved, dv))

    belt = spacecost.cheapest_propellant_for(catalog, 10_500)["name"].tolist()
    raw_belt = spacecost.cheapest_propellant_for(
        catalog, 10_500, apply_dv_penalty=False)["name"].tolist()
    assert raw_belt[0] == "VASIMR  (argon, variable Isp)"
    assert belt[0] != "VASIMR  (argon, variable Isp)", \
        "the penalty should cost VASIMR first place at the main belt"


def test_ranking_is_sorted_and_finite(catalog):
    costs = spacecost.cheapest_propellant_for(
        catalog, 6_500)["usd_per_kg_payload_for_dv"]
    assert costs.is_monotonic_increasing
    assert np.isfinite(costs).all()


# ------------------------------------------------------- cheapest_launch_to
def test_only_vehicles_that_reach_the_destination_are_ranked(catalog):
    """Electron, Vega C and Alpha carry nothing past LEO.

    Their `payload_gto_kg` is 0, so the old `payload >= min_payload_kg` filter
    admitted them at the default 0, and their NaN price sorted them last rather
    than out.
    """
    gto = spacecost.cheapest_launch_to(catalog, "gto")
    assert (gto["payload_gto_kg"] > 0).all()
    assert np.isfinite(gto["usd_per_kg_to_gto"]).all()
    assert "Electron" not in set(gto["name"])
    # And LEO, where they DO belong, still has them.
    leo = spacecost.cheapest_launch_to(catalog, "leo")
    assert "Electron" in set(leo["name"])


def test_launch_ranking_is_sorted(catalog):
    for dest in ("leo", "gto", "escape"):
        col = "usd_per_kg_to_" + dest
        assert spacecost.cheapest_launch_to(
            catalog, dest)[col].is_monotonic_increasing, dest


# --------------------------------------------------- mission_cost_breakdown
def _mission(catalog, propellant, **kw):
    kwargs = dict(payload_kg=1_000.0, delta_v_outbound=6_500.0,
                  delta_v_return=5_500.0,
                  launch_vehicle="Falcon Heavy (reusable side cores)",
                  propellant=propellant, mission_duration_yr=3.0,
                  hardware_kg=2_000.0)
    kwargs.update(kw)
    return spacecost.mission_cost_breakdown(catalog, **kwargs)


def test_a_chemical_mission_is_untouched_by_the_penalty(catalog):
    """Every default this function ships with is chemical, and 1.0x is 1.0x.

    So the v1.15.0 change must move NO number for the worked example, and this
    is what says so.
    """
    with_penalty = _mission(catalog, "methalox  (LCH4 / LOX)")
    without = _mission(catalog, "methalox  (LCH4 / LOX)",
                       apply_dv_penalty=False)
    assert with_penalty == without
    assert with_penalty["dv_penalty_factor"] == 1.0
    assert with_penalty["effective_dv_outbound"] == 6_500.0


def test_an_electric_mission_pays_the_penalty(catalog):
    """And it costs more propellant, which is the point."""
    with_penalty = _mission(catalog, "Xenon  (Hall / ion)")
    without = _mission(catalog, "Xenon  (Hall / ion)",
                       apply_dv_penalty=False)
    assert with_penalty["dv_penalty_factor"] == 1.5
    assert with_penalty["effective_dv_outbound"] == 9_750.0
    assert with_penalty["outbound_prop_kg"] > without["outbound_prop_kg"]
    assert with_penalty["total_usd"] > without["total_usd"]


def test_the_return_propellant_rides_out_as_dead_mass(catalog):
    """The bug-fix this function was written around, still fixed.

    Outbound must push payload + hardware + RETURN propellant. Omitting the
    last understates launch mass and gives an optimistic total.
    """
    from spacecost.rocket import propellant_mass_for_dv
    m = _mission(catalog, "methalox  (LCH4 / LOX)")
    naive = float(propellant_mass_for_dv(1_000.0 + 2_000.0, 6_500.0, 380))
    assert m["outbound_prop_kg"] > naive
    assert m["launched_mass_kg"] == pytest.approx(
        1_000.0 + 2_000.0 + m["return_prop_kg"] + m["outbound_prop_kg"])


def test_isru_takes_the_return_propellant_off_the_outbound_leg(catalog):
    """`isru_return_propellant` is a real dial, not a documented one.

    ⚠️  AND WHAT IT SAVES IS THE LAUNCH, NOT THE PROPELLANT.  The propellant
    line goes UP -- $50/kg on site against $0.24/kg for methalox on Earth, two
    hundred times -- and the total still falls, because return propellant made
    at the destination is not dead mass on the outbound leg and so is neither
    launched nor pushed through the outbound burn.  Asserted in that direction
    on purpose: the intuitive assertion is the wrong one, and writing it down
    is what stops somebody "fixing" the model to satisfy it.
    """
    cfg = spacecost.SpacecostConfig(isru_return_propellant=True)
    isru = _mission(catalog, "methalox  (LCH4 / LOX)", config=cfg)
    hauled = _mission(catalog, "methalox  (LCH4 / LOX)")

    assert isru["launched_mass_kg"] < hauled["launched_mass_kg"] / 2
    assert isru["launch_usd"] < hauled["launch_usd"]
    assert isru["outbound_prop_kg"] < hauled["outbound_prop_kg"]
    assert isru["return_prop_usd"] > hauled["return_prop_usd"],         "on-site propellant costs MORE per kg; only the mass is saved"
    assert isru["total_usd"] < hauled["total_usd"]


def test_the_totals_add_up(catalog):
    """Contingency is a fraction of the subtotal, and the parts sum to it."""
    m = _mission(catalog, "methalox  (LCH4 / LOX)")
    subtotal = (m["launch_usd"] + m["outbound_prop_usd"] + m["return_prop_usd"]
                + m["hardware_usd"] + m["ops_usd"])
    assert m["contingency_usd"] == pytest.approx(
        subtotal * spacecost.CONFIG.contingency_fraction)
    assert m["total_usd"] == pytest.approx(subtotal + m["contingency_usd"])
    assert m["usd_per_kg_returned"] == pytest.approx(m["total_usd"] / 1_000.0)


# ------------------------------------------- and the summary stays raw
def test_the_summary_does_not_apply_the_penalty():
    """The other half of the asymmetry, asserted so it cannot drift shut.

    `build_transportation_summary` is what economicspace's Stage 4 reads, and
    Stage 4 applies `dv_penalty_factor` itself. If this table started applying
    it too, every electric combination downstream would be charged 1.5x twice
    -- 2.25x -- and nothing would raise.
    """
    launch = spacecost.load_launch_vehicles().head(1)
    prop = merge_propellant_prices(spacecost.load_propellants(),
                                   pd.DataFrame())
    prop = prop[prop["name"] == "Xenon  (Hall / ion)"]
    assert float(prop["dv_penalty_factor"].iloc[0]) == 1.5, "fixture drifted"

    dv = spacecost.load_delta_v()
    dv = dv[dv["segment"] == "LEO  →  average NEA"]
    assert len(dv) == 1, "fixture drifted"

    summary = spacecost.build_transportation_summary(launch, prop, dv)
    assert len(summary) == 1
    # The segment's OWN dv, not a penalised one.
    assert summary["segment_dv_m_per_s"].iloc[0] == float(dv["dv_m_per_s"].iloc[0])
