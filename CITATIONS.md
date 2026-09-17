# Citations, sources and attribution

## What this file is, and what it is not

This is the bibliography and the licence position. It is **not** a second copy
of any number.

A launch price, a propellant density, a delta-v figure or an operational cost
is cited on the row that carries it, in the `notes` field, inside
`spacecost/*.py`. **That row stays the authority for its own number.** Restating
a value here would create two copies of one measurement, and two copies of one
measurement is a defect waiting to happen: one of them gets updated.

Each row also carries a `reference_year`, which is what makes staleness visible
without anyone having to remember when a table was last touched.

## Licence position

**No source behind these tables imposes a condition of use.** They are public
filings, government reports, published handbooks and traded commodity prices.
Prices, densities and delta-v figures are facts, and facts are not
copyrightable; the compilation, the derivations and the prose in the `notes`
fields are this project's own work, released under MIT.

⚠️  The upstream project this was extracted from, `economicspace`, does carry
three sources that require citation as a condition of use: IMCCE SsODNet /
ssoBFT, NEOWISE Diameters and Albedos V2.0, and the SDSS-based Asteroid Taxonomy
V1.1. **All three are asteroid catalog sources and none of them feeds any table
here.** If you are vendoring from that project rather than this one, read its
`CITATIONS.md` instead.

## 1. Launch vehicles

Pricing and payload figures, verified May 2026:

| source | what it establishes |
|---|---|
| SatBase 2026-02 SpaceX price update | Falcon 9 and Falcon Heavy list prices |
| SpaceX / Voyager Technologies contract, 2026 | Starship dedicated-launch price |
| NASA Office of Inspector General, IG-24-015 | SLS per-flight cost |
| ULA RocketBuilder, and SpaceNews 2024-2026 | Atlas V and Vulcan Centaur pricing |
| Blue Origin and Geekwire, April 2026 | New Glenn list price and payload |
| Rocket Lab Form 10-Q, FY2026 Q1 | Electron pricing |
| TASS / Glavkosmos 2018, escalated | Soyuz-2.1b pricing |
| Wikipedia (Vulcan, New Glenn, Ariane 6, H3) | payload masses, cross-checked |

Non-rocket concepts (mass drivers, launch loops, tethers, light-gas guns) are
cited individually in their own rows and are marked `concept`. They are included
so a study can state what it excluded.

## 2. Propellants and propulsion

| source | what it establishes |
|---|---|
| DOD Aerospace Standard Prices, FY20 | hydrazine, MMH, N2O4 pricing |
| SETS Space / Electric Propulsion, 2024 | xenon and argon ion pricing |
| Mobius / Energy CG, 2024 | liquid methane commodity pricing |
| NASA-STD-(I)-5019 class hardware | COPV burst performance factor, ~392 kJ/kg |
| Shuttle External Tank, Falcon 9 second stage, Centaur III | the flight anchors the tankage model is calibrated on |
| Manufacturer data sheets, per device | thruster kg/N, efficiency, thrust scaling |

Vacuum Isp values are the interplanetary-relevant figures. Sea-level Isp is
lower and matters only to a first stage, which is already priced into the launch
table's $/kg-to-orbit.

## 3. Delta-v segments

| source | what it establishes |
|---|---|
| NASA SP-125, and Curtis, *Orbital Mechanics for Engineering Students* | ascent and textbook segment values |
| Taylor et al. 2018, "Delta-v map of Main Belt Asteroids" | LEO to main-belt transfer |
| arXiv 1105.4152, arXiv 1406.5027 | near-Earth object delta-v accessibility distribution |
| NASA NTRS and JPL design handbooks | the remaining trajectory legs |

⚠️  These are **representative means**, not a trajectory. A real transfer needs a
Lambert solve against an ephemeris; these are what you price the answer with.

## 4. Operational costs

| source | what it establishes |
|---|---|
| NASA DSN Services Catalog 820-100-H | deep space network aperture fees, FY09 base |
| NASA / Planetary Society, and Wikipedia | OSIRIS-REx mission total cost |
| Plane Talking / Slingshot Aerospace, 2024 | launch insurance market rate |
| Damodaran (NYU Stern), Boeing and Howmet filings | cost-of-capital benchmark |
| NASA Mars 2020 / Perseverance autonomy programme | autonomous control development cost |

The mission profile these are costed against is **uncrewed and fully
autonomous**: no life support, no habitat, no crew operations. The autonomy
development line is what that design pays in exchange.

## 5. Destination environments

The `environments` table is the one place here where most columns are
**derived** rather than cited, so what a source establishes is an INPUT — a
distance, a mass, a radius, a rotation period, an illumination fraction — and
the flux, the array factor, the temperature, the gravity, the escape velocity
and the light time all follow from those by formula. The formulas are in
`spacecost/environments.py`; the inputs are cited on their rows.

**Physical constants**

| source | what it establishes |
|---|---|
| Kopp & Lean 2011, *GRL* 38 L01706 | total solar irradiance at 1 AU, 1361 W/m² — revised down from the long-quoted 1366, instrumentally |
| CODATA 2018 | the Newtonian constant of gravitation |
| BIPM / IAU definitions of the astronomical unit and of `c` | light time over 1 AU, which is a ratio of two defined integers and so exact |

**Bodies**

| source | what it establishes |
|---|---|
| NASA Moon Fact Sheet | lunar mass, radius and synodic day |
| NASA Mars Fact Sheet; Willner et al. 2014 | Mars and Phobos mass, radius and rotation |
| Lauretta et al. 2019, *Nature* (OSIRIS-REx) | Bennu mass, radius, rotation, orbit |
| Watanabe et al. 2019, *Science* (Hayabusa2) | Ryugu mass, radius, rotation, orbit |
| Yeomans et al. 2000, *Science* (NEAR Shoemaker) | Eros mass and radius |
| Daly et al. 2023, *Nature* (DART) | Didymos mass, radius, rotation |
| Russell et al. 2016, *Science* (Dawn) | Ceres mass and radius |
| Siltala & Granvik 2021 | Psyche mass and radius |
| JPL Small-Body Database | perihelion, semi-major axis and aphelion for every named body |

**Illumination and orbits**

| source | what it establishes |
|---|---|
| NASA ISS Facts and Figures | the LEO eclipse fraction and orbital period |
| ITU-R S.1003 and standard GEO practice | the geostationary eclipse seasons |
| Whitley & Martinez 2016, *Options for Staging Orbits in Cis-Lunar Space* | the NRHO period and its near-continuous illumination |
| Mazarico et al. 2011 (LRO LOLA illumination modelling) | lunar polar ridge illumination, ~86% over a year |
| NASA DRA 5.0 | the Mars 1-sol staging orbit |
| Appelbaum & Flood, NASA TM-102299 | Mars surface insolation, and the dust caveat on that row |
| Warner, Harris & Pravec, *Asteroid Lightcurve Database* | the 6-10 h rotation the generic asteroid rows use as a population median |

⚠️  Five rows are GENERIC — typical low-Δv NEA, the three main-belt zones, and
the Trojan swarm. Their distances are a class rather than a body and their
rotation periods are a population median, not a measurement. Every such row
says so in its own `notes`.

## 6. Commodity prices

Live quotes, when `use_yfinance` is on, come from Yahoo Finance via the
`yfinance` package. Free, no API key, and **off by default**.

| ticker | commodity | used as |
|---|---|---|
| `HO=F` | NY heating oil | RP-1 / kerosene proxy, No. 2 distillate |
| `NG=F` | Henry Hub natural gas | methane (LCH4) proxy |
| `CL=F` | WTI crude | upstream cross-check on `HO=F` |

Yahoo Finance data is subject to Yahoo's own terms of service. Nothing fetched
is redistributed by this project: a live price lands in a CSV you build
yourself, and the committed reference files are offline builds carrying
reference prices only.

## 7. Software this package depends on

Runtime: **numpy**, **pandas**. Optional live prices: **yfinance**. Tests:
**pytest**. All are BSD, MIT or Apache licensed.

## 8. Where citations live in the code

| what | where |
|---|---|
| every launch vehicle, propellant, delta-v segment, operational cost, storage system and environment | the `notes` field of its own row in `spacecost/*.py`, with `reference_year` tagging staleness |
| the environment derivations, and why they avoid transcendentals | the module docstring and `DERIVATIONS` block of `spacecost/environments.py` |
| the tankage derivation and its flight anchors | the comment block above `_TANK_BASE_KG_PER_L` in `spacecost/propellants.py` |
| the argon boil-off derivation | the comment block above `_LAR_BOILOFF_PCT_PER_DAY`, derived from the LOX rate rather than asserted |

## 9. Citing this package

There is no paper. Cite the repository, the release, and the data contract
version, because the last of those is what identifies the numbers:

> spacecost, https://github.com/loggger101/spacecost, package v0.2.0,
> data contract `pipeline_version` 1.15.0.

## 10. Citing the upstream project

These tables were built as Module 3 of `economicspace`. If your work leans on
the model rather than only on the tables, cite that instead:

> economicspace, https://github.com/loggger101/economicspace
