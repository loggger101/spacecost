# -*- coding: utf-8 -*-
"""spacecost: a cited reference dataset for space-mission cost and mass estimation.

Every cost that sits between "payload on the ground" and "payload delivered":

    Launch  +  Transit propellant  +  Operations  +  Return  +  Contingency

Five tables, every row carrying an inline citation and a `reference_year`:

    36 launch vehicles      $/kg to LEO, GTO and escape, payload, status
    41 propellant systems   vacuum Isp, bulk density, $/kg, storage class,
                            derived tankage, and the thruster device
    33 delta-v segments     m/s and trip duration per trajectory leg
    44 operational costs    $/mission-year and $/kg-payload lines
    20 storage systems      the domains a kilogram can be held in

Each is normalised to a unit the others compose with, which is the whole point
of collecting them together rather than separately:

    Launch        ->  USD per kg of payload to destination
    Propellant    ->  USD per kg, USD per L, AND USD per (kg-delta-v), which is
                      the rocket equivalent of "fuel cost per km"
    Mission dv    ->  m/s and trip duration (yr) per trajectory leg
    Operational   ->  USD per mission-year and USD per kg-payload

THE OPERATIONAL TABLE ASSUMES AN UNCREWED SPACECRAFT.  No life support, no
habitat, no crew operations, no return-vehicle uplift for people.  The
"Autonomous mining control & AI (NRE)" line is what that design pays instead.
If you are costing a crewed mission the launch, propellant, delta-v and storage
tables still apply and this one does not.

Quick start:

    >>> import spacecost
    >>> v = spacecost.load_launch_vehicles()
    >>> v.sort_values("usd_per_kg_to_leo")[["name", "usd_per_kg_to_leo"]].head(3)

    >>> spacecost.cost_per_dv_usd_per_kg(               # $/kg of payload
    ...     propellant_cost_usd_per_kg=20.0, isp_s=452, delta_v_m_per_s=6500)

    >>> catalog = spacecost.build_catalog()             # all six CSVs

PROVENANCE.  Extracted from Module 3 of `economicspace`, the asteroid-mining
profitability pipeline, at pipeline_version 1.14.0 (commit b0b18b2).  The
tables were built there over fourteen releases; they are split out because
nothing in their schema knows what an asteroid is, and a launch price is
useful to anyone costing a mission.  economicspace consumes this package as
its Stage 3.

THE OUTPUT IS A CONTRACT.  `build_catalog()` reproduces the six CSVs that
repo's Stage 4 reads, byte for byte, and `tests/test_parity.py` is that claim
as a test.  Two details of the writer are load-bearing and must not be tidied:
the CRLF line terminator is PINNED (`lineterminator="\r\n"`) because the
committed hashes are hashes of CRLF, and column order is the file's order.
"""

from ._log import is_verbose, say, set_verbose
from .build import build_catalog
from .config import CONFIG, SpacecostConfig
from .deltav import DELTA_V_REFERENCE
from .operations import OPERATIONAL_COSTS_REFERENCE
from .propellants import PROPELLANTS_REFERENCE
from .query import (cheapest_launch_to, cheapest_propellant_for,
                    mission_cost_breakdown)
from .rocket import cost_per_dv_usd_per_kg, propellant_mass_for_dv
from .storage import STORAGE_REFERENCE
from .tables import (build_transportation_summary, load_delta_v,
                     load_launch_vehicles, load_operational_costs,
                     load_propellants, load_storage)
from .units import (COMMODITY_DENSITY_KG_PER_L, G0_M_S2, LITRES_PER_BBL,
                    LITRES_PER_GAL)
from .validate import validate, validate_tables
from .vehicles import LAUNCH_VEHICLES_REFERENCE

# The PACKAGE release. Not the data contract -- that is
# `SpacecostConfig.pipeline_version`, which is stamped into every CSV. See
# spacecost/config.py for why the two are deliberately separate.
__version__ = "0.1.1"

# The DATA contract this release ships, repeated here for convenience only.
# config.py is the authority; this is a mirror, and a mirror can drift, so
# tests/test_parity.py asserts the two agree.
DATA_VERSION = CONFIG.pipeline_version

# Migration aliases. The two names this package changed on the way out of
# economicspace, kept importable so a call site moving over does not have to be
# rewritten to be tried. `build_transportation_catalog` is aliased in build.py
# for the same reason.
TransportConfig = SpacecostConfig
build_transportation_catalog = build_catalog

__all__ = [
    "__version__", "DATA_VERSION",
    "CONFIG", "SpacecostConfig",
    "TransportConfig", "build_transportation_catalog",
    "LAUNCH_VEHICLES_REFERENCE", "PROPELLANTS_REFERENCE",
    "DELTA_V_REFERENCE", "OPERATIONAL_COSTS_REFERENCE", "STORAGE_REFERENCE",
    "load_launch_vehicles", "load_propellants", "load_delta_v",
    "load_operational_costs", "load_storage",
    "build_transportation_summary", "build_catalog", "validate",
    "validate_tables",
    "propellant_mass_for_dv", "cost_per_dv_usd_per_kg",
    "cheapest_launch_to", "cheapest_propellant_for", "mission_cost_breakdown",
    "G0_M_S2", "LITRES_PER_GAL", "LITRES_PER_BBL",
    "COMMODITY_DENSITY_KG_PER_L",
    "say", "set_verbose", "is_verbose",
]
