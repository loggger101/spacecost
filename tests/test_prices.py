# -*- coding: utf-8 -*-
"""The live-price path, exercised OFFLINE against a stubbed yfinance.

WHY THIS FILE EXISTS.  `use_yfinance` is False by default and every committed
reference file is an offline build, which is the right default and leaves the
whole live path untested on every normal run: the fetcher, the three unit
conversions, and the mixture weighting that stops a kerosene quote from being
charged to the oxidiser half of kerolox.

⚠️  AND IT FAILS SILENTLY.  `fetch_yfinance_fuel_prices` catches every
exception per ticker and returns an empty frame, so a renamed ticker, a changed
quote unit or a broken conversion degrades to "reference prices" with no error
anywhere. That behaviour is correct for a library -- a launch price should not
become unavailable because Yahoo is down -- and it means a bug here is
invisible until somebody compares two builds and wonders why `price_basis`
never says "live".

CI carries a weekly canary that fetches for real, and that answers a DIFFERENT
question: whether Yahoo still serves those three tickers. It cannot run on a
pull request, because a third-party outage must not block a merge. This file is
the half that can: the arithmetic, on quotes whose answers are known, with no
network.

The stub is installed into `sys.modules` under the name the fetcher imports
lazily. That is why the import inside `fetch_yfinance_fuel_prices` is inside
the function and should stay there.
"""

import sys
import types

import pandas as pd
import pytest

import spacecost
from spacecost.config import SpacecostConfig
from spacecost.prices import (_LIVE_BLENDS, fetch_yfinance_fuel_prices,
                              merge_propellant_prices)
from spacecost.propellants import _COMPONENTS, fuel_mass_fraction
from spacecost.units import (LITRES_PER_BBL, LITRES_PER_GAL,
                             COMMODITY_DENSITY_KG_PER_L, _per_bbl_to_per_kg,
                             _per_gal_to_per_kg, _per_mmbtu_to_per_kg_ng)

# Round numbers, so an expected value can be worked out by hand in the
# assertion rather than copied from a previous run of the code under test.
FAKE_QUOTES = {
    "HO=F": 2.00,      # USD per US gallon
    "NG=F": 4.00,      # USD per MMBtu
    "CL=F": 80.00,     # USD per barrel
}
QUOTE_DATE = "2026-09-15"


class _FakeTicker(object):
    def __init__(self, symbol):
        self.symbol = symbol

    def history(self, period=None, auto_adjust=None):
        close = FAKE_QUOTES[self.symbol]
        # Two rows, so that taking `.iloc[-1]` rather than `.iloc[0]` is a
        # thing this test can actually get wrong.
        return pd.DataFrame(
            {"Close": [close * 0.5, close]},
            index=pd.to_datetime(["2026-09-14", QUOTE_DATE]),
        )


@pytest.fixture
def fake_yfinance(monkeypatch):
    """Install a stub `yfinance` for the duration of one test."""
    module = types.ModuleType("yfinance")
    module.Ticker = _FakeTicker
    monkeypatch.setitem(sys.modules, "yfinance", module)
    return module


# ------------------------------------------------------ unit conversions
def test_gallon_conversion_is_price_over_litres_times_density():
    """$/gal -> $/kg is a division by litres per gallon and by density."""
    rho = COMMODITY_DENSITY_KG_PER_L["heating_oil"]
    assert _per_gal_to_per_kg(2.00, "heating_oil") == pytest.approx(
        2.00 / (LITRES_PER_GAL * rho), rel=1e-12)
    # Sanity on the magnitude, which is what a unit error actually breaks:
    # kerosene is about half a dollar a kilogram at $2 a gallon.
    assert 0.5 < _per_gal_to_per_kg(2.00, "heating_oil") < 0.8


def test_barrel_conversion_agrees_with_the_gallon_one():
    """A barrel is 42 US gallons, and the two helpers must not disagree.

    They are separate functions over separate constants, so this is the check
    that `LITRES_PER_BBL` and `LITRES_PER_GAL` still describe the same world.
    """
    assert LITRES_PER_BBL == pytest.approx(42.0 * LITRES_PER_GAL, rel=1e-12)
    per_bbl = _per_bbl_to_per_kg(84.00, "crude_oil")
    per_gal = _per_gal_to_per_kg(84.00 / 42.0, "crude_oil")
    assert per_bbl == pytest.approx(per_gal, rel=1e-12)


def test_natural_gas_conversion_uses_the_energy_content_of_lng():
    """$/MMBtu -> $/kg goes through energy, not volume.

    1 kg of LNG is about 50 MJ, and 1 MMBtu is 1.055 GJ, so a kilogram is
    0.0474 MMBtu. This is the one conversion in the module that is not a unit
    of volume, and the one most likely to be "fixed" into a density.
    """
    assert _per_mmbtu_to_per_kg_ng(4.00) == pytest.approx(4.00 * 0.04739,
                                                          rel=1e-12)
    # 50 MJ/kg over 1.055 GJ/MMBtu, derived independently of the constant.
    assert 0.04739 == pytest.approx((50e6 / 1.055e9), rel=0.01)


# ------------------------------------------------------------- the fetcher
def test_fetch_returns_a_row_per_proxied_propellant(fake_yfinance):
    live = fetch_yfinance_fuel_prices(SpacecostConfig(use_yfinance=True))
    assert not live.empty
    proxied = {p["name"] for p in spacecost.PROPELLANTS_REFERENCE
               if p.get("yfinance_proxy")}
    assert set(live["name"]) == proxied
    for col in ("live_cost_usd_per_kg", "live_cost_usd_per_L",
                "live_price_date", "live_price_source"):
        assert col in live.columns


def test_fetch_takes_the_LATEST_close_not_the_first(fake_yfinance):
    """`.iloc[-1]`, and the stub's first row is deliberately half the second."""
    live = fetch_yfinance_fuel_prices(SpacecostConfig(use_yfinance=True))
    assert (live["live_price_date"] == QUOTE_DATE).all()


def test_a_bipropellant_moves_only_its_fuel_half(fake_yfinance):
    """The whole point of the mixture weighting.

    A live kerosene quote prices the RP-1 in kerolox and nothing else; the LOX
    stays at its reference price. Getting this wrong -- which is what the
    `startswith` prefix match risked -- charges the whole mixture at the fuel
    price, which for kerolox is roughly three times too much.
    """
    live = fetch_yfinance_fuel_prices(SpacecostConfig(use_yfinance=True))
    by_name = live.set_index("name")

    for row_name, blend in _LIVE_BLENDS.items():
        fuel_only = _per_gal_to_per_kg(FAKE_QUOTES["HO=F"], "heating_oil") \
            if blend == "kerolox" else _per_mmbtu_to_per_kg_ng(FAKE_QUOTES["NG=F"])
        frac = fuel_mass_fraction(blend)
        want = (frac * fuel_only
                + (1 - frac) * _COMPONENTS["LOX"]["cost_usd_per_kg"])
        got = float(by_name.loc[row_name, "live_cost_usd_per_kg"])
        assert got == pytest.approx(want, rel=1e-12), row_name
        # And the blended price must sit between the two components, which is
        # the property a weighting error breaks even when the algebra is right.
        lo, hi = sorted((fuel_only, _COMPONENTS["LOX"]["cost_usd_per_kg"]))
        assert lo <= got <= hi, row_name


def test_a_missing_ticker_degrades_rather_than_raising(monkeypatch):
    """One dead ticker must not take the other two down.

    This is the behaviour the weekly canary exists to police, asserted from the
    other side: the library keeps working, and it is CI's job to notice.
    """
    module = types.ModuleType("yfinance")

    class _Broken(_FakeTicker):
        def history(self, period=None, auto_adjust=None):
            if self.symbol == "HO=F":
                raise RuntimeError("Yahoo says no")
            return _FakeTicker.history(self, period, auto_adjust)

    module.Ticker = _Broken
    monkeypatch.setitem(sys.modules, "yfinance", module)

    live = fetch_yfinance_fuel_prices(SpacecostConfig(use_yfinance=True))
    names = set(live["name"])
    assert any("methalox" in n for n in names), "the good ticker still resolved"
    assert not any("kerolox" in n for n in names), "the dead one is absent"


def test_no_yfinance_at_all_returns_an_empty_frame(monkeypatch):
    """The `pip install spacecost` case: the extra is not installed."""
    monkeypatch.setitem(sys.modules, "yfinance", None)
    live = fetch_yfinance_fuel_prices(SpacecostConfig(use_yfinance=True))
    assert live.empty


# --------------------------------------------------------------- the merge
def test_live_prices_win_and_the_rest_fall_back(fake_yfinance):
    live = fetch_yfinance_fuel_prices(SpacecostConfig(use_yfinance=True))
    merged = merge_propellant_prices(spacecost.load_propellants(), live)

    n_live = int((merged["price_basis"] == "live").sum())
    assert n_live == len(live)
    assert (merged["price_basis"].isin({"live", "reference"})).all()

    # Every live row's resolved price IS its live price, and every other row's
    # is its reference price. The two columns are different names for a reason.
    for _, r in merged.iterrows():
        if r["price_basis"] == "live":
            assert r["cost_usd_per_kg"] == r["live_cost_usd_per_kg"]
        else:
            assert r["cost_usd_per_kg"] == pytest.approx(
                r["ref_cost_usd_per_kg"], nan_ok=True)


def test_an_offline_merge_resolves_everything_to_reference():
    """The path `_priced_catalog` and every offline build take."""
    merged = merge_propellant_prices(spacecost.load_propellants(),
                                     pd.DataFrame())
    assert (merged["price_basis"] == "reference").all()
    assert merged["live_cost_usd_per_kg"].isna().all()


def test_the_offline_merge_is_what_the_committed_tables_carry():
    """price_basis reads "reference" on all 41 rows, as config.py promises."""
    merged = merge_propellant_prices(spacecost.load_propellants(),
                                     pd.DataFrame())
    assert len(merged) == len(spacecost.PROPELLANTS_REFERENCE)
    assert set(merged["price_basis"]) == {"reference"}
