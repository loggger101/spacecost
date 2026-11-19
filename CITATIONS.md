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
V1.1. **None of the three feeds a value here, but ssoBFT is quoted:** the
average- and hard-NEA delta-v rows compare themselves with its NEA median (8.88
km/s) and main-belt fifth percentile (8.49 km/s). IMCCE asks that any use of
ssoBFT cite Berthier et al. (2023), A&A 671, A151, so a reuse of those two
rows' notes carries that citation (section 3; General_Research rc-767). If you
are vendoring from that project rather than this one, read its `CITATIONS.md`
instead.

## 1. Launch vehicles

Pricing and payload figures, verified May 2026 and re-audited September 2026
(data contract 1.16.0, fairing volumes 1.17.0). Every row names its own source in `notes`; these are the
ones that carry more than one row.

| source | what it establishes |
|---|---|
| SatBase 2026-02 SpaceX price update | Falcon 9 list price, and the rise used to carry Falcon Heavy's older quotes forward |
| Voyager Technologies final prospectus (SEC Form 424B4, Jun 2025), Commitments and Contingencies note | Starship dedicated-launch price (low end of its range): one Starlab launch committed at $90.0M |
| NASA Office of Inspector General, IG-22-003 (Nov 2021); and *NASA's Transition of the Space Launch System to a Commercial Services Contract*, IG-24-001 (12 Oct 2023), <https://oig.nasa.gov/wp-content/uploads/2023/10/ig-24-001.pdf> | SLS launch-only cost: $2.2B vehicle + $568M ground, "at least $2.5B"; from IG-24-001, Falcon Heavy's $178M Europa Clipper contract (PDF p. 24, printed p. 17) and the Shuttle's ~$1.45B a launch (PDF p. 23, printed p. 16) (rc-828) |
| NASA, FY 2027 Budget Estimates, pp39-40 (Apr 2026); Feb 2026 Artemis restructuring announcement (SpaceNews, SatNews) | SLS Block 1B and the Exploration Upper Stage cancelled |
| ULA RocketBuilder, and SpaceNews 2024-2026 | Atlas V pricing and sales end; Vulcan's "starting at $110M" |
| Blue Origin via Wikipedia and Spaceflight Now, 2025-2026 | New Glenn price range, payloads, and the NG-1 to NG-3 record; 9x4 payloads |
| Rocket Lab Form 10-Q, FY2026 Q1 (MD&A, revenue per launch), and Spaceflight Now Aug 2026 | Electron pricing (the band is Q1 2025 and Q1 2026 actual revenue per launch); Neutron price and schedule |
| TASS / Glavkosmos 2018 | Soyuz-2.1b pricing |
| ISRO / NSIL, and The Week Jan 2026 | LVM3, PSLV, GSLV and SSLV pricing; PSLV-C61 and C62 failures |
| CAS Space, Apr 2026 (30,000 yuan/kg) | Kinetica-2 price, the only published Chinese per-kg rate |
| SpaceNews, Spaceflight Now, NASASpaceFlight, 2025-2026 | Zhuque-3, Long March 10B, Tianlong-3, Pallas-1 and Soyuz-5 flight outcomes |
| Zapata (NASA KSC), The State of Play: US Space Systems Competitiveness, FISO presentation, Jul 2017, NTRS 20170009967, p16 | Delta IV Heavy and Atlas V 551 LEO payloads (200 km / 28.5 deg); the NRO's Delta IV Heavy price ($336M in 2017 dollars, with ELC) the Delta IV Heavy row is compared against; NASA's Pegasus XL price for ICON |
| Pielke & Byerly, Nature 2011 | Space Shuttle whole-programme cost per flight |
| Wikipedia vehicle articles and "Comparison of orbital launch systems", Sep 2026 | payload masses by configuration and orbit, cross-checked against the manufacturer where one publishes |
| Comparators named in 0.17.1's notes (General_Research rc-457 to rc-506; each note names its own). Full references below since 0.17.2 (rc-806); each keeps the comparator role its note gives it | |
| ESA, *Space Component tenders and contracts*, 2025 Copernicus award list (MFF21 Article 14), p. 1, <https://esamultimedia.esa.int/docs/EarthObservation/COPERNICUS_MFF21-Article_14_2025.pdf>; and ESA, *Ariane 6 to take Sentinel-1D into orbit* (28 Jan 2025), <https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Ariane_6_to_take_Sentinel-1D_into_orbit> | Sentinel-1D on Ariane 62, beside the Ariane 62 band |
| NewSpace Index, *Small Launchers: Absolute Prices vs Performance* (15 Jun 2024), <https://www.newspace.im/assets/fig/Newspace_launchers_abscostsperf_2024-06-15.pdf>; and FAA AST / The Tauri Group, *Annual Compendium of Commercial Space Transportation: 2016*, Epsilon fact sheet, <https://www.faa.gov/about/office_org/headquarters_offices/ast/media/2016_compendium.pdf> | Epsilon prices, beside Epsilon S |
| ESA, *Access to space today and tomorrow: what does Europe need?*, ESA INFO 10-2003 (16 May 2003), <https://www.esa.int/articles/business/business-with-esa/access-to-space-today-and-tomorrow-what-does-europe-need> | Ariane 5 ES service cost, beside Ariane 5 ECA |
| Powell, Maise & Rather, *Maglev Launch: Ultra Low Cost Ultra/High Volume Access to Space for Cargo and Humans*, SPESIF-2010, Table 5.4, <https://startram.com/wp-content/uploads/2020/12/StarTram2010.pdf> | StarTram's $43/kg projection |
| Xinhua, *China Focus: China achieves first-ever controlled rocket recovery in Long March-10B maiden flight* (10 Jul 2026), <https://english.news.cn/20260710/b4a934ab25284ea799ea3548b392c735/c.html> | Long March 10B reuse context |
| China Government Procurement Network, sole-source procurement notice for the eXTP launch vehicle, CAS National Space Science Center (8 Jun 2026), <https://www.ccgp.gov.cn/eadylynotice/202606/t20260608_26709230.htm> | the eXTP launch-service budget |
| United Launch Alliance, *Vulcan Leo 1: Delivering 40 satellites to space* (10 Nov 2026 schedule snapshot), <https://blog.ulalaunch.com/blog/vulcan-leo-1-delivering-40-satellites-to-space> | V-012, the first VC6 (a VC6L), beside Vulcan VC6 |
| FAA AST, *2010 U.S. Commercial Space Transportation Developments and Concepts*, p. 24 and endnote 53, p. 100 | Minotaur IV's 1,735 kg to LEO, the high end, from Orbital's fact sheet with no orbit given (rc-193) |
| Spaceflight Now (18 Nov 2010); NASA OIG IG-11-012, p. 12 and Table 4; FAA AST Minotaur IV fact sheet (2016) | Minotaur IV's $50M (2010), ~$50M (2012) and $63M average (2012-2020), and $46M: why its band is a mixed-year scenario (rc-617) |
| NASA X-Hab 2025 report, NTRS 20250005924, Table 19, p. 109 | Falcon Heavy's $97M (2022) from SpaceX's website, and an unexplained $107.9M 2025-adjusted figure (rc-554) |
| European Commission, EIC Horizon Prize ISAERO factsheet (2022), p. 201 | Spectrum's ~€10,000/kg target, a 2022 target (rc-521) |
| FAA AST, *2018 Commercial Space Transportation Compendium*, Proton M and Long March 2D fact sheets; GAO-17-609, Table 4, p. 30 and p. 21 | Proton-M's $65M estimated price; Long March 2D's 3,500 kg to 200 km LEO (rc-724, rc-719) |
| CNSA, Long March 2D page (2017-08-01); CGWIC, LM-2D technical data | the 4,000 kg unstated-orbit and 1,300 kg 645 km SSO ratings beside Long March 2D (rc-719) |
| CASC, Long March 2C page (2015-09-15); CASC, Jielong-3 release (2026-04-11); Xinhua (2021) | Long March 2C's 3,850 kg LEO; Jielong-3's official 1,500 kg to 500 km SSO (rc-717, rc-715) |
| ESA, 2022 Copernicus contract awards, p. 1; European Spaceflight on Sentinel-1C | Vega C's €48.62M Sentinel-1C launch-service contract, an institutional contract (rc-720) |
| LandSpace, ZQ-2E product page; LandSpace, Y5 flight release (2026-05-14) | Zhuque-2E's 6,000 kg to 200 km LEO and 4,000 kg to 500 km SSO (rc-714) |
| Galactic Energy, Pallas-1 maiden-flight release (2026-09-02) and product page | Pallas-1's general 5-7 t LEO and 7 t with Eros, beside the row's unsourced orbit ratings (rc-713) |
| JAXA, Epsilon S development status briefing (2023-07-07), p. 5; IHI Aerospace, Epsilon launch-service page | Epsilon S's 1,400 kg requirement and 1,200+ kg service lower bound to 500 km / 31.1 deg (rc-716) |
| TASS / Glavkosmos (2018) | Soyuz-2.1's $48.5M with Fregat, nominal 2018 and not variant-specific (rc-620) |
| O'Neill, *The Colonization of Space*, Physics Today 27(9), 32-40 (1974), <https://doi.org/10.1063/1.3128863>; NASA SP-428, *Space Resources and Space Settlements*, Mass Drivers III: Engineering, p. 149 | the lunar mass driver: the concept, and the 1977 model built at MIT and shown at Princeton (rc-790) |
| Raitt, *A Historical Look at Space Elevators*, New Space 3(4), 231-238 (2015), ref. 2 (Artsutanov, Komsomolskaya Pravda, 31 Jul 1960); Smitherman, NTRS 20040161582 (2004) | the Earth space elevator's attribution, and CNT composites as a critical technology; neither gives the row's strength or TRL figures (rc-791) |
| Pearson, *Anchored Lunar Satellites*, J. Astronautical Sci. 27(1), 39 (1979); Eubanks & Radley, Space Policy 37 (2016), p. 98 and Table 1 | the lunar elevator's material case: available composites, Zylon and Dyneema; M5 is named by neither (rc-792) |
| SpinLaunch, Orbital Accelerator FAQ; SpinLaunch, Flight Test 10 release (2022-10-03); Meridian Space announcement (2026-09-29) | SpinLaunch Orbital's ~5,000 mph and 200 kg design, the suborbital test record, and the company's 2026 status (rc-795) |
| Space Pioneer, TL-3 product page; Carrier Space, Tianlong-3 and Zhuque-2E profiles ('Price on request') | no published price behind the Tianlong-3 and Zhuque-2E scenario bands (rc-543, rc-547) |
| LandSpace, ZQ-3 product page (LEO @ 450 km: 12.5 t return-site, 18.3 t downrange, 21.3 t expendable) | beside Zhuque-3's unexplained 8 t (rc-611) |
| Indian Express (27 Jan 2022), K. Sivan's 2019 'around Rs 30 crore'; ISRO, Rajya Sabha Unstarred Question 2164(b) (Rs 169.07 crore for development and three flights) | SSLV: the traced part of its Rs 30-35 crore (rc-553) |
| FAA AST, *2018 Commercial Space Transportation Compendium*, Long March 5 fact sheet (price 'Undisclosed') | why Long March 5's band is a scenario (rc-592) |
| ISRO, LVM3 vehicle page (8,000 kg to 600 km LEO) and Launchers overview (10-tonne class) | the two statements LVM3's 8,000-10,000 kg band spans; neither gives 8,940 kg (rc-612) |
| Galactic Energy, CERES-1 product page (420 kg LEO, 300 kg SSO); IEEE Spectrum, pre-first-flight interview ($4M) | beside Ceres-1's 400 kg and $4.5M (rc-613, rc-614) |
| Manhattan Venture Partners, report of 30 Nov 2023 ('Terran R is expected to cost $55 million') | Terran R's low end; the $70M has no source (rc-616) |
| Next Spaceflight, Long March 8A profile; CASC (2026) and a CNSA-hosted report (2019) | Long March 8A's 3,500 kg GTO, a secondary figure with no variant-matched primary basis (rc-703) |
| NASA Office of Inspector General, *NASA's Management of Space Launch System Block 1B Development*, IG-24-015 (8 Aug 2024), <https://oig.nasa.gov/wp-content/uploads/2024/08/ig-24-015.pdf>, PDF p. 3 | Block 1B's first flight moved to Artemis IV and its ~$5.7B projected development cost: context for the SLS Block 1B (Cargo) row's concept status; no row value is taken from it (rc-832) |
| ESA, *ExoMars Factsheet* (17 Oct 2016), <https://www.esa.int/articles/exomars-factsheet> | Proton-M's escape payload: the ExoMars 2016 mission stack, TGO plus Schiaparelli, 4,332 kg including fuel on Proton-M/Breeze-M (3,732 kg orbiter, 577 kg Schiaparelli), which the row rounds to 4,300 kg; not the orbiter alone (rc-838) |
| JAXA, *H-IIA Launch Vehicle No.6: Why did the accident happen?* (2003), <https://global.jaxa.jp/article/special/h2a6/h2a_e.html> | H-IIA 204's low end: 9.3 billion yen for F4, one flight's cost and not a 204 quote (rc-839) |
| Maemura, Akiyama, Watanabe et al. (MHI), *New H-IIA Launch Vehicle Technology and Maiden Flight Results*, Mitsubishi Heavy Industries Technical Report 39(1) (2002), <https://dl.ndl.go.jp/view/prepareDownload?contentNo=1&itemId=info:ndljp/pid/3527426> | the standard type's cost, which the H-IIA 204 note treats as a floor for the 204 (rc-839) |
| The Space Review, *A review of Japan's space policy after the H3 launch vehicle failure* (Mar 2023), <https://www.thespacereview.com/article/4595/1> | H-IIA 204's high end: the programme's ~10 billion yen, 'about $75 million', a programme statement rather than a 204 quote (rc-839) |
| World Bank, official exchange rate, period average, USD/JPY (PA.NUS.FCRF, JPN), <https://data.worldbank.org/indicator/PA.NUS.FCRF?locations=JP> | the 2025 rate of 149.66 yen/$ that converts the H-IIA yen figures (rc-839) |
| JAXA, *H3 Launch Vehicle* project page, <https://www.rocket.jaxa.jp/e/rocket/h3/> | H3 (30): the ~JPY 5B target for the light configuration with no solid boosters; the page gives no target date or dollar conversion, so the row's ~$33M is a conversion made here (rc-840) |
| Space Writers Club, transcript of the JAXA/MHI H3 F6 prelaunch briefing (8 Jun 2026), <https://sacj.org/news/archives/1202> | H3 (24L): the project manager's ~60% above H3-30, a relative cost, not an absolute launch price (rc-840) |
| United Launch Alliance, *Vulcan Cert-1* archived mission page, <https://www.ulalaunch.com/missions/archived-launched/vulcan-cert-1> | Vulcan's first launch, Cert-1, on 8 Jan 2024 carrying Peregrine Mission One: VC2's `first_flight_year` and maiden-flight note; nothing on payload or price (rc-843) |

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
| DLA Energy, Aerospace Standard Prices FY2025 (effective Oct 1 2024) | the LOX component ($0.37/kg, rc-185), and the government price of MMH, NTO and hydrazine, quoted beside the rows as a comparison and not used for a value |
| Space Insider, How Much Does Rocket Fuel Really Cost? (J. Seibert, Jun 13 2023) | hydrazine's commercial price, up to ~$75.8/kg (once cited as "AIAA 2024") |
| SETS Space / Electric Propulsion, 2024 | argon ion pricing, and the high end of krypton's band ("$2,100-$4,800" flight grade) |
| Idaho National Laboratory, INL/RPT-23-75203, Krypton and xenon recovery cost-benefit, 2023 | the low end of krypton's band: a market survey putting bulk Kr prices at "around $1/L"; and the price of xenon, around $60/L in Q1 2023 |
| World Bank Commodity Markets (Pink Sheet), natural gas US and LNG Japan, 2025 means | the two ends of the bracket liquid methane's $0.40/kg sits in |
| Rafalskyi et al., Nature 599, 2021; USGS Mineral Commodity Summaries 2026, Iodine | iodine's flight record, and its market; the paper's US$60 is a total cost, not a price per kg |
| CME Rulebook Chapter 220; Sabine Pipe Line tariff section 7.1; ASHRAE 2021 Fundamentals ch. 28 Table 3; NIST SP 811 Appendix B.8 | the gross-heat basis of a Henry Hub quote and the conversion to methane's USD/kg |
| NASA-STD-(I)-5019 class hardware | COPV burst performance factor, ~392 kJ/kg |
| Shuttle External Tank, Falcon 9 second stage, Centaur III | the flight anchors the tankage model is calibrated on |
| Rumerman, *NASA Historical Data Book, Vol. VII: NASA Launch Systems, Space Transportation, Human Spaceflight, and Space Science, 1989-1998*, NASA SP-2009-4012 (2009), <https://www.nasa.gov/wp-content/uploads/2023/04/sp-4012v7.pdf>, Table 2-86, printed pp. 165-166 | the Shuttle Super Lightweight External Tank anchor only (0.0129 kg/L); it does not establish the Falcon 9 or Centaur anchors or the 0.025 kg/L base (rc-844) |
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
| Sekine, Ataka, Moriai et al. (University of Tokyo / JAXA), *On-orbit Performance Evaluation of AQUARIUS: a Water Resistojet Propulsion System*, Trans. JSASS 67(5), 274-284, 2024, Table 3, p. 282 (cited as Asakawa, Koizumi et al. until 0.18.0) | water resistojet: the one flight-measured Isp (rc-764) |
| JAXA, AQT-D deployment from Kibo (3 Dec 2019); JAXA Launch Records (Artemis I, EQUULEUS); JAXA, RAISE-3 / KIR mission page; Pale Blue, EYE in-orbit release (13 Mar 2023); Momentus, Vigoride-5 orbit-raise release (8 May 2023); NASA, Pathfinder Technology Demonstrator page (PTD-1, HYDROS-C) | water resistojet flight history: AQT-D in 2019 is the first launch; HYDROS-C electrolyses water and is not a resistojet (rc-764) |
| LandSpace, About Us, Milestones | methalox: Zhuque-2 Mission F1, its first launch, in 2022, and F2, the first LOX/LCH4 rocket to orbit, in 2023 (rc-760) |
| UK Space Agency, *50 years since Black Arrow launched the UK into space* (4 Mar 2020); Wight Aviation Museum, *Black Arrow History* | HTP / RP-1: Black Arrow R0 (1969, first launch), R1 (1970) and R3 (1971, Prospero to orbit) (rc-761) |
| Science Museum Group, *De Havilland Super Sprite Rocket Engine*, object 1962-104 | HTP monoprop: first fired 1949, flight trials from 1951, the row's first flight (rc-762) |
| Curren & Byers, *NASA Hydrazine Arcjets*, NASA-TM-106695 / AIAA 94-2463, NTRS 19950004443; Hoskins et al., *30 Years of Electric Propulsion Flight Experience at Aerojet Rocketdyne*, IEPC-2013-439, p. 2; Lockheed Martin, A2100 fleet release (17 Jul 2006) | hydrazine arcjet: first-generation arcjets on Telstar 401 (Dec 1993); the MR-510 a later upgrade on A2100, first launched 1996 (rc-763) |
| Monheiser, Goodfellow, Aubuchon et al., A Summary of the NEXT-C Flight Thruster Proto-Flight Testing, NTRS 20210018563 | xenon gridded-ion Isp envelope |
| Shastry et al., 12-kW Advanced Electric Propulsion System Hall Current Thruster Qualification and Production Status, IEPC-2024, NTRS 20240006249 | xenon Hall-thruster Isp, as a comparison |
| Boddy (Rockwell, for AFRPL), Solar Rocket System Concept Analysis, 1980, NTRS 19800022964 | solar thermal: the measured 680 s |
| Woodcock & Byers, Results of Evaluation of Solar Thermal Propulsion, 2003, NTRS 20030068437 | solar thermal: the 811 s design figure |
| Hepp, Landis & Kubiak (NASA), Chemical Approaches to Carbon Dioxide Utilization for Manned Mars Missions, NASA TM-103728, 1991 | CO / LOX Isp, ~300 s |
| Linne (NASA Lewis), Experimental Evaluation of the Ignition Process of Carbon Monoxide and Oxygen in a Rocket Engine, NASA TM-107267 / AIAA-96-2943 | CO / LOX subscale combustion at O/F 0.55 |
| General Atomic Division of General Dynamics, Nuclear Pulse Vehicle Study, condensed summary report GA-4891, 1964 | nuclear pulse: programme dates and design Isp |
| Schmidt, Bonometti & Morton (NASA MSFC), Nuclear Pulse Propulsion - Orion and Beyond, AIAA 2000-3856 | nuclear pulse: the external-pulse Isp range |
| Polzin, Curran, Rao, Myers, Duchek, Presby et al., Technology Maturation Plan for High Power Nuclear Electric Propulsion, NASA/TP-20260001499, Table 2.1 | nuclear electric: TRL, and the power-system specific-mass KPPs (24 kg/kWe threshold, 13 target) |
| Poston et al., KRUSTY Reactor Design, Nuclear Technology 206, 2020 (section 4) | nuclear electric: what KRUSTY demonstrated |
| SpaceX, Starlink Progress Report 2023, p. 48 | krypton on first-generation Starlink, argon on the second (rc-363) |
| NASA, State-of-the-Art of Small Spacecraft Technology, ch. 4, Table 4-10 (2026) | krypton Hall devices, a comparator beside the row's generic Isp and kg/N (rc-364) |
| Woodcock, NTRS 20000085870, 2000, p. 7 | impulsive against low-thrust Earth escape, the anchor beside the 1.5 low-thrust penalty (rc-361) |
| NASA Glenn, RL10B-2 propulsion options, NTRS 20200002036, slide 7 | the tug's 465 s Isp (rc-358) |
| NASA, SLS Reference Guide, 2022, p. 9 | ICPS unfueled and fueled mass, the tug dry-fraction analogue (rc-359) |
| NASA, Apollo 10 Press Kit, p. 44 | LM-4 descent stage dry mass and propellant, the lander dry fraction (rc-360) |
| Arbit, Clapp, Dickerson & Nagai, NASA-CR-72325, 1968; NASA-CR-110530, 1970, Sec. 3.3.4 | Li / F2 / H2: 542 s theoretical, about 509 s achieved in test (rc-485) |
| Jacobson & Manzella, NASA/TM-2003-212700, Appendix p. 8 | NASA-457M krypton discharge efficiency, beside the 0.45 total efficiency (rc-458) |
| Honour et al., NTRS 20110013691; Perrin & Casler, NTRS 20160012100, Table 11 | modelled depot boil-off beside the hydrolox and depot scenarios (rc-490) |
| Boyce (Aerojet), chapter on the AJ10-137 in *Remembering the Giants: Apollo Rocket Propulsion Development*, NASA, 2010, NTRS 20100027319, <https://ntrs.nasa.gov/citations/20100027319>, p. 3 | Aerozine-50 / NTO: the AJ10-137's rated 314.5 s vacuum Isp at area ratio 62.5:1, the row's value (rc-754) |
| Cuffe & Jacobs (NASA MSC), *Apollo Spacecraft Engine Specific Impulse*, D2-I17060-1, 1970, NTRS 19700026467, <https://ntrs.nasa.gov/citations/19700026467>, p. 32 | Aerozine-50 / NTO: AEDC's injector-level measurements, 312.8 s and 311.4 s on two thrust chambers with a 0.2 s allocated uncertainty; a comparison, not the row's value (rc-754) |
| U.S. Department of Defense, DoD Manual 4145.26, *DoD Contractors' Safety Manual for Ammunition and Explosives*, Appendix 2, Table AP2.T18, p. 214, <https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodm/414526m.pdf> | component densities at 20.0 C: RP-1 0.81, N2O4 1.45, MMH 0.87, hydrazine 1.01, UDMH 0.79 kg/L; UDMH's stored 0.793 has a third decimal the table does not give (rc-675, rc-676) |
| IMO, Resolution MSC.420(97), *Interim Recommendations for Carriage of Liquefied Hydrogen in Bulk*, Annex 18, Table 3 (2016) | LCH4: pure methane at its 111.6 K normal boiling point, 422.5 kg/m³; LH2 at 20.3 K, 70.8 kg/m³ (rc-673, rc-674) |
| NIST, *Cryogen Safety* (NIST S 7101.52 Ver. 3), Appendix B, Table 1, p. 17 | LOX 1141 g/L at 90.2 K and liquid argon 1395 g/L at 87.3 K, at 101.325 kPa (rc-674) |
| Muscatello et al., NASA NTRS 20130009664 (SPACE 2013 abstract) | methalox: a Mars-analog bench demonstration, 31.7 g CH4/hr and 2.22 kg CH4/O2 per 14-hour day; nothing made on Mars (rc-663) |
| Ganguly & Saxena, *Space Manufacturing 7*, NTRS 19910015908, p. 97 | CO / LOX: an equilibrium estimate of ~135 g volatiles per kg of C2 chondrite, CO among them, with no recovery process (rc-662) |
| Epstein, Joppin, Kerrebrock & Schneider, *Microfabricated Liquid Rocket Motors*, final report on NAG3-2506, NTRS 20030020732, <https://ntrs.nasa.gov/citations/20030020732>, Appendix A, Table 6.1, p. 165 | HTP-98: 98% H2O2 at 25 C and 1 atm, 1430.9 kg/m³, reproduced from FMC Chemicals' Technical Bulletin 67 (Raleigh 1969) (rc-677) |
| Arnett, NASA TM-X-53859, 1969, NTRS 19700004114, <https://ntrs.nasa.gov/citations/19700004114>, Table 1, p. 8 | Aerozine-50: specific gravity 0.894-0.903, whose top the component takes; and 56.1 lb/ft³ at 77 F (0.8986 kg/L) (rc-678) |
| World Health Organization, *Iodine in drinking-water*, WHO/HEP/ECH/WSH/2020.5, Table 1.1, p. 2 | iodine: solid density 4.93 g/cm³ at 25 C, the material and not a packed reservoir (rc-808) |
| Nguyen & Steele, *An Overview of SBIR Phase 2 In-Space Propulsion and Cryogenic Fluids Management*, NASA/TM-2015-218829, NTRS 20150015569, <https://ntrs.nasa.gov/citations/20150015569>, p. 19 | iodine: Busek's ~2,000 s target for a full-scale iodine Hall system at high thrust; the row's Isp is a scenario on it (rc-807) |
| Mulkey & Cardiff (NASA GSFC), *Green Propulsion: A NASA GSFC Assessment*, 3AF Space Propulsion 2024, NTRS 20240006111, <https://ntrs.nasa.gov/citations/20240006111>, pp. 10-11 | PRISMA (2010) and its LMP-103S HPGP system, the green monoprop row's earlier flight; no performance figure is taken from it (rc-756) |
| Pourpoint, Wood, Pfeil, Tsohas & Son, *Feasibility Study and Demonstration of an Aluminum and Ice Solid Propellant*, Int. J. Aerospace Eng. 2012, 874076, <https://doi.org/10.1155/2012/874076>, sec. 7 | ALICE: the 7 Aug 2009 flight, and the 210 s peak Isp calculated from ground tests as the flight estimate (rc-755) |
| Risha, Connell, Yetter, Sundaram & Yang, *Combustion of Frozen Nanoaluminum and Water Mixtures*, J. Propulsion & Power 30(1), 133-142, 2014, <https://doi.org/10.2514/1.B34783>, Sec. I and Table 7 | ALICE: the ideal 207 / 230 s and the static-motor 56 / 83 / 133 s (rc-755) |
| Kerslake et al., *Flight and Ground Performance of the SERT II Thruster*, NASA-TM-X-52848, 1970, NTRS 19700022477, <https://ntrs.nasa.gov/citations/19700022477> | mercury ion: SERT-II's mercury bombardment thrusters, 1970 (rc-757) |
| Worlock, James, Hunter & Bartlett, *ATS-6 Cesium Bombardment Engine North-South Stationkeeping Experiment*, IEEE Trans. AES-11, 1975, NTRS 19760034957, <https://ntrs.nasa.gov/citations/19760034957> | ATS-6 flew cesium, not mercury (rc-757) |
| Hamidian & Dahlgren, *Testing and Evaluation of the LES-6 Pulsed Plasma Thruster*, JPL TM 33-630, 1973, NTRS 19740002615, <https://ntrs.nasa.gov/citations/19740002615>, p. 1 | PPT: LES-6's use in 1968 (rc-759) |
| Zalawski, Benson, Smernan & Hoskins, *On-Orbit Testing of the EO-1 Pulsed Plasma Thruster*, 2002, NTRS 20030025690, Table 1, p. 2; and NASA Science, *Earth Observing-1* mission page, <https://science.nasa.gov/mission/eo-1/> | PPT: EO-1's launch (21 Nov 2000), its flown unit's 650-1,400 s and 8% efficiency, the row's 0.08 (rc-759) |
| Oleson & McGuire, *COMPASS Final Report: Enceladus Solar Electric Propulsion Stage*, NASA/TM-2011-216973 (2011), NTRS 20110007141, <https://ntrs.nasa.gov/citations/20110007141>, pp. 37-38 | xenon: the NEXT PM1 mass (12.7 kg bare, 13.5 kg with harnesses) and 236 mN behind the row's 54 kg/N, a predecessor proxy and not NEXT-C (rc-829) |
| Fisher et al., *NEXT-C Flight Ion System Status*, AIAA 2020-3604 (2020), NTRS 20205005689, <https://ntrs.nasa.gov/citations/20205005689>, Table 1 p. 4 and p. 5 | xenon: NEXT-C's ~235 mN and 'approximately 14 kg', the comparator beside the PM1 proxy (rc-830) |
| Moran, *Conceptual study of on orbit production of cryogenic propellants by water electrolysis*, NASA-TM-103730 / AIAA 91-1844, 27th Joint Propulsion Conference (Jul 1991), NTRS 19910010004, <https://ntrs.nasa.gov/citations/19910010004> | hydrolox ISRU: 4.41 kWh/kg of water for electrolysis and 398 kW for the lunar processor (Table II, printed p. 16); the Mars-scaled plant at 378.2 kg/h of water (printed p. 6) and 2,790 kW (printed p. 17), about 7.4 kWh/kg; a comparator below the row's 15,200 Wh/kg (rc-836) |
| JAXA ISAS, *IKAROS* mission page, <https://www.isas.jaxa.jp/en/missions/spacecraft/past/ikaros.html>; The Planetary Society, *LightSail 2 Marks 1 Month of Solar Sailing* (23 Aug 2019), <https://www.planetary.org/articles/ls2-one-month-sailing>; NASA Marshall, *NEA Scout Status Update* (9 Dec 2022), <https://www.nasa.gov/centers-and-facilities/marshall/nea-scout-status-update/>; NASA PDS, NEA Scout spacecraft context record, <https://pds.nasa.gov/ds-view/pds/viewContext.jsp?identifier=urn%3Anasa%3Apds%3Acontext%3Ainstrument_host%3Aspacecraft.neas&version=1.1>; NASA, *NASA Composite Booms Deploy, Mission Sets Sail in Space* (29 Aug 2024), <https://www.nasa.gov/blogs/smallsatellites/2024/08/29/nasa-composite-booms-deploy-mission-sets-sail-in-space/> | solar sail milestones: IKAROS (launched 21 May 2010) the first solar-sail demonstration and the row's `first_flight`; LightSail 2's 7.2 km apogee raise; NEA Scout separated from SLS on 16 Nov 2022 but no contact was made and its sail deployment was never confirmed, and it was considered lost; ACS3's full deployment (rc-837) |
| Duplay, Bao, Rodriguez Rosero, Sinha & Higgins, *Design of a rapid transit to Mars mission using laser-thermal propulsion*, Acta Astronautica 192, 143-156 (2022), <https://doi.org/10.1016/j.actaastro.2021.11.032>, abstract and sec. 3.1 | beamed laser-thermal: a conceptual design assuming 3,000 s, within a stated 1,000-3,000 s range; it does not support the row's 900 s, which is a scenario (rc-842) |
| Squire et al., *VASIMR VX-200 Operation at 200 kW and Plume Measurements*, IEPC-2011-154, 32nd International Electric Propulsion Conference (2011), <https://www.adastrarocket.com/technical-papers-archives/Jared_IEPC11-154.pdf>, p. 1 | VASIMR: VX-200's measured argon point at 200 kW, 4,900 +/- 300 s and 72 +/- 9%, beside the row's 4,000 s and 0.50 scenario (rc-845) |
| Squire et al., *VASIMR Spaceflight Engine System Mass Study and Scaling with Power*, IEPC-2013-149, 33rd International Electric Propulsion Conference (2013), <https://www.adastrarocket.com/technical-papers-archives/IEPC13-149_JPSquire_submit.pdf> | VASIMR: a full-system mass study, against which the row's 53 kg/N has no recorded mass boundary (rc-845) |
| Chang Díaz, Giambusso, Corrigan, Dean & Warrayat, *Recent Progress on the VASIMR Engine*, IEPC-2022-525, 37th International Electric Propulsion Conference (2022), <https://www.adastrarocket.com/wp-content/uploads/2022/06/VASIMR_IEPC2022_525-Paper-final.pdf>, pp. 1 and 9 | VASIMR: VX-200SS's 88-hour endurance run at 80 kW, a different benchmark from VX-200's performance (rc-845) |
| Polk, Choueiri, Sheppard, Smith, Goebel, Martin & Polzin, *Development of High Power Lithium Magnetoplasmadynamic Thrusters to Support Human Mars Exploration*, IEPC-2024-841, 38th International Electric Propulsion Conference, Toulouse (2024), <https://alfven.princeton.edu/publications/pdf/polk-iepc-2024.pdf>, pp. 2 and 6 | lithium MPD: Princeton's 150 kW and 200 kW results (44% at 3,724 s, 50% at 4,240 s), beside the row's 4,000 s, 0.40 and 40 kg/N scenarios (rc-845) |

`first_flight` is the year of the first launch or flight of a vehicle using
that propulsion, successful or not, as `first_flight_year` is for a launch
vehicle (since 0.18.0; rc-760 to rc-764).

Vacuum Isp values are the interplanetary-relevant figures. Sea-level Isp is
lower and matters only to a first stage, which is already priced into the launch
table's $/kg-to-orbit.

## 3. Delta-v segments

| source | what it establishes |
|---|---|
| Curtis, *Orbital Mechanics for Engineering Students* | ascent and textbook segment values |
| Taylor et al. 2018, "Delta-v map of Main Belt Asteroids" | LEO to main-belt transfer, outbound only; the return row is a scenario (rc-515) |
| Cohen et al., Robotic Asteroid Prospector, NIAC Phase I, 2013, NTRS 20190001162, Sec. 4.2.2 and Table 4.1 | a typical-NEA return budget beside the propulsive return (rc-514) |
| Elvis et al. 2011, arXiv 1105.4152 | near-Earth object delta-v accessibility distribution, and its 6.65 km/s peak |
| Berthier, Carry, Mahlke & Normand, *SsODNet: Solar system Open Database Network*, A&A 671, A151 (2023), <https://doi.org/10.1051/0004-6361/202244878> | the ssoBFT NEA median (8.88 km/s) and main-belt fifth percentile (8.49 km/s) the average- and hard-NEA rows are compared against; IMCCE asks that any use of ssoBFT cite this paper (rc-767) |
| NASA DRA 5.0 (SP-2009-566), Fig 4-2 | the swing of trans-Mars injection across the synodic cycle |
| Orloff, *Apollo by the Numbers* (NASA SP-2000-4029), lunar-orbit phase tables | trans-lunar injection, lunar orbit insertion, and the Lunar Module's powered descent and ascent as flown on Apollo 14-17; trans-earth injection on Apollo 8, 10-12 and 14-17, the middle leg of the lunar surface to LEO row |
| Lyons (JPL), Magellan / MGS aerobraking; Long et al. 2007, MRO aerobraking operations | the aerobraked return's flight record |
| NASA NTRS and JPL design handbooks | the remaining trajectory legs |
| NASA-CR-195527, Table 2.1; Benson, Asher & Reese, 2025 | TLI and TLI-to-NRHO components, a cross-study benchmark for the NRHO row (rc-357) |
| Benson, Asher & Reese, *Enhancing Fast Transfer Launch Availability to the NRHO Using a Phasing Loop Approach*, AAS GN&C 2025, NTRS 20250000718, <https://ntrs.nasa.gov/citations/20250000718>, slide 5 | TLI → NRHO insertion: 400-450 m/s, whose top the row takes (rc-683) |
| Martinez & Whitley, *Options for Staging Orbits in Cis-Lunar Space*, IEEE Aerospace 2015, NTRS 20150019648 | NRO-to-LLO access (730 m/s, Table 3), context for the NRHO row; it gives no TLI-to-NRHO figure (rc-683) |
| NASA ISPT, Aerocapture for Discovery Missions, 2010, p. 12 | all-propulsive insertion for NEO return, ~4-5 km/s; why the aerocapture saving is unsourced (rc-293) |
| Beaurain, Souchier, Moravie, Sackheim & Cikanek, *Earth-to-Orbit Rocket Propulsion*, International Air and Space Symposium and Exposition preprint (Jul 2003), NTRS 20030066115, <https://ntrs.nasa.gov/citations/20030066115>, abstract | ~9 km/s to an Earth parking orbit with gravity and drag losses: the scale beside the 9,400 m/s surface-to-LEO scenario, not its exact value (rc-831) |

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
| Kleinhenz & Paz, An ISRU Propellant Production System for a Fully Fueled Mars Ascent Vehicle (the NTRS-hosted copy of the same paper titles it An ISRU Propellant Production System to Fully Fuel a Mars Ascent Vehicle), AIAA 2017-0423 / DOI 10.2514/6.2017-0423, NTRS 20170005179 | the high end of the plant throughput band (1.7 t for 29.7 t of CH4/O2 in 480 days) |
| Plane Talking (Gallagher) / Slingshot Aerospace, 2024 | launch insurance market rate, and the 2023 losses behind it |
| Damodaran (NYU Stern), Cost of Capital by Industry Sector (Jan 2026) | cost-of-capital floor: industry averages, with no startup premium |
| McKeown, What is an appropriate investment hurdle rate for commercial space resource development projects?, 2024 | the 10% standard discount rate for space-resource projects, and hurdle rates near 25% |
| Scottoline & Coleman, Effectiveness of Loan Guarantees versus Tax Incentives for Space Launch Ventures, 1999, NTRS 19990101869 | launch-venture debt at 14% or more without guarantees |
| The Planetary Society, Planetary Exploration Budget Dataset | Perseverance development + launch cost, the scale behind the autonomy NRE (the autonomy share itself is unsourced) |
| MIL-HDBK-189C (Jun 2011), 5.2.6 and Table II | the Duane growth model, and the historical growth rates the mining reliability exponent sits inside |
| 14 CFR Part 440 (eCFR), 440.9(c) and (e) | the third-party and US Government property caps on required liability insurance |
| FAA, Space Launch and Reentry Licensing and Permitting User Fees, 91 FR 21591 (22 Apr 2026) | the per-launch user fee owed from 2026 under 51 U.S.C. 50924 |
| Cross & Vesely, Synthesizing a New Launch Vehicle Failure Probability Based on Historical Flight Data, 2018, NTRS 20180006947 | first-flight failure probability of a new launch vehicle |
| Kinnett, Green, Klein & Lin (JPL), Remote Diagnosis and Operational Response to an In-Flight Failure of the Drill Feed Mechanism Onboard the Mars Science Laboratory Rover, Aerospace Mechanisms Symposium 2022 | the Curiosity drill entry in the mining success tally; and, pp. 1 and 13, the feed stall at sol 1536 and the first feed-extended sample at sol 2057 beside the rig trip limit (rc-698) |
| Berry et al., *Contact with Bennu! OSIRIS-REx TAG sample-collection performance*, NTRS 20210025295, <https://ntrs.nasa.gov/citations/20210025295>; ESA, *Philae's extraordinary comet landing relived* (2024); NASA Science, *Common Questions about InSight's "Mole"* (2020, updated 2024) | TAGSAM's single contact, Philae's unfired harpoons and HP3's want of soil friction: one-shot and failure-mode context beside the rig trip limit, not evidence for its value (rc-698) |
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
| Dawson & Bowles, Taming Liquid Hydrogen: The Centaur Upper Stage Rocket, 1958-2002, NASA SP-2004-4230, 2004 | Centaur programme costs, and the absence of a per-stage price behind the ~$30M high anchor |
| Kleinhenz & Paz 2017 and 2021 (above) | the published in-space processing rates the refinery throughput row is compared against |
| NASA OIG IG-18-016, Audit of Commercial Resupply Services to the International Space Station, 2018 | the whole-mission ceiling over depot berthing and sample recovery operations |
| NASA/TM-2011-215988, Issues of Long-Term Cryogenic Propellant Storage in Microgravity; Plachta et al., NASA Cryocooler Technology Developments and Goals to Achieve Zero Boil-Off, 2017 | named as out of scope for volatile cargo containment, which is an engineering estimate |
| Nugent, Grotenrath & Johnson, 20 Watt 20 Kelvin Reverse Turbo-Brayton Cycle Cryocooler Testing and Applications, 2022, NTRS 20220009350, Tables 1 and 3 | cryocooler specific power (91.6 W/W tested, 80 threshold) and specific mass (5.5 kg/W) |
| Hastings et al., Large-Scale Demonstration of Liquid Hydrogen Storage With Zero Boiloff for In-Space Applications, NASA/TP-2010-216453 | the Gifford-McMahon cooler's 350 W/W at 4% of Carnot |
| Poston, Gibson, Godfroy & McClure, KRUSTY Reactor Design, Nuclear Technology 206, S13-S30, 2020; McClure et al., Kilopower Project: The KRUSTY Fission Power Experiment and Potential Missions, same issue, S1-S12 | what KRUSTY demonstrated: a 5 kW(thermal) reactor, with electrical conversion shown in part |
| Bennett, Smith & Jakupca, Analysis of 100-W Regenerative Fuel Cell Demonstration, NASA/TM-20205000357, 2020, Table III | regenerative fuel cell round-trip efficiency, 47.4% |
| Greene et al., COPV Stress Rupture Testing, NTRS 20100021151; Kezirian, Johnson & Phoenix, COPV: Flight Rationale for the Space Shuttle Program, NTRS 20110015972; Parker & Prosser, NASA/TM-20260002192 | named as not giving a PV/W |
| NASA NTRS 20080009730, Tables 1-3 | measured COPV burst P_b V/W, 326.5-416.6 kJ/kg, a comparator for the performance factor (rc-417) |
| FRED CPIAUCSL (BLS CPI-U) | the mission-operations Dec 2018 sensitivity (rc-295) |
| Bennett & Baldwin, NASA/TM-2010-216906, Table 5 | five protected Li-ion packs at 124-133 Wh/kg, the analogy behind 130 Wh/kg (rc-342) |
| Gibson, Mason & Bowman, NASA/TM-2015-218460, Table I | the 10 kWe Kilopower design estimate, 1,544 kg (rc-349) |
| JPL D-101316, Solar Power Technologies for Future Planetary Science Missions, 2017, Table 3-3 | the ~150 W/kg roll-out array benchmark (rc-362) |
| Surampudi et al., JPL D-24454, 2002, Sec. 2.6 | historical array-only cost per watt beside the power-system cost (rc-374) |
| Sandvik, Rebuild Solutions, B15-1183ENG, p. 6 | major rebuild intervals by machine type, beside the rig trip limit (rc-365) |
| Jones, ICES-2017-87, p. 4 | water tank mass per kg of water, beside volatile containment (rc-373) |
| Mas, NBER WP 13138, 2007 | condition-priced used-equipment resale, beside the salvage fraction (rc-375) |
| Kascak et al., NASA/TM-2001-211138, p. 1 | the ISS 35-minute eclipse in a 92-minute orbit (rc-410) |
| Stubbs & Wang, Icarus 217, 2012, p. 275 | Vesta's surface solar visibility, beside the dark fraction (rc-413) |
| Csank, Electric Power on the Lunar Surface, NTRS 20240013588, slide 12 | regenerative fuel cell system Wh/kg by mission case (rc-414) |
| Comparators named in 0.16.2's notes (General_Research rc-202 to rc-416; each note names its own) | DLA FY2026 aerospace standard prices; SSC and NASA launch task orders; Firefly, Orienspace, JAXA, Xinhua and Guangzhou Daily price statements; Epignosis Insights and Epic Aerospace propellant prices; NASA KSC MLI tests (NTRS 20110014002); NASA G2 flywheel; NASA OIG IG-24-013 and IG-26-010; NASA Glenn NEXT-C contract; JPL MOCS 2014; Gallagher Q3 2026; Leucht, Prater & Vetcha 2024; NASA LuSTR; Herberhold et al. 2026; Barker et al. 2021; Daly et al. 2020 |
| Lewis et al. 2020 (NASA Langley), Table 2; Palaszewski, NTRS 20210026187, Table 3 | Mars ascent delta-v bracketing the 4,100 m/s scenario (rc-377) |
| Morren, NASA TM-105877, 1992, Table II | the 234 s water resistojet measurement, the top of the band (rc-378) |
| Carrier 1974; Graf 1993 (NASA RP-1265); Shearer et al. 2023; Nakamura et al. 2025 and 2012; Bonitz et al. 2009; Lauretta et al. 2024; NASA Release 21-117; Jia et al. 2021; Wang et al. 2024; ESA's Philae account; the InSight team's NASA Q&A | each flight outcome in the mining success tally (rc-396 to rc-407) |
| Plachta, Johnson & Feller, Cryogenic Boil-Off Reduction System Testing, NTRS 20150000134 | named as not giving an MLI areal density |
| Jansen & Dever, G2 Flywheel Module Design, NASA/CR-2006-213862 | the G2 flywheel's 60,000 rpm and 525 W-hr; it gives no Wh/kg |
| Comparators named in 0.17.1's notes (General_Research rc-451 to rc-517; each note names its own). Full references below since 0.17.2 (rc-805); each keeps the comparator role its note gives it | |
| Evans, Gallo & Kaminskiy, *A Bayesian Framework for Reliability Analysis of Spacecraft Deployments*, 2013 IEEE Aerospace Conference, NTRS 20120013705, <https://ntrs.nasa.gov/citations/20120013705> | 19 deployable-subsystem anomalies in 123 GSFC missions, beside mature mining success |
| Schuler et al., *ISRU Pilot Excavator (IPEx) Technology Readiness Level 5 Design Overview*, AIAA ASCEND 2024, NTRS 20240008162, <https://ntrs.nasa.gov/citations/20240008162> | IPEx's wheel-actuator life test, beside mature mining success |
| Grile & Bettinger, *Reliability analysis of deep space satellites launched 1991–2020: Bulk population and deployable satellite performance analysis*, Quality and Reliability Engineering International 40(7), 3809–3830 (2024), <https://doi.org/10.1002/qre.3600> | deep-space satellite reliability beside the spacecraft MTBF |
| SpaceX, *EU Prospectus*, approved by BaFin 5 Jun 2026, §§4.3.10.1–4.3.10.2, p. 58, <https://content.spacex.com/cms-assets/FINAL_Documents%20and%20Updates/SpaceX%20-%20EU%20Prospectus%20%28Approved%20by%20Bafin%29%20-%20June%205%2C%202026.pdf> | over 99% mission success across about 620 Falcon 9 launches, one family's aggregate, beside launch vehicle reliability |
| NASA / JPL, *Stardust Sample Return Press Kit* (2006), Quick Facts, p. 6, <https://www.jpl.nasa.gov/news/press_kits/stardust-return.pdf> | Stardust's 46 kg capsule, beside the return capsule cost |
| Johnson et al., *Demonstration of Multilayer Insulation, Vapor Cooling of Structure, and Mass Gauging for Large-Scale Upper Stages: Structural Heat Intercept, Insulation, and Vibration Evaluation Rig (SHIIVER) Final Report*, NASA/TP-20205008233 (2021), <https://ntrs.nasa.gov/citations/20205008233> | vapour cooling beside the vapour-cooled shield |
| Johnson & Stephens, *NASA's Cryogenic Fluid Management Technology Development Roadmaps*, JANNAF In-Space Chemical Propulsion TIM (2018), NTRS 20190000305, <https://ntrs.nasa.gov/citations/20190000305> | the CFM roadmap beside the vapour-cooled shield |
| Sibille et al., *Vacuum Sintering of Highland Simulant CSM-LHT-1G* (2023), NTRS 20230008596, <https://ntrs.nasa.gov/citations/20230008596>; Effinger & Allen, *Microwave Sintering Lunar Landing Pads & Horizontal Infrastructure* (2020), NTRS 20205010871, <https://ntrs.nasa.gov/citations/20205010871> | lunar-simulant sintering work, beside sintered / consolidated cargo |
| Dec & Braun, *An Approximate Ablative Thermal Protection System Sizing Tool for Entry System Design*, AIAA 2006-780, 44th AIAA Aerospace Sciences Meeting, <https://doi.org/10.2514/6.2006-780>, NTRS 20080013535, Table 2 | shield thickness against entry speed (PICA 8.324 cm at an 11 km/s lunar return, 10.873 cm at 14 km/s Mars return), the sensitivity beside `DOWNLEG_TPS_FRAC`'s 0.15 scenario; thickness, not a mass fraction (rc-739) |
| Stackpoole, Kao, Qu & Gonzales, *Post-Flight Evaluation of PICA and PICA-X: Comparisons of the Stardust SRC and Space-X Dragon 1 Forebody Heatshield Materials*, International Planetary Probe Workshop 2013, NASA ARC-E-DAA-TN9994, NTRS 20140005558, <https://ntrs.nasa.gov/citations/20140005558> | PICA / PICA-X heritage and material performance, the "material data" the heat shield row points to; it gives no cost, and the row's $/kg stays engineering judgement (rc-783) |
| Krog & Berstad, *Strategies for zero boil-off liquid hydrogen transfer: an export terminal case-study*, arXiv:2512.04609 (2025, preprint, not peer reviewed), <https://doi.org/10.48550/arXiv.2512.04609> | a ground export-terminal transfer study, the limited comparator for the 1% low end of in-space transfer loss; the 3% and 8% are not from it (rc-785) |
| Navard, *Modelling Early Failures on Space Station Freedom*, NASA/ASEE Summer Faculty Fellowship final report, JSC, 1993, NTRS 19940020890, <https://ntrs.nasa.gov/citations/19940020890>, p. 8 | a fitted electronics-survival model, which by its own account "does not model the early failures very well"; beside the spacecraft MTBF (rc-753) |
| Jacklin, *Small-Satellite Mission Failure Rates*, NASA/TM-2018-220034 (Mar 2019), NTRS 20190002705, <https://ntrs.nasa.gov/citations/20190002705>, pp. 15 and 17 | a different population and evidence type: small-satellite missions of 2000-2016, 41.3% total or partial failures, and annual success rates. Neither it nor Navard is a deep-space MTBF; the row's 30 years [15, 60] is an unfitted scenario (rc-753) |
| NASA Office of Inspector General, *NASA's Management of the Human Landing System Contracts*, IG-26-004 (10 Mar 2026), <https://oig.nasa.gov/wp-content/uploads/2026/03/final-report-ig-26-004-nasas-management-of-the-human-landing-system-contracts.pdf>, p. 11 | more than 10 tanker launches after a depot launch, one every 6 days: a lunar-HLS plan, the comparator the 12 [8, 16] tanker-launch scenario sits inside, not evidence for an asteroid departure (rc-826) |
| NASA Office of Inspector General, *NASA's Management of Space Launch System Program Costs and Contracts*, IG-20-012 (10 Mar 2020), <https://oig.nasa.gov/wp-content/uploads/2024/02/IG-20-012.pdf>, p. 23 | the $29M second-ICPS hardware purchase: a whole-stage comparator beside the expendable upper stage rate, not a Centaur III or tank-only cost (rc-833) |
| Parcero, Allen, Witkowski, McKee & Torres, *Planetary Mission Entry Vehicles Quick Reference Guide*, Version 4.0, NASA/SP-20220010761 (2022), <https://ntrs.nasa.gov/citations/20220010761>, Hayabusa table, printed p. 23 | Hayabusa's 18 kg capsule and 1.04 kg payload: a sample-return comparator beside the generic 0.10 capsule factor, not a substitute for it (rc-834) |
| Leucht, Prater & Vetcha, *Overview and Results from NASA's Break The Ice Lunar Challenge*, conference paper for the 46th IEEE Aerospace Conference (1-8 Mar 2025), NTRS 20240015957 (record acquired 12 Dec 2024), <https://ntrs.nasa.gov/citations/20240015957>, printed p. 2 | a 5-year system lifetime target for lunar regolith and resource delivery, beside the mining rig's 15 years [5, 30]; a lunar technology target, not an asteroid rig life (rc-846) |

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
| NIST, *2018 CODATA Recommended Values of the Fundamental Constants of Physics and Chemistry*, NIST SP 959 (Jun 2019), p. 1, <https://physics.nist.gov/cuu/pdf/wallet_2018.pdf> | the Stefan-Boltzmann constant behind `BLACKBODY_TEMP_1AU_K`: the stored 5.670374419e-8 is CODATA's first ten significant digits, and 278.3 K rounds (1361 / 4σ)^(1/4) = 278.32 K (rc-669) |
| 3rd CGPM (1901), Declaration 2, *Proceedings* p. 70, <https://doi.org/10.59161/CGPM1901DECL2E> | `G0_M_S2`, the conventional standard acceleration of gravity g_n = 980.665 cm/s², not a local gravity (rc-667) |
| NIST Handbook 133 (2026), Appendix E, p. 248, <https://doi.org/10.6028/NIST.HB.133-2026>; Thompson & Taylor, NIST SP 811 (2008), Appendix B.9, <https://doi.org/10.6028/NIST.SP.811e2008> | `LITRES_PER_GAL`, the US gallon at 3.785 411 784 L, and `LITRES_PER_BBL`, the 42-US-gallon petroleum barrel, 158.987 294 928 L (rc-668) |
| BIPM / IAU definitions of the astronomical unit and of `c` | light time over 1 AU, which is a ratio of two defined integers and so exact |

**Bodies**

| source | what it establishes |
|---|---|
| NASA Moon Fact Sheet | lunar mass, radius and synodic day |
| NASA Mars Fact Sheet | Mars mass, radius and rotation; the Phobos mass and axes the Phobos row is compared against |
| Willner, Shi & Oberst 2014, Phobos' shape and topography models, *Planet. Space Sci.* 102:51-59 (with the GM it quotes from Andert et al. 2011) | the Phobos mean radius, volume and mass the Phobos row is compared against (neither prints the row's radius) |
| Guo et al., MNRAS 548, stag578, 2026, Table 3 | Phobos GM, the mass since 1.26.0 (rc-331) |
| Farnocchia et al., AJ 168:21, 2024, Table 2 | Psyche GM and mass since 1.26.0 (rc-332) |
| Lauretta et al. 2019, *Nature* (OSIRIS-REx) | Bennu mass, radius, rotation, orbit |
| Watanabe et al. 2019, *Science* (Hayabusa2) | Ryugu mass, radius, rotation, orbit |
| Yeomans et al. 2000, *Science* (NEAR Shoemaker) | Eros mass and radius |
| Daly et al. 2023, *Nature* (DART) | Didymos rotation, and the system mass and diameter the row's unsourced mass and radius sit inside |
| Russell et al. 2016, *Science* (Dawn) | Ceres mass and radius |
| Kretlow 2020, SiMDA data set (as tabulated in Kretlow 2022, *A&A* 668:A141, Table 2) | Psyche mass |
| Siltala & Granvik 2021 | Psyche radius, and a mass 3% below the row's as a cross-check |
| Ferrais, Vernazza, Jorda et al., A&A 638:L15 (2020), DOI 10.1051/0004-6361/202038100 | Psyche's volume-equivalent diameter, the one Siltala & Granvik adopt |
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
| McGuire, McCarty & Burke, *Power and Propulsion Element (PPE) Spacecraft Reference Trajectory Document*, NASA/TM-2020-220481, sec. 3.1, p. 5 | Gateway's 9:2 L2 Southern NRHO, 6.56 days, lunar eclipses under 90 minutes: the NRHO row's 0.01 as one eclipse per orbit (rc-747) |
| NASA, Webb FAQ; ESA, Gaia operations | Sun-Earth L2: eclipse-free halo and Lissajous orbits, the row's 0 for both Earth and Moon shadows (rc-746) |
| NASA NSSDCA, Moon Fact Sheet (1,737.4 km mean radius) | low lunar orbit: the zero-beta cylindrical-shadow check, 0.3945 (rc-744) |
| Rucker, *Mars Surface Power Generation Challenges and Considerations*, NASA NTRS 20230015763, p. 2; NASA Mars Fact Sheet | Mars surface: ~50% illumination for a typical mid-latitude mission, and the 24.6597 h sol (rc-751) |
| NASA Mars Fact Sheet, Satellites of Mars | Phobos: 0.31891 d sidereal orbit and rotation; its 0.50 is a surface-night scenario without Mars eclipses (rc-752) |
| NASA NSSDCA, *Magellan: Mission Plan*; McNutt et al., *MESSENGER at Mercury: Early orbital operations*, Acta Astronautica (2012), pp. 2-3 | Venus and Mercury orbits: Magellan's 3 h 15 min and MESSENGER's 12 h orbits as comparators; both eclipse fractions are scenarios (rc-742) |
| Stubbs & Wang, Icarus 217 (2012), sec. 5.1, p. 275 | the small bodies' shared 0.50, an equatorial no-tilt scenario beside Vesta's 0.363-0.566 (rc-745) |

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

The per-volume quotes become $/kg through `units.COMMODITY_DENSITY_KG_PER_L`.
`heating_oil`'s 0.845 kg/L is a proxy: HO=F is NY Harbor ULSD, Grade 62, with
its volume set at 60 F (CME NYMEX Rulebook, Chapter 150, p. 1), while the
matching 0.845 is IEA's French household *fuel oil domestique* (*Energy
Prices 2022*, Documentation, p. 146), a different product at no stated
temperature (rc-670).

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
`pipeline_version` column. A build also writes `build_manifest.json` beside
the tables, naming both with the catalog date.

## 10. Citing the upstream project

These tables were built as Module 3 of `economicspace`. If your work leans on
the model rather than only on the tables, cite that instead:

> economicspace, https://github.com/loggger101/economicspace
