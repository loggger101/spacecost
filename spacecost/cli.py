# -*- coding: utf-8 -*-
"""Command line: `python -m spacecost`.

    python -m spacecost build            write the seven CSVs
    python -m spacecost build --live     fetch live fuel prices first
    python -m spacecost show vehicles    print a table
    python -m spacecost propellant 6500  cheapest propellant for a given delta-v
    python -m spacecost launch leo       cheapest vehicle to a destination
    python -m spacecost environment 2.7  the power/thermal/comms penalty at a distance
    python -m spacecost validate         run the sanity bands, --strict to fail
    python -m spacecost example          a worked mission cost breakdown

`build` is the only subcommand that writes anything.  Everything prints ASCII
only -- see tests/test_quiet.py for why that is a rule and not a preference.
"""

import argparse
import sys

from . import __version__
from ._log import set_verbose
from .build import build_catalog
from .config import SpacecostConfig
from .query import (cheapest_launch_to, cheapest_propellant_for,
                    mission_cost_breakdown)
from .tables import (load_delta_v, load_environments, load_launch_vehicles,
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
    "environments": (load_environments,
                     ["name", "kind", "au_mean", "solar_flux_w_per_m2",
                      "solar_array_mass_factor", "dark_period_hr",
                      "escape_velocity_m_per_s", "one_way_light_time_min"]),
}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="spacecost",
        description="Cited reference tables for space-mission cost estimation.")
    p.add_argument("--version", action="version",
                   version="spacecost " + __version__)
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="write the seven reference CSVs")
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

    lv = sub.add_parser("launch",
                        help="cheapest launch vehicle to a destination")
    lv.add_argument("destination", choices=["leo", "gto", "escape"])
    lv.add_argument("--min-payload-kg", type=float, default=0.0)
    lv.add_argument("-n", "--rows", type=int, default=10)

    en = sub.add_parser(
        "environment",
        help="the power, thermal and comms penalty at a heliocentric distance")
    en.add_argument("au", type=float,
                    help="heliocentric distance in AU (1.0 = Earth)")

    va = sub.add_parser(
        "validate", help="run the sanity bands over the tables")
    va.add_argument("--strict", action="store_true",
                    help="exit non-zero if any check WARNs. NOTEs never fail")

    ex = sub.add_parser("example",
                        help="worked mission cost breakdown, end to end")
    ex.add_argument("--payload-kg", type=float, default=1_000.0)
    ex.add_argument("--dv-outbound", type=float, default=6_500.0)
    ex.add_argument("--dv-return", type=float, default=5_500.0)
    ex.add_argument("--years", type=float, default=3.0)
    ex.add_argument("--hardware-kg", type=float, default=2_000.0)
    ex.add_argument("--vehicle", default="Falcon Heavy (reusable side cores)")
    ex.add_argument("--propellant", default="methalox  (LCH4 / LOX)")

    return p


def _priced_catalog():
    """The frames the query helpers need, resolved offline.

    `cheapest_propellant_for` and `mission_cost_breakdown` read
    `cost_usd_per_kg`, which is the RESOLVED price -- live where a quote
    exists, reference otherwise -- and only `merge_propellant_prices` produces
    it.  Handing them the raw reference frame raises `KeyError`, because the
    reference column is named `ref_cost_usd_per_kg`.  An empty live frame
    resolves every row to its reference price with no network call.
    """
    import pandas as pd

    from .prices import merge_propellant_prices
    return {
        "launch_vehicles": load_launch_vehicles(),
        "propellants": merge_propellant_prices(load_propellants(), pd.DataFrame()),
        "operational_costs": load_operational_costs(),
    }


def _make_stdout_total():
    """Never die printing a DATA value.

    Every string this package prints is ASCII, and tests/test_quiet.py keeps it
    that way -- but the `notes` fields are data, not output, and they carry a
    yen sign, degree symbols and em-dashes. `show` prints them. Windows picks
    cp1252 for a REDIRECTED stdout, so `spacecost show storage > out.txt` would
    raise UnicodeEncodeError on the first one, and never in a console, which is
    what makes it invisible until somebody logs it.

    `errors="replace"` is deliberate over `"strict"`: a mangled character in a
    citation is a far better outcome than a dead command.
    """
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def main(argv=None) -> int:
    """Entry point. Returns a process exit code."""
    _make_stdout_total()
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
        ranked = cheapest_propellant_for(_priced_catalog(), args.delta_v_m_per_s)
        print(ranked.head(args.rows).to_string(index=False))
        return 0

    if args.command == "launch":
        found = cheapest_launch_to(_priced_catalog(), args.destination,
                                   min_payload_kg=args.min_payload_kg)
        if found is None or (hasattr(found, "empty") and found.empty):
            print("no vehicle carries " + str(args.min_payload_kg)
                  + " kg to " + args.destination)
            return 1
        cols = ["name", "operator", "status", "payload_leo_kg",
                "payload_gto_kg", "payload_escape_kg",
                "usd_per_kg_to_" + args.destination, "list_price_usd"]
        found = found[[c for c in cols if c in found.columns]]
        print(found.head(args.rows).to_string(index=False))
        return 0

    if args.command == "environment":
        # Not a table lookup: the derivations answer at ANY distance, and a
        # trade study's asteroid is rarely one of the 23 rows.
        from .environments import (blackbody_temp_k, one_way_light_time_min,
                                   solar_array_mass_factor,
                                   solar_flux_w_per_m2)
        au = args.au
        if au <= 0:
            print("heliocentric distance must be positive")
            return 1
        print("    %-34s : %18s" % ("heliocentric distance (AU)",
                                    format(au, ",.4f")))
        print("    %-34s : %18s" % ("solar flux (W/m2)",
                                    format(solar_flux_w_per_m2(au), ",.1f")))
        print("    %-34s : %18s" % ("array mass per watt (x 1 AU)",
                                    format(solar_array_mass_factor(au), ",.2f")))
        print("    %-34s : %18s" % ("blackbody temperature (K)",
                                    format(blackbody_temp_k(au), ",.1f")))
        # The range at conjunction, which is the worst case a link budget and a
        # command round trip both have to survive.
        print("    %-34s : %18s" % ("one-way light time at conjunction (min)",
                                    format(one_way_light_time_min(au + 1.0167),
                                           ",.1f")))
        return 0

    if args.command == "validate":
        import pandas as pd

        from .prices import merge_propellant_prices
        from .validate import ValidationError, validate_tables
        frames = (load_launch_vehicles(),
                  merge_propellant_prices(load_propellants(), pd.DataFrame()),
                  load_delta_v(), load_operational_costs(),
                  load_environments(), load_storage())
        try:
            findings = validate_tables(*frames, config=SpacecostConfig(),
                                       strict=args.strict)
        except ValidationError as exc:
            for item in exc.findings:
                print("%-5s %-18s %s" % (item["level"], item["table"],
                                         item["message"]))
                for line in item["detail"]:
                    print("      " + line)
            return 1
        for item in findings:
            print("%-5s %-18s %s" % (item["level"], item["table"],
                                     item["message"]))
            for line in item["detail"]:
                print("      " + line)
        warns = sum(1 for item in findings if item["level"] == "WARN")
        print("%d finding(s), %d of them warnings" % (len(findings), warns))
        return 0

    if args.command == "example":
        breakdown = mission_cost_breakdown(
            _priced_catalog(),
            payload_kg          = args.payload_kg,
            delta_v_outbound    = args.dv_outbound,
            delta_v_return      = args.dv_return,
            launch_vehicle      = args.vehicle,
            propellant          = args.propellant,
            mission_duration_yr = args.years,
            hardware_kg         = args.hardware_kg,
        )
        for key, value in breakdown.items():
            if isinstance(value, float):
                # Whole dollars and whole kilograms above 100, two decimals
                # below it.  A single format ruined the one line that is a
                # RATIO rather than a quantity: `,.0f` printed a 1.5x low-thrust
                # penalty as "2", which is not a rounding of the output, it is
                # a different claim about the mission.
                spec = ",.0f" if abs(value) >= 100 else ",.2f"
                print("    %-30s : %18s" % (key, format(value, spec)))
            else:
                print("    %-30s : %s" % (key, value))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
