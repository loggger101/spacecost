# -*- coding: utf-8 -*-
"""Launch vehicle reference table: 76 vehicles, one row each, every row cited.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).  Re-audited and
expanded from 36 to 76 rows at pipeline_version 1.16.0 (2026-09-23).
"""

import math
from typing import List

import numpy as np

from ._log import say
from .fairings import FAIRINGS

# ─────────────────────────────────────────────────────────────────────────────
# LAUNCH VEHICLE REFERENCE TABLE
# ─────────────────────────────────────────────────────────────────────────────
# One row per vehicle CONFIGURATION.  $/kg-to-LEO is the headline figure;
# $/kg-to-GTO and $/kg-to-escape are list_price_usd divided by the
# corresponding payload mass for that destination.
#
# For reusable vehicles the payload masses MUST be self-consistent with the
# stated list price's recovery mode (e.g. Falcon Heavy partial-reuse $97M
# pairs with the partial-reuse payload, NOT the 63.8 t all-expendable max).
# A different recovery mode is a different price, so it is a different ROW:
# that is why Falcon 9 and Falcon Heavy each appear twice.
#
# Sources cited inline in each row's `notes`; reference_year tags staleness.
#
# ─── THE HEADLINE IS THE CENTRE OF ITS BAND  (v1.16.0) ──────────────────────
# A row states EITHER one figure, where the source gives one, OR the low and
# high ends of its credible range.  With a range, the headline price and
# payload are DERIVED as the geometric centre of the band (`band_centre`), so
# a wide range lands in the middle rather than at whichever end was to hand.
# The bands themselves were chosen conservatively: where the source is a
# target (anything not yet flying) the target is the optimistic end, because
# launch-vehicle targets are optimistic by construction, and the other end is
# what the vehicle has actually shown or what a comparable one costs.
#
# ─── PAYLOAD SEMANTICS: 0 AND NaN ARE DIFFERENT  (v1.16.0) ──────────────────
#   0     the vehicle does not go there at all (Electron to GTO)
#   NaN   it could, but no figure is published, and this table will not
#         invent one.  `cheapest_launch_to` drops both, since neither is a
#         price, but only one of them is a statement about the vehicle.
#
# `payload_escape_kg` is C3 ≈ 0 where published, else trans-lunar injection
# (C3 ≈ -2, slightly easier) or Mars transfer (C3 ≈ 8-15, harder).  Which one
# is in each row's notes.

# ─── SCHEMA ADDED v1.9.0 ─────────────────────────────────────────────────────
# Five fields, applied to every row by _apply_launch_defaults() below so that a
# conventional rocket only has to state what makes it unusual:
#
#   launch_type    chemical_rocket | kinetic | maglev | gun | airbreathing |
#                  tether.  The table used to assume every launcher was a
#                  chemical rocket, which meant the alternatives could not be
#                  written down at all; not that they had been rejected.
#   origin         earth_surface | lunar_surface.  A lunar mass driver or
#                  elevator is a launch system whose $/kg is an order of
#                  magnitude below anything on this list, and it is only
#                  reachable AFTER there is something on the Moon.  Module 4
#                  models Earth departure only, so non-Earth origins are gated.
#   trl            Technology readiness, 1-9, same scale as the propellants.
#   max_accel_g    Peak axial acceleration the payload sees.  A rocket is 4-6 g.
#                  It is in this table because it is DISQUALIFYING for the
#                  kinetic launchers: SpinLaunch is ~10,000 g and a gun is
#                  ~30,000 g, which passes propellant and steel and destroys
#                  every mining rig, optic and reaction wheel in the catalog.
#   tanker_flights_for_escape
#                  Refuelling flights the escape-payload figure assumes.  Zero
#                  for everything that reaches escape in one launch.  Starship's
#                  own notes field has said "Module 4 should add ~$90M ×
#                  N_tankers" since v1.4.0 and nothing ever did, so its 27 t to
#                  escape was being priced at one launch.  Now it is a column
#                  rather than a sentence, and Module 4 reads it.
#
# ─── SCHEMA ADDED v1.16.0 ────────────────────────────────────────────────────
# Stated on every row (no default, because a wrong default here is silent):
#
#   country          who builds and flies it.
#   availability     open | restricted | government_only | sold_out |
#                    unavailable.  `status` says whether it FLIES; this says
#                    whether YOU can buy it.  Atlas V is operational and
#                    sold out.  A Chinese or Russian vehicle is operational and,
#                    for any payload with US-controlled parts or a Western
#                    operator, not a real option (`restricted`).  Kept separate
#                    from `status` so the Module 4 gate is unchanged.
#   core_propellant  kerolox | methalox | hydrolox | hypergolic | solid |
#                    propalox | not_applicable.  The core or first stage at
#                    liftoff, strap-on boosters excluded.
#   first_flight_year  first launch of the full vehicle in this
#                    configuration, orbital or not; None if it has not flown.
#   price_basis      published | contract | reported | estimate | target.
#                    How much the price column should be trusted.
#
# Defaulted when a row does not state them:
#
#   reusability      expendable | first_stage | side_boosters | partial |
#                    full | not_applicable.  Default expendable.
#   list_price_usd_low / _high, payload_{leo,gto,escape}_kg_low / _high
#                    the credible band.  A row with one figure gets a band of
#                    zero width.  A row with a band gets its headline DERIVED
#                    as the band's geometric centre; stating both raises.
#
# DERIVED, never typed (a row that types one raises at import):
#
#   fairing_volume_m3, fairing_basis        from fairings.FAIRINGS, by name;
#                                           see that module.  `notes` gains a
#                                           closing "Fairing volume:" sentence
#                                           naming the source.  (v1.17.0)
#   usd_per_kg_to_{leo,gto,escape}          list_price_usd / payload
#   usd_per_kg_to_{leo,gto,escape}_low      list_price_usd_low / payload_high
#   usd_per_kg_to_{leo,gto,escape}_high     list_price_usd_high / payload_low
#
# All rounded to whole dollars.  Until v1.16.0 the headline $/kg was typed
# beside the price and payload it restates, and a test at 1% was the only thing
# holding the three together.  Deriving it removes the way that goes wrong.
_LAUNCH_DEFAULTS = {
    "launch_type":               "chemical_rocket",
    "origin":                    "earth_surface",
    "trl":                       9,
    "max_accel_g":               6.0,
    "tanker_flights_for_escape": 0,
    "reusability":               "expendable",
}

_REF_YEAR_LAUNCH = 2026

# EUR -> USD for the European rows, and the 2026 SpaceX price rise used to
# carry older Falcon Heavy quotes forward.  Named so the notes can say which.
_USD_PER_EUR = 1.15
_SPACEX_2026_RISE = 74 / 70     # Falcon 9 list price, $70M -> $74M, Feb 2026

LAUNCH_VEHICLES_REFERENCE: List[dict] = [
    # ═════════════════════════════════════════════════════════════════════════
    # OPERATIONAL — UNITED STATES
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                          "Falcon 9 (reusable)",
        "operator":                      "SpaceX",
        "country":                       "USA",
        "status":                        "operational",
        "availability":                  "open",
        "reusability":                   "first_stage",
        "core_propellant":               "kerolox",
        "first_flight_year":             2010,
        "payload_leo_kg_low":            17_400,    # demonstrated Starlink stack
        "payload_leo_kg_high":           17_500,    # SpaceX reusable figure
        "payload_gto_kg":                 5_500,    # reusable drone-ship (8,300 is EXPENDABLE)
        "payload_escape_kg":              2_500,    # C3=0 reusable estimate (expendable row lifts 4,020)
        "list_price_usd":            74_000_000,    # SatBase 2026-02 price hike (was $70M)
        "price_basis":                   "published",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: SpaceX list price (raised to $74M Feb 2026 per SatBase) + "
                 "Falcon 9 Payload User's Guide.  All payload figures are the "
                 "drone-ship recovery (reusable) config; see the expendable row. "
                 "689 launches, 2 in-flight failures (CRS-7, Starlink 9-3) as of "
                 "mid-2026.  The LEO low end is the ~17.4 t Starlink stack "
                 "actually flown, to a LOW insertion orbit: a customer payload "
                 "to a 400-500 km orbit gets less.",
    },
    {
        "name":                          "Falcon 9 (expendable)",
        "operator":                      "SpaceX",
        "country":                       "USA",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "kerolox",
        "first_flight_year":             2010,
        "payload_leo_kg":                22_800,
        "payload_gto_kg":                 8_300,
        "payload_escape_kg":              4_020,    # Mars transfer, SpaceX figure
        "list_price_usd_high":      120_000_000,
        "list_price_usd_low":        90_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: SpaceX payload figures; 22,800 kg LEO is also Zapata "
                 "2017 (NASA, 'State of Play', p16).  SpaceX does not "
                 "publish an expendable price; $90-120M is the range implied by "
                 "NASA and NSSL task orders flown expendable, in nominal "
                 "dollars; the headline is the centre of that range.  The same "
                 "chart prices NASA LSP Class C science at $92M and DoD GPS at "
                 "$97M in 2017 dollars, $124M and $131M at CPI-U x1.3484 (Dec "
                 "2017 to Aug 2026), above the band's top.  "
                 "Escape is the published Mars-transfer figure, which is "
                 "harder than C3=0 and so conservative for it.",
    },
    {
        "name":                          "Falcon Heavy (reusable side cores)",
        "operator":                      "SpaceX",
        "country":                       "USA",
        "status":                        "operational",
        "availability":                  "open",
        "reusability":                   "side_boosters",
        "core_propellant":               "kerolox",
        "first_flight_year":             2018,
        "payload_leo_kg":                30_000,    # conservative partial-reuse figure
        "payload_gto_kg":                 8_000,    # SpaceX: "$97M, up to 8 t to GTO"
        "payload_escape_kg":              3_500,    # partial-reusable interplanetary
        "list_price_usd_high": int(round(97_000_000 * _SPACEX_2026_RISE, -6)),
        "list_price_usd_low":        97_000_000,    # SpaceX list price (2022)
        "price_basis":                   "published",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: SpaceX $97M (2022) for up to 8 t to GTO with boosters "
                 "recovered.  The high end carries that forward by the Feb 2026 Falcon "
                 "9 rise ($70M -> $74M) to $103M, since SpaceX raised one and the "
                 "other quote is four years old.  SpaceX publishes no LEO figure "
                 "for this config: 30 t is the figure in Wikipedia's launcher "
                 "comparison.  The 57 t this row carried until v1.16.0 had no "
                 "source and is gone rather than kept as an optimistic end: "
                 "the headline is now the centre of each band, so an unsourced "
                 "end would move it.  13 flights, 13 "
                 "successes; 1 of 3 centre-core landings.",
    },
    {
        "name":                          "Falcon Heavy (expendable)",
        "operator":                      "SpaceX",
        "country":                       "USA",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "kerolox",
        "first_flight_year":             2018,
        "payload_leo_kg":                63_800,
        "payload_gto_kg":                26_700,
        "payload_escape_kg":             16_800,    # Mars transfer
        "list_price_usd_high":      178_000_000,    # NASA, Europa Clipper (2021)
        "list_price_usd_low":       150_000_000,    # SpaceX (2017)
        "price_basis":                   "published",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: SpaceX $150M (2017) for the fully expendable config "
                 "is the low end.  The high end is what NASA paid for the "
                 "Falcon Heavy that launched Europa Clipper, $178M (NASA OIG "
                 "IG-24-001, p24; awarded 2021), a government full-service "
                 "price the band spans by decision.  Until 0.8.0 the high end "
                 "was the $150M carried forward by the 2026 Falcon 9 rise "
                 "($159M), and the centre $154M.  This row mixes nominal "
                 "years: the 2017 low end is $202M at CPI-U x1.3484 (Dec 2017 "
                 "to Aug 2026), above the high end.  The "
                 "63.8 t LEO figure (Zapata 2017, NASA, 'State of Play', p16) "
                 "has never been flown; no Falcon Heavy "
                 "payload has come close to it.  Volume, not mass, binds first "
                 "at this size: the fairing is the Falcon 9 fairing.",
    },
    {
        "name":                          "SLS Block 1",
        "operator":                      "NASA",
        "country":                       "USA",
        "status":                        "operational",
        "availability":                  "government_only",
        "core_propellant":               "hydrolox",
        "first_flight_year":             2022,
        "payload_leo_kg":                95_000,    # 200 km, 28.5 deg
        "payload_gto_kg":                np.nan,    # none published
        "payload_escape_kg":             27_000,    # TLI, ">27 t"
        "list_price_usd_high":    2_800_000_000,
        "list_price_usd_low":     2_500_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: NASA OIG — $2.2B SLS production + $568M ground systems "
                 "per launch (IG-22-003, Nov 2021), and 'at least $2.5B' recurring "
                 "(Oct 2023).  Launch vehicle ONLY: the widely quoted ~$4.1B is "
                 "per Artemis flight and includes Orion and its service module. "
                 "Artemis I (Nov 2022) and Artemis II (crewed, Apr 2026).  In Feb "
                 "2026 NASA cancelled Block 1B and the Exploration Upper Stage "
                 "and standardised on this configuration.  It has only ever flown "
                 "Orion; the fairing volume is the cargo configuration NASA "
                 "documents for it, which has not flown.",
    },
    {
        "name":                          "Atlas V 551",
        "operator":                      "ULA",
        "country":                       "USA",
        "status":                        "operational",
        "availability":                  "sold_out",
        "core_propellant":               "kerolox",
        "first_flight_year":             2006,
        "payload_leo_kg":                18_814,
        "payload_gto_kg":                 8_900,
        "payload_escape_kg":              6_500,
        "list_price_usd":           211_000_000,
        "price_basis":                   "published",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: ULA RocketBuilder $153M base (2016), carried to 2026 "
                 "dollars by CPI-U (Dec 2016 to Aug 2026, x1.3771): $211M.  "
                 "Until 0.6.0 the 2016 figure stood unescalated.  Government missions "
                 "add $30-80M for mission assurance (SpaceNews 2024).  NOT FOR "
                 "SALE: ULA stopped selling Atlas V in Aug 2021 and every "
                 "remaining vehicle is allocated, the last of them to Starliner. "
                 "Kept because its flight record is the reference that newer "
                 "vehicles' prices are argued against.  LEO payload: Atlas V "
                 "Launch Services User's Guide Rev 11 (Mar 2010), Table "
                 "2.6.5-2f, single burn to 200 km, 18,814 kg of payload system "
                 "weight, adapter included.  Zapata 2017 (NASA, 'State of "
                 "Play', p16) charts 18,856 kg to 200 km / 28.5 deg, 42 kg "
                 "above it.  The 18,850 kg high end this row carried until "
                 "0.15.0 matches no table in the guide.",
    },
    {
        "name":                          "Vulcan Centaur VC2",
        "operator":                      "ULA",
        "country":                       "USA",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "methalox",
        "first_flight_year":             2024,
        "payload_leo_kg":                16_300,
        "payload_gto_kg":                 8_300,
        "payload_escape_kg_low":          3_600,    # Mars transfer
        "payload_escape_kg_high":         6_200,    # TLI
        "list_price_usd":           110_000_000,
        "price_basis":                   "published",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: ULA 'starting at $110M', which is the smallest "
                 "configuration, so this row is the only one it prices "
                 "directly.  LEO: Vulcan User's Guide (Oct 2023), Table "
                 "2.2.1-1, 16,300 kg to the 407 km / 51.6 deg ISS orbit.  Escape band runs "
                 "from Mars transfer (harder than C3=0) to TLI (easier).  Maiden "
                 "flight carried Peregrine, Jan 2024.",
    },
    {
        "name":                          "Vulcan Centaur VC4",
        "operator":                      "ULA",
        "country":                       "USA",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "methalox",
        "first_flight_year":             2025,
        "payload_leo_kg":                21_400,
        "payload_gto_kg":                11_600,
        "payload_escape_kg_low":          6_000,    # Mars transfer
        "payload_escape_kg_high":         9_100,    # TLI
        "list_price_usd_high":      130_000_000,
        "list_price_usd_low":       110_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "LEO: Vulcan User's Guide (Oct 2023), Table 2.2.1-1, 21,400 kg "
                 "to the 407 km / 51.6 deg ISS orbit, on the long upper stage.  ULA's $110M is a "
                 "STARTING price and each pair of GEM 63XL boosters adds to it; "
                 "$130M is an estimate, not a quote.  Two of four Vulcan flights "
                 "to Feb 2026 had a GEM 63XL anomaly (a lost nozzle Oct 2024, a "
                 "malfunction Feb 2026) that the core stage flew through.",
    },
    {
        "name":                          "Vulcan Centaur VC6",
        "operator":                      "ULA",
        "country":                       "USA",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "methalox",
        "first_flight_year":             None,
        "trl":                           8,     # this config unflown; see notes
        "payload_leo_kg_low":            25_600,
        "payload_leo_kg_high":           27_200,    # with RL10E / early ULA figure
        "payload_gto_kg_low":            14_400,
        "payload_gto_kg_high":           15_300,    # with RL10E
        "payload_escape_kg_low":          7_600,    # Mars transfer
        "payload_escape_kg_high":        11_300,    # TLI
        "list_price_usd_high":      150_000_000,
        "list_price_usd_low":       110_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "LEO band spans two orbits: 25,600 kg to the 407 km / 51.6 deg "
                 "ISS orbit (Vulcan User's Guide, Oct 2023, Table 2.2.1-1, long "
                 "upper stage) and 27,200 kg to 200 km / 28.7 deg (ULA technical "
                 "summary, 2022); the GTO high end is the RL10E-upgraded "
                 "Centaur.  Until v1.16.0 this row priced VC6 "
                 "at $110M, which is ULA's STARTING price for the smallest "
                 "config; six GEM 63XLs are not free, and $150M is an estimate. "
                 "Its old 7,200 kg 'escape' figure was the GEO payload; escape "
                 "now runs Mars transfer to TLI.  THIS CONFIGURATION HAS NOT "
                 "FLOWN: all four Vulcan flights to Feb 2026 were VC2S or VC4S, "
                 "and the first VC6 is manifested for Oct 2026.  Kept "
                 "'operational' as a configuration of a flying vehicle, at TRL 8.",
    },
    {
        "name":                          "New Glenn",
        "operator":                      "Blue Origin",
        "country":                       "USA",
        "status":                        "operational",
        "availability":                  "open",
        "reusability":                   "first_stage",
        "core_propellant":               "methalox",
        "first_flight_year":             2025,
        "payload_leo_kg":                45_000,
        "payload_gto_kg":                13_600,
        "payload_escape_kg":              7_000,    # TLI
        "list_price_usd_high":      110_000_000,
        "list_price_usd_low":        68_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Blue Origin / Wikipedia, $68-110M reported range.  "
                 "Until v1.16.0 this row used the LOW end; the headline is now "
                 "the centre of the range.  Three flights: NG-1 Jan 2025 (orbit, booster "
                 "lost), NG-2 Nov 2025 (ESCAPADE, first landing), NG-3 Apr 2026 "
                 "(first booster reuse, but BlueBird 7 was left in an "
                 "off-nominal orbit).  The 45 t LEO figure has not been flown.",
    },
    {
        "name":                          "Electron",
        "operator":                      "Rocket Lab",
        "country":                       "USA / New Zealand",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "kerolox",
        "first_flight_year":             2017,
        "payload_leo_kg":                   300,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd_low":         7_100_000,    # 10-Q FY2026 Q1: Q1 2025 actual
        "list_price_usd_high":        9_300_000,    # 10-Q FY2026 Q1: Q1 2026 actual
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Rocket Lab Form 10-Q FY2026 Q1, MD&A: revenue per "
                 "launch was $9.3M in Q1 2026 and $7.1M in Q1 2025, which "
                 "are the band's ends; the filing puts the rise down to "
                 "customer mix and mission complexity, and gives cost per "
                 "launch as $5.4M and $5.7M.  Until 0.7.0 the row carried "
                 "$7.5M, attributed to this filing, which does not contain "
                 "it.  Payload User's Guide v8.0: up to 300 kg LEO, nominal 200 "
                 "kg to 500 km SSO; the 320 kg high end this row carried until "
                 "0.15.0 is not in the guide.  Small-sat "
                 "dedicated; useful for prospector probes only.  Its Photon "
                 "kick stage did send CAPSTONE (~25 kg) to the Moon, but that "
                 "is a spacecraft bus, not a launch capability, so escape is 0.",
    },
    {
        "name":                          "Alpha",
        "operator":                      "Firefly Aerospace",
        "country":                       "USA",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "kerolox",
        "first_flight_year":             2021,
        "payload_leo_kg":                 1_030,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd_high":       17_600_000,
        "list_price_usd_low":        15_000_000,
        "price_basis":                   "published",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Firefly, $15-17.6M.  Small-lift kerolox.  Seven flights "
                 "to Mar 2026: 3 successes, 2 partial failures, 2 failures (the "
                 "latest Apr 2025), then a clean return to flight Mar 2026. "
                 "Listed for market completeness at the bottom end.",
    },
    {
        "name":                          "Minotaur IV",
        "operator":                      "Northrop Grumman",
        "country":                       "USA",
        "status":                        "operational",
        "availability":                  "government_only",
        "core_propellant":               "solid",
        "first_flight_year":             2010,
        "payload_leo_kg_low":             1_591,
        "payload_leo_kg_high":            1_735,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd_high":       76_000_000,
        "list_price_usd_low":        50_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — ~$50M (2010), carried to 2026 dollars by "
                 "CPI-U (Dec 2010 to Aug 2026, x1.5155) for the high end; it "
                 "used x1.45, an annual chain that stopped at 2024, until 0.6.0.  "
                 "Payload low end: Wikipedia's infobox, 200 km / 28.5 deg; the "
                 "User's Guide 2.5 (Nov 2025) gives curves in section 3.3, "
                 "counting the separation system and adapter as payload.  The "
                 "1,735 kg high end's source is not recorded.  "
                 "US GOVERNMENT MISSIONS ONLY: it "
                 "flies surplus Peacekeeper ICBM motors, which law restricts to "
                 "government use.  Still flying (NROL-174 Apr 2025, STP Apr "
                 "2026).",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # OPERATIONAL — RUSSIA
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                          "Soyuz-2.1a",
        "operator":                      "Roscosmos",
        "country":                       "Russia",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "kerolox",
        "first_flight_year":             2004,
        "payload_leo_kg_low":             6_800,    # Plesetsk, 72 deg
        "payload_leo_kg_high":            7_460,    # Vostochny, 51.6 deg
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":             np.nan,
        "list_price_usd_high":       35_000_000,
        "list_price_usd_low":        30_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia (Soyuz-2) payloads by launch site.  Price "
                 "estimated against the 2018 $35M quote for a 2.1b without an "
                 "upper stage.  Flies Progress and crewed Soyuz.  Effectively "
                 "unavailable to Western customers under sanctions.",
    },
    {
        "name":                          "Soyuz-2.1b",
        "operator":                      "Roscosmos",
        "country":                       "Russia",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "kerolox",
        "first_flight_year":             2006,
        "payload_leo_kg_low":             7_730,    # Plesetsk
        "payload_leo_kg_high":            8_670,    # Baikonur
        "payload_gto_kg_low":             2_900,    # with Fregat, from Russian soil
        "payload_gto_kg_high":            3_250,    # from Kourou, ended 2022
        "payload_escape_kg":              2_400,
        "list_price_usd":            48_500_000,    # Glavkosmos 2018 with Fregat
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Glavkosmos / TASS 2018 price ($48.5M w/ Fregat); "
                 "payloads from Wikipedia by launch site.  The 3,250 kg GTO "
                 "figure this row used until v1.16.0 was the Kourou one, and "
                 "Soyuz has not flown from Kourou since Feb 2022.  Effectively "
                 "unavailable to Western customers under sanctions.",
    },
    {
        "name":                          "Angara A5",
        "operator":                      "Khrunichev / Roscosmos",
        "country":                       "Russia",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "kerolox",
        "first_flight_year":             2014,
        "payload_leo_kg":                24_500,    # 200 km x 60 deg
        "payload_gto_kg_low":             5_400,    # with Briz-M
        "payload_gto_kg_high":            7_500,    # with KVTK, not yet flown
        "payload_escape_kg":             np.nan,
        "list_price_usd":           100_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Khrunichev's 2019 financial report via BBC Russian, "
                 "production cost 7.0 billion rubles against a 2024 target of "
                 "4.0: $108M at the 2019 rate and $95M at 2021's, either side of "
                 "this $100M.  LEO: 24.5 t (Khrunichev, via BBC; Roscosmos, 24-"
                 "24.5 t, Scientific Russia, 2024).  Five flights "
                 "since 2014, one partial failure; first from Vostochny Apr "
                 "2024.  Replaces Proton.  Sanctions-restricted.",
    },
    {
        "name":                          "Proton-M",
        "operator":                      "Khrunichev / Roscosmos",
        "country":                       "Russia",
        "status":                        "operational",
        "availability":                  "sold_out",
        "core_propellant":               "hypergolic",
        "first_flight_year":             2001,
        "payload_leo_kg_low":            21_000,
        "payload_leo_kg_high":           23_000,
        "payload_gto_kg_low":             6_300,    # GTO-1500
        "payload_gto_kg_high":            6_920,    # GTO-1800
        "payload_escape_kg":              4_300,    # ExoMars TGO 2016, to Mars
        "list_price_usd":            65_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia (Proton-M) — $65M.  LEO: ILS Proton Mission "
                 "Planner's Guide Rev 7, Table 2.2-1, circular 180 km on three "
                 "stages: 22 t at 64.8 deg, 23 t at 51.5 deg, 21 t at 72.6 deg. "
                 "116 launches, 9 failures "
                 "and 2 partial.  Being retired: no new contracts are expected "
                 "and the last manifested flights are for 2029.  Escape is "
                 "ExoMars TGO's ~4.3 t Mars departure, a flown figure.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # OPERATIONAL — EUROPE
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                          "Ariane 6 (A62)",
        "operator":                      "ArianeGroup / ESA",
        "country":                       "Europe",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "hydrolox",
        "first_flight_year":             2024,
        "payload_leo_kg_low":            10_300,
        "payload_leo_kg_high":           10_350,
        "payload_gto_kg":                 4_500,
        "payload_escape_kg_low":          3_000,
        "payload_escape_kg_high":         3_500,    # lunar transfer
        "list_price_usd_high": int(round(100_000_000 * _USD_PER_EUR, -6)),
        "list_price_usd_low":        80_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Price €100M (2024 est.) at $1.15/€ = $115M, an estimate "
                 "with no institutional source: Arianespace publishes no list "
                 "price (contracts are negotiated) and the ESA Ariane 6 "
                 "overview, which this row once cited, states payloads only: "
                 "approximately 10.3 t LEO, so the 10,350 kg high end is a "
                 "tolerance, not a source.  "
                 "Against the ~€70M this row used to assume.  "
                 "Worse $/kg than A64, which is the usual result when a vehicle "
                 "is flown below its designed lift.  Nine Ariane 6 flights to "
                 "Aug 2026, one partial failure (VA262, Jul 2024).",
    },
    {
        "name":                          "Ariane 6 (A64)",
        "operator":                      "ArianeGroup / ESA",
        "country":                       "Europe",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "hydrolox",
        "first_flight_year":             2026,
        "payload_leo_kg_low":            21_500,
        "payload_leo_kg_high":           21_650,
        "payload_gto_kg":                11_500,
        "payload_escape_kg_low":          8_000,
        "payload_escape_kg_high":         8_600,    # lunar transfer
        "list_price_usd_high": int(round(115_000_000 * _USD_PER_EUR, -6)),
        "list_price_usd_low":       115_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "€115M (2018 est.) at $1.15/€ = $132M as the high end, an "
                 "estimate with no institutional source (Arianespace publishes "
                 "no list price; the ESA overview states payloads only), with the $115M this row used to carry "
                 "as the low end.  Payload: the ESA overview's approximately "
                 "21.6 t LEO; the 21,500 and 21,650 kg ends are a tolerance "
                 "around it, and the VA269 launch kit (Jun 2026) gives "
                 "approximately 22 t after the P160C booster upgrade.  "
                 "Four-booster config; first flew Feb 2026.",
    },
    {
        "name":                          "Vega C",
        "operator":                      "Avio / ESA",
        "country":                       "Europe",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "solid",
        "first_flight_year":             2022,
        "payload_leo_kg":                 2_250,    # 500 km polar, adapter included
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd_high": int(round(48_000_000 * _USD_PER_EUR, -6)),
        "list_price_usd_low":        37_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Avio / ESA via Wikipedia — €48M (2022) = $55M.  "
                 "Payload: Vega C User's Manual Issue 0 Rev 0, Table 2.4.2.a, "
                 "2,250 kg to 500 km polar at 88 deg, adapter included; its "
                 "Figure 2.4.1.e reads about 2,150-2,250 kg to 700 km SSO.  The "
                 "3,300 kg this row carried until 0.15.0 is not in the manual, "
                 "whose SSO chart stops at 2,700 kg.  VV22 failed Dec 2022 (Zefiro 40 nozzle); "
                 "returned to flight Dec 2024.  Useful for a prospector probe, "
                 "not a mining rig.",
    },
    {
        "name":                          "Spectrum",
        "operator":                      "Isar Aerospace",
        "country":                       "Germany",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "propalox",
        "first_flight_year":             2025,
        "payload_leo_kg":                 1_000,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd":     int(round(10_000_000 * _USD_PER_EUR, -5)),
        "price_basis":                   "target",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Isar Aerospace target of €10,000/kg, i.e. ~€10M for "
                 "the full 1 t, at $1.15/€.  Maiden flight Mar 2025 lost control "
                 "and fell into the sea; second flight reached orbit Sep 2026. "
                 "One success in two.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # OPERATIONAL — JAPAN, INDIA, SOUTH KOREA
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                          "H3 (24L)",
        "operator":                      "MHI / JAXA",
        "country":                       "Japan",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "hydrolox",
        "first_flight_year":             2025,
        "payload_leo_kg_low":            16_000,
        "payload_leo_kg_high":           16_500,
        "payload_gto_kg_low":             6_500,
        "payload_gto_kg_high":            7_900,
        "payload_escape_kg_low":          4_000,
        "payload_escape_kg_high":         6_000,    # TLI, "over 6 t"
        "list_price_usd_high":       75_000_000,
        "list_price_usd_low":        50_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: JAXA / Wikipedia payloads.  The ¥5B (~$33M) target this "
                 "row used to cite is for the H3-30, the SMALLEST config; the "
                 "four-booster 24L costs more and has no published price, so "
                 "$50-75M is an estimate.  First 24 flight carried HTV-X1, Oct "
                 "2025.  H3 has 2 failures in 9 flights: TF1 (Mar 2023) and F8 "
                 "(Dec 2025, payload adapter failure, QZS-5 lost).",
    },
    {
        "name":                          "H3 (30)",
        "operator":                      "MHI / JAXA",
        "country":                       "Japan",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "hydrolox",
        "first_flight_year":             2026,
        "payload_leo_kg":                 4_000,    # 500 km SSO; no LEO figure published
        "payload_gto_kg":                 2_100,
        "payload_escape_kg":                  0,
        "list_price_usd_high":       40_000_000,
        "list_price_usd_low":        33_000_000,
        "price_basis":                   "target",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: JAXA target ¥5B (~$33M at 2024 rates); no boosters, "
                 "three LE-9s.  The LEO column holds the 4 t SSO figure because "
                 "no LEO figure is published, and SSO is the harder orbit.  "
                 "First operational flight Jun 2026.",
    },
    {
        "name":                          "LVM3 (GSLV Mk III)",
        "operator":                      "ISRO",
        "country":                       "India",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "hypergolic",
        "first_flight_year":             2017,
        "payload_leo_kg_low":             8_000,
        "payload_leo_kg_high":           10_000,
        "payload_gto_kg_low":             4_000,
        "payload_gto_kg_high":            4_200,
        "payload_escape_kg_low":          2_000,
        "payload_escape_kg_high":         3_000,    # TLI
        "list_price_usd_high":       51_000_000,
        "list_price_usd_low":        42_000_000,    # ISRO ₹402 crore
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: ISRO ₹402 crore (~$42M) cost, and ~$51M NSIL commercial "
                 "rate; payloads from the ISRO user manual via Wikipedia.  9 for "
                 "9 to Dec 2025, including Chandrayaan-3 and two OneWeb batches. "
                 "The human-rated HLVM3 for Gaganyaan has NOT yet flown crew; "
                 "earlier versions of this row said it was human-rated.",
    },
    {
        "name":                          "PSLV-XL",
        "operator":                      "ISRO",
        "country":                       "India",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "solid",
        "first_flight_year":             2008,
        "payload_leo_kg":                 3_800,
        "payload_gto_kg_low":             1_300,
        "payload_gto_kg_high":            1_425,    # sub-GTO
        "payload_escape_kg":                  0,
        "list_price_usd_high":       31_000_000,
        "list_price_usd_low":        16_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: ISRO / NSIL, ₹130-200 crore ($16-24M, 2023) cost and "
                 "~$31M commercial.  Escape is 0: Chandrayaan-1 and the Mars "
                 "Orbiter Mission were both put into elongated EARTH orbits and "
                 "raised themselves, so the 1,100 kg escape figure this row used "
                 "to carry was not a PSLV capability.  ISRO's mission pages: "
                 "C61 (May 2025) was normal to the second stage, with an "
                 "observation in the third, and the mission was not "
                 "accomplished; C62 (Jan 2026) had an anomaly at the end of the "
                 "third stage, with detailed analysis started.",
    },
    {
        "name":                          "GSLV Mk II",
        "operator":                      "ISRO",
        "country":                       "India",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "solid",
        "first_flight_year":             2010,
        "payload_leo_kg":                 6_000,
        "payload_gto_kg_low":             2_250,
        "payload_gto_kg_high":            2_500,
        "payload_escape_kg":             np.nan,
        "list_price_usd":            47_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — $47M.  Payload: ISRO's vehicle page, "
                 "whose GTO figure is this band's low end; the high end is not "
                 "in ISRO's specification.  ISRO's manifest: 19 launches to Sep "
                 "2026, 4 marked unsuccessful.  Solid core "
                 "with hypergolic strap-ons and an Indian cryogenic upper stage. "
                 "Flew NISAR.  Mostly Indian government payloads.",
    },
    {
        "name":                          "SSLV",
        "operator":                      "ISRO / HAL",
        "country":                       "India",
        "status":                        "operational",
        "availability":                  "open",
        "core_propellant":               "solid",
        "first_flight_year":             2022,
        "payload_leo_kg":                   500,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd_high":        4_000_000,
        "list_price_usd_low":         3_500_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: ISRO, Rs 30-35 crore (~$3.5-4M) per launch.  First "
                 "flight (Aug 2022) failed to reach a usable orbit.  Production "
                 "and operations transferred to HAL from 2025.",
    },
    {
        "name":                          "Nuri (KSLV-II)",
        "operator":                      "KARI / Hanwha Aerospace",
        "country":                       "South Korea",
        "status":                        "operational",
        "availability":                  "government_only",
        "core_propellant":               "kerolox",
        "first_flight_year":             2021,
        "payload_leo_kg":                 3_300,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd_high":       45_000_000,
        "list_price_usd_low":        30_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — 3.3 t to 200 km, 1.9 t to 700 km SSO, an "
                 "altitude KARI never quotes: its pages give a 1.5 t class "
                 "satellite to 600-800 km, about $24,500/kg at this price; "
                 "launch cost 'estimated around $30M', the band's low end, with "
                 "room above it for an unpriced government vehicle.  First flight failed (2021); "
                 "three successes since, the latest Nov 2025.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # OPERATIONAL — CHINA.  Chinese launch pricing is not published: every
    # price here is an estimate unless its notes say otherwise, and every one
    # is `restricted`, because ITAR bars US-controlled components from them.
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                          "Long March 2C",
        "operator":                      "CASC (China)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "hypergolic",
        "first_flight_year":             1982,
        "payload_leo_kg":                 3_850,
        "payload_gto_kg":                 1_250,    # 2C/SM
        "payload_escape_kg":                  0,
        "list_price_usd_high":       35_000_000,
        "list_price_usd_low":        25_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia payloads; price estimated against the $30M "
                 "Long March 2D.  88 launches, 1 failure, 1 partial (to Aug "
                 "2026).",
    },
    {
        "name":                          "Long March 2D",
        "operator":                      "CASC (China)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "hypergolic",
        "first_flight_year":             1992,
        "payload_leo_kg":                 3_500,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd":            30_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — $30M.  ~100 launches.  LEO/SSO only.",
    },
    {
        "name":                          "Long March 3B/E",
        "operator":                      "CASC (China)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "hypergolic",
        "first_flight_year":             2007,
        "payload_leo_kg":                11_500,
        "payload_gto_kg":                 5_500,
        "payload_escape_kg":              3_780,    # Chang'e-3 TLI mass
        "list_price_usd_high":       70_000_000,
        "list_price_usd_low":        50_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — $50-70M.  China's GTO workhorse, 112+ "
                 "successes, 96.5% success rate.  Escape is Chang'e-3's ~3.8 t "
                 "sent to TLI, a flown figure rather than a rating.",
    },
    {
        "name":                          "Long March 4C",
        "operator":                      "CASC (China)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "hypergolic",
        "first_flight_year":             2006,
        "payload_leo_kg":                 4_200,
        "payload_gto_kg":                 1_500,
        "payload_escape_kg":                  0,
        "list_price_usd_high":       50_000_000,
        "list_price_usd_low":        30_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia's Long March 4C article for LEO and GTO, "
                 "resting on one skyrocket.de snapshot of Apr 2008; CASC states "
                 "only 2.8 t to 800 km sun-synchronous (2015) and 3 t to 700 km "
                 "SSO (Apr 2026).  Price estimated against the "
                 "sister Long March 4B's $50M (2006).  ~59 launches.",
    },
    {
        "name":                          "Long March 5",
        "operator":                      "CASC (China)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "hydrolox",
        "first_flight_year":             2016,
        "payload_leo_kg":                25_000,
        "payload_gto_kg":                14_000,
        "payload_escape_kg_low":          8_200,    # Chang'e-5 TLI
        "payload_escape_kg_high":         9_400,    # rated TLI
        "list_price_usd_high":      160_000_000,
        "list_price_usd_low":       110_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia / China-in-Space — payload masses "
                 "authoritative; ~$160M is Wikipedia's estimate and the high "
                 "end, against the $110M this row used to carry.  The State "
                 "Council Information Office gives Long March 5 25 t to LEO or "
                 "14 t to GTO (2018), and the 5B 22 t to LEO (2020).  "
                 "Chang'e-5 and Tianwen-1 heritage (Mars transfer "
                 "~6 t).  17 of 18 successful.",
    },
    {
        "name":                          "Long March 6A",
        "operator":                      "CASC (China)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "kerolox",
        "first_flight_year":             2022,
        "payload_leo_kg":                 8_000,
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":             np.nan,
        "list_price_usd_high":       60_000_000,
        "list_price_usd_low":        35_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia payloads (8 t LEO, 6.5 t 500 km SSO); CASC "
                 "states only not less than 4 t to 700 km SSO.  Price "
                 "estimated.  26 for 26 to Jul 2026, but its upper stage has "
                 "broken up in orbit (Nov 2022 and Mar, Jul and Aug 2024), the "
                 "Nov 2022 one into 781 catalogued pieces, 722 still on orbit "
                 "in June 2023 (NASA ODQN 27-3, Table 1).",
    },
    {
        "name":                          "Long March 7",
        "operator":                      "CASC (China)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "government_only",
        "core_propellant":               "kerolox",
        "first_flight_year":             2016,
        "payload_leo_kg":                13_500,
        "payload_gto_kg":                 7_000,    # the three-stage 7A
        "payload_escape_kg":             np.nan,
        "list_price_usd_high":       70_000_000,
        "list_price_usd_low":        50_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: CALT via China Daily, 13.5 t to LEO (Jul 2025) and 7 t "
                 "to GTO (Aug 2026); Wikipedia alone gives the orbit, 200-400 km "
                 "/ 42 deg; price estimated. "
                 "The LEO figure is the two-stage 7, which flies Tianzhou cargo "
                 "to the Chinese station; the GTO figure is the three-stage 7A "
                 "(2 failures in 18).  The 4,000 kg escape figure this row used "
                 "to carry had no source.",
    },
    {
        "name":                          "Long March 8A",
        "operator":                      "CASC (China)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "kerolox",
        "first_flight_year":             2025,
        "payload_leo_kg":                 7_000,
        "payload_gto_kg":                 3_500,
        "payload_escape_kg":             np.nan,
        "list_price_usd_high":       70_000_000,
        "list_price_usd_low":        40_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: CALT via the State Council Information Office, about "
                 "7 t to LEO; Wikipedia's per-variant row gives the same 7,000 "
                 "kg, to 700 km SSO.  The 10 t this row carried until 0.15.0 is "
                 "in neither, and Wikipedia's 8,100 kg infobox figure is the "
                 "base CZ-8.  The GTO figure has no current source.  Price "
                 "estimated.  11 flights since "
                 "Feb 2025, all successful, mostly constellation deployment from "
                 "Hainan commercial pads.",
    },
    {
        "name":                          "Long March 12",
        "operator":                      "CASC (China)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "kerolox",
        "first_flight_year":             2024,
        "payload_leo_kg_low":            10_000,    # 300 km
        "payload_leo_kg_high":           12_000,    # 200 km
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":             np.nan,
        "list_price_usd_high":       80_000_000,
        "list_price_usd_low":        50_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "LEO: the low end is SAST's design target (Straits Times, Feb "
                 "2024); the high end is Xinhua's 'no less than 12 tonnes' (Dec "
                 "2024), an official floor, so the band's top understates it.  "
                 "Price estimated.  8 for 8, all "
                 "Guowang deployments.  Reusable 12A and 12B variants first flew "
                 "Dec 2025 and Jun 2026 and are not yet listed.",
    },
    {
        "name":                          "Long March 10B",
        "operator":                      "CASC (China)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "reusability":                   "first_stage",
        "core_propellant":               "kerolox",
        "first_flight_year":             2026,
        "payload_leo_kg":                16_000,    # 200 km
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":             np.nan,
        "list_price_usd_high":       70_000_000,
        "list_price_usd_low":        40_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — 'at least 16 t' to 200 km, 11 t to 900 km "
                 "at 50 deg.  One flight (Jul 2026), successful, with China's "
                 "first controlled recovery of an orbital first stage.  One "
                 "flight is a thin record for 'operational'; read the TRL as "
                 "flown, not proven.  Price estimated.",
    },
    {
        "name":                          "Kuaizhou-1A",
        "operator":                      "ExPace (CASIC)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "solid",
        "first_flight_year":             2017,
        "payload_leo_kg_low":               300,
        "payload_leo_kg_high":              400,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd_high":        8_000_000,
        "list_price_usd_low":         6_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — ~$20,000/kg, i.e. $6-8M across the "
                 "300-400 kg payload range.  The operator states 300 kg LEO and "
                 "200 kg SSO (China Daily, Oct 2021; the Gansu bureau's report "
                 "says under 300 kg), the band's floor; its 400 kg ceiling is "
                 "Wikipedia's alone.  Road-mobile solid.  2 failures "
                 "(2020, 2021).",
    },
    {
        "name":                          "Kuaizhou-11",
        "operator":                      "ExPace (CASIC)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "solid",
        "first_flight_year":             2020,
        "payload_leo_kg":                 1_500,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd_high":       15_000_000,
        "list_price_usd_low":        10_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — ~$10,000/kg, i.e. ~$15M full.  Maiden "
                 "flight failed (Jul 2020).",
    },
    {
        "name":                          "Ceres-1",
        "operator":                      "Galactic Energy",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "solid",
        "first_flight_year":             2020,
        "payload_leo_kg":                   400,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd":             4_500_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — $4.5M; 400 kg LEO, 300 kg 500 km SSO.  23 "
                 "launches, 2 failures, to Jan 2026.  A sea-launched 1S variant "
                 "also flies.",
    },
    {
        "name":                          "Gravity-1",
        "operator":                      "Orienspace",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "solid",
        "first_flight_year":             2024,
        "payload_leo_kg":                 6_500,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd":            39_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — ~$39M.  Payload: Orienspace's product "
                 "page, 6.5 t LEO and 4.2 t 500 km SSO; Wikipedia gives the LEO "
                 "figure at 200 km.  The "
                 "largest all-solid launcher flying; sea-launched.  4 for 4 to "
                 "Sep 2026.",
    },
    {
        "name":                          "Kinetica-1",
        "operator":                      "CAS Space",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "solid",
        "first_flight_year":             2022,
        "payload_leo_kg":                 2_000,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd_high":       15_000_000,
        "list_price_usd_low":         8_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: CAS Space's product page and gov.cn, 2 t LEO and 1.5 "
                 "t to 500 km SSO, as Wikipedia gives them; price "
                 "estimated.  16 launches, 1 failure (Dec 2024, third stage).",
    },
    {
        "name":                          "Kinetica-2",
        "operator":                      "CAS Space",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "kerolox",
        "first_flight_year":             2026,
        "payload_leo_kg":                12_000,
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":             np.nan,
        "list_price_usd":            50_000_000,
        "price_basis":                   "published",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: CAS Space's Yang Haoliang in Cailianshe, 31 Mar 2026: "
                 "a non-recoverable launch COST of 30,000 yuan/kg, i.e. ~¥360M or "
                 "~$50M for the full 12 t, not a price; TMTPost puts common "
                 "Chinese quotes at 50,000-100,000 yuan/kg.  12 t is to 200 km, "
                 "and 8 t to 500 km SSO.  One flight (Mar 2026), carrying a "
                 "Qingzhou cargo-vessel prototype.  First-stage recovery is "
                 "planned from 2027; flies expendable today.",
    },
    {
        "name":                          "Jielong-3",
        "operator":                      "China Rocket (CALT)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "solid",
        "first_flight_year":             2022,
        "payload_leo_kg":                 1_600,    # 500 km SSO; no LEO figure published
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd_high":       20_000_000,
        "list_price_usd_low":        10_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — 1.6 t to 500 km SSO, used as the LEO "
                 "figure because no LEO figure is published.  Sea-launched solid; "
                 "12 for 12.  Price estimated.",
    },
    {
        "name":                          "Zhuque-2E",
        "operator":                      "LandSpace (China)",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "methalox",
        "first_flight_year":             2024,
        "payload_leo_kg":                 6_000,
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":             np.nan,
        "list_price_usd_high":       35_000_000,
        "list_price_usd_low":        20_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia payloads (6 t LEO, 4 t SSO); price "
                 "estimated.  Zhuque-2 family: 9 launches, 2 failures, the "
                 "latest failure a 2E in Aug 2025 (second-stage voltage fault), "
                 "and a sixth 2E flew in Sep 2026 (China Daily, 2025 and 2026).  The "
                 "first methalox rocket to reach orbit (2023).",
    },
    {
        "name":                          "Zhuque-3",
        "operator":                      "LandSpace (China)",
        "country":                       "China",
        "status":                        "operational",    # promoted v1.16.0: 2 of 2 to orbit
        "availability":                  "restricted",
        "reusability":                   "first_stage",
        "core_propellant":               "methalox",
        "first_flight_year":             2025,
        "payload_leo_kg":                 8_000,    # reusable, downrange landing
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":             np.nan,
        "list_price_usd_high":       50_000_000,
        "list_price_usd_low":        25_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — ZQ-3 lifts 8 t reusable (downrange "
                 "landing) or 11.8 t expendable; this row is the reusable mode, "
                 "and at 11.8 t the same price is about $3,000/kg.  Until "
                 "v1.16.0 it carried 21 t / 18.3 t, which Wikipedia gives to an "
                 "enlarged ZQ-3E, though LandSpace's own release gives 21.3 t / "
                 "18.3 t to the 76.6 m ZQ-3, and the vehicle that flew stood "
                 "66.1 m (Global Times, Dec 2025).  Flights Dec 2025 (orbit, "
                 "landing failed) and Aug 2026 (orbit, first landing, stage "
                 "toppled afterwards).  Price estimated; LandSpace has not "
                 "published one.",
    },
    {
        "name":                          "Pallas-1",
        "operator":                      "Galactic Energy",
        "country":                       "China",
        "status":                        "operational",
        "availability":                  "restricted",
        "core_propellant":               "kerolox",
        "first_flight_year":             2026,
        "payload_leo_kg":                 5_000,    # 400 km
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":             np.nan,
        "list_price_usd_high":       40_000_000,
        "list_price_usd_low":        20_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — 5 t to 400 km, 3 t to 700 km SSO.  One "
                 "flight, 1 Sep 2026, successful, boilerplate payload, no "
                 "recovery attempted.  Designed for first-stage reuse but has "
                 "only flown expendable, so it is listed as flown.  Price "
                 "estimated.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # RETIRED, flew, will not fly again.  Kept for the same reason mercury ion
    # is kept in the propellant table: so that a historical $/kg figure found
    # elsewhere can be identified as unavailable rather than as an oversight.
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                          "Delta IV Heavy",
        "operator":                      "ULA",
        "country":                       "USA",
        "status":                        "retired",
        "availability":                  "unavailable",
        "core_propellant":               "hydrolox",
        "first_flight_year":             2004,
        "payload_leo_kg":                28_790,
        "payload_gto_kg":                14_220,
        "payload_escape_kg":             10_000,
        "list_price_usd":           440_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Last flight April 2024 (NROL-70).  Hydrolox, three cores, and "
                 "the launcher that sent Parker Solar Probe to the highest "
                 "departure energy ever flown.  Replaced by Vulcan.  LEO "
                 "payload 28,790 kg to 200 km / 28.5 deg (Zapata 2017, NASA, "
                 "'State of Play', p16).  The $440M price has no recorded "
                 "source.  The one registered price is the same chart's Delta "
                 "IV Heavy for the NRO: $336M (2017 dollars) for the launch "
                 "service plus its share of the EELV Launch Capability (ELC) "
                 "contract, the yearly ELC amount divided evenly over DoD-only "
                 "launches.  At the CPI-U factor used for Pegasus XL (Dec 2017 "
                 "to Aug 2026, x1.3484) that is $453M, 3% above this row.",
    },
    {
        "name":                          "H-IIA 204",
        "operator":                      "MHI / JAXA",
        "country":                       "Japan",
        "status":                        "retired",
        "availability":                  "unavailable",
        "core_propellant":               "hydrolox",
        "first_flight_year":             2006,
        "payload_leo_kg":                15_000,
        "payload_gto_kg":                 6_000,
        "payload_escape_kg":              3_600,
        "list_price_usd_high":       75_000_000,
        "list_price_usd_low":        62_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Price: 9.3 billion yen for F4 (JAXA) at the World Bank's 2025 "
                 "rate of 149.66 yen/$ is $62.1M, the low end, and the "
                 "programme's ~10 billion yen is $66.8M at the same rate; the "
                 "high end is The Space Review's 'about $75 million' (Mar 2023). "
                 "The standard type's cost, so a floor for the 204.  Until 0.15.0 "
                 "this row carried $90M, which reconciles only below 111 yen/$.  "
                 "H-IIA's last flight was F50, June 2025 (GOSAT-GW): 50 flights "
                 "and one failure (F6, 2003).  Launched Hayabusa2 — the most "
                 "relevant flight heritage in this entire table to what this "
                 "pipeline models.  Succeeded by H3.",
    },
    {
        "name":                          "Pegasus XL",
        "operator":                      "Northrop Grumman",
        "country":                       "USA",
        "status":                        "retired",
        "availability":                  "unavailable",
        "core_propellant":               "solid",
        "first_flight_year":             1994,
        "payload_leo_kg_low":               443,
        "payload_leo_kg_high":              450,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd_low":        54_000_000,    # $40M (2017) list, CPI-U
        "list_price_usd_high":       76_000_000,    # NASA LSP ICON, $56M (2017), CPI-U
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Air-launched from an L-1011.  Low end: a $40M (2017) list "
                 "price, whose own source is not recorded, carried to 2026 "
                 "dollars by CPI-U (Dec 2017 to Aug 2026, x1.3484): $54M.  "
                 "High end: what NASA's Launch Services Program paid for ICON, "
                 "$56M (2017) for a 443 kg LEO capacity (Zapata 2017, 'State of "
                 "Play', p16), at the same factor: $76M.  That is a government "
                 "full-service price, which the band now spans by decision.  "
                 "Until 0.6.0 the 2017 figure stood unescalated; until 0.7.0 "
                 "the row carried the list price alone.  Final flight Jul "
                 "2026, the Swift reboost mission.  46 flights, 3 failures and "
                 "2 partial.  The price per kilogram is why nobody asks for it "
                 "any more.",
    },
    {
        "name":                          "Ariane 5 ECA",
        "operator":                      "Arianespace / ESA",
        "country":                       "Europe",
        "status":                        "retired",
        "availability":                  "unavailable",
        "core_propellant":               "hydrolox",
        "first_flight_year":             2002,
        "payload_leo_kg":                20_000,
        "payload_gto_kg_low":            10_500,
        "payload_gto_kg_high":           10_865,    # record, 2016
        "payload_escape_kg":              6_100,    # JWST to Sun-Earth L2
        "list_price_usd_high":      220_000_000,
        "list_price_usd_low":       165_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Last flight Jul 2023.  Usually flew two GTO satellites at "
                 "once, so its per-customer price was lower than the €150-190M "
                 "vehicle cost this band brackets.  Launched JWST (~6.2 t, near "
                 "C3=0).",
    },
    {
        "name":                          "Vega",
        "operator":                      "Avio / ESA",
        "country":                       "Europe",
        "status":                        "retired",
        "availability":                  "unavailable",
        "core_propellant":               "solid",
        "first_flight_year":             2012,
        "payload_leo_kg":                 1_500,    # 700 km SSO-class
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd":     int(round(32_000_000 * _USD_PER_EUR, -5)),
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "The original Vega, replaced by Vega C; last flight Sep 2024. "
                 "~€32M.  Two failures in its last four years (VV15, VV17).",
    },
    {
        "name":                          "Space Shuttle",
        "operator":                      "NASA",
        "country":                       "USA",
        "status":                        "retired",
        "availability":                  "unavailable",
        "reusability":                   "partial",
        "core_propellant":               "hydrolox",
        "first_flight_year":             1981,
        "payload_leo_kg_low":            24_400,
        "payload_leo_kg_high":           27_500,    # 204 km, 28.5 deg
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":              2_380,    # Galileo on IUS
        "list_price_usd_high":    2_100_000_000,
        "list_price_usd_low":       450_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Retired 2011.  Whole-programme cost per flight was ~$1.5B in "
                 "2011 dollars (Pielke & Byerly, Nature 472:38, 2011; NASA "
                 "OIG IG-24-001 independently puts it at ~$1.45B a launch) — "
                 "the source of the famous "
                 "$54,500/kg — carried to 2026 dollars (~x1.44) as the "
                 "high end; the marginal cost of one more flight, ~$450M, is "
                 "the low end.  Mixed dollar years on purpose: the band is "
                 "what a reader might have been quoted.  Two orbiters lost in "
                 "135 flights.  Escape is Galileo on an IUS upper stage.",
    },
    {
        "name":                          "Saturn V",
        "operator":                      "NASA",
        "country":                       "USA",
        "status":                        "retired",
        "availability":                  "unavailable",
        "core_propellant":               "kerolox",
        "first_flight_year":             1967,
        "payload_leo_kg_low":           118_000,
        "payload_leo_kg_high":          140_000,
        "payload_gto_kg":                np.nan,
        "payload_escape_kg_low":         43_500,
        "payload_escape_kg_high":        48_600,    # Apollo 17 TLI
        "list_price_usd_high":    1_550_000_000,
        "list_price_usd_low":     1_230_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Last flight 1973 (Skylab).  ~$185M per vehicle in 1969-73 "
                 "dollars, carried to 2026 dollars; the low end is the "
                 "frequently-quoted 2020-dollar figure.  Excludes the "
                 "programme's development cost, which was most of it.  LEO: "
                 "285,000 lb (129,274 kg) in the Apollo 8 press kit is the "
                 "headline, 262,000 lb (118.8 t) in Sumrall et al. 2009 the low "
                 "end, and the 140 t high end is an engineering tolerance that "
                 "no NASA document states; the heaviest payload delivered was "
                 "Skylab, about 77 t.  Escape "
                 "is TLI.  The only vehicle before SLS to send people beyond "
                 "LEO.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # DEVELOPMENT: announced, hardware in test, not yet flown to orbit.
    # Gated out of Module 4 by operational_vehicles_only.
    # Prices are targets, and launch-vehicle targets are optimistic by
    # construction; the target is the optimistic end of each band, never the
    # whole of it, and the headline is the band's centre.
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                          "Starship (projected)",
        "operator":                      "SpaceX",
        "country":                       "USA",
        "status":                        "development",
        "availability":                  "open",
        "reusability":                   "full",
        "core_propellant":               "methalox",
        "first_flight_year":             2023,
        "trl":                           6,
        # v1.9.0: the escape figure below assumes orbital refuelling.  SpaceX
        # has said ~8 flights to refill a ship in LEO and NASA has said ~16 for
        # a lunar lander; 12 is the centre, and it is the value the storage
        # table's depot row carries for the same quantity.
        "tanker_flights_for_escape":     12,
        "payload_leo_kg_low":            35_000,    # what Block 2 reached in practice
        "payload_leo_kg_high":          100_000,    # Block 3 reusable target
        "payload_gto_kg_low":             7_000,    # 21 t scaled to the 35 t LEO floor
        "payload_gto_kg_high":           21_000,    # SpaceX single-launch figure
        "payload_escape_kg":             27_000,    # WITH orbital refueling
        "list_price_usd_high":      100_000_000,    # SpaceX, expendable
        "list_price_usd_low":        90_000_000,    # Voyager 424B4 prospectus, Jun 2025
        "price_basis":                   "contract",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Voyager Technologies final prospectus (Form 424B4, "
                 "Jun 2025), Commitments and Contingencies: a commitment for "
                 "ONE Starship launch for Starlab at $90.0M, as of Dec 31 2024 "
                 "and Mar 31 2025 (cancelling for convenience owes the "
                 "provider $13.5M).  Voyager's FY2025 10-K names the contract "
                 "but states no price, and until 0.6.1 this note cited it as a "
                 "2026 contract.  SpaceX's own $100M expendable figure is the "
                 "high end.  NOT YET ORBITAL: 13 test flights to Jul 2026, 8 "
                 "successful, all suborbital by design.  Block 2 was built for "
                 "100 t and fell to ~35 t, which is the low end; the V3 target "
                 "of 100 t is the high end.  GTO scales SpaceX's 21 t by the "
                 "same 35%.  CAVEAT: escape payload (27 t) > GTO only because it "
                 "assumes orbital refueling; tanker_flights_for_escape carries "
                 "the 12 flights (8-16 quoted), and 12 x ~$95M is the cost "
                 "that caveat is about.",
    },
    {
        "name":                          "New Glenn 9x4",
        "operator":                      "Blue Origin",
        "country":                       "USA",
        "status":                        "development",
        "availability":                  "open",
        "reusability":                   "first_stage",
        "core_propellant":               "methalox",
        "first_flight_year":             None,
        "trl":                           5,
        "payload_leo_kg":                70_000,    # ">70 t"
        "payload_gto_kg":                np.nan,    # only a GSO figure (>14 t) is published
        "payload_escape_kg":             20_000,    # TLI, ">20 t"
        "list_price_usd_high":      250_000_000,
        "list_price_usd_low":       150_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Blue Origin, blueorigin.com/new-glenn/9x4: 70 t LEO, "
                 "14 t direct to GSO, 20 t TLI, nine booster "
                 "engines, four upper-stage engines, 8.7 m fairing.  No price "
                 "published; $150-250M is an estimate.  GTO is NaN because "
                 "only a direct-to-GSO figure (>14 t) has been given, which is "
                 "a different and much harder orbit.",
    },
    {
        "name":                          "Neutron",
        "operator":                      "Rocket Lab",
        "country":                       "USA",
        "status":                        "development",
        "availability":                  "open",
        "reusability":                   "first_stage",
        "core_propellant":               "methalox",
        "first_flight_year":             None,
        "trl":                           6,
        "payload_leo_kg":                13_000,    # reusable; 15,000 expendable
        "payload_gto_kg":                 1_500,
        "payload_escape_kg_low":          1_000,
        "payload_escape_kg_high":         1_500,    # Mars / Venus, Rocket Lab
        "list_price_usd_high":       55_000_000,
        "list_price_usd_low":        50_000_000,
        "price_basis":                   "target",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Rocket Lab — ~$50-55M, 13 t LEO reusable.  Methalox, "
                 "captive fairing, first-stage return.  First flight has slipped "
                 "from 2024 to NET Q4 2026 (a stage-1 tank failed in test Jan "
                 "2026).  Beyond-LEO capability is thin: the upper stage is "
                 "sized for constellation work.",
    },
    {
        "name":                          "Terran R",
        "operator":                      "Relativity Space",
        "country":                       "USA",
        "status":                        "development",
        "availability":                  "open",
        "reusability":                   "first_stage",
        "core_propellant":               "methalox",
        "first_flight_year":             None,
        "trl":                           5,
        "payload_leo_kg":                23_500,    # reusable first stage
        "payload_gto_kg":                 5_500,
        "payload_escape_kg":              4_000,
        "list_price_usd_high":       70_000_000,
        "list_price_usd_low":        55_000_000,
        "price_basis":                   "target",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Relativity, relativityspace.com/terran-r: 23.5 t LEO "
                 "and 5.5 t GTO with downrange landing, 33.5 t LEO expendable; "
                 "$55M per Wikipedia.  Until v1.16.0 this row paired "
                 "the 33.5 t EXPENDABLE figure with a reusable price.  NET late "
                 "2026.  Escape is the older published figure, not re-stated "
                 "for the reusable config.",
    },
    {
        "name":                          "Nova",
        "operator":                      "Stoke Space",
        "country":                       "USA",
        "status":                        "development",
        "availability":                  "open",
        "reusability":                   "full",
        "core_propellant":               "methalox",
        "first_flight_year":             None,
        "trl":                           5,
        "payload_leo_kg":                 3_000,    # fully reusable; 7,000 expendable
        "payload_gto_kg":                   720,
        "payload_escape_kg":                480,
        "list_price_usd_high":       30_000_000,
        "list_price_usd_low":        20_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Stoke Space via Wikipedia — 3 t fully reusable, 7 t "
                 "expendable; the 5 t this row carried until v1.16.0 was not a "
                 "fully-reusable figure.  Those are the Pathfinder demonstrator; "
                 "Nova Block 2 is up to 15 t fully reusable, 23 t expendable and "
                 "4 t to GTO (stokespace.com/nova-block-2).  Stoke publishes no "
                 "price or escape figure: the price is an estimate and GTO / "
                 "escape here are the old 1,200 / 800 kg scaled by 3/5.  The only "
                 "vehicle here besides Starship designed for FULL reuse, "
                 "including a regeneratively cooled upper-stage heat shield.",
    },
    {
        "name":                          "Eclipse (MLV)",
        "operator":                      "Firefly / Northrop Grumman",
        "country":                       "USA",
        "status":                        "development",
        "availability":                  "open",
        "reusability":                   "first_stage",
        "core_propellant":               "methalox",
        "first_flight_year":             None,
        "trl":                           5,
        "payload_leo_kg":                16_300,
        "payload_gto_kg":                 3_200,
        "payload_escape_kg_low":          2_000,
        "payload_escape_kg_high":         2_300,    # TLI
        "list_price_usd":            80_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Firefly, fireflyspace.com/eclipse: 16,300 kg LEO, "
                 "3,200 kg GTO, 59 m overall.  Formerly MLV; renamed May 2025. "
                 "NET 2027, early flights expendable with reuse targeted by "
                 "the sixth.  No published price.",
    },
    {
        "name":                          "Tianlong-3",
        "operator":                      "Space Pioneer (China)",
        "country":                       "China",
        "status":                        "development",
        "availability":                  "restricted",
        "core_propellant":               "kerolox",
        "first_flight_year":             2026,
        "trl":                           6,
        "payload_leo_kg":                17_000,
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":             np.nan,
        "list_price_usd_high":       45_000_000,
        "list_price_usd_low":        25_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Space Pioneer via Wikipedia — 17 t LEO, 14 t SSO; "
                 "price estimated.  Maiden flight, 3 Apr 2026, FAILED at about "
                 "T+189 s after a nominal first stage: separation at T+182.2 s, "
                 "second-stage ignition at T+185.9 s, then loss of control and "
                 "commanded termination (Space Pioneer's investigation "
                 "statement; China Daily).  A first stage also broke loose from its test stand "
                 "and flew in Jun 2024.  Reusable first stage intended.  The "
                 "GTO and escape figures this row carried had no source.",
    },
    {
        "name":                          "Long March 10",
        "operator":                      "CASC (China)",
        "country":                       "China",
        "status":                        "development",
        "availability":                  "government_only",
        "core_propellant":               "kerolox",
        "first_flight_year":             None,
        "trl":                           6,
        "payload_leo_kg":                70_000,
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":             27_000,    # TLI, crewed lunar architecture
        "list_price_usd_high":      300_000_000,
        "list_price_usd_low":       150_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: CASC crewed-lunar-programme disclosures; price "
                 "estimated.  70 t LEO / 27 t TLI for a 2030 crewed lunar "
                 "landing.  The single-core 10A tested its escape system on a "
                 "suborbital flight (Feb 2026) and the 10B is flying (own row), "
                 "so the core hardware is real; the three-core vehicle has not "
                 "flown.",
    },
    {
        "name":                          "Long March 9",
        "operator":                      "CASC (China)",
        "country":                       "China",
        "status":                        "development",
        "availability":                  "government_only",
        "reusability":                   "first_stage",
        "core_propellant":               "methalox",
        "first_flight_year":             None,
        "trl":                           3,
        "payload_leo_kg":               150_000,
        "payload_gto_kg":                np.nan,
        "payload_escape_kg_low":         50_000,
        "payload_escape_kg_high":        54_000,    # TLI, 2023 design
        "list_price_usd_high":    1_000_000_000,
        "list_price_usd_low":       500_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: CASC roadmap presentations; the 2023 design is 150 t "
                 "LEO / 54 t TLI with a reusable 30-engine methalox first "
                 "stage, first flight planned for 2033.  TRL 3.  Price is a "
                 "guess, stated as one.  Present because it is the only "
                 "announced vehicle in the Starship class that is not Starship.",
    },
    {
        "name":                          "Soyuz-5",
        "operator":                      "RKTs Progress / Roscosmos",
        "country":                       "Russia",
        "status":                        "development",
        "availability":                  "restricted",
        "core_propellant":               "kerolox",
        "first_flight_year":             2026,
        "trl":                           6,
        "payload_leo_kg_low":            15_500,
        "payload_leo_kg_high":           18_000,
        "payload_gto_kg":                 5_000,
        "payload_escape_kg":             np.nan,
        "list_price_usd_high":       60_000_000,
        "list_price_usd_low":        40_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia — 18 t uncrewed / 15.5 t crewed-profile LEO, "
                 "5 t GTO; Roscosmos says up to 17 t to the support orbit "
                 "(Interfax, 2025), below this band's top, and gives no GTO "
                 "figure.  Zenit's successor.  First flight Apr 2026 was a "
                 "successful SUBORBITAL test with a mass simulator; not yet "
                 "orbital.  Price estimated.",
    },
    {
        "name":                          "Epsilon S",
        "operator":                      "IHI Aerospace / JAXA",
        "country":                       "Japan",
        "status":                        "development",
        "availability":                  "open",
        "core_propellant":               "solid",
        "first_flight_year":             None,
        "trl":                           6,
        "payload_leo_kg":                 1_400,    # 500 km
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd_high":       38_000_000,
        "list_price_usd_low":        25_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: JAXA via Wikipedia — 1.4 t to 500 km, 600 kg to 700 km "
                 "SSO.  The new second-stage motor exploded in test twice (Jul "
                 "2023, Nov 2024); JAXA reverted to the Enhanced Epsilon stage, "
                 "first flight possibly late 2026.  The high end is the "
                 "original Epsilon's $38M, since the S has not beaten it yet.",
    },
    {
        "name":                          "Hyperbola-3",
        "operator":                      "i-Space (China)",
        "country":                       "China",
        "status":                        "development",
        "availability":                  "restricted",
        "reusability":                   "first_stage",
        "core_propellant":               "methalox",
        "first_flight_year":             None,
        "trl":                           5,
        "payload_leo_kg":                 8_500,    # reusable; 13,400 expendable
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":             np.nan,
        "list_price_usd_high":       60_000_000,
        "list_price_usd_low":        30_000_000,
        "price_basis":                   "estimate",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: i-Space via Wikipedia — 8.5 t reusable, 13.4 t "
                 "expendable; this row is the reusable mode, also the State "
                 "Council Information Office's figure, which gives the "
                 "expendable as 12.9 t.  At 13.4 t the same price is about "
                 "$3,160/kg.  Hop tests in 2023; orbital debut slipped from "
                 "2025.  Price estimated.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # CANCELLED before flight.  A figure for it will still turn up in older
    # studies, so it is kept, marked, and gated like a concept.
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                          "SLS Block 1B (Cargo)",
        "operator":                      "NASA",
        "country":                       "USA",
        "status":                        "concept",
        "availability":                  "unavailable",
        "core_propellant":               "hydrolox",
        "first_flight_year":             None,
        "trl":                           6,
        "payload_leo_kg":               105_000,    # Block 1B Cargo LEO (NASA SLS factsheet)
        "payload_gto_kg":                np.nan,
        "payload_escape_kg":             42_000,    # TLI (NASA Block 1B factsheet)
        "list_price_usd_high":    2_800_000_000,
        "list_price_usd_low":     2_500_000_000,
        "price_basis":                   "reported",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "CANCELLED along with the Exploration Upper Stage: announced "
                 "Feb 2026, and NASA's FY 2027 budget estimates (pp39-40) "
                 "propose no funding for Block 1B; "
                 "never flew.  Until v1.16.0 this row was marked OPERATIONAL "
                 "and priced at $4.1B, which is NASA OIG's per-Artemis-flight "
                 "figure including Orion and its service module, not a launch "
                 "price.  Now carries the same launch-only band as Block 1, a "
                 "floor for a vehicle that would have cost more.  Its 41 t GTO "
                 "figure had been scaled from TLI, not published, and is gone.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # NON-ROCKET LAUNCH, concept.  Every one of these promises a $/kg an order
    # of magnitude below the chemical rockets above, and every one is gated out
    # of Module 4.  Two things to read here rather than the price column:
    #
    #   • max_accel_g.  The kinetic launchers do not have a cost problem, they
    #     have a payload problem.  10,000 g passes bulk propellant, water and
    #     steel billets.  It does not pass a mining rig, a solar array, an
    #     optic, a reaction wheel or a radio.  A launch system that can only
    #     lift consumables changes the economics of a mining programme without
    #     lifting any of its hardware, and this pipeline has no way to express
    #     a split manifest.
    #   • origin.  A lunar mass driver or elevator beats everything here on
    #     $/kg and cannot be used until something is already on the Moon.
    #     Module 4 departs from Earth, so those rows are unreachable by
    #     construction rather than merely immature.
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                          "SpinLaunch Orbital",
        "operator":                      "SpinLaunch",
        "country":                       "USA",
        "status":                        "concept",
        "availability":                  "unavailable",
        "launch_type":                   "kinetic",
        "reusability":                   "not_applicable",
        "core_propellant":               "not_applicable",
        "first_flight_year":             None,
        "trl":                           4,
        "max_accel_g":                   10_000.0,
        "payload_leo_kg":                   200,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd":             1_250_000,
        "price_basis":                   "target",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "A vacuum centrifuge throws the vehicle to ~2 km/s and a small "
                 "rocket stage does the rest.  The suborbital accelerator flew "
                 "10 test articles from 2021, so this is a real machine, not a "
                 "paper one — TRL 4.  ~10,000 g at release is the whole story. "
                 "Since 2025 the company's priority is its Meridian satellite "
                 "constellation, launched on conventional rockets; the orbital "
                 "accelerator is 'exploratory' as of May 2026.  The $/kg is the "
                 "published target and assumes a cadence nobody has shown.",
    },
    {
        "name":                          "Light-gas gun (orbital)",
        "operator":                      "Green Launch / HARP lineage",
        "country":                       "USA / Canada",
        "status":                        "concept",
        "availability":                  "unavailable",
        "launch_type":                   "gun",
        "reusability":                   "not_applicable",
        "core_propellant":               "not_applicable",
        "first_flight_year":             None,
        "trl":                           3,
        "max_accel_g":                   30_000.0,
        "payload_leo_kg":                    30,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "list_price_usd":               300_000,
        "price_basis":                   "target",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Gerald Bull's HARP put a 180 kg slug to 180 km in 1966 — the "
                 "altitude record for a gun still stands.  Orbital insertion "
                 "needs a kick stage, and ~30,000 g means the kick stage has to "
                 "survive it too.  Hydrogen-driven light-gas guns reach ~7 km/s "
                 "in the laboratory.  Payload-limited to consumables forever.",
    },
    {
        "name":                          "StarTram (maglev)",
        "operator":                      "concept — Powell & Maise",
        "country":                       "USA",
        "status":                        "concept",
        "availability":                  "unavailable",
        "launch_type":                   "maglev",
        "reusability":                   "not_applicable",
        "core_propellant":               "not_applicable",
        "first_flight_year":             None,
        "trl":                           2,
        "max_accel_g":                     30.0,
        "payload_leo_kg":                40_000,
        "payload_gto_kg":                15_000,
        "payload_escape_kg":             10_000,
        "list_price_usd":             1_600_000,
        "price_basis":                   "target",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Superconducting maglev accelerator in an evacuated tube, "
                 "exiting at altitude through a magnetically-levitated tether. "
                 "The Gen-1 cargo variant is quoted near $40/kg — two orders "
                 "below anything flying — on a claimed ~$20B of infrastructure "
                 "and 30 g, which is survivable by hardware unlike the two rows "
                 "above.  TRL 2: no element of the launch tube has been built. "
                 "The $/kg assumes the capital is already sunk and the traffic "
                 "exists to amortise it, which is the assumption doing all the "
                 "work in every entry in this section.",
    },
    {
        "name":                          "Skylon / SABRE",
        "operator":                      "concept — Reaction Engines",
        "country":                       "UK",
        "status":                        "concept",
        "availability":                  "unavailable",
        "launch_type":                   "airbreathing",
        "reusability":                   "full",
        "core_propellant":               "hydrolox",
        "first_flight_year":             None,
        "trl":                           4,
        "max_accel_g":                     3.0,
        "payload_leo_kg":                15_000,
        "payload_gto_kg":                 4_000,
        "payload_escape_kg":              2_000,
        "list_price_usd":            15_000_000,
        "price_basis":                   "target",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Air-breathing single-stage-to-orbit spaceplane: a precooler "
                 "chills Mach-5 intake air in ~1/100 s so a rocket engine can "
                 "breathe it to Mach 5.5, then closes the cycle. The precooler "
                 "was demonstrated at Mach-5 conditions in 2019 and is the only "
                 "part that was.  Reaction Engines Ltd entered administration in "
                 "October 2024 — status 'concept' here is a statement about the "
                 "company as much as the technology.",
    },
    {
        "name":                          "Sea Dragon",
        "operator":                      "concept — Truax / Aerojet 1962",
        "country":                       "USA",
        "status":                        "concept",
        "availability":                  "unavailable",
        "launch_type":                   "chemical_rocket",
        "core_propellant":               "kerolox",
        "first_flight_year":             None,
        "trl":                           2,
        "max_accel_g":                     4.0,
        "payload_leo_kg":               550_000,
        "payload_gto_kg":               200_000,
        "payload_escape_kg":            150_000,
        "list_price_usd":           300_000_000,
        "price_basis":                   "target",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Truax's 1962 sea-launched pressure-fed two-stage vehicle: "
                 "550 t to LEO, 23 m in diameter, built to shipyard tolerances "
                 "in 8 mm steel rather than to aerospace ones.  TRW reviewed the "
                 "design and found it sound.  It is here because it is the "
                 "canonical demonstration that launch cost is an engineering "
                 "CHOICE about tolerance and scale, not a physical constant — "
                 "the entire premise the $/kg column rests on.",
    },
    {
        "name":                          "Lunar mass driver",
        "operator":                      "concept — O'Neill 1974",
        "country":                       "USA",
        "status":                        "concept",
        "availability":                  "unavailable",
        "launch_type":                   "kinetic",
        "origin":                        "lunar_surface",
        "reusability":                   "not_applicable",
        "core_propellant":               "not_applicable",
        "first_flight_year":             None,
        "trl":                           3,
        "max_accel_g":                    1_000.0,
        "payload_leo_kg":               100_000,     # per year, to lunar escape; see notes
        "payload_gto_kg":                     0,
        "payload_escape_kg":            100_000,
        "list_price_usd":             1_000_000,
        "price_basis":                   "target",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Electromagnetically launch lunar regolith to escape velocity "
                 "— 2.4 km/s, against Earth's 11.2 — with no atmosphere in the "
                 "way.  O'Neill and Snow built and ran a prototype at Princeton "
                 "in 1977.  The $/kg is electricity and amortisation, and it is "
                 "roughly two hundred times below the cheapest rocket here.\n"
                 "⚠️  The payload columns are ANNUAL THROUGHPUT, not per-launch "
                 "mass, and the origin is the lunar surface.  Module 4 departs "
                 "from Earth and prices a discrete launch, so it cannot read "
                 "either column correctly — which is why origin is gated rather "
                 "than merely status.  This row is a marker for a delivery "
                 "architecture the pipeline does not model, not an input to it.",
    },
    {
        "name":                          "Lunar space elevator",
        "operator":                      "concept — Pearson 1979",
        "country":                       "USA",
        "status":                        "concept",
        "availability":                  "unavailable",
        "launch_type":                   "tether",
        "origin":                        "lunar_surface",
        "reusability":                   "not_applicable",
        "core_propellant":               "not_applicable",
        "first_flight_year":             None,
        "trl":                           2,
        "max_accel_g":                      0.2,
        "payload_leo_kg":                50_000,     # per year; see notes
        "payload_gto_kg":                     0,
        "payload_escape_kg":             50_000,
        "list_price_usd":               500_000,
        "price_basis":                   "target",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "A tether from the lunar surface through Earth-Moon L1. "
                 "Unlike an Earth elevator this needs NO new material: the "
                 "Moon's shallow well and the L1 balance point put the required "
                 "specific strength inside what Zylon and M5 already deliver "
                 "(Pearson 1979; Eubanks & Radley 2016).  It is a manufacturing "
                 "and capital problem, not a materials-science one — the single "
                 "most under-appreciated entry in this table.\n"
                 "⚠️  Same caveats as the lunar mass driver: annual throughput, "
                 "lunar origin, gated.",
    },
    {
        "name":                          "Earth space elevator",
        "operator":                      "concept — Artsutanov 1960",
        "country":                       "USSR",
        "status":                        "concept",
        "availability":                  "unavailable",
        "launch_type":                   "tether",
        "reusability":                   "not_applicable",
        "core_propellant":               "not_applicable",
        "first_flight_year":             None,
        "trl":                           1,
        "max_accel_g":                      0.1,
        "payload_leo_kg":                20_000,     # per year; see notes
        "payload_gto_kg":                20_000,
        "payload_escape_kg":             20_000,
        "list_price_usd":             2_000_000,
        "price_basis":                   "target",
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "The one that needs a material nobody has.  A geostationary "
                 "tether wants ~50-100 GPa·cm³/g of specific strength; carbon "
                 "nanotube achieves it in single tubes millimetres long and "
                 "nothing has been spun into a macroscopic fibre within an "
                 "order of magnitude of it.  TRL 1, and unlike every other row "
                 "here the gap is physics of materials rather than money.  "
                 "Listed so that its absence is not read as an oversight, and "
                 "so the LUNAR elevator two rows up is not tarred with it.",
    },
]

_LAUNCH_STATUS_VALUES = {"operational", "development", "concept", "retired"}

# Closed vocabularies for the v1.16.0 columns.  Filter columns, so a typo
# silently empties a filtered search; checked at import like `status`.
_LAUNCH_VOCAB = {
    "availability":    {"open", "restricted", "government_only", "sold_out",
                        "unavailable"},
    "reusability":     {"expendable", "first_stage", "side_boosters",
                        "partial", "full", "not_applicable"},
    "core_propellant": {"kerolox", "methalox", "hydrolox", "hypergolic",
                        "solid", "propalox", "not_applicable"},
    "price_basis":     {"published", "contract", "reported", "estimate",
                        "target"},
}

# Stated on every row; no default, because a wrong default here is silent.
_LAUNCH_REQUIRED = ("country", "availability", "core_propellant",
                    "first_flight_year", "price_basis")

_DESTINATIONS = ("leo", "gto", "escape")

# Output column order.  The pre-1.16.0 columns keep their positions so a
# consumer that reads the CSV by position does not move; everything new is
# appended after them.
_LAUNCH_COLUMNS = (
    "name", "operator", "status",
    "payload_leo_kg", "payload_gto_kg", "payload_escape_kg",
    "fairing_volume_m3", "list_price_usd",
    "usd_per_kg_to_leo", "usd_per_kg_to_gto", "usd_per_kg_to_escape",
    "reference_year", "notes",
    "launch_type", "origin", "trl", "max_accel_g",
    "tanker_flights_for_escape",
    # v1.16.0
    "country", "availability", "reusability", "core_propellant",
    "first_flight_year", "price_basis",
    "list_price_usd_low", "list_price_usd_high",
    "payload_leo_kg_low", "payload_leo_kg_high",
    "payload_gto_kg_low", "payload_gto_kg_high",
    "payload_escape_kg_low", "payload_escape_kg_high",
    "usd_per_kg_to_leo_low", "usd_per_kg_to_leo_high",
    "usd_per_kg_to_gto_low", "usd_per_kg_to_gto_high",
    "usd_per_kg_to_escape_low", "usd_per_kg_to_escape_high",
    # v1.17.0
    "fairing_basis",
)


def _usd_per_kg(price, payload):
    """Whole dollars per kilogram, or NaN where the vehicle does not go."""
    if payload is None or not math.isfinite(payload) or payload <= 0:
        return np.nan
    return round(price / payload)


def band_centre(low, high):
    """The headline of a band: its geometric mean, to 3 significant figures.

    Geometric rather than arithmetic because launch prices and payloads are
    uncertain by FACTORS, not by fixed amounts: $450M-$2.1B is "within ~2x
    either way of ~$1B", and the arithmetic midpoint ($1.28B) sits closer to
    the top than that.  It also makes the derived $/kg behave: when price and
    payload are both geometric means, their ratio is exactly the geometric
    mean of the $/kg band's own ends, before rounding.

    3 significant figures because the band is the claim and the centre is a
    summary of it; a nine-digit centre would be false precision.  Clamped back
    inside the band, which rounding can otherwise step out of on a narrow one
    (18,814-18,850 kg centres at 18,832, which rounds to 18,800).

    Uses only sqrt and decimal formatting, both correctly rounded, so the
    committed CSV stays byte-identical on every platform.
    """
    if not (math.isfinite(low) and math.isfinite(high)):
        return np.nan
    if low == high:
        return low
    if low <= 0:
        raise ValueError("a band with a zero or negative end has no "
                         "geometric centre: [%s, %s]" % (low, high))
    centre = float("%.3g" % math.sqrt(low * high))
    return int(min(max(centre, low), high))


def _check_band(row: dict, low_key: str, mid_key: str, high_key: str) -> None:
    """A headline outside its own band is a typo or a stale edit, not a range."""
    lo, mid, hi = row[low_key], row[mid_key], row[high_key]
    if all(math.isfinite(x) for x in (lo, mid, hi)) and not lo <= mid <= hi:
        raise ValueError(
            f"launch vehicle {row['name']!r}: {mid_key} {mid} is outside its "
            f"own band [{lo}, {hi}]")
    if math.isfinite(mid) != math.isfinite(lo) or math.isfinite(mid) != math.isfinite(hi):
        raise ValueError(
            f"launch vehicle {row['name']!r}: {mid_key} and its band disagree "
            f"about whether a figure is published")


def _apply_launch_defaults(rows: List[dict], fairings: dict = None) -> None:
    """Fill the defaulted fields, derive the $/kg columns, and check the row.

    Keeps a conventional expendable rocket's entry to the fields that make it
    that particular rocket, rather than restating `launch_type =
    "chemical_rocket"` seventy times.  Mutates in place, once, at import, and
    leaves each row's keys in `_LAUNCH_COLUMNS` order.
    """
    for row in rows:
        for key, default in _LAUNCH_DEFAULTS.items():
            row.setdefault(key, default)
        if row["status"] not in _LAUNCH_STATUS_VALUES:
            raise ValueError(
                f"launch vehicle {row['name']!r} has status {row['status']!r}; "
                f"Module 4 gates on this field, so it must be one of "
                f"{sorted(_LAUNCH_STATUS_VALUES)}"
            )
        for key in _LAUNCH_REQUIRED:
            if key not in row:
                raise ValueError(
                    f"launch vehicle {row['name']!r} does not state {key!r}; "
                    f"it has no default, on purpose")
        for key, allowed in _LAUNCH_VOCAB.items():
            if row[key] not in allowed:
                raise ValueError(
                    f"launch vehicle {row['name']!r} has {key} {row[key]!r}; "
                    f"must be one of {sorted(allowed)}")

        # A row states EITHER one figure OR a low and a high.  One figure is a
        # band of zero width; a band's headline is its geometric centre and is
        # derived, never typed, so the two can not drift apart.
        for mid in ("list_price_usd",) + tuple(
                "payload_%s_kg" % d for d in _DESTINATIONS):
            lo_k, hi_k = mid + "_low", mid + "_high"
            if mid in row:
                if lo_k in row or hi_k in row:
                    raise ValueError(
                        f"launch vehicle {row['name']!r} states {mid} AND a "
                        f"band; with a band, {mid} is derived as its centre, "
                        f"so state only {lo_k} and {hi_k}")
                row[lo_k] = row[hi_k] = row[mid]
            else:
                if lo_k not in row or hi_k not in row:
                    raise ValueError(
                        f"launch vehicle {row['name']!r} states neither {mid} "
                        f"nor both of {lo_k} and {hi_k}")
                if not row[lo_k] <= row[hi_k]:
                    raise ValueError(
                        f"launch vehicle {row['name']!r}: {lo_k} "
                        f"{row[lo_k]} is above {hi_k} {row[hi_k]}")
                row[mid] = band_centre(row[lo_k], row[hi_k])
            _check_band(row, lo_k, mid, hi_k)

        # Derived, never typed.
        for dest in _DESTINATIONS:
            col = "usd_per_kg_to_%s" % dest
            pay = "payload_%s_kg" % dest
            for suffix in ("", "_low", "_high"):
                if col + suffix in row:
                    raise ValueError(
                        f"launch vehicle {row['name']!r} types {col + suffix}; "
                        f"it is derived from price and payload, so delete it")
            row[col] = _usd_per_kg(row["list_price_usd"], row[pay])
            row[col + "_low"] = _usd_per_kg(row["list_price_usd_low"],
                                            row[pay + "_high"])
            row[col + "_high"] = _usd_per_kg(row["list_price_usd_high"],
                                             row[pay + "_low"])

        # Derived, never typed: the fairing volume and how it was obtained.
        for col in ("fairing_volume_m3", "fairing_basis"):
            if col in row:
                raise ValueError(
                    f"launch vehicle {row['name']!r} types {col}; it is derived "
                    f"in fairings.py from a cited source, so delete it")
        fairing = (FAIRINGS if fairings is None else fairings).get(row["name"])
        if fairing is None:
            raise ValueError(
                f"launch vehicle {row['name']!r} has no entry in fairings.py; "
                f"every row states where its fairing volume comes from, or "
                f"why there is none")
        row["fairing_volume_m3"] = fairing["volume"]
        row["fairing_basis"] = fairing["basis"]
        row["notes"] = (row["notes"].rstrip()
                        + "  Fairing volume: " + fairing["source"] + ".")

        unknown = set(row) - set(_LAUNCH_COLUMNS)
        if unknown:
            raise ValueError(
                f"launch vehicle {row['name']!r} carries unknown keys "
                f"{sorted(unknown)}")
        ordered = {k: row[k] for k in _LAUNCH_COLUMNS}
        row.clear()
        row.update(ordered)


_apply_launch_defaults(LAUNCH_VEHICLES_REFERENCE)

# The other half of the register: a fairing entry with no row behind it is a
# source still being cited for a vehicle that has gone.
_orphans = set(FAIRINGS) - {v["name"] for v in LAUNCH_VEHICLES_REFERENCE}
if _orphans:
    raise ValueError(f"fairings.py cites vehicles with no launch row: "
                     f"{sorted(_orphans)}")

say(f"OK  Launch vehicles reference loaded - {len(LAUNCH_VEHICLES_REFERENCE)} vehicles "
      f"({sum(1 for v in LAUNCH_VEHICLES_REFERENCE if v['status'] == 'operational')} operational, "
      f"{sum(1 for v in LAUNCH_VEHICLES_REFERENCE if v['status'] == 'development')} development, "
      f"{sum(1 for v in LAUNCH_VEHICLES_REFERENCE if v['status'] == 'concept')} concept, "
      f"{sum(1 for v in LAUNCH_VEHICLES_REFERENCE if v['status'] == 'retired')} retired)")
