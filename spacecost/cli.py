# -*- coding: utf-8 -*-
"""Command line: `python -m spacecost`.

    python -m spacecost build            write the six CSVs
    python -m spacecost build --live     fetch live fuel prices first
    python -m spacecost show vehicles    print a table
    python -m spacecost propellant 6500  cheapest propellant for a given delta-v

`build` is the only subcommand that writes anything.  Everything prints ASCII
only -- see tests/test_quiet.py for why that is a rule and not a preference.
"""

import argparse
import os
import sys

from . import __version__
from ._log import set_verbose
from .build import build_catalog
from .config import SpacecostConfig
from .query import cheapest_propellant_for, mission_cost_breakdown
from .tables import (load_delta_v, load_launch_vehicles,
                     load_operational_costs, load_propellants, load_storage)

_SHOW = {
    "vehicles":    (load_launch_vehicles,
                    ["name", "operator", "status", "payload_leo_kg",
                     "usd_per_kg_to_leo", "usd_per_kg_to_gto"]),
    "propellants": (load_propellants,
                    ["name", "type", "isp_vac_s", "density_kg_per_L",
                     "cost_usd_per_kg", "storage_class"]),
    "deltav":      (load_delta_v, ["segment", "dv_m_per_s", "duration_yr"]),
    "operations":  (load_operational_costs,
                    ["category", "value", "unit", "range_low", "range_high"]),
    "storage":     (load_storage, None),
}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="spacecost",
        description="Cited reference tables for space-mission cost estimation.")
    p.add_argument("--version", action="version",
                   version="spacecost " + __version__)
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="write the six reference CSVs")
    b.add_argument("-o", "--output-dir", default=None,
                   help="where to write (default: $SPACECOST_OUTPUT_DIR, "
                        "else ./spacecost_data)")
    b.add_argument("--live", action="store_true",
                   help="fetch live commodity fuel prices first. OFF by "
                        "default: a build is deterministic and offline unless "
                        "you ask for the network")
    b.add_argument("--date", default=None, metavar="YYYY-MM-DD",
                   help="pin the catalog_date provenance stamp, for "
                        "comparing two builds")
    b.add_argument("-q", "--quiet", action="store_true",
                   help="suppress progress output")

    s = sub.add_parser("show", help="print one reference table")
    s.add_argument("table", choices=sorted(_SHOW))
    s.add_argument("-n", "--rows", type=int, default=0,
                   help="limit to the first N rows (default: all)")

    q = sub.add_parser("propellant",
                       help="rank propellants by fuel cost for a given delta-v")
    q.add_argument("delta_v_m_per_s", type=float)
    q.add_argument("-n", "--rows", type=int, default=10)

    return p


def main(argv=None) -> int:
    """Entry point. Returns a process exit code."""
    args = _build_parser().parse_args(argv)

    if args.command == "build":
        set_verbose(not args.quiet)
        cfg = SpacecostConfig(output_dir=args.output_dir or "",
                              use_yfinance=args.live)
        build_catalog(cfg, catalog_date=args.date)
        if args.quiet:
            print(cfg.table_dir())
        return 0

    if args.command == "show":
        loader, cols = _SHOW[args.table]
        df = loader()
        if cols:
            df = df[[c for c in cols if c in df.columns]]
        if args.rows:
            df = df.head(args.rows)
        print(df.to_string(index=False))
        return 0

    if args.command == "propellant":
        # `cheapest_propellant_for` reads `cost_usd_per_kg`, which is the
        # RESOLVED price -- live where a quote exists, reference otherwise --
        # and only `merge_propellant_prices` produces it. Handing it the raw
        # reference frame gets a KeyError, because the reference column is
        # named `ref_cost_usd_per_kg`. Passing an empty live frame resolves
        # every row to its reference price with no network call.
        import pandas as pd

        from .prices import merge_propellant_prices
        catalog = {"propellants": merge_propellant_prices(
            load_propellants(), pd.DataFrame())}
        ranked = cheapest_propellant_for(catalog, args.delta_v_m_per_s)
        print(ranked.head(args.rows).to_string(index=False))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
