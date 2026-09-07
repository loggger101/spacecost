# -*- coding: utf-8 -*-
"""Configuration for a catalog build.

Adapted from `TransportConfig` in economicspace modules/transportation.py,
pipeline_version 1.14.0, commit b0b18b2de301653ee23de1bd3779867ae5b617a1.

Three things changed on the way out of that repo, and nothing else:

  * the output directory defaults to `./spacecost_data` and reads
    `SPACECOST_OUTPUT_DIR`, where the original hard-coded a Colab path and
    read `ASTEROID_PIPELINE_OUTPUT_DIR`,
  * the module no longer creates that directory at import time, because a
    library that makes a folder when you import it for one constant is a
    library that has a side effect,
  * the module no longer prints its configuration at import time.

TWO VERSION NUMBERS LIVE HERE AND THEY MEAN DIFFERENT THINGS.  Do not
conflate them:

    `pipeline_version`     the DATA contract.  It is stamped into every
                           output CSV and is the only way to tell which
                           tables produced a given file.  It tracks the
                           reference rows, and it is the number a consumer
                           pins against.
    `spacecost.__version__`  the PACKAGE release.  It moves for a bug fix in
                           the loader, a new helper, a docs pass -- changes
                           that alter no row and no output byte.

A package release can leave `pipeline_version` alone.  A change to any row
must move `pipeline_version`, and that rule is one-directional: moving it is
not evidence that a number changed.  See CHANGELOG.md.
"""

import os
from dataclasses import dataclass


def _default_output_dir() -> str:
    """Where a build writes, unless the caller says otherwise.

    `SPACECOST_OUTPUT_DIR` wins when set.  Otherwise `./spacecost_data` under
    the current working directory -- a relative default, deliberately, because
    an absolute one is wrong on every machine but the author's.
    """
    env = os.environ.get("SPACECOST_OUTPUT_DIR")
    if env:
        return env
    return os.path.join(os.getcwd(), "spacecost_data")


@dataclass
class SpacecostConfig:
    """User-editable configuration for the transportation-cost catalog."""

    # --- SOURCE TOGGLES ------------------------------------------------------
    # `use_yfinance` fetches live commodity quotes as proxies for the three
    # liquid propellants that have a traded analogue (RP-1 via heating oil,
    # methane via natural gas, with WTI crude as a cross-check).  Turn it OFF
    # for a deterministic, offline, reproducible build: every propellant then
    # takes its reference price and `price_basis` reads "reference" on all 41
    # rows.  That is the setting the parity test runs under.
    use_yfinance:        bool = False
    use_reference_table: bool = True   # curated launch / propellant / dv / ops

    # --- NETWORK -------------------------------------------------------------
    request_timeout: int = 60   # seconds per HTTP call; a timeout is a soft failure

    # --- OUTPUT --------------------------------------------------------------
    output_dir:       str = ""   # "" means _default_output_dir() at build time
    # Five reference files land in `<output_dir>/<subdir>/`:
    #     launch_vehicles.csv, propellants.csv, delta_v_segments.csv,
    #     operational_costs.csv, storage_systems.csv
    # plus one composite summary file (vehicle x segment x propellant):
    #     transportation_summary.csv
    subdir:           str = "transportation"

    # --- UNIT INVARIANT ------------------------------------------------------
    # All monetary values are USD.  All physical quantities are SI (kg, m, s,
    # m/s).  Volumes are in litres rather than cubic metres, because that is
    # how propellant tanks are quoted in the trade.  The invariant is carried
    # by each output column's own name (`_usd_per_kg`, `_m_per_s`, ...) and
    # checked by validate(), not by config fields: CURRENCY / MASS_UNIT /
    # DV_UNIT / TIME_UNIT constants used to live here and nothing ever read
    # them, so they documented an invariant they did not enforce.

    # --- IN-SITU PROPELLANT --------------------------------------------------
    # If True, the return-leg propellant is assumed to be manufactured at the
    # destination rather than launched; its $/kg drops to the on-site
    # processing cost below.  Default False = conservative (haul fuel both
    # ways).  Read only by `mission_cost_breakdown`.
    isru_return_propellant:        bool  = False
    isru_processing_usd_per_kg:    float = 50.0   # rough lit estimate

    # --- CONTINGENCY ---------------------------------------------------------
    # Industry-standard mission-cost contingency.  20% is typical for a
    # well-characterised flight programme; 35-50% for first-of-kind.
    contingency_fraction: float = 0.20

    # --- DATA CONTRACT VERSION -----------------------------------------------
    # Stamped into every output CSV.  BUMP IT when a change moves any number a
    # build produces.  See this module's docstring for why it is not the same
    # thing as `spacecost.__version__`, and CHANGELOG.md for what moved when.
    pipeline_version: str = "1.14.0"
    preview_rows:     int = 15   # rows per table in the CLI preview

    def resolved_output_dir(self) -> str:
        """`output_dir`, or the environment/CWD default when it is blank."""
        return self.output_dir or _default_output_dir()

    def table_dir(self) -> str:
        """The directory the six CSVs are written into."""
        return os.path.join(self.resolved_output_dir(), self.subdir)


CONFIG = SpacecostConfig()
