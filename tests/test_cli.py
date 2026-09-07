# -*- coding: utf-8 -*-
"""Every subcommand runs, and every exported helper is reachable from one.

The second half is the point. A helper that is exported but has no CLI path and
no README mention is a helper nobody will find, and this package exists partly
so that people who are not going to `import spacecost` can still use the
tables. `cheapest_launch_to` and `mission_cost_breakdown` were both in that
state after the extraction; the audit caught them, and this keeps them caught.
"""

import os

import pytest

import spacecost
from spacecost.cli import main


def test_show_every_table(capsys):
    for table in ("vehicles", "propellants", "deltav", "operations", "storage"):
        assert main(["show", table, "-n", "3"]) == 0
        out = capsys.readouterr().out
        assert out.strip(), table + " printed nothing"


def test_propellant_ranking(capsys):
    assert main(["propellant", "6500", "-n", "5"]) == 0
    out = capsys.readouterr().out
    assert "usd_per_kg_payload_for_dv" in out


def test_launch_ranking(capsys):
    assert main(["launch", "leo", "--min-payload-kg", "5000", "-n", "3"]) == 0
    out = capsys.readouterr().out
    assert "usd_per_kg_to_leo" in out
    # The notes column is long enough to make the table unreadable; the CLI
    # trims to the columns somebody comparing vehicles actually wants.
    assert "Source:" not in out


def test_launch_with_an_impossible_payload(capsys):
    """Nothing lifts 10,000 t. That is a clean 'no', not a traceback."""
    rc = main(["launch", "leo", "--min-payload-kg", "10000000"])
    assert rc == 1
    assert "no vehicle" in capsys.readouterr().out


def test_worked_example(capsys):
    assert main(["example"]) == 0
    out = capsys.readouterr().out
    for line in ("launch_usd", "outbound_prop_usd", "contingency_usd",
                 "total_usd", "launched_mass_kg"):
        assert line in out, line + " missing from the worked example"


def test_build_writes_six_files(tmp_path, capsys):
    assert main(["build", "-q", "-o", str(tmp_path)]) == 0
    written = sorted(os.listdir(os.path.join(str(tmp_path), "transportation")))
    assert written == sorted([
        "delta_v_segments.csv", "launch_vehicles.csv", "operational_costs.csv",
        "propellants.csv", "storage_systems.csv", "transportation_summary.csv"])


def test_build_is_quiet_when_asked(tmp_path, capsys):
    """`-q` prints the output directory and nothing else, so it pipes."""
    main(["build", "-q", "-o", str(tmp_path)])
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1 and out[0].endswith("transportation")


@pytest.mark.parametrize("name", [
    n for n in spacecost.__all__
    if not n.startswith("_") and not n.isupper()
    and n not in {"SpacecostConfig", "TransportConfig", "say", "set_verbose",
                  "is_verbose", "validate", "build_transportation_summary",
                  "build_transportation_catalog"}
])
def test_public_helper_is_documented_or_reachable(name):
    """No exported helper is invisible: it is in the CLI, or in the README."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cli = open(os.path.join(here, "spacecost", "cli.py"), encoding="utf-8").read()
    readme = open(os.path.join(here, "README.md"), encoding="utf-8").read()
    assert name in cli or name in readme, (
        name + " is exported but appears in neither the CLI nor the README")


def test_migration_aliases_resolve():
    """The two names that changed on the way out still import."""
    assert spacecost.TransportConfig is spacecost.SpacecostConfig
    assert spacecost.build_transportation_catalog is spacecost.build_catalog
