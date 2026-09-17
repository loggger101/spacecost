# -*- coding: utf-8 -*-
"""Destination environments: solar flux, dark period, gravity, light time.

NEW IN v1.15.0, and the first table not inherited from economicspace Module 3.

WHY IT EXISTS.  The other five tables price a kilogram; none of them knows
WHERE.  Three first-order cost drivers in this dataset are functions of
heliocentric distance alone, and until this table there was nowhere to read the
distance from:

  * `operational_costs` carries "Power system specific mass", 60 W/kg, and
    its unit string is careful to say AT 1 AU.  What it cannot say is what to
    do about it: flux falls as 1/r², so the same array is worth a seventh as
    much at the main belt.  `solar_array_mass_factor` is the multiplier that
    row has always needed and never had.
  * `storage_systems` carries "Eclipse / night-side power fraction" and
    `operational_costs` carries an energy-storage specific energy.  What sizes
    a battery is not the fraction, it is the DARK PERIOD in hours, and the two
    barely move together: 38% of a 93-minute LEO orbit is a 35-minute battery,
    50% of a lunar synodic day is a 354-hour one.  A third more of the cycle,
    604 times the stored energy, and not the same spacecraft.
    `dark_period_hr` is the number you multiply by watts.
  * `operational_costs` carries "Autonomous mining control & AI (NRE)", which
    is a line item that exists BECAUSE teleoperation stops working somewhere
    past a light-second.  `one_way_light_time_min` is where that somewhere is:
    1.3 s at the Moon, 22 minutes at Mars, 35 at the main belt.

WHAT IS DERIVED AND WHAT IS ASSERTED.  A row asserts the things a mission
measures — a distance, a mass, a radius, a rotation period, an illumination
fraction — and every column that follows from them is computed here rather than
typed in.  So a row cannot disagree with itself, which is the failure mode of
every hand-maintained table of derived quantities.

⚠️  EVERY DERIVATION USES ONLY IEEE-754 EXACT OPERATIONS: multiplication,
division and `sqrt`, all of which the standard requires to be correctly
rounded.  No `exp`, no `pow`, no `**0.25`.  That is deliberate and it is a
CONTRACT, not a style: it is what lets `environments.csv` join the other five
reference tables in the byte-identical-on-every-platform promise instead of
joining the summary in the few-ULP one.  `tests/test_parity.py` checks the
bytes on every CI platform.  If you add a column, add it in those operations or
state it as a literal; do not introduce a transcendental here.

⚠️  THE TABLE DOES NOT FLY A TRAJECTORY, and `au_mean` is a semi-major axis,
not where a body is on the day you ask.  `au_min` and `au_max` are the
perihelion and aphelion, so the flux at a real arrival date sits somewhere in
a band this table gives you the ends of.  For Didymos that band is a factor of
5 in available power.  Size for `au_max`.
"""

import math
from typing import List

from ._log import say
from .units import (AU_LIGHT_TIME_S, BLACKBODY_TEMP_1AU_K,
                    NEWTON_G_M3_PER_KG_S2, SOLAR_CONSTANT_W_PER_M2)

_REF_YEAR_ENV = 2026

# Earth's aphelion, in AU.  `max_earth_range_au` on a heliocentric row is the
# body's aphelion plus this: the two on opposite sides of the Sun, which is the
# conjunction geometry that sets the worst-case link budget and the longest
# command round trip.  Earth-bound rows state the orbital radius instead.
_EARTH_APHELION_AU = 1.0167


# ─────────────────────────────────────────────────────────────────────────────
# DERIVATIONS
# ─────────────────────────────────────────────────────────────────────────────
def solar_flux_w_per_m2(au: float) -> float:
    """Solar irradiance at `au`, W/m2.  `SOLAR_CONSTANT_W_PER_M2` / r²."""
    return SOLAR_CONSTANT_W_PER_M2 / (float(au) * float(au))


def solar_array_mass_factor(au: float) -> float:
    """Array area, and so array mass, per watt at `au`, relative to 1 AU.

    Exactly r², because flux is 1/r² and a panel's output is proportional to
    the flux on it.

    ⚠️  A LOWER BOUND on the penalty, and the error grows with distance.  Cells
    beyond ~3 AU also lose efficiency to low-intensity low-temperature effects
    that this does not model: Juno's arrays are 60 m2 for 486 W at Jupiter,
    which is worse than r² alone predicts.  Inside 1 AU the factor is below 1
    and the neglected term is thermal derating, which pushes the other way.
    """
    return float(au) * float(au)


def blackbody_temp_k(au: float) -> float:
    """Equilibrium temperature of a rapidly rotating black sphere at `au`, K.

    The spacecraft-thermal number, not a surface temperature: no albedo, no
    internal dissipation, no body underneath radiating at you.  A real surface
    runs hotter on the day side and colder at night than this.
    """
    return BLACKBODY_TEMP_1AU_K / math.sqrt(float(au))


def one_way_light_time_min(range_au: float) -> float:
    """One-way light time over `range_au`, in minutes.

    Double it for a command round trip.  Past about a light-second a human
    cannot close a control loop, which is the whole argument for the autonomy
    line in `operational_costs`.
    """
    return float(range_au) * (AU_LIGHT_TIME_S / 60.0)


def _surface_gravity(mass_kg, radius_m):
    """GM/r², m/s2.  None for a row that is an orbit rather than a body."""
    if mass_kg is None or radius_m is None:
        return None
    return NEWTON_G_M3_PER_KG_S2 * float(mass_kg) / (float(radius_m) * float(radius_m))


def _escape_velocity(mass_kg, radius_m):
    """sqrt(2GM/r), m/s.  Ignores rotation, which on a fast spinner is not a
    small correction: Didymos turns in 2.26 h and its equator sits within a few
    percent of the spin barrier, so the figure there is an upper bound on what
    leaving actually costs."""
    if mass_kg is None or radius_m is None:
        return None
    return math.sqrt(2.0 * NEWTON_G_M3_PER_KG_S2 * float(mass_kg) / float(radius_m))


def _env(name, kind, au_min, au_mean, au_max, cycle_period_hr, eclipse_fraction,
         max_earth_range_au, notes, mass_kg=None, mean_radius_m=None):
    """One environment row, with every derived column filled from the rest."""
    return {
        "name":                     name,
        "kind":                     kind,
        "au_min":                   au_min,
        "au_mean":                  au_mean,
        "au_max":                   au_max,
        "solar_flux_w_per_m2":      solar_flux_w_per_m2(au_mean),
        "solar_array_mass_factor":  solar_array_mass_factor(au_mean),
        "blackbody_temp_k":         blackbody_temp_k(au_mean),
        "cycle_period_hr":          cycle_period_hr,
        "eclipse_fraction":         eclipse_fraction,
        "dark_period_hr":           (None if cycle_period_hr is None
                                     else cycle_period_hr * eclipse_fraction),
        "mass_kg":                  mass_kg,
        "mean_radius_m":            mean_radius_m,
        "surface_gravity_m_per_s2": _surface_gravity(mass_kg, mean_radius_m),
        "escape_velocity_m_per_s":  _escape_velocity(mass_kg, mean_radius_m),
        "max_earth_range_au":       max_earth_range_au,
        "one_way_light_time_min":   one_way_light_time_min(max_earth_range_au),
        "reference_year":           _REF_YEAR_ENV,
        "notes":                    notes,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENVIRONMENT REFERENCE TABLE
# ─────────────────────────────────────────────────────────────────────────────
# `kind` is a closed vocabulary, the same discipline `status` gets on the launch
# and propellant tables, because a typo in a filter column removes a row from
# every filtered search silently:
#
#   earth_orbit      LEO, GEO.  Cycle period is the ORBIT period.
#   libration_point  Sun-Earth L1/L2.  No cycle; permanently lit.
#   cislunar         Lunar orbits and NRHO.
#   moon_surface     On a moon.  Cycle period is the rotation period.
#   planet_orbit     Around a planet.
#   planet_surface   On a planet.
#   neo              Near-Earth object, a < 1.3 AU-ish.
#   main_belt        2.0-3.5 AU.
#   trojan           Jupiter's L4/L5 swarms.
#
# ⚠️  `eclipse_fraction` is the fraction of the local cycle an asset spends in
# darkness, and on a BODY row that asset is on the surface.  A spacecraft
# station-keeping a few kilometres off Bennu is in sunlight continuously; a
# lander on it sees a 4.3-hour day and half of it dark.  The two size very
# different power systems and this column describes the second one.
#
# ⚠️  Rotation periods for the three generic rows (typical NEA, main belt
# inner/mean/outer, Trojans) are the ~6-10 h that the main-belt rotation
# distribution peaks at (Warner, Harris & Pravec, Asteroid Lightcurve Database).
# They are a population median, not a measurement, and an individual body can be
# anywhere from minutes to weeks.  Where the body is NAMED, the period is that
# body's measured one.

ENVIRONMENTS_REFERENCE: List[dict] = [
    # ═════════════════════════════════════════════════════════════════════════
    # Earth orbit and cislunar space
    # ═════════════════════════════════════════════════════════════════════════
    _env("Low Earth orbit (400 km)", "earth_orbit",
         0.9833, 1.0000, 1.0167, 1.545, 0.38, 0.000_002_674,
         "ISS-class orbit: 92.7-min period, up to ~36 min of it in Earth's "
         "shadow (NASA ISS Facts and Figures).  The most demanding eclipse "
         "DUTY CYCLE anywhere in this table - 16 charge/discharge cycles a day, "
         "5,800 a year - and the least demanding dark PERIOD.  Battery sizing "
         "reads the second, battery LIFE reads the first."),
    _env("Geostationary orbit", "earth_orbit",
         0.9833, 1.0000, 1.0167, 23.934, 0.012, 0.000_239_2,
         "Eclipses only near the equinoxes: two 45-day seasons, up to 72 min a "
         "day, so ~1.2% of the year averaged over it (ITU-R S.1003 / standard "
         "GEO mission practice).  Full sun the rest of the time, which is why "
         "GEO arrays are sized on end-of-life radiation damage rather than on "
         "eclipse."),
    _env("Sun-Earth L2", "libration_point",
         0.9933, 1.0100, 1.0267, None, 0.0, 0.010_03,
         "1.5 million km anti-sunward.  A halo orbit there is chosen so the "
         "spacecraft never enters Earth's umbra, which is why JWST and Gaia "
         "are there: continuous sun, continuous cold-side view, no thermal "
         "cycling at all.  Eclipse fraction is 0 by construction of the orbit, "
         "not by luck."),
    _env("Cislunar NRHO (Gateway)", "cislunar",
         0.9833, 1.0000, 1.0167, 157.4, 0.01, 0.002_57,
         "6.56-day near-rectilinear halo orbit (Whitley & Martinez 2016).  The "
         "orbit is selected for near-continuous illumination; eclipses are "
         "rare and under 90 minutes.  Cheap to hold, cheap to power - the same "
         "two properties that make it the cislunar depot orbit in "
         "DELTA_V_REFERENCE."),
    _env("Low lunar orbit (100 km)", "cislunar",
         0.9833, 1.0000, 1.0167, 1.965, 0.40, 0.002_57,
         "118-min period, ~40% of it behind the Moon.  Worse than LEO for both "
         "dark period and duty cycle, and unlike LEO there is no atmosphere "
         "below to drag a dead spacecraft down: LLO orbits are also unstable "
         "against lunar mascons and need station-keeping."),
    _env("Lunar surface (equatorial)", "moon_surface",
         0.9833, 1.0000, 1.0167, 708.7, 0.50, 0.002_57,
         "The 29.53-day synodic day, half of it night: a 354-HOUR dark period. "
         "At 100 W that is 35.4 kWh of storage, which at the 104 usable "
         "Wh/kg in OPERATIONAL_COSTS is 341 kg of battery to keep a 100 W load "
         "alive through one night.  This single row is the reason lunar surface "
         "power architectures reach for fission rather than for solar.  Mass "
         "7.342e22 kg, mean radius 1,737.4 km (NASA Moon Fact Sheet).",
         mass_kg=7.342e22, mean_radius_m=1_737_400.0),
    _env("Lunar surface (polar ridge)", "moon_surface",
         0.9833, 1.0000, 1.0167, 708.7, 0.14, 0.002_57,
         "A peak of near-eternal light on the Shackleton or de Gerlache rim: "
         "~86% illumination over a year, worst continuous darkness of a few "
         "days rather than a fortnight (LRO LOLA illumination modelling, "
         "Mazarico et al. 2011).  The reason every lunar south-pole "
         "architecture wants the same handful of ridges - and note that the "
         "ICE is in the crater below, permanently shadowed, so the power and "
         "the water are not in the same place.",
         mass_kg=7.342e22, mean_radius_m=1_737_400.0),

    # ═════════════════════════════════════════════════════════════════════════
    # Near-Earth objects.  All four named ones have had a spacecraft at them,
    # so their masses and radii are measured rather than inferred.
    # ═════════════════════════════════════════════════════════════════════════
    _env("Near-Earth asteroid (low-dv class)", "neo",
         1.0000, 1.2000, 1.5000, 8.0, 0.50, 2.5167,
         "The accessibility class DELTA_V_REFERENCE prices at 4,500 m/s: "
         "Earth-like orbit, low eccentricity, low inclination (Elvis et al. "
         "2011, arXiv:1105.4152).  Generic row - distance is the class, not a "
         "body, and the flux band between perihelion and aphelion is a factor "
         "of 2.25."),
    _env("101955 Bennu", "neo",
         0.8969, 1.1264, 1.3559, 4.296, 0.50, 2.3726,
         "OSIRIS-REx target, sampled 2020, 121.6 g returned to Utah in 2023 - "
         "the best-characterised carbonaceous asteroid there is, and the "
         "closest thing this dataset has to a validated mining site.  Mass "
         "7.329e10 kg, mean radius 244.5 m (Lauretta et al. 2019, Nature).  "
         "The derived 0.20 m/s escape velocity is the whole problem with "
         "operating there: a tossed pebble leaves.",
         mass_kg=7.329e10, mean_radius_m=244.5),
    _env("162173 Ryugu", "neo",
         0.9633, 1.1896, 1.4159, 7.633, 0.50, 2.4326,
         "Hayabusa2 target, sampled 2019, 5.4 g returned 2020.  Mass 4.50e11 "
         "kg, mean radius 448 m (Watanabe et al. 2019, Science).  A rubble "
         "pile like Bennu, and the two returned samples agreeing on hydrated "
         "carbonaceous composition is the empirical basis for asteroid water "
         "as a resource rather than an assumption.",
         mass_kg=4.50e11, mean_radius_m=448.0),
    _env("433 Eros", "neo",
         1.1334, 1.4583, 1.7832, 5.270, 0.50, 2.7999,
         "NEAR Shoemaker orbited it for a year and landed on it in 2001.  Mass "
         "6.687e15 kg, mean radius 8.42 km (Yeomans et al. 2000, Science).  "
         "Four orders of magnitude more massive than Bennu, and the derived "
         "10.3 m/s escape velocity is the difference between anchoring and "
         "merely parking - the largest S-type in easy reach.",
         mass_kg=6.687e15, mean_radius_m=8_420.0),
    _env("65803 Didymos", "neo",
         1.0128, 1.6443, 2.2758, 2.260, 0.50, 3.2925,
         "DART hit its moonlet Dimorphos in 2022 and moved it, and Hera "
         "arrives in 2026 to measure what that did.  Mass 5.28e11 kg, mean "
         "radius 390 m (Daly et al. 2023, Nature).  ⚠️  The 2.26-hour rotation "
         "puts its equator within a few percent of the spin barrier, so "
         "effective gravity there is near zero and the derived escape velocity "
         "is an upper bound.  A factor of 5 in flux between perihelion and "
         "aphelion, the widest band in this table.",
         mass_kg=5.28e11, mean_radius_m=390.0),

    # ═════════════════════════════════════════════════════════════════════════
    # Mars system
    # ═════════════════════════════════════════════════════════════════════════
    _env("Mars 1-sol staging orbit", "planet_orbit",
         1.3814, 1.5237, 1.6660, 24.62, 0.05, 2.6827,
         "The 250 x 33,793 km elliptical orbit NASA DRA 5.0 parks a Mars "
         "vehicle in, and the destination DELTA_V_REFERENCE prices at 4,500 "
         "m/s from LEO.  Most of the period is spent near apoapsis in "
         "sunlight, so the eclipse fraction is small and orientation-dependent; "
         "0.05 is representative rather than fixed."),
    _env("Mars surface (mid-latitude)", "planet_surface",
         1.3814, 1.5237, 1.6660, 24.66, 0.50, 2.6827,
         "The sol is 24.66 h, so the night is a manageable 12 - the one "
         "planetary surface in this table where solar power is routine.  "
         "⚠️  What this row does NOT carry is dust: a global storm cut "
         "Opportunity's array output by over 99% and ended the mission, and "
         "Mars surface flux at the panel runs 40-60% of the orbital figure "
         "even on a clear day (Appelbaum & Flood, NASA TM-102299).  Size for "
         "the storm, not for the geometry.  Mass 6.4171e23 kg, mean radius "
         "3,389.5 km (NASA Mars Fact Sheet).",
         mass_kg=6.4171e23, mean_radius_m=3_389_500.0),
    _env("Phobos", "moon_surface",
         1.3814, 1.5237, 1.6660, 7.653, 0.50, 2.6827,
         "Tidally locked, 7.65-h orbit and rotation.  Mass 1.0659e16 kg, mean "
         "radius 11.267 km (NASA Mars Fact Sheet / Willner et al. 2014).  The "
         "derived 11.2 m/s escape velocity and a Mars-orbit position make it "
         "the cheapest large mass in the Mars system to work from - the "
         "argument behind every Phobos-first mission architecture.",
         mass_kg=1.0659e16, mean_radius_m=11_267.0),

    # ═════════════════════════════════════════════════════════════════════════
    # Main belt.  Where the mass is, and where solar power stops being easy.
    # ═════════════════════════════════════════════════════════════════════════
    _env("Main belt, inner edge", "main_belt",
         2.0600, 2.2000, 2.5000, 8.0, 0.50, 3.5167,
         "The 3:1 Kirkwood gap at 2.5 AU is the outer bound of the inner belt. "
         "Array mass per watt is already 4.8x the 1 AU figure here."),
    _env("Main belt, mean", "main_belt",
         2.2000, 2.7000, 3.2000, 8.0, 0.50, 4.2167,
         "The 10,500 m/s destination in DELTA_V_REFERENCE, quoted at 2.7 AU. "
         "7.3x the array mass per watt of a 1 AU mission for the same "
         "electrical power, and a 35-minute one-way light time: the two "
         "numbers that make main-belt mining an autonomy problem before it is "
         "a propulsion problem."),
    _env("1 Ceres", "main_belt",
         2.5578, 2.7660, 2.9773, 9.074, 0.50, 3.9940,
         "Dawn orbited it 2015-2018.  Mass 9.3835e20 kg, mean radius 469.73 km "
         "(Russell et al. 2016, Science) - a third of the belt's entire mass "
         "in one object, water-rich, and with a 516 m/s escape velocity that "
         "makes it the only main-belt body in this table where leaving costs "
         "real propellant.",
         mass_kg=9.3835e20, mean_radius_m=469_730.0),
    _env("16 Psyche", "main_belt",
         2.5136, 2.9230, 3.3287, 4.196, 0.50, 4.3454,
         "The Psyche mission arrives 2029.  Mass 2.29e19 kg, mean radius ~111 "
         "km (Siltala & Granvik 2021).  Present because it is the body most "
         "often named as a metal resource; ⚠️  the '$10 quintillion' framing "
         "that follows it around is a spot price multiplied by a mass, which "
         "is not a market, and nothing in this dataset supports it.",
         mass_kg=2.29e19, mean_radius_m=111_000.0),
    _env("Main belt, outer edge", "main_belt",
         3.0000, 3.2000, 3.5000, 8.0, 0.50, 4.5167,
         "Past the 2:1 Kirkwood gap.  10.2x the array mass per watt of 1 AU, "
         "and blackbody equilibrium is down to 156 K - the distance at which "
         "solar electric propulsion stops being the obvious choice and nuclear "
         "electric starts to be."),
    _env("Jupiter Trojans (L4/L5)", "trojan",
         4.9000, 5.2044, 5.5000, 10.0, 0.50, 6.5167,
         "Lucy is touring them through 2033.  27x the array mass per watt of 1 "
         "AU, a 54-minute one-way light time, and 122 K.  Included as the "
         "boundary case: this is where 1/r² stops being a penalty you pay and "
         "becomes an architecture you change."),

    # ═════════════════════════════════════════════════════════════════════════
    # Inside 1 AU.  The factor runs the OTHER way here.
    # ═════════════════════════════════════════════════════════════════════════
    _env("Venus orbit", "planet_orbit",
         0.7184, 0.7233, 0.7282, 3.30, 0.40, 1.7449,
         "1.9x the flux of Earth orbit, so 0.52x the array mass per watt - the "
         "reason a solar-electric spacecraft gains, not loses, on an inner "
         "gravity-assist leg.  ⚠️  The array is smaller and the RADIATOR is "
         "bigger; this table gives the first and not the second."),
    _env("Mercury orbit", "planet_orbit",
         0.3075, 0.3871, 0.4667, 12.0, 0.15, 1.4834,
         "6.7x Earth's flux and a 0.15x array factor, which MESSENGER and "
         "BepiColombo both answer by pointing the arrays AWAY from the Sun: "
         "past about 3 solar constants the limit is cell temperature, not "
         "cell area, and this column stops describing the design.  The end of "
         "the range where 1/r² is the whole story."),
]

say("OK  Environment reference loaded - %d destinations"
    % len(ENVIRONMENTS_REFERENCE))
