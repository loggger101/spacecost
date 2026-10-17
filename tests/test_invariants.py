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
    assert len(spacecost.LAUNCH_VEHICLES_REFERENCE) == 76
    assert len(spacecost.PROPELLANTS_REFERENCE) == 41
    assert len(spacecost.DELTA_V_REFERENCE) == 34
    assert len(spacecost.OPERATIONAL_COSTS_REFERENCE) == 46
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


def test_every_isru_row_states_its_processing_energy():
    """Data contract 1.23.0.  A row with an ISRU feed says what making it costs.

    Zero is a claim (the feed is used as it comes), so it is stated, never a
    default; NaN marks a row with no source, and every one is gated out of an
    operational-only search.  Hydrolox carries the low end of its band.
    """
    df = spacecost.load_propellants()
    isru = df[df["isru_feed_kg_per_kg"].notna()]
    assert not isru.empty
    for _, row in isru.iterrows():
        v = row["isru_processing_wh_per_kg"]
        if pd.isna(v):
            assert row["status"] != "operational", row["name"]
        else:
            assert v >= 0.0, row["name"]
    assert df[df["isru_feed_kg_per_kg"].isna()]["isru_processing_wh_per_kg"].isna().all()
    hl = df[df["name"] == "hydrolox  (LH2 / LOX)"].iloc[0]
    assert hl["isru_processing_wh_per_kg"] == 15_200.0
    # Electrolysis (55 kWh/kg H2) plus the pre-cooled H2 liquefier (35 kW / 0.3
    # kg/h / 3) plus the O2 bound (2 kW / 0.96 kg/h), per kg at O/F 6.
    low = (55.0 + 35.0 / 0.3 / 3.0) / 7.0 + 2.0 / 0.96 * 6.0 / 7.0
    assert hl["isru_processing_wh_per_kg"] / 1000.0 == pytest.approx(low, abs=0.05)
    for name in ("Water  (gridded ion / ECR)", "Water  (electrothermal / resistojet)"):
        assert df[df["name"] == name].iloc[0]["isru_processing_wh_per_kg"] == 0.0


def test_an_isru_row_with_no_processing_entry_raises():
    """A silent zero is free propellant, so a missing entry is an error."""
    from spacecost.propellants import _apply_isru_processing
    df = pd.DataFrame([{"name": "a propellant nobody costed", "isru_feed_kg_per_kg": 1.0}])
    with pytest.raises(KeyError):
        _apply_isru_processing(df)


def test_isru_plant_throughput_row():
    """The plant row is Kleinhenz & Paz 2021's ridge: 11.67 t in 0.616 yr on 2.6 t."""
    ops = spacecost.load_operational_costs()
    row = ops[ops["category"] == "ISRU propellant plant throughput"].iloc[0]
    assert row["value"] == pytest.approx(11_670.0 / (225.0 / 365.25) / 2_600.0, abs=0.01)
    assert row["range_low"] <= row["value"] <= row["range_high"]
