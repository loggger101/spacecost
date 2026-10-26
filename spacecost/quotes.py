# -*- coding: utf-8 -*-
"""Recorded market quotes: the one input a build cannot make again.

Everything else a build reads is a cited table in this package, and the same
release gives the same bytes on every run.  A live quote breaks that.  Fetch
the heating-oil future on Monday and again on Tuesday and the propellant table
moves, and once the old table is overwritten nothing can say what Monday's
price was.  economicspace learned this the hard way: its rule was "never re-run
Stages 2 or 3", and it kept folders of hand-made input backups to work around
the rule.

So quotes are recorded once, as a SNAPSHOT, and committed:

    spacecost/quotes/fuel-2026-10-17.csv     one row per ticker
    spacecost/quotes/SHA256SUMS              one line per snapshot

A build that names a snapshot (`SpacecostConfig.quote_snapshot`) reads its
closes in place of yfinance's and gives the same tables on every run, offline.
Fetching live is still there (`use_yfinance`), for anyone who wants today's
price and accepts that it is not reproducible.

A snapshot is never edited.  A newer quote is a new file under a new name.
`check_snapshots` holds every file to its SHA256SUMS line, in both directions:
a changed byte, a file with no line and a line with no file all fail it, and
CI runs it.

THE FORMAT IS THE QUOTE AS THE SOURCE GAVE IT, NOT A PRICE PER KG.  Converting
a close to $/kg is the consumer's arithmetic: heating oil needs a density and
natural gas an energy content, which belong to the table that uses them.
Storing the raw close keeps one snapshot usable by every consumer, and keeps
each consumer's arithmetic exactly what it was when it fetched live.  A close
is written with `repr`, so it reads back as the same float, bit for bit.

The code is shared.  economicspace's Stage 2 package, spacevalue, keeps its
metal quotes in its own `quotes/` directory with these same functions, because
it already depends on this package and this package must not depend on it.

Nothing here imports pandas or numpy, and nothing touches the network except
`fetch_closes`.
"""

import csv
import hashlib
import io
import math
import os
import re
from datetime import date, datetime
from typing import Dict, Iterable, List, NamedTuple, Optional, Tuple

from ._log import say

# The columns of a snapshot, in file order.
COLUMNS = ("ticker", "source", "close", "unit", "close_date",
           "recorded_date", "note")

# The checksum file beside the snapshots, in `sha256sum` format.
SUMS_FILE = "SHA256SUMS"

# `<family>-<YYYY-MM-DD>` plus an optional letter for a second snapshot taken
# the same day: `fuel-2026-10-26`, `metals-2026-10-26b`.
_NAME = re.compile(r"^[a-z][a-z0-9]*-\d{4}-\d{2}-\d{2}[a-z]?$")

# Where this package keeps its own snapshots.
PACKAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quotes")


class Quote(NamedTuple):
    """One close, as the source reported it."""
    ticker:        str     # the source's symbol, e.g. "HO=F"
    source:        str     # where it came from, e.g. "yfinance"
    close:         float   # the close, in `unit`
    unit:          str     # what the close is per, e.g. "gallon"
    close_date:    str     # the trading day the close belongs to, YYYY-MM-DD
    recorded_date: str     # the day it was written into a snapshot or table
    note:          str     # provenance a reader needs, or ""


def _is_date(text: str) -> bool:
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except (TypeError, ValueError):
        return False
    return True


def snapshot_path(name: str, directory: str = PACKAGE_DIR) -> str:
    """The file a snapshot name refers to.  Refuses a malformed name."""
    if not _NAME.match(name or ""):
        raise ValueError(
            "%r is not a snapshot name; they look like fuel-2026-10-17"
            % (name,))
    return os.path.join(directory, name + ".csv")


def list_snapshots(directory: str = PACKAGE_DIR,
                   family: Optional[str] = None) -> List[str]:
    """Snapshot names in `directory`, oldest first; one `family` if given."""
    if not os.path.isdir(directory):
        return []
    names = sorted(f[:-4] for f in os.listdir(directory)
                   if f.endswith(".csv") and _NAME.match(f[:-4]))
    if family is not None:
        names = [n for n in names if n.split("-", 1)[0] == family]
    return names


def _read_rows(path: str) -> List[Quote]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if tuple(header or ()) != COLUMNS:
            raise ValueError("%s: header is %s, expected %s"
                             % (path, header, list(COLUMNS)))
        rows = []
        for n, cells in enumerate(reader, start=2):
            if len(cells) != len(COLUMNS):
                raise ValueError("%s line %d: %d cells, expected %d"
                                 % (path, n, len(cells), len(COLUMNS)))
            try:
                close = float(cells[2])
            except ValueError:
                raise ValueError("%s line %d: close %r is not a number"
                                 % (path, n, cells[2])) from None
            rows.append(Quote(cells[0], cells[1], close, cells[3], cells[4],
                              cells[5], cells[6]))
    return rows


def row_problems(rows: Iterable[Quote], where: str = "") -> List[str]:
    """What is wrong with these rows on their own, or [] if nothing is."""
    bad, seen = [], set()
    tag = (where + ": ") if where else ""
    for q in rows:
        if not q.ticker or not q.source or not q.unit:
            bad.append("%sa row has a blank ticker, source or unit" % tag)
        if q.ticker in seen:
            bad.append("%s%s appears twice" % (tag, q.ticker))
        seen.add(q.ticker)
        if not (math.isfinite(q.close) and q.close > 0):
            bad.append("%s%s close is %r; a close is finite and above zero"
                       % (tag, q.ticker, q.close))
        if not (_is_date(q.close_date) and _is_date(q.recorded_date)):
            bad.append("%s%s has a date that is not YYYY-MM-DD" % (tag, q.ticker))
        elif q.close_date > q.recorded_date:
            bad.append("%s%s closed %s, after it was recorded on %s"
                       % (tag, q.ticker, q.close_date, q.recorded_date))
    return bad


def load_snapshot(name: str, directory: str = PACKAGE_DIR) -> List[Quote]:
    """Every quote in a snapshot, checked against its SHA256SUMS line.

    Raises rather than returns something partial: a snapshot that fails its
    checksum, or whose rows are malformed, is not a snapshot.
    """
    path = snapshot_path(name, directory)
    if not os.path.exists(path):
        known = ", ".join(list_snapshots(directory)) or "none"
        raise FileNotFoundError("no snapshot %r in %s (have: %s)"
                                % (name, directory, known))
    sums = _read_sums(directory)
    want = sums.get(os.path.basename(path))
    if want is None:
        raise ValueError("%s has no line in %s" % (path, SUMS_FILE))
    have = _sha256(path)
    if have != want:
        raise ValueError("%s has sha256 %s; %s says %s.  A snapshot is never "
                         "edited: restore it, and record new quotes under a "
                         "new name." % (path, have, SUMS_FILE, want))
    rows = _read_rows(path)
    bad = row_problems(rows, os.path.basename(path))
    if bad:
        raise ValueError("; ".join(bad))
    return rows


def closes_by_ticker(rows: Iterable[Quote]) -> Dict[str, Quote]:
    """The rows keyed by ticker."""
    return {q.ticker: q for q in rows}


def recorded_date(rows: Iterable[Quote]) -> str:
    """The one `recorded_date` a snapshot carries.  Refuses a mix."""
    dates = sorted({q.recorded_date for q in rows})
    if len(dates) != 1:
        raise ValueError("a snapshot carries one recorded_date, found %s"
                         % (dates or "none"))
    return dates[0]


def missing(rows: Iterable[Quote], required: Dict[str, str]) -> List[str]:
    """Problems with a snapshot measured against what a consumer needs.

    `required` maps ticker to the unit the consumer converts from.  A ticker
    that is absent, or quoted in another unit, is a problem: the consumer would
    otherwise fall back to a reference price, or convert with the wrong factor,
    and say nothing.
    """
    have = closes_by_ticker(rows)
    bad = []
    for ticker, unit in sorted(required.items()):
        q = have.get(ticker)
        if q is None:
            bad.append("no %s quote" % ticker)
        elif q.unit != unit:
            bad.append("%s is quoted per %s; the conversion expects %s"
                       % (ticker, q.unit, unit))
    return bad


# ─────────────────────────────────────────────────────────────────────────────
# CHECKSUMS
# ─────────────────────────────────────────────────────────────────────────────
def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_sums(directory: str) -> Dict[str, str]:
    path = os.path.join(directory, SUMS_FILE)
    sums: Dict[str, str] = {}
    if not os.path.exists(path):
        return sums
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            digest, _, fname = line.partition("  ")
            sums[fname.strip()] = digest.strip()
    return sums


def check_snapshots(directory: str = PACKAGE_DIR) -> List[str]:
    """Every snapshot against SHA256SUMS, both ways, and every row read.

    Returns the problems found; [] means every file is what was recorded.
    """
    sums = _read_sums(directory)
    files = {n + ".csv" for n in list_snapshots(directory)}
    stray = sorted(f for f in os.listdir(directory)
                   if f.endswith(".csv") and f not in files) \
        if os.path.isdir(directory) else []
    bad = ["%s is not named like a snapshot (fuel-2026-10-17.csv)" % f
           for f in stray]
    for fname in sorted(files - set(sums)):
        bad.append("%s has no line in %s" % (fname, SUMS_FILE))
    for fname in sorted(set(sums) - files):
        bad.append("%s names %s, which does not exist" % (SUMS_FILE, fname))
    for fname in sorted(files & set(sums)):
        path = os.path.join(directory, fname)
        if _sha256(path) != sums[fname]:
            bad.append("%s does not match its %s line: a snapshot was edited"
                       % (fname, SUMS_FILE))
            continue
        try:
            rows = _read_rows(path)
        except ValueError as exc:
            bad.append(str(exc))
            continue
        bad.extend(row_problems(rows, fname))
        try:
            recorded_date(rows)
        except ValueError as exc:
            bad.append("%s: %s" % (fname, exc))
    return bad


# ─────────────────────────────────────────────────────────────────────────────
# RECORDING
# ─────────────────────────────────────────────────────────────────────────────
def write_snapshot(name: str, rows: List[Quote],
                   directory: str = PACKAGE_DIR) -> str:
    """Write a new snapshot and its SHA256SUMS line.  Never overwrites.

    The file is CRLF like every other CSV this package writes, and each close
    is written with `repr` so it reads back as the same float.
    """
    path = snapshot_path(name, directory)
    if os.path.exists(path):
        raise FileExistsError(
            "%s exists, and a snapshot is never rewritten.  Take a second one "
            "the same day as %sb." % (path, name))
    bad = row_problems(rows, name)
    if bad:
        raise ValueError("; ".join(bad))
    recorded_date(rows)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(COLUMNS)
    for q in sorted(rows, key=lambda q: q.ticker):
        w.writerow([q.ticker, q.source, repr(float(q.close)), q.unit,
                    q.close_date, q.recorded_date, q.note])
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        fh.write(buf.getvalue())
    with open(os.path.join(directory, SUMS_FILE), "a", newline="\n",
              encoding="utf-8") as fh:
        fh.write("%s  %s\n" % (_sha256(path), os.path.basename(path)))
    return path


def fetch_closes(tickers: Dict[str, str], today: Optional[str] = None,
                 completed_only: bool = False,
                 ) -> Tuple[List[Quote], List[str]]:
    """The latest close of each ticker from yfinance, and what failed.

    `tickers` maps symbol to the unit the source quotes it in.  This is the
    loop both of economicspace's fetching stages ran: five days of history,
    the last non-blank close.  A ticker that fails is reported in the second
    list rather than raised, so the caller decides whether a partial answer is
    acceptable; `missing()` is how a recorder refuses one.

    While a market is open, yfinance's last bar is TODAY'S, and its "close" is
    the latest trade, not a settlement.  The live builds have always taken it.
    A snapshot should not: `completed_only` drops a bar dated `today` or
    later, so what is recorded is the last finished session.
    """
    try:
        import yfinance as yf
    except ImportError:
        return [], ["yfinance is not installed (pip install yfinance)"]
    stamp = today or date.today().strftime("%Y-%m-%d")
    rows, failed = [], []
    for ticker, unit in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d", auto_adjust=False)
            closes = hist["Close"].dropna() if "Close" in hist else None
            if closes is not None and completed_only:
                days = [d.strftime("%Y-%m-%d") for d in closes.index]
                closes = closes[[d < stamp for d in days]]
            if closes is None or closes.empty:
                failed.append("%s: no close data" % ticker)
                continue
            rows.append(Quote(ticker, "yfinance", float(closes.iloc[-1]),
                              unit, closes.index[-1].strftime("%Y-%m-%d"),
                              stamp, ""))
            say("     OK  %-6s = %12s USD/%s  [%s]"
                % (ticker, "%.4f" % rows[-1].close, unit, rows[-1].close_date))
        except Exception as exc:                       # noqa: BLE001
            failed.append("%s: %s: %s" % (ticker, type(exc).__name__, exc))
    return rows, failed


def record_snapshot(family: str, tickers: Dict[str, str],
                    directory: str = PACKAGE_DIR,
                    today: Optional[str] = None) -> str:
    """Fetch every ticker's last finished close and write a new snapshot.

    All or nothing: one ticker failing, or quoted in an unexpected unit, and
    nothing is written.  The name is `<family>-<today>`, with a letter added
    when a snapshot of that name exists already.
    """
    stamp = today or date.today().strftime("%Y-%m-%d")
    rows, failed = fetch_closes(tickers, today=stamp, completed_only=True)
    bad = failed + missing(rows, tickers)
    if bad:
        raise RuntimeError("nothing recorded: " + "; ".join(bad))
    name = "%s-%s" % (family, stamp)
    for suffix in [""] + list("bcdefghijklmnopqrstuvwxyz"):
        if not os.path.exists(snapshot_path(name + suffix, directory)):
            return write_snapshot(name + suffix, rows, directory)
    raise RuntimeError("26 snapshots of %s on one day" % family)
