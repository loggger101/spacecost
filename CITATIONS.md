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

Pricing and payload figures, verified May 2026 and re-audited September 2026
(data contract 1.16.0, fairing volumes 1.17.0). Every row names its own source in `notes`; these are the
ones that carry more than one row.

| source | what it establishes |
|---|---|
| SatBase 2026-02 SpaceX price update | Falcon 9 list price, and the rise used to carry Falcon Heavy's older quotes forward |
| Voyager Technologies final prospectus (SEC Form 424B4, Jun 2025), Commitments and Contingencies note | Starship dedicated-launch price (low end of its range): one Starlab launch committed at $90.0M |
| NASA Office of Inspector General, IG-22-003 (Nov 2021) and Oct 2023 audit | SLS launch-only cost: $2.2B vehicle + $568M ground, "at least $2.5B" |
| NASA, Feb 2026 Artemis restructuring (SpaceNews, SatNews) | SLS Block 1B and the Exploration Upper Stage cancelled |
| ULA RocketBuilder, and SpaceNews 2024-2026 | Atlas V pricing and sales end; Vulcan's "starting at $110M" |
| Blue Origin via Wikipedia and Spaceflight Now, 2025-2026 | New Glenn price range, payloads, and the NG-1 to NG-3 record; 9x4 payloads |
| Rocket Lab Form 10-Q, FY2026 Q1 (MD&A, revenue per launch), and Spaceflight Now Aug 2026 | Electron pricing (the band is Q1 2025 and Q1 2026 actual revenue per launch); Neutron price and schedule |
| TASS / Glavkosmos 2018 | Soyuz-2.1b pricing |
| ISRO / NSIL, and The Week Jan 2026 | LVM3, PSLV, GSLV and SSLV pricing; PSLV-C61 and C62 failures |
| CAS Space, Apr 2026 (30,000 yuan/kg) | Kinetica-2 price, the only published Chinese per-kg rate |
| SpaceNews, Spaceflight Now, NASASpaceFlight, 2025-2026 | Zhuque-3, Long March 10B, Tianlong-3, Pallas-1 and Soyuz-5 flight outcomes |
| Pielke & Byerly, Nature 2011 | Space Shuttle whole-programme cost per flight |
| Wikipedia vehicle articles and "Comparison of orbital launch systems", Sep 2026 | payload masses by configuration and orbit, cross-checked against the manufacturer where one publishes |

### Fairing volumes (data contract 1.17.0)

Each `fairing_volume_m3` is derived in `spacecost/fairings.py` from the
document below, and the row's `notes` name the figure. `guide` means the
usable envelope is read off the drawing, and `published` means the maker
states the volume.

| source | rows |
|---|---|
| SpaceX, Falcon User's Guide (Sep 2021, Fig 12-5; outer size from the May 2025 edition) | Falcon 9 and Falcon Heavy, all four |
| SpaceX, Starship Users Guide Rev 1.0 (Mar 2020), Fig 4 | Starship |
| ULA, Atlas V Launch Services User's Guide Rev 11 (Mar 2010), Fig 6-4 | Atlas V 551 |
| ULA, Vulcan Launch Systems User's Guide (Oct 2023), Fig 4.3.1-1 | Vulcan VC2, VC4, VC6 |
| Boeing Launch Services, Delta IV Technical Summary, payload fairing envelopes | Delta IV Heavy; SLS Block 1 |
| NASA, SLS Mission Planner's Guide ESD 30000 Rev A (Dec 2018), s6.2.1 and Fig 6-7 | SLS Block 1 (which fairing), SLS Block 1B (Cargo) |
| NASA, NSTS 21492 Space Shuttle Payload Bay Payload User's Guide, s4.0 | Space Shuttle |
| Douglas, SM-47274 Saturn V Payload Planner's Guide (1965) | Saturn V |
| Blue Origin, New Glenn Payload User's Guide Rev C (Oct 2018), Fig 5-2 | New Glenn |
| Rocket Lab, Electron Payload User's Guide 7.0; Neutron Payload User's Guide 1.0 (Jan 2025), Fig 13 | Electron, Neutron |
| Firefly, Alpha Payload User's Guide v2.0 (Aug 2019), Fig 8 | Alpha |
| Northrop Grumman, Minotaur IV/V/VI User's Guide Rel 2.5 (Nov 2025); Pegasus User's Guide Rel 8.2 (Sep 2020) | Minotaur IV, Pegasus XL |
| Arianespace, Ariane 5 User's Manual Iss 5 Rev 1; Ariane 6 User's Manual Iss 2; Vega User's Manual Iss 4; Vega C User's Manual Iss 0; Soyuz CSG User's Manual Iss 2 | Ariane 5 ECA, Ariane 6 A62 and A64, Vega, Vega C, Soyuz-2.1a and 2.1b |
| ILS, Proton Mission Planner's Guide Rev 7 (Jul 2009), App E | Proton-M |
| MHI, H-IIA User's Manual Ver 4.0, Fig 4.5-2 | H-IIA 204 |
| CALT, LM-2C User's Manual (1999); CGWIC, LM-3A Series User's Manual (2011), Fig 4-5b | Long March 2C, Long March 3B/E |
| Galactic Energy, Ceres-1 and Pallas-1 User's Manuals (2023) | Ceres-1, Pallas-1 |
| Reaction Engines, SKYLON Users' Manual Rev 1, Fig 13 | Skylon |
| VSSC (ISRO), GSLV MkIII specifications (`published`, 110 m³) | LVM3 |
| Orienspace via Tencent News, 2023-11-22 (`published`, 100 m³) | Gravity-1 |
| Kawasaki Heavy Industries; CGWIC; RussianSpaceWeb; Sohu 2024-05-06; Tencent News 2026-07-13 (outer size only, `estimate`) | H3 (24L) and (30), Long March 2D, Angara A5, Long March 5, Long March 10B |

⚠️  **Most Chinese prices, and every price marked `estimate` in
`price_basis`, are not sourced numbers.** They are bands chosen against the
nearest vehicle that does have a price, and the headline is their centre. Filter on
`price_basis` if a study cannot use them.

Non-rocket concepts (mass drivers, launch loops, tethers, light-gas guns) are
cited individually in their own rows and are marked `concept`. They are included
so a study can state what it excluded.

## 2. Propellants and propulsion

| source | what it establishes |
|---|---|
| DOD Aerospace Standard Prices, FY20 | hydrazine, MMH, N2O4 pricing (a list no longer findable to re-check) |
| DLA Energy, Aerospace Standard Prices FY2025 (effective Oct 1 2024) | the government price of MMH, NTO and hydrazine, quoted beside the rows as a comparison and not used for a value |
| Space Insider, How Much Does Rocket Fuel Really Cost? (J. Seibert, Jun 13 2023) | hydrazine's commercial price, up to ~$75.8/kg (once cited as "AIAA 2024") |
| SETS Space / Electric Propulsion, 2024 | xenon and argon ion pricing, and the high end of krypton's band ("$2,100-$4,800" flight grade) |
| Idaho National Laboratory, INL/RPT-23-75203, Krypton and xenon recovery cost-benefit, 2023 | the low end of krypton's band: a market survey putting bulk Kr prices at "around $1/L" |
| Mobius / Energy CG, 2024 | liquid methane commodity pricing |
| NASA-STD-(I)-5019 class hardware | COPV burst performance factor, ~392 kJ/kg |
| Shuttle External Tank, Falcon 9 second stage, Centaur III | the flight anchors the tankage model is calibrated on |
| Manufacturer data sheets, per device | thruster kg/N, efficiency, thrust scaling |
| DOE Hydrogen and Fuel Cell Technologies Office, Technical Targets for Proton Exchange Membrane Electrolysis | hydrolox ISRU electrolysis, 55 kWh/kg H2 at system level (2022 status) |
| W. Johnson (NASA GRC), Concepts for the Liquefaction of Hydrogen for In-Situ Operations on the Lunar or Martian Surface, AIAA ASCEND 2023, NTRS 20230014839 | hydrolox ISRU liquefaction: 35 kW for 0.3 kg/h of H2 through one 20 K cryocooler, up to 3x less pre-cooled, and under 2 kW for the oxygen |
| F. H. Jue (Boeing Rocketdyne), Space Shuttle Main Engine - Thirty Years of Innovation, NTRS 20020046693 | hydrolox Isp: the RS-25 table |
| J. F. Baumeister (NASA GRC), RL10 Engine Ability to Transition from Atlas to Shuttle/Centaur Program, NASA/TM-2015-218736 | hydrolox: the RL10A-3-3A's measured Isp, as a comparison |
| Kim, Jung & Kim, State of the Art in the Development of Methane/Oxygen Liquid-bipropellant Rocket Engine, J. Korean Soc. Propulsion Eng. 17(6), 2013, doi:10.6108/kspe.2013.17.6.120 | methalox Isp (Raptor, Table 3); kerolox Isp against the RD-191 (Table 5) |
| R. Thapa, Evolution in Propellant of the Rocket Engine, J. Materials Physics and Chemistry 11(1), 2023, doi:10.12691/jmpc-11-1-2 | kerolox: the Saturn V first stage's Isp, the family's low end |
| Spores, Masse, Kimbrel & McLean, GPIM AF-M315E Propulsion System, AIAA Joint Propulsion Conference 2014, NTRS 20140012587 | green monoprop Isp (GR-1, Table 1) and its density-impulse comparison with hydrazine |
| Borowski, McCurdy & Packard (NASA), Nuclear Thermal Propulsion (NTP): A Proven Growth Technology for Human NEO/Mars Exploration Missions, IEEE Aerospace 2012, NTRS 20120003776 | nuclear thermal Isp |
| Price & Evans (JPL), The Status of Monopropellant Hydrazine Technology, JPL TR 32-1227, 1968, NTRS 19680006875 | hydrazine monoprop Isp: the measured catalytic-bed figure |
| Hitt, Zakrzwski & Thomas (NASA), MEMS-based satellite micropropulsion via catalyzed hydrogen peroxide decomposition, Smart Materials and Structures 10(6), 2001, NTRS 20010102648 | HTP Isp: theoretical and empirical bounds |
| Morren & Curran (NASA Lewis), Preliminary Performance and Life Evaluations of a 2-kW Arcjet, NASA TM-105149 / AIAA-91-2228 | hydrazine arcjet Isp: state of the art, programme goal and endurance test |
| Schoenman (NASA Lewis), Test experience, 490 N high performance (321 sec Isp) engine, AIAA-92-3800, NTRS 19920066503 | UDMH / NTO Isp, bracketed by a measured NTO/MMH engine |
| Asakawa, Koizumi et al. (JAXA), On-orbit Performance of the Water Resistojet Propulsion System AQUARIUS on EQUULEUS, Trans. JSASS 67(5), 2024 | water resistojet: the one flight-measured Isp |
| Monheiser, Goodfellow, Aubuchon et al., A Summary of the NEXT-C Flight Thruster Proto-Flight Testing, NTRS 20210018563 | xenon gridded-ion Isp envelope |
| Shastry et al., 12-kW Advanced Electric Propulsion System Hall Current Thruster Qualification and Production Status, IEPC-2024, NTRS 20240006249 | xenon Hall-thruster Isp, as a comparison |
| Boddy (Rockwell, for AFRPL), Solar Rocket System Concept Analysis, 1980, NTRS 19800022964 | solar thermal: the measured 680 s |
| Woodcock & Byers, Results of Evaluation of Solar Thermal Propulsion, 2003, NTRS 20030068437 | solar thermal: the 811 s design figure |
| Hepp, Landis & Kubiak (NASA), Chemical Approaches to Carbon Dioxide Utilization for Manned Mars Missions, NASA TM-103728, 1991 | CO / LOX Isp, ~300 s |
| Linne (NASA Lewis), Experimental Evaluation of the Ignition Process of Carbon Monoxide and Oxygen in a Rocket Engine, NASA TM-107267 / AIAA-96-2943 | CO / LOX subscale combustion at O/F 0.55 |
| General Atomic Division of General Dynamics, Nuclear Pulse Vehicle Study, condensed summary report GA-4891, 1964 | nuclear pulse: programme dates and design Isp |
| Schmidt, Bonometti & Morton (NASA MSFC), Nuclear Pulse Propulsion - Orion and Beyond, AIAA 2000-3856 | nuclear pulse: the external-pulse Isp range |

Vacuum Isp values are the interplanetary-relevant figures. Sea-level Isp is
lower and matters only to a first stage, which is already priced into the launch
table's $/kg-to-orbit.

## 3. Delta-v segments

| source | what it establishes |
|---|---|
| Curtis, *Orbital Mechanics for Engineering Students* | ascent and textbook segment values |
| Taylor et al. 2018, "Delta-v map of Main Belt Asteroids" | LEO to main-belt transfer |
| Elvis et al. 2011, arXiv 1105.4152 | near-Earth object delta-v accessibility distribution, and its 6.65 km/s peak |
| NASA DRA 5.0 (SP-2009-566), Fig 4-2 | the swing of trans-Mars injection across the synodic cycle |
| Orloff, *Apollo by the Numbers* (NASA SP-2000-4029), lunar-orbit phase tables | trans-lunar injection, lunar orbit insertion, and the Lunar Module's powered descent and ascent as flown on Apollo 14-17 |
| Lyons (JPL), Magellan / MGS aerobraking; Long et al. 2007, MRO aerobraking operations | the aerobraked return's flight record |
| NASA NTRS and JPL design handbooks | the remaining trajectory legs |

⚠️  These are **representative means**, not a trajectory. A real transfer needs a
Lambert solve against an ephemeris; these are what you price the answer with.

## 4. Operational costs

| source | what it establishes |
|---|---|
| NASA DSN Services Catalog 820-100-H | deep space network aperture fees: the $1,792 hourly rate base (Jun 2022), carried to 2026 by CPI-U |
| NASA / Planetary Society, and Wikipedia | OSIRIS-REx mission total cost |
| The Planetary Society, Planetary Exploration Budget Dataset | OSIRIS-REx operations obligations by fiscal year |
| NASA OIG IG-23-010 | MMRTG mass, and Pu-238 production against its goal |
| Frieman et al. 2021 (AEPS ETU-2) | Hall thruster total efficiency across the throttle range |
| Metzger, Zacny & Morrison 2020; Zeng et al. 2007 | the excavation energy literature |
| Kleinhenz & Paz, A Lunar Water ISRU System Study for Human-Scale Propellant Production, PTMSS/SRR 2021, NTRS 20210016820 | ISRU propellant plant throughput (2.6 t for 11.67 t of hydrolox in 225 days), and the whole-plant cross-check on the processing energy (46 kW) |
| Kleinhenz & Paz, An ISRU Propellant Production System for a Fully Fueled Mars Ascent Vehicle, AIAA 2017-0423, NTRS 20170005179 | the high end of the plant throughput band (1.7 t for 29.7 t of CH4/O2 in 480 days) |
| Plane Talking (Gallagher) / Slingshot Aerospace, 2024 | launch insurance market rate, and the 2023 losses behind it |
| Damodaran (NYU Stern), Cost of Capital by Industry Sector (Jan 2026); Boeing and Howmet filings | cost-of-capital floor: industry averages, with no startup premium |
| McKeown, What is an appropriate investment hurdle rate for commercial space resource development projects?, 2024 | the 10% standard discount rate for space-resource projects, and hurdle rates near 25% |
| Scottoline & Coleman, Effectiveness of Loan Guarantees versus Tax Incentives for Space Launch Ventures, 1999, NTRS 19990101869 | launch-venture debt at 14% or more without guarantees |
| The Planetary Society, Planetary Exploration Budget Dataset | Perseverance development + launch cost, the scale behind the autonomy NRE (the autonomy share itself is unsourced) |
| MIL-HDBK-189C (Jun 2011), 5.2.6 and Table II | the Duane growth model, and the historical growth rates the mining reliability exponent sits inside |
| 14 CFR Part 440 (eCFR), 440.9(c) and (e) | the third-party and US Government property caps on required liability insurance |
| FAA, Space Launch and Reentry Licensing and Permitting User Fees, 91 FR 21591 (22 Apr 2026) | the per-launch user fee owed from 2026 under 51 U.S.C. 50924 |
| Cross & Vesely, Synthesizing a New Launch Vehicle Failure Probability Based on Historical Flight Data, 2018, NTRS 20180006947 | first-flight failure probability of a new launch vehicle |
| Kinnett, Green, Klein & Lin (JPL), Remote Diagnosis and Operational Response to an In-Flight Failure of the Drill Feed Mechanism Onboard the Mars Science Laboratory Rover, Aerospace Mechanisms Symposium 2022 | the Curiosity drill entry in the mining success tally |
| Shapiro, Murray, Howarth & Fusaro, Space Mechanisms Lessons Learned Study, Vol. I (NASA TM-107046) and Vol. II (TM-107047), 1995 | the fleet deployment-anomaly record, and flight lessons by mechanism type |
| NASA CR-3349, Satellite Power System Salvage and Disposal Alternatives, 1980 | the space-asset salvage values that bracket the rig salvage fraction |
| US DOE, Mining Industry Energy Bandwidth Study, 2007, Exhibit 24 | terrestrial beneficiation energy per kg of ore |
| Whitley & Shinn, The Economics of NASA Mission Cost Reserves, 2012, NTRS 20120002314 | NASA's fixed-percentage reserves and how often they were spent |
| National Research Council, Controlling Cost Growth of NASA Earth and Space Science Missions, 2010 | average cost growth across prior studies |
| Schmitz et al., A Comparison of Radioisotope and Solar Array/Battery Power Systems in the Solar System, IEEE Aerospace 2023, NTRS 20230001487 | Li-ion state of the art (Table 3), and Lucy's array specific power |
| Ali, Beltran, Lindsey & Pecht, Assessment of the calendar aging of lithium-ion batteries for a long-term space missions, Frontiers in Energy Research, 2023 | Li-ion cell specific energy |
| Hoffman, Kerslake, Hepp, Jacobs & Ponnusamy, Thin-Film Photovoltaic Solar Array Parametric Assessment, NASA/TM-2000-210342 | array mass for a main-belt asteroid tour |
| The NEXT-C Power Processing Unit: Lessons Learned from the Design, Build, and Test of the NEXT-C PPU for APL's DART Mission, Aerojet Rocketdyne / NASA, 2020 | NEXT-C PPU mass and output range |
| NASA OIG IG-24-003 (Oct 2023) and IG-21-004 (Nov 2020) | Gateway PPE price and power, and its government-furnished thrusters |
| NASA OIG IG-17-009 (Jan 2017), Table 3; IG-23-010, Table 2 | MMRTG unit cost, and notional cost per mission watt |
| Howe et al., Economical Production of Pu-238, NASA NIAC Phase I, NTRS 20160010587 | Pu-238 price from a new reactor |
| Elon Musk, public statement, 2018 (no document) | the low anchor of the expendable upper stage cost, ~$10M for Falcon 9's second stage |
| Dawson & Bowles, Taming Liquid Hydrogen: The Centaur Upper Stage Rocket, 1958-2002, NASA SP-4176, 2004 | Centaur programme costs, and the absence of a per-stage price behind the ~$30M high anchor |
| Kleinhenz & Paz 2017 and 2021 (above) | the published in-space processing rates the refinery throughput row is compared against |
| NASA OIG IG-18-016, Audit of Commercial Resupply Services to the International Space Station, 2018 | the whole-mission ceiling over depot berthing and sample recovery operations |
| NASA/TM-2011-215988, Issues of Long-Term Cryogenic Propellant Storage in Microgravity; Plachta et al., NASA Cryocooler Technology Developments and Goals to Achieve Zero Boil-Off, 2017 | named as out of scope for volatile cargo containment, which is an engineering estimate |

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
| Daly et al. 2023, *Nature* (DART) | Didymos rotation, and the system mass and diameter the row's unsourced mass and radius sit inside |
| Russell et al. 2016, *Science* (Dawn) | Ceres mass and radius |
| Kretlow 2020, SiMDA data set (as tabulated in Kretlow 2022, *A&A* 668:A141, Table 2) | Psyche mass |
| Siltala & Granvik 2021 | Psyche radius, and a mass 3% below the row's as a cross-check |
| JPL Small-Body Database | perihelion, semi-major axis and aphelion for every named body |

**Illumination and orbits**

| source | what it establishes |
|---|---|
| orbital mechanics for a 400-km circular orbit; NASA ISS Facts and Figures as the ~90-min cross-check | the LEO eclipse fraction and orbital period |
| ECSS-E-HB-31-01 Part 15A, and GEO geometry | the geostationary eclipse seasons and their 72-minute maximum |
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
| the delivery chains: the tug and lander dry-mass fractions (Centaur V, DCSS, Apollo LM descent stage) and the Mars entry survival fraction (MSL 28.5%, Perseverance 30.5%, on JPL's best-estimated entry masses) | the comment blocks above `TUG_DRY_MASS_FRAC` and `MARS_LANDED_MASS_FRACTION` in `spacecost/delivery.py`; every delta-v in a chain is a lookup into `DELTA_V_REFERENCE` and carries that row's citation |

## 9. Citing this package

There is no paper. Cite the repository, the release, and the data contract
version, because the last of those is what identifies the numbers:

> spacecost, https://github.com/loggger101/spacecost, package v*X.Y.Z*,
> data contract `pipeline_version` *A.B.C*.

Fill both in from the copy you used rather than from this page:
`spacecost.__version__` is the package release and `spacecost.DATA_VERSION`
the data contract, which every output CSV also carries in its
`pipeline_version` column.

## 10. Citing the upstream project

These tables were built as Module 3 of `economicspace`. If your work leans on
the model rather than only on the tables, cite that instead:

> economicspace, https://github.com/loggger101/economicspace
