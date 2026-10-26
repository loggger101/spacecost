# -*- coding: utf-8 -*-
"""Recorded quotes: the snapshots, their checksums, and a build priced from one.

Two promises are tested here.  A snapshot reads back exactly what was written,
and stays that way: one edited byte, a missing checksum line, or a line naming
no file each fail `check_snapshots`.  And a build from a snapshot is the build
that fetching those same closes live would have made, row for row, because
both paths go through `fuel_prices_from_quotes`.

Every failure case below is planted on a copy in a temporary directory.  The
committed snapshots are only ever read.
"""

import os
import shutil
import sys
import types

import pandas as pd
import pytest

from spacecost import quotes
from spacecost.config import SpacecostConfig
from spacecost.prices import (FUEL_TICKERS, fetch_yfinance_fuel_prices,
                              fuel_prices_from_quotes, required_fuel_tickers,
                              snapshot_fuel_prices)

SEED = "fuel-2026-10-17"


def _row(ticker="HO=F", close=2.5, unit="gallon", close_date="2026-10-23",
         recorded="2026-10-26", note=""):
    return quotes.Quote(ticker, "yfinance", close, unit, close_date, recorded,
                        note)


@pytest.fixture
def copy_dir(tmp_path):
    """The committed snapshots, copied somewhere a test may damage them."""
    dest = tmp_path / "quotes"
    shutil.copytree(quotes.PACKAGE_DIR, dest)
    return str(dest)


# ------------------------------------------------------- the committed files
def test_every_committed_snapshot_matches_its_checksum():
    assert quotes.check_snapshots() == []


def test_the_seed_is_the_closes_that_rebuild_the_2026_10_17_tables():
    rows = quotes.closes_by_ticker(quotes.load_snapshot(SEED))
    assert rows["HO=F"].close == 4.559800148010254
    assert rows["NG=F"].close == 3.134999990463257
    assert {q.recorded_date for q in rows.values()} == {"2026-10-17"}


def test_the_seed_prices_the_rows_economicspace_recorded():
    """The three live rows of economicspace's Stage 3 tables of 2026-10-17.

    Typed from that file, read back with full precision.  The seed was chosen
    as the one float32 close per ticker that reproduces them, so equality here
    is exact, not approximate.
    """
    got = snapshot_fuel_prices(SpacecostConfig(quote_snapshot=SEED))
    got = got.set_index("name")["live_cost_usd_per_kg"].to_dict()
    assert got == {
        "kerolox  (RP-1 / LOX)":               0.5713723376162302,
        "methalox  (LCH4 / LOX)":              0.1888190542495769,
        "HTP / RP-1  (peroxide bipropellant)": 1.4255287141335595,
    }


def test_only_tickers_that_price_a_row_are_required():
    assert required_fuel_tickers() == {"HO=F": "gallon", "NG=F": "MMBtu"}
    assert set(FUEL_TICKERS) == {"HO=F", "NG=F", "CL=F"}


# ------------------------------------------------------------- round trips
def test_a_close_reads_back_as_the_same_float(tmp_path):
    awkward = [0.1 + 0.2, 4.559800148010254, 1e-7 * 3, 12345.678901234567]
    rows = [_row("T%d" % i, c) for i, c in enumerate(awkward)]
    quotes.write_snapshot("test-2026-10-26", rows, str(tmp_path))
    back = quotes.load_snapshot("test-2026-10-26", str(tmp_path))
    assert [q.close for q in sorted(back)] == [q.close for q in sorted(rows)]


def test_a_snapshot_is_crlf_like_every_other_csv_here(tmp_path):
    path = quotes.write_snapshot("test-2026-10-26", [_row()], str(tmp_path))
    raw = open(path, "rb").read()
    assert raw.count(b"\r\n") == 2 and b"\n" not in raw.replace(b"\r\n", b"")


def test_a_snapshot_is_never_overwritten(tmp_path):
    quotes.write_snapshot("test-2026-10-26", [_row()], str(tmp_path))
    with pytest.raises(FileExistsError):
        quotes.write_snapshot("test-2026-10-26", [_row(close=3.0)],
                              str(tmp_path))


# ---------------------------------------------- planted defects, all caught
def test_an_edited_byte_is_caught(copy_dir):
    path = os.path.join(copy_dir, SEED + ".csv")
    data = bytearray(open(path, "rb").read())
    i = data.index(b"4.5598")
    data[i + 3] = ord("6")                       # same length, one digit
    open(path, "wb").write(bytes(data))
    assert any("edited" in p for p in quotes.check_snapshots(copy_dir))
    with pytest.raises(ValueError, match="never edited"):
        quotes.load_snapshot(SEED, copy_dir)


def test_a_snapshot_with_no_checksum_line_is_caught(copy_dir):
    shutil.copy(os.path.join(copy_dir, SEED + ".csv"),
                os.path.join(copy_dir, "fuel-2026-10-18.csv"))
    assert any("no line" in p for p in quotes.check_snapshots(copy_dir))


def test_a_checksum_line_with_no_file_is_caught(copy_dir):
    os.remove(os.path.join(copy_dir, SEED + ".csv"))
    assert any("does not exist" in p for p in quotes.check_snapshots(copy_dir))


def test_a_misnamed_file_is_caught(copy_dir):
    shutil.copy(os.path.join(copy_dir, SEED + ".csv"),
                os.path.join(copy_dir, "fuel latest.csv"))
    assert any("not named like" in p for p in quotes.check_snapshots(copy_dir))


@pytest.mark.parametrize("bad", [
    _row(close=float("nan")),
    _row(close=0.0),
    _row(close=-1.0),
    _row(close_date="2026-10-27"),               # closed after it was recorded
    _row(close_date="23/10/2026"),
])
def test_an_impossible_row_is_refused(tmp_path, bad):
    with pytest.raises(ValueError):
        quotes.write_snapshot("test-2026-10-26", [bad], str(tmp_path))


def test_a_ticker_twice_is_refused(tmp_path):
    with pytest.raises(ValueError, match="twice"):
        quotes.write_snapshot("test-2026-10-26", [_row(), _row(close=3.0)],
                              str(tmp_path))


def test_a_malformed_name_is_refused():
    for name in ("fuel", "fuel-2026-10", "Fuel-2026-10-17", "../fuel-2026-10-17"):
        with pytest.raises(ValueError):
            quotes.snapshot_path(name)


def test_an_unknown_snapshot_names_the_ones_there_are():
    with pytest.raises(FileNotFoundError, match=SEED):
        quotes.load_snapshot("fuel-1999-01-01")


# ----------------------------------------- what a consumer needs, enforced
def test_a_snapshot_missing_a_priced_ticker_is_refused(tmp_path):
    quotes.write_snapshot("fuel-2026-10-26", [_row("HO=F")], str(tmp_path))
    rows = quotes.load_snapshot("fuel-2026-10-26", str(tmp_path))
    assert quotes.missing(rows, required_fuel_tickers()) == ["no NG=F quote"]


def test_a_ticker_in_the_wrong_unit_is_refused():
    rows = [_row("HO=F", unit="barrel"), _row("NG=F", unit="MMBtu")]
    assert quotes.missing(rows, required_fuel_tickers()) == [
        "HO=F is quoted per barrel; the conversion expects gallon"]


def test_live_and_snapshot_together_are_refused():
    from spacecost.build import build_catalog
    with pytest.raises(ValueError, match="not both"):
        build_catalog(SpacecostConfig(use_yfinance=True, quote_snapshot=SEED))


# ------------------------------------------- one conversion for both paths
class _Ticker(object):
    def __init__(self, symbol):
        self.symbol = symbol

    def history(self, period=None, auto_adjust=None):
        seed = quotes.closes_by_ticker(quotes.load_snapshot(SEED))
        if self.symbol not in seed:
            return pd.DataFrame()
        q = seed[self.symbol]
        return pd.DataFrame({"Close": [q.close]},
                            index=pd.to_datetime([q.close_date]))


def test_a_snapshot_build_is_the_live_build_of_the_same_closes(monkeypatch):
    module = types.ModuleType("yfinance")
    module.Ticker = _Ticker
    monkeypatch.setitem(sys.modules, "yfinance", module)
    live = fetch_yfinance_fuel_prices(SpacecostConfig(use_yfinance=True))
    recorded = snapshot_fuel_prices(SpacecostConfig(quote_snapshot=SEED))
    pd.testing.assert_frame_equal(live, recorded, check_exact=True)


def test_a_snapshot_build_carries_the_day_it_was_recorded(tmp_path):
    from spacecost.build import build_catalog
    frames = build_catalog(SpacecostConfig(output_dir=str(tmp_path),
                                           quote_snapshot=SEED))
    for df in frames.values():
        assert set(df["catalog_date"]) == {"2026-10-17"}
    props = frames["propellants"]
    assert (props["price_basis"] == "live").sum() == 3


def test_completed_only_skips_todays_unfinished_bar(monkeypatch):
    class _Open(object):
        def __init__(self, symbol):
            pass

        def history(self, period=None, auto_adjust=None):
            return pd.DataFrame({"Close": [2.0, 9.0]},
                                index=pd.to_datetime(["2026-10-23",
                                                      "2026-10-26"]))

    module = types.ModuleType("yfinance")
    module.Ticker = _Open
    monkeypatch.setitem(sys.modules, "yfinance", module)
    live, _ = quotes.fetch_closes({"HO=F": "gallon"}, today="2026-10-26")
    done, _ = quotes.fetch_closes({"HO=F": "gallon"}, today="2026-10-26",
                                  completed_only=True)
    assert live[0].close == 9.0 and live[0].close_date == "2026-10-26"
    assert done[0].close == 2.0 and done[0].close_date == "2026-10-23"


def test_record_writes_nothing_when_a_ticker_fails(monkeypatch, tmp_path):
    class _Half(object):
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, period=None, auto_adjust=None):
            if self.symbol == "NG=F":
                raise RuntimeError("Yahoo is down")
            return pd.DataFrame({"Close": [2.0]},
                                index=pd.to_datetime(["2026-10-23"]))

    module = types.ModuleType("yfinance")
    module.Ticker = _Half
    monkeypatch.setitem(sys.modules, "yfinance", module)
    with pytest.raises(RuntimeError, match="nothing recorded"):
        quotes.record_snapshot("fuel", FUEL_TICKERS, str(tmp_path),
                               today="2026-10-26")
    assert os.listdir(str(tmp_path)) == []


def test_record_adds_a_letter_for_a_second_snapshot_the_same_day(
        monkeypatch, tmp_path):
    module = types.ModuleType("yfinance")
    module.Ticker = _Ticker
    monkeypatch.setitem(sys.modules, "yfinance", module)
    first = quotes.record_snapshot("fuel", required_fuel_tickers(),
                                   str(tmp_path), today="2026-10-26")
    second = quotes.record_snapshot("fuel", required_fuel_tickers(),
                                    str(tmp_path), today="2026-10-26")
    assert first.endswith("fuel-2026-10-26.csv")
    assert second.endswith("fuel-2026-10-26b.csv")
    assert quotes.check_snapshots(str(tmp_path)) == []


def test_the_frame_from_no_quotes_is_empty():
    assert fuel_prices_from_quotes({}).empty
