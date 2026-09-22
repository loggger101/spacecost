# -*- coding: utf-8 -*-
"""What it costs to put a kilogram somewhere, and to bring one home.

NEW IN v0.3.0.  Moved from economicspace `modules/mineral_value.py` (Stage 2,
pipeline_version 1.9.0), where it had been since v1.2.0.

WHY IT MOVED.  That block opened by saying what it was:

    Constants below are cross-referenced to Module 3.  They are duplicated
    rather than imported because Module 2 runs BEFORE Module 3 in the pipeline
    order (and in the concatenated master.py), so the tables are not in scope.
    If you change one of these, change it in Module 3 too.

Every Δv in it was a row of `DELTA_V_REFERENCE` retyped by hand, the launch
price was a `LAUNCH_VEHICLES_REFERENCE` row, and three of the downleg cost
lines were `OPERATIONAL_COSTS_REFERENCE` rows.  A manual-sync instruction over
nine duplicated numbers.

The justification died when Stage 3 became this package.  A pip-installed
package has no position in a pipeline: economicspace's `master.py` installs it
in its header, before any stage's code runs, so Module 2 can import it exactly
as Module 4 does.  The reason for the second copy was concatenation order, and
concatenation order stopped applying.

Nothing here knows what an asteroid is.  "Cost of putting 1 kg of payload at
`destination`, launched from Earth" is this package's own scope sentence.

WHAT IS DERIVED AND WHAT IS TYPED, WHICH IS THE PART TO READ.  Every Δv in
`DELIVERY_CHAINS` is looked up in `DELTA_V_REFERENCE` by segment name, so the
table is the single authority and a row that moves moves the chain with it.
`DOWNLEG_DEPARTURE_DV_M_S` is NOT, and that is deliberate rather than lazy:
two of its six values have no row at all and a third disagrees with its row by
2 m/s.  Snapping those to the table would change published numbers that nobody
has re-measured, so they stay as literals and the mismatch is written down in
the comment above them.  Deriving what agrees and typing what does not is the
honest split; quietly deriving all six would have moved a price.

⚠️  THIS MODULE IS NOT A SEVENTH REFERENCE TABLE, and must not become one
casually.  `build_catalog()` writes the same seven CSVs it wrote at v0.2.0 and
the data contract stays at 1.15.0, which is why this release needs no
regenerated `reference/` and no re-run of the consumer's Stage 3.  Adding a
CSV here would move `pipeline_version`, restamp every output, and oblige
economicspace to re-run a stage that re-fetches live prices — the one operation
its own notes call unrecoverable.  This is a DERIVATION over the tables, like
`rocket.py` and `query.py`, not data.

⚠️  `math.exp`, NOT `np.exp`, AND THAT IS LOAD-BEARING.  `rocket.py` is the
vectorised entry point and this is the scalar one, and they are not
interchangeable here: the consumer's releases are argued from bit-identity, and
the two libraries are free to round the last bit differently.  The exponential
below is the one economicspace has been running since its v1.2.0.  Do not
"unify" this with `propellant_mass_for_dv`.
"""

import math
from typing import Dict, List, Optional, Tuple

from ._log import say
from .deltav import DELTA_V_REFERENCE
from .operations import OPERATIONAL_COSTS_REFERENCE
from .units import G0_M_S2
from .vehicles import LAUNCH_VEHICLES_REFERENCE


# ─────────────────────────────────────────────────────────────────────────────
# READING THE TABLES
# ─────────────────────────────────────────────────────────────────────────────
# Three lookups, each of which raises at IMPORT if the row it names has gone.
# That is the house pattern: a renamed row should fail the import of anything
# that depends on it, loudly and next to the name, rather than fall through a
# `.get(..., default)` into a plausible wrong number.

_DV_BY_SEGMENT: Dict[str, int] = {r["segment"]: r["dv_m_per_s"]
                                  for r in DELTA_V_REFERENCE}


def _dv(segment: str) -> float:
    """The Δv of one named `DELTA_V_REFERENCE` segment, m/s.

    Returns a float even though the table stores ints, because the chains are
    built of floats and a chain that silently produced an int would change the
    dtype of a consumer's output column.
    """
    if segment not in _DV_BY_SEGMENT:
        raise KeyError(
            "delivery.py needs the delta-v segment %r and DELTA_V_REFERENCE no "
            "longer has it.  A renamed segment is a breaking change for the "
            "delivery chains: fix the name here in the same commit."
            % (segment,))
    return float(_DV_BY_SEGMENT[segment])


def _ops(category: str) -> float:
    """One named `OPERATIONAL_COSTS_REFERENCE` value."""
    for row in OPERATIONAL_COSTS_REFERENCE:
        if row["category"] == category:
            return float(row["value"])
    raise KeyError(
        "delivery.py needs the operational row %r and it is gone." % (category,))


def _vehicle_usd_per_kg_to_leo(name: str) -> float:
    """One named `LAUNCH_VEHICLES_REFERENCE` launch price."""
    for row in LAUNCH_VEHICLES_REFERENCE:
        if row["name"] == name:
            return float(row["usd_per_kg_to_leo"])
    raise KeyError(
        "delivery.py needs the launch vehicle %r and it is gone." % (name,))


# ─────────────────────────────────────────────────────────────────────────────
# THE STAGES THAT WOULD HAVE CARRIED IT
# ─────────────────────────────────────────────────────────────────────────────
# Falcon 9 reusable $/kg-to-LEO, the cheapest operational figure in
# LAUNCH_VEHICLES_REFERENCE, so every price derived from it is a LOWER bound on
# the launch cost avoided.
LEO_LAUNCH_USD_PER_KG = _vehicle_usd_per_kg_to_leo("Falcon 9 (reusable)")

# Isp 465 s = hydrolox upper stage (PROPELLANTS_REFERENCE: LH2/LOX, 450-465 s
# vacuum).  Dry-mass fraction 0.10 is mid-range for a cryogenic upper stage
# (Centaur V ~0.08, DCSS ~0.11), stage dry mass / (dry + propellant).
TUG_ISP_S          = 465.0
TUG_DRY_MASS_FRAC  = 0.10
# A LANDER is structurally much heavier than a tug for the same propellant
# load: throttleable engines, landing legs, terminal-guidance sensors.
# Apollo LM descent stage flew 2,134 kg dry on 8,200 kg of propellant = 0.21.
LANDER_DRY_MASS_FRAC = 0.20

# Fraction of Mars ENTRY mass that survives to be useful payload on the
# surface.  Aeroshell, backshell, parachute and descent stage are all
# discarded.  Measured, not assumed:
#     MSL           entry 3,257 kg  ->  rover   899 kg  = 27.6%
#     Perseverance  entry 3,440 kg  ->  rover 1,025 kg  = 29.8%
# 0.30 takes the better of the two and is generous to Mars; larger entry
# vehicles should scale better than MSL's sky-crane, but nothing that size
# has flown.
MARS_LANDED_MASS_FRACTION = 0.30


# ─────────────────────────────────────────────────────────────────────────────
# DELIVERY LEG CHAINS
# ─────────────────────────────────────────────────────────────────────────────
# Each destination is a SEQUENCE of legs above LEO, flown by real stages, and
# the mass ratios chain.  Modelling it leg-by-leg rather than as one big Δv
# matters: staging is worth a great deal, and a single-stage lunar lander
# burning 5,920 m/s would come out roughly twice as expensive as the two-stage
# chain that would actually be flown (10.96 against 4.99 kg in LEO per kg
# landed).
#
#   ("burn", Δv m/s, Isp s, dry fraction)  - a propulsive leg
#   ("edl",  surviving mass fraction)      - atmospheric entry, descent, landing
#
# 🚨  `None` AND `[]` ARE DIFFERENT AND THE DIFFERENCE IS LOAD-BEARING.
# `earth_surface` maps to None: there is no chain because the material is
# already at the market and no launch is avoided, so its delivered cost is
# 0 $/kg.  `leo` maps to []: the chain is EMPTY because nothing sits above LEO,
# and its delivered cost is the whole LEO launch price.  A truthiness test
# (`if legs:`) reads them as the same thing and prices LEO at zero.  That is
# not hypothetical — it is exactly the defect economicspace's own
# `worked_calculation.py` shipped and had to fix.  Test `is None`.
DELIVERY_CHAINS: Dict[str, Optional[List[tuple]]] = {
    "earth_surface": None,                       # already at the market
    "leo": [],                                   # nothing above LEO
    # Two stages, because that is how a GEO delivery is actually flown: an
    # upper stage to GTO, then an apogee burn that circularises AND removes the
    # 28.5 deg parking inclination in one go.  Staging is worth 5.3% here
    # (2.945 kg in LEO per kg against 3.101), which is smaller than the lunar
    # chain's 2x but is the same argument.
    "geo": [
        ("burn", _dv("LEO  →  GTO (perigee burn)"),
         TUG_ISP_S, TUG_DRY_MASS_FRAC),                          # LEO -> GTO
        ("burn", _dv("GTO  →  GEO (circularise + plane change)"),
         TUG_ISP_S, TUG_DRY_MASS_FRAC),                          # + plane change
    ],
    "cislunar": [
        ("burn", _dv("LEO  →  cislunar NRHO depot"),
         TUG_ISP_S, TUG_DRY_MASS_FRAC),                          # TLI + NRHO insertion
    ],
    "lunar_surface": [
        # TLI + LOI, as two rows rather than the table's own "LEO -> lunar
        # surface" 5,920, because that composite is the thing this chain exists
        # to beat: it is the single-stage figure, and staging halves it.
        ("burn", _dv("LEO  →  TLI (trans-lunar injection)")
               + _dv("TLI  →  low lunar orbit (LOI)"),
         TUG_ISP_S, TUG_DRY_MASS_FRAC),
        ("burn", _dv("LLO  →  lunar surface (descent)"),
         TUG_ISP_S, LANDER_DRY_MASS_FRAC),                       # powered descent
    ],
    # The 1-sol elliptical staging orbit (250 x 33,793 km).  Capture BINDS the
    # orbit instead of circularising it, so MOI is 900 m/s where a 200-km orbit
    # costs 2,100 at the same arrival energy; the same trade NRHO wins on at the
    # Moon.  Nothing lands, so there is no `edl` leg and no survival fraction.
    "mars_orbit": [
        ("burn", _dv("LEO  →  trans-Mars injection"),
         TUG_ISP_S, TUG_DRY_MASS_FRAC),                          # TMI
        ("burn", _dv("Mars arrival  →  1-sol orbit (MOI)"),
         TUG_ISP_S, TUG_DRY_MASS_FRAC),                          # 1-sol capture
    ],
    "mars_surface": [
        ("burn", _dv("LEO  →  trans-Mars injection"),
         TUG_ISP_S, TUG_DRY_MASS_FRAC),                          # TMI
        ("edl",  MARS_LANDED_MASS_FRACTION),                     # aeroentry + landing
        ("burn", _dv("Mars entry  →  surface (retroprop)"),
         TUG_ISP_S, LANDER_DRY_MASS_FRAC),                       # retropropulsion
    ],
}

# The Δv every chain leg carries, asserted against what this module was moved
# with.  Deriving from a table is only an improvement while the derivation
# still lands on the numbers the consumer's published results were computed
# from; this is the line that says so, and it fails at import rather than at a
# price three steps later.
_CHAIN_DV_AT_MOVE: Dict[str, Tuple[float, ...]] = {
    "earth_surface": (),
    "leo":           (),
    "geo":           (2_455.0, 1_836.0),
    "cislunar":      (3_600.0,),
    "lunar_surface": (4_050.0, 1_870.0),
    "mars_orbit":    (3_600.0, 900.0),
    "mars_surface":  (3_600.0, 800.0),
}
for _dest, _expected in _CHAIN_DV_AT_MOVE.items():
    _legs = DELIVERY_CHAINS[_dest]
    _got = tuple(l[1] for l in (_legs or []) if l[0] == "burn")
    if _got != _expected:
        raise AssertionError(
            "DELIVERY_CHAINS[%r] now burns %s where the move recorded %s.  A "
            "delta-v row has moved under it.  That is allowed, but it changes "
            "every in-space price downstream, so update _CHAIN_DV_AT_MOVE "
            "deliberately and tell economicspace." % (_dest, _got, _expected))


# ─────────────────────────────────────────────────────────────────────────────
# DOWNLEG: FROM A DEPOT TO THE TERRESTRIAL MARKET
# ─────────────────────────────────────────────────────────────────────────────
# A commodity with no in-space demand is not worthless at a depot; it is worth
# its Earth price MINUS whatever it costs to fly it the rest of the way down.
# Coming down is far cheaper than going up: you need a heat shield, not a
# launch vehicle, which is why these are a fraction of the figures above.
DOWNLEG_CAPSULE_DRY_FRAC   = 0.10   # capsule dry mass per kg of cargo
# Mirrors economicspace's Module 4 config dial `heat_shield_frac_of_payload`.
# Typed rather than read, because it is a modelling choice belonging to that
# pipeline and there is no TPS-fraction row in these tables to derive it from.
DOWNLEG_TPS_FRAC           = 0.15
DOWNLEG_CAPSULE_USD_PER_KG = _ops("Return capsule recurring cost")
DOWNLEG_TPS_USD_PER_KG     = _ops("Heat shield / TPS for Earth return")
DOWNLEG_RECOVERY_USD       = _ops("Sample recovery operations")
DOWNLEG_BATCH_KG           = 10_000.0   # nominal batch the recovery is spread over

# 🚨  TYPED, NOT DERIVED, AND THE TABLE BELOW IS WHY.  Four of these six agree
# with a `DELTA_V_REFERENCE` row exactly and two do not, so a uniform lookup
# would silently move two published prices:
#
#   destination      value    the row                                  agrees?
#   leo                120    (no row: a LEO deorbit burn is not tabulated)
#   geo              1,490    "GEO -> Earth (deorbit to entry)"  1,488   NO, 2 m/s
#   cislunar           450    "TLI -> NRHO insertion"              450   yes, symmetric
#   lunar_surface    2,720    1,870 ascent (symmetric with the descent
#                             row) + ~850 TEI, which has no row
#   mars_orbit         900    "1-sol Mars orbit -> Earth (TEI)"     900   yes
#   mars_surface     6,200    "Mars surface -> low Mars orbit" 4,100 +
#                             "Low Mars orbit -> Earth (TEI)"  2,100     yes, sum
#
# The two that disagree are hand figures that predate the rows; reconciling
# them is a real question and a separate release, because it changes what a
# kilogram of platinum is worth at GEO and in LEO.  Do not fix it here on the
# way past.
#
# The surface cases are punishing, and correctly so: hauling material back UP
# out of a gravity well you just landed in is close to the worst thing you can
# do with it.
DOWNLEG_DEPARTURE_DV_M_S: Dict[str, float] = {
    "leo":            120.0,
    "geo":          1_490.0,
    "cislunar":       450.0,
    "lunar_surface": 2_720.0,
    "mars_orbit":      900.0,
    "mars_surface":  6_200.0,
}


# ─────────────────────────────────────────────────────────────────────────────
# THE ARITHMETIC
# ─────────────────────────────────────────────────────────────────────────────

def stage_mass_ratio(dv_m_s: float, isp_s: float, dry_mass_frac: float) -> float:
    """Initial mass needed per kg of payload for one propulsive leg.

        R  = exp(Δv / (Isp·g0))                        rocket equation
        p  = (R − 1)(1 + d)                            propellant per kg payload
        δ  = d / (d + p)   ⇒   d = δ(R−1) / (1 − δR)   stage dry mass
        m0 = R (1 + d)                                 total mass to start with

    Returns inf when δ·R ≥ 1; the tank cannot close on that Δv and no amount
    of propellant will fix it.  That is the same condition `propellants.py`
    hits on its own tankage term, and it is a feasibility statement rather than
    an expensive answer.
    """
    if dv_m_s <= 0:
        return 1.0
    r = math.exp(float(dv_m_s) / (isp_s * G0_M_S2))
    if dry_mass_frac * r >= 1.0:
        return float("inf")
    d = dry_mass_frac * (r - 1.0) / (1.0 - dry_mass_frac * r)
    return r * (1.0 + d)


def delivery_mass_ratio(destination: str) -> float:
    """Kilograms that must reach LEO per kilogram delivered to `destination`.

    Walk the chain BACKWARDS from the payload, multiplying up the mass each leg
    demands.  An `edl` leg divides rather than multiplies: surviving 30% of
    entry mass means you must arrive with 1/0.30 = 3.33 kg for every kg that
    lands.

    1.0 at `leo`, which has an empty chain; 0.0 at `earth_surface`, which has
    no chain at all.  `inf` where a tank cannot close.
    """
    legs = DELIVERY_CHAINS.get(str(destination or "").strip().lower())
    if legs is None:
        return 0.0                       # earth_surface avoids no launch at all

    mass = 1.0                           # kg that must exist at the start of the chain
    for leg in reversed(legs):
        if leg[0] == "edl":
            frac = float(leg[1])
            mass = mass / frac if frac > 0 else float("inf")
        else:
            _, dv, isp, dry = leg
            mass *= stage_mass_ratio(dv, isp, dry)
        if not math.isfinite(mass):
            return float("inf")
    return mass


def delivered_cost_usd_per_kg(
    destination:    str,
    leo_usd_per_kg: float = LEO_LAUNCH_USD_PER_KG,
) -> float:
    """Cost of putting 1 kg of payload at `destination`, launched from Earth.

    This is the "launch cost avoided" that gives material already in space its
    value.  Derived, not tabulated: the leg chain's mass ratio, charged at the
    LEO launch price.

    Unknown destinations return 0.0 rather than raising, which is the
    behaviour its consumer has always had: a destination with no chain avoids
    no launch.
    """
    mass = delivery_mass_ratio(destination)
    if not math.isfinite(mass):
        return float("inf")
    return float(leo_usd_per_kg) * mass


def downleg_cost_usd_per_kg(destination: str) -> float:
    """Cost of moving 1 kg from an in-space depot to the terrestrial market.

    Capsule + TPS + a share of the recovery campaign, all scaled by the mass
    ratio of the departure burn, because that propellant is extra mass that has
    to be built and flown.

    Returns 0.0 for `earth_surface` and for anything unrecognised; the material
    is already there.
    """
    key = str(destination or "").strip().lower()
    if key not in DOWNLEG_DEPARTURE_DV_M_S:
        return 0.0
    capsule_kg = DOWNLEG_CAPSULE_DRY_FRAC
    tps_kg     = DOWNLEG_TPS_FRAC * (1.0 + capsule_kg)
    hardware   = (capsule_kg * DOWNLEG_CAPSULE_USD_PER_KG
                  + tps_kg * DOWNLEG_TPS_USD_PER_KG)
    recovery   = DOWNLEG_RECOVERY_USD / DOWNLEG_BATCH_KG
    # Departure burn shows up as extra mass to be built and flown.
    r = math.exp(DOWNLEG_DEPARTURE_DV_M_S[key] / (TUG_ISP_S * G0_M_S2))
    return (hardware + recovery) * r


say("OK  Delivery chains loaded - %d destinations, %d with a downleg"
    % (len(DELIVERY_CHAINS), len(DOWNLEG_DEPARTURE_DV_M_S)))
