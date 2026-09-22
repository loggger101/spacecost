# -*- coding: utf-8 -*-
"""The surface `economicspace` imports, declared here so removing one is loud.

WHY THIS FILE EXISTS.  This package was extracted from economicspace's Module 3
and that project is its consumer: `modules/transportation.py` is a 374-line
adapter that re-exports the names below and delegates everything else.  The
consumer pins a TAG, so what it gets is whatever a release contains, and a name
dropped between releases is not discovered until somebody installs the new tag
and an import fails.

THAT HAS ALREADY HAPPENED ONCE.  The `v0.1.0` tag predated `validate_tables`,
so a clean install of it could not satisfy economicspace's import at all.  The
guard added then was the CI step that asserts every name in `__all__` is
importable from the built wheel, and that is a real check of PACKAGING.  It is
not a check of this CONTRACT: delete a name from the package and from `__all__`
in one commit and that step still passes, because it only ever asks about the
names `__all__` currently lists.  This file asks the other question.

WHAT A FAILURE MEANS.  Not that the name must come back.  It means the change
is BREAKING for the known consumer, so it needs a major-version bump and a note
in CHANGELOG.md rather than a patch release -- and economicspace's
`modules/transportation.py` has to move in the same breath.  Deleting a line
here is how you say you have done that.

⚠️  THIS LIST IS DELIBERATELY NOT DERIVED.  Reading it out of economicspace at
test time would need that repo checked out, which CI does not have, and a check
that skips on every run is a check that does not exist.  A hand-kept list is
the right shape for a contract: it changes only when somebody decides it
changes.

⚠️  `validate_tables` IS NOT A SYNONYM ANYBODY CAN DROP.  economicspace builds
its single-file `master.py` by concatenating its four modules and resolving
name collisions with a whole-word regex over the entire file text, comments and
string literals included.  It rewrites `validate`, so `from spacecost import
validate as _v` becomes a request for a name this package does not export and
the import fails.  `validate_tables` exists precisely so that a rewriting build
has a word to keep.  See economicspace's CLAUDE.md, "Name collisions are
handled by hand".
"""

import spacecost

# Every attribute economicspace reaches, as of its transportation 1.15.0 and
# mineral_value 1.9.0.  Mostly its Stage 3 adapter, grouped the way that adapter
# groups them; the last group is Stage 2, which imports this package directly.
CONSUMER_SURFACE = (
    # The five reference tables, re-exported as attributes of the adapter
    # module because economicspace's docs harness holds README row counts to
    # them and its dashboard renders them.
    "LAUNCH_VEHICLES_REFERENCE",
    "PROPELLANTS_REFERENCE",
    "DELTA_V_REFERENCE",
    "OPERATIONAL_COSTS_REFERENCE",
    "STORAGE_REFERENCE",

    # Physical constants and unit helpers.
    "G0_M_S2",
    "LITRES_PER_GAL",
    "LITRES_PER_BBL",
    "COMMODITY_DENSITY_KG_PER_L",

    # Loaders.
    "load_launch_vehicles",
    "load_propellants",
    "load_delta_v",
    "load_operational_costs",
    "load_storage",

    # Rocket-equation helpers and the query utilities.
    "propellant_mass_for_dv",
    "cost_per_dv_usd_per_kg",
    "build_transportation_summary",
    "cheapest_launch_to",
    "cheapest_propellant_for",
    "mission_cost_breakdown",

    # The delivery chains, moved out of economicspace's Module 2 at v0.3.0.
    # ⚠️  Module 2 imports these, not Module 3, and it is the FIRST stage to
    # reach this package -- so a name dropped here fails a pricing stage that
    # runs before the adapter does, and the traceback will not mention Stage 3.
    "DELIVERY_CHAINS",
    "LEO_LAUNCH_USD_PER_KG",
    "delivered_cost_usd_per_kg",
    "downleg_cost_usd_per_kg",

    # The pipeline entry point and the collision-proof validator alias.
    "build_catalog",
    "validate_tables",

    # Config, verbosity and the stamps.
    "SpacecostConfig",
    "set_verbose",
    "DATA_VERSION",
    "__version__",
)


def test_every_name_the_consumer_imports_still_exists():
    """The contract itself.  A missing name is a breaking change, not a patch."""
    missing = [n for n in CONSUMER_SURFACE if not hasattr(spacecost, n)]
    assert not missing, (
        "economicspace imports these and this package no longer exports them: "
        + ", ".join(missing)
        + ".  That is a MAJOR version change; bump it, note it in CHANGELOG.md, "
          "and move modules/transportation.py in the same breath."
    )


def test_the_contract_is_public():
    """Everything in it is in `__all__`, so the wheel check covers it too.

    Belt and braces rather than redundancy: the CI wheel step walks `__all__`,
    so a consumer name that is reachable but UNDECLARED would be tested by this
    file and not by that one, and would be one refactor away from vanishing
    from a built distribution while the source tree still imported fine.
    `__version__` is exempt only if the package chooses not to list it.
    """
    declared = set(spacecost.__all__)
    undeclared = [n for n in CONSUMER_SURFACE
                  if n not in declared and n != "__version__"]
    assert not undeclared, (
        "these are part of the consumer contract but absent from __all__: "
        + ", ".join(undeclared))


def test_config_surface_is_what_the_adapter_mirrors():
    """`SpacecostConfig`'s field NAMES are the adapter's ten dials.

    economicspace keeps its own `TransportConfig` because two of its defaults
    belong to a pipeline rather than to a library: `output_dir` points into its
    own tree, and `use_yfinance` is True there and False here, since a pipeline
    stage is expected to fetch and a library must not.  It asserts the two
    field sets are equal AT IMPORT and raises if they are not, so a field added
    on either side alone fails the consumer's import rather than its run.

    The count is asserted here so that adding a dial is a deliberate act on
    both sides.  It is not a style rule: the adapter builds its call as
    `SpacecostConfig(**{f.name: ... for f in fields(config)})`, so a field this
    package gains and economicspace does not is one the consumer never passes.
    """
    import dataclasses
    names = {f.name for f in dataclasses.fields(spacecost.SpacecostConfig)}
    assert len(names) == 10, (
        "the dial surface moved to %d fields: %s.  economicspace mirrors this "
        "set in modules/transportation.py and asserts equality at import, so "
        "both sides move together or the consumer stops importing."
        % (len(names), sorted(names)))
