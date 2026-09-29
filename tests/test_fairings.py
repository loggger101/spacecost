# -*- coding: utf-8 -*-
"""Fairing volumes are derived from a cited drawing, or say why they are not.

Until data contract 1.17.0, 37 of the 76 launch rows carried no fairing volume
and the other 39 carried one nobody had sourced.  A consumer filling the blanks
with a default was pricing a third of the table on a number nobody chose.
"""

import math

import pytest

import spacecost
from spacecost import fairings
from spacecost.fairings import FAIRINGS, envelope_m3


def _rows():
    return {v["name"]: v for v in spacecost.LAUNCH_VEHICLES_REFERENCE}


def test_every_row_says_how_its_volume_was_obtained():
    for v in spacecost.LAUNCH_VEHICLES_REFERENCE:
        basis, vol = v["fairing_basis"], v["fairing_volume_m3"]
        assert basis in {"guide", "published", "estimate", "none"}, v["name"]
        if basis == "none":
            assert math.isnan(vol), v["name"]
        else:
            assert math.isfinite(vol) and vol > 0, v["name"]
        assert "Fairing volume: " in v["notes"], v["name"]


def test_the_register_and_the_table_name_the_same_vehicles():
    """Both halves: a row with no source, and a source with no row."""
    assert set(FAIRINGS) == set(_rows())


def _bare_row(**over):
    row = {"name": "Test rocket", "operator": "x", "country": "x",
           "status": "operational", "availability": "open",
           "core_propellant": "kerolox", "first_flight_year": 2020,
           "payload_leo_kg": 1_000, "payload_gto_kg": 0,
           "payload_escape_kg": 0, "list_price_usd": 10_000_000,
           "price_basis": "published", "reference_year": 2026, "notes": "x"}
    row.update(over)
    return row


def test_a_typed_fairing_volume_raises():
    from spacecost.vehicles import _apply_launch_defaults
    with pytest.raises(ValueError, match="types fairing_volume_m3"):
        _apply_launch_defaults([_bare_row(fairing_volume_m3=100.0)],
                               {"Test rocket": FAIRINGS["Electron"]})


def test_a_row_with_no_fairing_source_raises():
    from spacecost.vehicles import _apply_launch_defaults
    with pytest.raises(ValueError, match="no entry in fairings.py"):
        _apply_launch_defaults([_bare_row()], {})


def test_a_sourced_row_takes_its_volume_and_says_where_from():
    from spacecost.vehicles import _apply_launch_defaults
    row = _bare_row()
    _apply_launch_defaults([row], {"Test rocket": FAIRINGS["Electron"]})
    assert row["fairing_volume_m3"] == FAIRINGS["Electron"]["volume"]
    assert row["fairing_basis"] == "guide"
    assert row["notes"].endswith(FAIRINGS["Electron"]["source"] + ".")


@pytest.mark.parametrize("name,stated", [
    ("New Glenn", 458.0),               # Blue Origin PUG Rev C, Fig 5-2
    ("SLS Block 1B (Cargo)", 621.0),    # NASA ESD 30000, Fig 6-7
])
def test_the_method_reproduces_the_two_totals_a_guide_prints(name, stated):
    """The check that a drawing is being read the way its maker reads it."""
    assert _rows()[name]["fairing_volume_m3"] == pytest.approx(stated, rel=0.005)


def test_a_cylinder_revolves_to_a_cylinder():
    assert envelope_m3([(0.0, 2.0), (3.0, 2.0)]) == pytest.approx(3.0 * math.pi)


def test_a_drawn_arc_holds_more_than_its_chord():
    """A nose followed along its printed radius never under-counts its cone."""
    chord = envelope_m3([(0.0, 3.05), (2.289, 1.0)])
    arc = envelope_m3(fairings._arc(0.0, 3.05, 2.289, 1.0, 4.226))
    assert chord < arc < envelope_m3([(0.0, 3.05), (2.289, 3.05)])


def test_heights_must_not_run_backwards():
    with pytest.raises(ValueError, match="must not decrease"):
        envelope_m3([(0.0, 1.0), (2.0, 1.0), (1.0, 0.5)])


def test_an_estimate_is_the_derived_ratio_times_the_outer_cylinder():
    for name, (d, l, _) in fairings.OUTER_ONLY.items():
        expected = fairings.FAIRING_FILL_RATIO * math.pi / 4 * d * d * l
        assert _rows()[name]["fairing_volume_m3"] == pytest.approx(
            expected, rel=0.005), name


def test_the_fill_ratio_is_the_median_of_the_calibration_rows():
    lo, hi = fairings.FILL_RATIO_RANGE
    assert lo <= fairings.FAIRING_FILL_RATIO <= hi
    # Every calibration row is a guide-drawn row, never an estimate of itself.
    for name, *_ in fairings._CALIBRATION:
        assert FAIRINGS[name]["basis"] == "guide", name


def test_an_envelope_never_exceeds_its_outer_cylinder():
    """A usable envelope bigger than the fairing around it is a misread."""
    for name, r in fairings.FILL_RATIOS.items():
        assert 0.0 < r < 1.0, name
