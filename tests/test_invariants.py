# -*- coding: utf-8 -*-
"""Invariants over the tables themselves, independent of any committed file.

These catch a bad ROW rather than a bad extraction: they need no baseline, and
they still pass on a tree where somebody has deliberately re-measured a value.
"""

import numpy as np
import pandas as pd
import pytest

import spacecost


def test_row_counts():
    """The documented sizes.  A count stated in prose is a number waiting to rot."""
    assert len(spacecost.LAUNCH_VEHICLES_REFERENCE) == 36
    assert len(spacecost.PROPELLANTS_REFERENCE) == 41
    assert len(spacecost.DELTA_V_REFERENCE) == 33
    assert len(spacecost.OPERATIONAL_COSTS_REFERENCE) == 44
    assert len(spacecost.STORAGE_REFERENCE) == 20


def test_every_row_is_cited():
    """Every reference row carries a `notes` field.  That is the whole premise."""
    for table_name in ("LAUNCH_VEHICLES_REFERENCE", "PROPELLANTS_REFERENCE",
                       "DELTA_V_REFERENCE", "OPERATIONAL_COSTS_REFERENCE",
                       "STORAGE_REFERENCE"):
        for row in getattr(spacecost, table_name):
            note = row.get("notes", "")
            assert note and note.strip(), table_name + ": uncited row " + str(row)[:120]


def test_every_row_carries_a_reference_year():
    """`reference_year` is what tells a reader a price has gone stale."""
    for table_name in ("LAUNCH_VEHICLES_REFERENCE", "PROPELLANTS_REFERENCE",
                       "OPERATIONAL_COSTS_REFERENCE", "STORAGE_REFERENCE"):
        for row in getattr(spacecost, table_name):
            assert isinstance(row.get("reference_year"), int), \
                table_name + ": a row has no reference_year"


def test_launch_status_values_are_closed():
    """A typo in `status` silently removes a vehicle from every filtered search."""
    allowed = {"operational", "development", "concept", "retired"}
    got = {v["status"] for v in spacecost.LAUNCH_VEHICLES_REFERENCE}
    assert got <= allowed, "unknown status: " + str(got - allowed)


def test_propellant_isp_is_physical():
    """Chemical rockets cannot beat ~550 s; anything higher must be electric.

    Propellantless rows are the deliberate exception: they carry infinite Isp
    because they carry no propellant, which is what `propellantless` means.
    """
    for p in spacecost.PROPELLANTS_REFERENCE:
        isp = p["isp_vac_s"]
        if p.get("propellantless"):
            assert not np.isfinite(isp), "propellantless row with finite Isp"
            continue
        assert np.isfinite(isp) and isp > 0
        if p.get("type") in ("chemical", "cold_gas", "monopropellant", "solid"):
            assert isp <= 550, "a chemical row above 550 s"


def test_tankage_raises_rather_than_defaulting():
    """`_tank_kg_per_L` raises on an unknown class rather than defaulting.

    A silent default is how a new propellant gets a free ride on tank mass,
    which is the failure the storage-class taxonomy exists to prevent.
    """
    from spacecost.propellants import _tank_kg_per_L
    assert _tank_kg_per_L("deep_cryogen") > _tank_kg_per_L("storable_liquid")
    with pytest.raises(KeyError):
        _tank_kg_per_L("a_class_that_does_not_exist")


def test_rocket_equation_matches_hand_calculation():
    """Tsiolkovsky, against the closed form."""
    want = np.exp(6_500 / (452 * spacecost.G0_M_S2)) - 1.0
    got = float(spacecost.propellant_mass_for_dv(1.0, 6_500, 452))
    assert got == pytest.approx(want, rel=1e-12)
    assert spacecost.cost_per_dv_usd_per_kg(10.0, 452, 6_500) == pytest.approx(
        want * 10.0, rel=1e-12)


def test_zero_dv_needs_no_propellant():
    assert float(spacecost.propellant_mass_for_dv(1_000.0, 0.0, 300)) == 0.0


def test_loaders_return_frames():
    for loader in (spacecost.load_launch_vehicles, spacecost.load_propellants,
                   spacecost.load_delta_v, spacecost.load_operational_costs,
                   spacecost.load_storage):
        df = loader()
        assert isinstance(df, pd.DataFrame) and not df.empty
