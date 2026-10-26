# -*- coding: utf-8 -*-
"""The surface `economicspace` imports, declared here so removing one is loud.

WHY THIS FILE EXISTS.  This package was extracted from economicspace's Module 3
and that project is its consumer: `modules/transportation.py` is the adapter
that drives Stage 3, spacevalue (its Stage 2, split out) takes the delivery
chains and the quote-snapshot code from here, and its worked calculation and
verification sheet reach into submodules.  The consumer pins a TAG, so what it gets is whatever a release
contains, and a name dropped between releases is not discovered until somebody
installs the new tag and an import fails.

THAT HAS ALREADY HAPPENED ONCE.  The `v0.1.0` tag predated a name economicspace
imported, so a clean install of it could not satisfy that import at all.  The
guard added then was the CI step that asserts every name in `__all__` is
importable from the built wheel, and that is a real check of PACKAGING.  It is
not a check of this CONTRACT: delete a name from the package and from `__all__`
in one commit and that step still passes, because it only ever asks about the
names `__all__` currently lists.  This file asks the other question, and CI
asks it twice: of the source tree with the rest of the suite, and of the BUILT
WHEEL from outside the tree, which is what a consumer installing a tag gets.

WHAT A FAILURE MEANS.  Not that the name must come back.  It means the change
is BREAKING for the known consumer, so it needs a minor-version bump while this
package is 0.x and a note in CHANGELOG.md rather than a patch release -- and
the economicspace module that reads the name has to move in the same breath.
Deleting a line here is how you say you have done that.

⚠️  THIS LIST IS DELIBERATELY NOT DERIVED.  Reading it out of economicspace at
test time would need that repo checked out, which CI does not have, and a check
that skips on every run is a check that does not exist.  A hand-kept list is
the right shape for a contract: it changes only when somebody decides it
changes.
"""

import ast
import dataclasses
import inspect
import io
import tokenize

import spacecost

# Every attribute the two consumers reach: economicspace on its main at the
# v0.14.0 repin (master v1.59.0, transportation 1.23.6), and spacevalue v0.1.0,
# which is economicspace's Stage 2 split out (mineral_value 1.16.0 became its
# data contract 1.17.0).  Found by grepping both for `spacecost.<name>`,
# `from spacecost import` and `getattr(spacecost, ...)`, which is the way to
# refresh it.
#
# ⚠️  THIS LIST IS WHAT THE CONSUMER READS, NOT WHAT IT ONCE RE-EXPORTED.  It
# used to mirror the Stage 3 adapter, which re-exports most of `__all__`, and
# so it missed four names Stage 2 reads directly.
CONSUMER_SURFACE = (
    # The six reference tables, re-exported as attributes of the adapter:
    # economicspace's docs harness holds README row counts to them, and its
    # Stage 3 banner counts them.
    "LAUNCH_VEHICLES_REFERENCE",
    "PROPELLANTS_REFERENCE",
    "DELTA_V_REFERENCE",
    "OPERATIONAL_COSTS_REFERENCE",
    "STORAGE_REFERENCE",
    "ENVIRONMENTS_REFERENCE",

    # Loaders.  The verification sheet cites installed rows through them, by
    # name (`getattr(spacecost, loader)`).
    "load_launch_vehicles",
    "load_propellants",
    "load_delta_v",
    "load_operational_costs",
    "load_storage",

    # The adapter's standalone preview.
    "cheapest_propellant_for",

    # The delivery chains, moved out of economicspace's Module 2 at v0.3.0.
    # ⚠️  spacevalue (that Module 2, split out) imports these at import time,
    # so a name dropped here breaks every price table, and the traceback will
    # name spacevalue rather than this package.
    "DELIVERY_CHAINS",
    "LEO_LAUNCH_USD_PER_KG",
    "LEO_LAUNCH_VEHICLE",
    "delivered_cost_usd_per_kg",
    "delivery_hardware_usd_per_kg",
    "delivery_mass_ratio",
    "downleg_cost_usd_per_kg",

    # The pipeline entry point and the validator.
    "build_catalog",
    "validate",

    # Config, verbosity and the stamps.  Stage 3's CONFIG is a SpacecostConfig
    # instance, and its dashboard help is scraped from this package's
    # config.py; see test_every_config_field_has_help below.
    "SpacecostConfig",
    "say",
    "set_verbose",
    "DATA_VERSION",
    "__version__",
)

# Names reached through a SUBMODULE rather than the top level, so `__all__`
# does not cover them.  economicspace's worked calculation and verification
# sheet re-derive the delivered price from the rates and the chain, and one of
# these is private: a private name a consumer reaches is a contract all the
# same, and this is where it is written down.
SUBMODULE_SURFACE = (
    ("config", "SpacecostConfig"),
    ("delivery", "STAGE_HARDWARE_USD_PER_KG"),
    ("delivery", "TUG_PROPELLANT_USD_PER_KG"),
    ("delivery", "ENTRY_SYSTEM_USD_PER_KG"),
    ("delivery", "CHAIN_BURN_DV_BEFORE_V090"),
    ("delivery", "TUG_DRY_MASS_FRAC"),
    ("delivery", "LANDER_DRY_MASS_FRAC"),
    ("delivery", "LEO_LAUNCH_VEHICLE"),
    ("delivery", "_HYDROLOX"),
    # The quote snapshots (v0.14.0).  spacevalue records and reads its metal
    # snapshots with these, from its own directory, and economicspace's Stage 3
    # names a fuel snapshot through `SpacecostConfig.quote_snapshot`.
    ("quotes", "Quote"),
    ("quotes", "SUMS_FILE"),
    ("quotes", "check_snapshots"),
    ("quotes", "closes_by_ticker"),
    ("quotes", "fetch_closes"),
    ("quotes", "list_snapshots"),
    ("quotes", "load_snapshot"),
    ("quotes", "missing"),
    ("quotes", "record_snapshot"),
    ("quotes", "recorded_date"),
    ("quotes", "write_snapshot"),
)


def test_every_submodule_name_the_consumer_reaches_still_exists():
    """The half of the contract that `__all__` cannot see."""
    import importlib
    missing = ["spacecost.%s.%s" % (mod, name)
               for mod, name in SUBMODULE_SURFACE
               if not hasattr(importlib.import_module("spacecost." + mod), name)]
    assert not missing, (
        "economicspace reaches these and this package no longer has them: "
        + ", ".join(missing))


def test_every_name_the_consumer_imports_still_exists():
    """The contract itself.  A missing name is a breaking change, not a patch."""
    missing = [n for n in CONSUMER_SURFACE
               if not hasattr(spacecost, n)]
    assert not missing, (
        "a consumer imports these and this package no longer exports them: "
        + ", ".join(missing)
        + ".  That is a BREAKING change; bump the minor version, note it in "
          "CHANGELOG.md, and move the economicspace module that reads it "
          "(economicspace's transportation.py for Stage 3, or spacevalue) in "
          "the same breath."
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


def _field_help(cls):
    """field name -> its help text, by the rule economicspace's dashboard uses.

    The comment block directly above the field, stopping at a blank line or a
    section banner (`# --- TITLE ---`) or rule, else a trailing comment on the
    field's own line.  A banner is a heading, not help: a bare field directly
    under one has none.
    economicspace's `ui_meta.scrape_field_docs` reads this file's
    `SpacecostConfig` that way and shows the result as each Stage 3 dial's help.
    """
    src = inspect.getsource(inspect.getmodule(cls))
    lines = src.split("\n")
    trailing = {}
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            row, col = tok.start
            if lines[row - 1][:col].strip():
                trailing[row] = tok.string.lstrip("#").strip()
    node = next(n for n in ast.walk(ast.parse(src))
                if isinstance(n, ast.ClassDef) and n.name == cls.__name__)
    out = {}
    for stmt in node.body:
        if not (isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)):
            continue
        block, i = [], stmt.lineno - 2
        while i >= 0 and lines[i].strip().startswith("#"):
            text = lines[i].strip().lstrip("#").strip()
            if text[:2] and set(text[:2]) <= set("-=─━═"):
                break
            block.append(text)
            i -= 1
        out[stmt.target.id] = (" ".join(b for b in reversed(block) if b)
                               or trailing.get(stmt.lineno, ""))
    return out


def test_every_config_field_has_help():
    """Every `SpacecostConfig` dial carries a comment the dashboard can show.

    economicspace's Stage 3 config IS a `SpacecostConfig` instance, so its
    dashboard help is scraped from this file, and its docs harness fails on a
    dial with none.  A field added here without a comment would fail that
    consumer's checks rather than this package's.
    """
    fields = {f.name for f in dataclasses.fields(spacecost.SpacecostConfig)}
    helps = _field_help(spacecost.SpacecostConfig)
    assert set(helps) == fields
    bare = sorted(n for n, h in helps.items() if not h)
    assert not bare, "SpacecostConfig fields with no help comment: %s" % bare


def test_the_snapshot_field_the_consumer_sets_exists():
    """economicspace's Stage 3 pins a fuel snapshot by this field's name."""
    fields = {f.name for f in dataclasses.fields(spacecost.SpacecostConfig)}
    assert "quote_snapshot" in fields
