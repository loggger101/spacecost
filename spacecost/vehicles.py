# -*- coding: utf-8 -*-
"""Launch vehicle reference table: 36 vehicles, one row each, every row cited.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

from typing import List

import numpy as np

from ._log import say

# ─────────────────────────────────────────────────────────────────────────────
# LAUNCH VEHICLE REFERENCE TABLE
# ─────────────────────────────────────────────────────────────────────────────
# One row per vehicle.  $/kg-to-LEO is the headline figure; $/kg-to-GTO and
# $/kg-to-escape are list_price_usd divided by the corresponding published
# payload mass for that destination, every row in this table uses real
# manufacturer / agency figures, not rules-of-thumb.
#
# For reusable vehicles the payload masses MUST be self-consistent with the
# stated list price's recovery mode (e.g. Falcon Heavy partial-reuse $97M
# pairs with ~57 t LEO, NOT the 63.8 t all-expendable max).  Watch for
# refueling-architecture caveats on Starship escape numbers.
#
# Sources cited inline in each row's `notes`; reference_year tags staleness.

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
_LAUNCH_DEFAULTS = {
    "launch_type":               "chemical_rocket",
    "origin":                    "earth_surface",
    "trl":                       9,
    "max_accel_g":               6.0,
    "tanker_flights_for_escape": 0,
}

_REF_YEAR_LAUNCH = 2026

LAUNCH_VEHICLES_REFERENCE: List[dict] = [
    {
        "name":                          "Falcon 9 (reusable)",
        "operator":                      "SpaceX",
        "status":                        "operational",
        "payload_leo_kg":                17_400,
        "payload_gto_kg":                 5_500,    # reusable drone-ship (8,300 is EXPENDABLE)
        "payload_escape_kg":              2_500,    # C3=0 reusable estimate (~$120M expendable lifts 4,020)
        "fairing_volume_m3":                145,
        "list_price_usd":            74_000_000,    # SatBase 2026-02 price hike (was $70M)
        "usd_per_kg_to_leo":              4_253,    # 74M / 17,400
        "usd_per_kg_to_gto":             13_455,    # 74M / 5,500
        "usd_per_kg_to_escape":          29_600,    # 74M / 2,500
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: SpaceX list price (raised to $74M Feb 2026 per SatBase) + "
                 "Falcon 9 Payload User's Guide.  All payload figures are the "
                 "drone-ship recovery (reusable) config.  Expendable mode lifts "
                 "5.5→8.3 t GTO and ~4 t to escape but costs ~$120M.",
    },
    {
        "name":                          "Falcon Heavy (reusable side cores)",
        "operator":                      "SpaceX",
        "status":                        "operational",
        "payload_leo_kg":                57_000,    # partial-reusable config (Wikipedia 2026)
        "payload_gto_kg":                 8_000,    # partial-reusable GTO
        "payload_escape_kg":              3_500,    # partial-reusable interplanetary
        "fairing_volume_m3":                145,
        "list_price_usd":            97_000_000,    # SpaceX list price, partial reusable
        "usd_per_kg_to_leo":              1_702,    # 97M / 57,000
        "usd_per_kg_to_gto":             12_125,    # 97M / 8,000
        "usd_per_kg_to_escape":          27_714,    # 97M / 3,500
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: SpaceX $97M for partial-reusable config (side cores "
                 "recovered, center core expended).  All payload figures "
                 "self-consistent with this config.  All-expendable mode lifts "
                 "63.8 t LEO / 26.7 t GTO but costs ~$150M (Wikipedia 2026).",
    },
    {
        "name":                          "Starship (projected)",
        "operator":                      "SpaceX",
        "status":                        "development",
        "trl":                           6,
        # v1.9.0: the escape figure below assumes orbital refuelling.  SpaceX
        # has quoted 8-16 tanker flights for a fully-fuelled departure stage;
        # 12 is the midpoint.  Module 4 now charges them.
        "tanker_flights_for_escape":     12,
        "payload_leo_kg":               100_000,    # fully reusable lower bound
        "payload_gto_kg":                21_000,    # single-launch, no refuel
        "payload_escape_kg":             27_000,    # WITH orbital refueling
        "fairing_volume_m3":              1_000,
        "list_price_usd":            90_000_000,    # Voyager Technologies contract 2026
        "usd_per_kg_to_leo":                900,    # 90M / 100,000
        "usd_per_kg_to_gto":              4_286,    # 90M / 21,000
        "usd_per_kg_to_escape":           3_333,    # 90M / 27,000; see CAVEAT below
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: SpaceX-Voyager Technologies dedicated-launch contract "
                 "disclosed 2026 at $90M.  LEO at lower bound of 100-150 t fully-"
                 "reusable range, pending orbital qualification.  "
                 "CAVEAT: escape payload (27 t) > GTO (21 t) only because the "
                 "escape figure assumes orbital refueling (8-16 tanker flights). "
                 "Module 4 should add ~$90M × N_tankers to the escape-direct "
                 "scenario for an apples-to-apples comparison.",
    },
    {
        "name":                          "SLS Block 1B (Cargo)",
        "operator":                      "NASA",
        "status":                        "operational",
        "payload_leo_kg":               105_000,    # Block 1B Cargo LEO (NASA SLS factsheet)
        "payload_gto_kg":                41_000,    # GTO via EUS (~scaled to BLEO=42t)
        "payload_escape_kg":             42_000,    # TLI / interplanetary (NASA Artemis)
        "fairing_volume_m3":                340,
        "list_price_usd":         4_100_000_000,    # NASA OIG IG-24-015 fully-burdened
        "usd_per_kg_to_leo":             39_048,    # 4.1B / 105,000
        "usd_per_kg_to_gto":            100_000,    # 4.1B / 41,000
        "usd_per_kg_to_escape":          97_619,    # 4.1B / 42,000
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: NASA OIG IG-24-015 reports $4.1B per flight fully-burdened "
                 "(vehicle + Orion + service module + ground ops); OIG calls "
                 "'unsustainable'.  Payload masses from NASA SLS Block 1B Cargo "
                 "factsheet: 105 t LEO / 42 t TLI.",
    },
    {
        "name":                          "Atlas V 551",
        "operator":                      "ULA",
        "status":                        "operational",
        "payload_leo_kg":                18_850,
        "payload_gto_kg":                 8_900,
        "payload_escape_kg":              6_500,
        "fairing_volume_m3":                233,
        "list_price_usd":           153_000_000,
        "usd_per_kg_to_leo":              8_117,
        "usd_per_kg_to_gto":             17_191,
        "usd_per_kg_to_escape":          23_538,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: ULA RocketBuilder $153M base; government missions add "
                 "$30-80M for mission-assurance overhead (per SpaceNews 2024).",
    },
    {
        "name":                          "Vulcan Centaur VC6",
        "operator":                      "ULA",
        "status":                        "operational",
        "payload_leo_kg":                27_200,
        "payload_gto_kg":                14_400,
        "payload_escape_kg":              7_200,
        "fairing_volume_m3":                233,
        "list_price_usd":           110_000_000,
        "usd_per_kg_to_leo":              4_044,
        "usd_per_kg_to_gto":              7_639,
        "usd_per_kg_to_escape":          15_278,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: ULA / SpaceInsider 2025 — $110M starting price for "
                 "VC6 config (6 SRBs).  Payloads from ULA datasheet.",
    },
    {
        "name":                          "New Glenn",
        "operator":                      "Blue Origin",
        "status":                        "operational",   # promoted: 3 successful flights, 1st reuse Apr 2026
        "payload_leo_kg":                45_000,
        "payload_gto_kg":                13_600,
        "payload_escape_kg":              7_000,
        "fairing_volume_m3":                480,
        "list_price_usd":            68_000_000,
        "usd_per_kg_to_leo":              1_511,
        "usd_per_kg_to_gto":              5_000,
        "usd_per_kg_to_escape":           9_714,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Geekwire / Blue Origin May 2026 ($68-110M range, used "
                 "low end as customer base price).  First booster reuse Apr 2026.",
    },
    {
        "name":                          "Electron",
        "operator":                      "Rocket Lab",
        "status":                        "operational",
        "payload_leo_kg":                   320,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "fairing_volume_m3":               1.85,
        "list_price_usd":             7_500_000,
        "usd_per_kg_to_leo":             23_438,
        "usd_per_kg_to_gto":              np.nan,
        "usd_per_kg_to_escape":           np.nan,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Rocket Lab Form 10-Q FY2026 Q1 — $7.5M / 320 kg LEO. "
                 "Small-sat dedicated; useful for prospector probes only.",
    },
    {
        "name":                          "Soyuz-2.1b",
        "operator":                      "Roscosmos",
        "status":                        "operational",
        "payload_leo_kg":                 8_300,    # Wikipedia 2026
        "payload_gto_kg":                 3_250,    # with Fregat upper stage
        "payload_escape_kg":              2_400,
        "fairing_volume_m3":                 80,
        "list_price_usd":            48_500_000,    # Glavkosmos 2018 with Fregat
        "usd_per_kg_to_leo":              5_843,
        "usd_per_kg_to_gto":             14_923,
        "usd_per_kg_to_escape":          20_208,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Glavkosmos / TASS 2018 price ($48.5M w/ Fregat). "
                 "Effectively unavailable to Western customers under sanctions.",
    },
    {
        "name":                          "Ariane 6 (A64)",
        "operator":                      "ArianeGroup / ESA",
        "status":                        "operational",
        "payload_leo_kg":                21_500,    # ESA datasheet
        "payload_gto_kg":                11_500,
        "payload_escape_kg":              8_000,
        "fairing_volume_m3":                124,
        "list_price_usd":           115_000_000,    # €100M+ per SpaceNexus 2026
        "usd_per_kg_to_leo":              5_349,
        "usd_per_kg_to_gto":             10_000,
        "usd_per_kg_to_escape":          14_375,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: ESA Ariane 6 overview + SpaceNexus 2026 ($77-115M range). "
                 "Four-booster A64 config; 30+ flights booked end-2025.",
    },
    {
        "name":                          "Long March 5",
        "operator":                      "CASC (China)",
        "status":                        "operational",
        "payload_leo_kg":                25_000,
        "payload_gto_kg":                14_000,
        "payload_escape_kg":              8_200,
        "fairing_volume_m3":                157,
        "list_price_usd":           110_000_000,    # estimate; pricing opaque
        "usd_per_kg_to_leo":              4_400,
        "usd_per_kg_to_gto":              7_857,
        "usd_per_kg_to_escape":          13_415,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Wikipedia / China-in-Space — payload masses authoritative; "
                 "$110M is an estimate (Chinese commercial pricing is opaque). "
                 "Chang'e-5 and Tianwen-1 launch heritage.",
    },
    {
        "name":                          "H3 (24L)",
        "operator":                      "MHI / JAXA",
        "status":                        "operational",
        "payload_leo_kg":                16_500,    # H3-24L per Wikipedia 2026 (was 6,500, wrong)
        "payload_gto_kg":                 6_500,
        "payload_escape_kg":              4_000,
        "fairing_volume_m3":                184,
        "list_price_usd":            51_000_000,    # JAXA target ¥5B
        "usd_per_kg_to_leo":              3_091,    # 51M / 16,500
        "usd_per_kg_to_gto":              7_846,
        "usd_per_kg_to_escape":          12_750,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: JAXA H3 program target ¥5B (~$51M) per JAXA / Payload Space. "
                 "Successor to H-IIA targeting ~50% cost reduction.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # OPERATIONAL, added v1.9.0.  Mostly the non-Western and small-lift end,
    # which the table had skipped entirely.  None of these will win a heavy
    # asteroid mission; they are here so "cheapest $/kg" is a claim about the
    # whole market rather than about twelve vehicles somebody happened to list.
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                          "LVM3 (GSLV Mk III)",
        "operator":                      "ISRO",
        "status":                        "operational",
        "payload_leo_kg":                10_000,
        "payload_gto_kg":                 4_000,
        "payload_escape_kg":              2_000,
        "fairing_volume_m3":                110,
        "list_price_usd":            51_000_000,
        "usd_per_kg_to_leo":              5_100,
        "usd_per_kg_to_gto":             12_750,
        "usd_per_kg_to_escape":          25_500,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: ISRO / NSIL commercial rate ~$51M; payloads from the "
                 "ISRO LVM3 user manual.  Flew Chandrayaan-3 and two OneWeb "
                 "batches.  India's heaviest, and the cheapest human-rated-class "
                 "vehicle on this list per launch.",
    },
    {
        "name":                          "Ariane 6 (A62)",
        "operator":                      "ArianeGroup / ESA",
        "status":                        "operational",
        "payload_leo_kg":                10_300,
        "payload_gto_kg":                 4_500,
        "payload_escape_kg":              3_000,
        "fairing_volume_m3":                124,
        "list_price_usd":            80_000_000,
        "usd_per_kg_to_leo":              7_767,
        "usd_per_kg_to_gto":             17_778,
        "usd_per_kg_to_escape":          26_667,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: ESA Ariane 6 overview — the two-booster config, "
                 "roughly €70M against A64's €115M.  Worse $/kg than A64, which "
                 "is the usual result when a vehicle is flown below its "
                 "designed lift.",
    },
    {
        "name":                          "Long March 7",
        "operator":                      "CASC (China)",
        "status":                        "operational",
        "payload_leo_kg":                13_500,
        "payload_gto_kg":                 7_000,
        "payload_escape_kg":              4_000,
        "fairing_volume_m3":                111,
        "list_price_usd":            60_000_000,    # estimate; pricing opaque
        "usd_per_kg_to_leo":              4_444,
        "usd_per_kg_to_gto":              8_571,
        "usd_per_kg_to_escape":          15_000,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: CASC / Wikipedia payload figures; $60M is an estimate "
                 "on the same basis as the Long March 5 row — Chinese "
                 "commercial pricing is not published.  Kerolox, Tianzhou "
                 "cargo heritage.",
    },
    {
        "name":                          "Vega C",
        "operator":                      "Avio / ESA",
        "status":                        "operational",
        "payload_leo_kg":                 3_300,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "fairing_volume_m3":                 47,
        "list_price_usd":            37_000_000,
        "usd_per_kg_to_leo":             11_212,
        "usd_per_kg_to_gto":             np.nan,
        "usd_per_kg_to_escape":          np.nan,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Avio / ESA — ~€34M.  Solid first three stages, "
                 "restartable AVUM+ upper.  Small-lift; useful for a prospector "
                 "probe, not for a mining rig.",
    },
    {
        "name":                          "PSLV-XL",
        "operator":                      "ISRO",
        "status":                        "operational",
        "payload_leo_kg":                 3_800,
        "payload_gto_kg":                 1_425,
        "payload_escape_kg":              1_100,
        "fairing_volume_m3":                 34,
        "list_price_usd":            31_000_000,
        "usd_per_kg_to_leo":              8_158,
        "usd_per_kg_to_gto":             21_754,
        "usd_per_kg_to_escape":          28_182,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: ISRO / NSIL.  Flew Chandrayaan-1 and Mars Orbiter "
                 "Mission — the cheapest vehicle that has actually delivered a "
                 "payload to another planet, which is the only reason a "
                 "3.8 t launcher is in this table.",
    },
    {
        "name":                          "Alpha",
        "operator":                      "Firefly Aerospace",
        "status":                        "operational",
        "payload_leo_kg":                 1_030,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "fairing_volume_m3":                 22,
        "list_price_usd":            15_000_000,
        "usd_per_kg_to_leo":             14_563,
        "usd_per_kg_to_gto":             np.nan,
        "usd_per_kg_to_escape":          np.nan,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Firefly published price.  Small-lift kerolox.  Listed "
                 "for market completeness at the bottom end.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # RETIRED, flew, will not fly again.  Kept for the same reason mercury ion
    # is kept in the propellant table: so that a historical $/kg figure found
    # elsewhere can be identified as unavailable rather than as an oversight.
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                          "Delta IV Heavy",
        "operator":                      "ULA",
        "status":                        "retired",
        "payload_leo_kg":                28_790,
        "payload_gto_kg":                14_220,
        "payload_escape_kg":             10_000,
        "fairing_volume_m3":                310,
        "list_price_usd":           440_000_000,
        "usd_per_kg_to_leo":             15_283,
        "usd_per_kg_to_gto":             30_942,
        "usd_per_kg_to_escape":          44_000,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Last flight April 2024 (NROL-70).  Hydrolox, three cores, and "
                 "the launcher that sent Parker Solar Probe to the highest "
                 "departure energy ever flown.  Replaced by Vulcan.",
    },
    {
        "name":                          "H-IIA 204",
        "operator":                      "MHI / JAXA",
        "status":                        "retired",
        "payload_leo_kg":                15_000,
        "payload_gto_kg":                 6_000,
        "payload_escape_kg":              3_600,
        "fairing_volume_m3":                122,
        "list_price_usd":            90_000_000,
        "usd_per_kg_to_leo":              6_000,
        "usd_per_kg_to_gto":             15_000,
        "usd_per_kg_to_escape":          25_000,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Last flight June 2025 (GOSAT-GW), 49 flights and one failure. "
                 "Launched Hayabusa2 — the most relevant flight heritage in "
                 "this entire table to what this pipeline models.  Succeeded "
                 "by H3.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # DEVELOPMENT: announced, hardware in test, not yet flown to orbit.
    # Gated out of Module 4 by operational_vehicles_only, same as Starship.
    # Prices are targets, and launch-vehicle targets are optimistic by
    # construction; treat every list_price_usd here as a floor.
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                          "Neutron",
        "operator":                      "Rocket Lab",
        "status":                        "development",
        "trl":                           6,
        "payload_leo_kg":                13_000,    # reusable; 15,000 expendable
        "payload_gto_kg":                 1_500,
        "payload_escape_kg":              1_000,
        "fairing_volume_m3":                113,
        "list_price_usd":            55_000_000,
        "usd_per_kg_to_leo":              4_231,
        "usd_per_kg_to_gto":             36_667,
        "usd_per_kg_to_escape":          55_000,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Rocket Lab investor materials — ~$50-55M, 13 t LEO "
                 "reusable.  Methalox, captive fairing, first-stage return. "
                 "Beyond-LEO capability is thin: the upper stage is sized for "
                 "constellation work, so the escape figure is poor for the class.",
    },
    {
        "name":                          "Terran R",
        "operator":                      "Relativity Space",
        "status":                        "development",
        "trl":                           5,
        "payload_leo_kg":                33_500,
        "payload_gto_kg":                 5_500,
        "payload_escape_kg":              4_000,
        "fairing_volume_m3":                340,
        "list_price_usd":            70_000_000,    # not published; class estimate
        "usd_per_kg_to_leo":              2_090,
        "usd_per_kg_to_gto":             12_727,
        "usd_per_kg_to_escape":          17_500,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Relativity published payload figures; price is an "
                 "estimate against the Falcon 9 / New Glenn class, since "
                 "Relativity has not published one.  Methalox, reusable first "
                 "stage, largely additively manufactured.",
    },
    {
        "name":                          "Nova",
        "operator":                      "Stoke Space",
        "status":                        "development",
        "trl":                           5,
        "payload_leo_kg":                 5_000,    # fully reusable; 7,000 expendable
        "payload_gto_kg":                 1_200,
        "payload_escape_kg":                800,
        "fairing_volume_m3":                 80,
        "list_price_usd":            25_000_000,
        "usd_per_kg_to_leo":              5_000,
        "usd_per_kg_to_gto":             20_833,
        "usd_per_kg_to_escape":          31_250,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Stoke Space published figures.  The only vehicle in "
                 "this table besides Starship designed for FULL reuse including "
                 "the second stage — an actively-cooled regeneratively-shielded "
                 "upper stage.  If that works, the $/kg here is a ceiling rather "
                 "than a floor, which is the opposite of every other row.",
    },
    {
        "name":                          "Eclipse (MLV)",
        "operator":                      "Firefly / Northrop Grumman",
        "status":                        "development",
        "trl":                           5,
        "payload_leo_kg":                16_300,
        "payload_gto_kg":                 3_000,
        "payload_escape_kg":              2_000,
        "fairing_volume_m3":                160,
        "list_price_usd":            80_000_000,
        "usd_per_kg_to_leo":              4_908,
        "usd_per_kg_to_gto":             26_667,
        "usd_per_kg_to_escape":          40_000,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Firefly / Northrop announcements.  Formerly MLV; "
                 "16.3 t LEO on a reusable methalox first stage.",
    },
    {
        "name":                          "Zhuque-3",
        "operator":                      "LandSpace (China)",
        "status":                        "development",
        "trl":                           6,
        "payload_leo_kg":                21_000,    # expendable; 18,300 reusable
        "payload_gto_kg":                 6_000,
        "payload_escape_kg":              4_000,
        "fairing_volume_m3":                190,
        "list_price_usd":            30_000_000,    # estimate; pricing opaque
        "usd_per_kg_to_leo":              1_429,
        "usd_per_kg_to_gto":              5_000,
        "usd_per_kg_to_escape":           7_500,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: LandSpace published payloads; price estimated on the "
                 "same opaque basis as the other Chinese rows.  Stainless "
                 "methalox with a returning first stage — the closest analogue "
                 "to Falcon 9 outside SpaceX, and its estimated $/kg to LEO is "
                 "the lowest on this table after Starship.  That estimate is "
                 "doing a lot of work; treat the ranking, not the number.",
    },
    {
        "name":                          "Tianlong-3",
        "operator":                      "Space Pioneer (China)",
        "status":                        "development",
        "trl":                           5,
        "payload_leo_kg":                17_000,
        "payload_gto_kg":                 5_000,
        "payload_escape_kg":              3_000,
        "fairing_volume_m3":                150,
        "list_price_usd":            25_000_000,    # estimate
        "usd_per_kg_to_leo":              1_471,
        "usd_per_kg_to_gto":              5_000,
        "usd_per_kg_to_escape":           8_333,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: Space Pioneer announcements; price estimated. "
                 "Kerolox, reusable first stage intended.",
    },
    {
        "name":                          "Long March 10",
        "operator":                      "CASC (China)",
        "status":                        "development",
        "trl":                           5,
        "payload_leo_kg":                70_000,
        "payload_gto_kg":                31_000,
        "payload_escape_kg":             27_000,    # TLI, crewed lunar architecture
        "fairing_volume_m3":                310,
        "list_price_usd":           200_000_000,    # estimate
        "usd_per_kg_to_leo":              2_857,
        "usd_per_kg_to_gto":              6_452,
        "usd_per_kg_to_escape":           7_407,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: CASC crewed-lunar-programme disclosures; price "
                 "estimated.  70 t LEO / 27 t TLI targeting a 2030 crewed lunar "
                 "landing.  Would be the best $/kg-to-escape on this table if "
                 "the price estimate holds, which is a large if.",
    },
    {
        "name":                          "Long March 9",
        "operator":                      "CASC (China)",
        "status":                        "development",
        "trl":                           3,
        "payload_leo_kg":               150_000,
        "payload_gto_kg":                65_000,
        "payload_escape_kg":             50_000,
        "fairing_volume_m3":              1_000,
        "list_price_usd":           500_000_000,    # estimate
        "usd_per_kg_to_leo":              3_333,
        "usd_per_kg_to_gto":              7_692,
        "usd_per_kg_to_escape":          10_000,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "Source: CASC roadmap presentations; the design has been "
                 "revised repeatedly, most recently toward a reusable "
                 "Starship-like configuration, and no flight date before the "
                 "mid-2030s is credible.  TRL 3.  Present because it is the "
                 "only announced vehicle in the Starship class that is not "
                 "Starship.",
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
        "status":                        "concept",
        "launch_type":                   "kinetic",
        "trl":                           4,
        "max_accel_g":                   10_000.0,
        "payload_leo_kg":                   200,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "fairing_volume_m3":                0.6,
        "list_price_usd":             1_250_000,
        "usd_per_kg_to_leo":              6_250,
        "usd_per_kg_to_gto":             np.nan,
        "usd_per_kg_to_escape":          np.nan,
        "reference_year":          _REF_YEAR_LAUNCH,
        "notes": "A vacuum centrifuge throws the vehicle to ~2 km/s and a small "
                 "rocket stage does the rest.  The suborbital accelerator flew "
                 "test articles in 2022, so this is a real machine, not a paper "
                 "one — TRL 4.  ~10,000 g at release is the whole story: the "
                 "company's own manifest talk is propellant and bulk materials. "
                 "The $/kg here is the published target and assumes a cadence "
                 "nobody has demonstrated.",
    },
    {
        "name":                          "Light-gas gun (orbital)",
        "operator":                      "Green Launch / HARP lineage",
        "status":                        "concept",
        "launch_type":                   "gun",
        "trl":                           3,
        "max_accel_g":                   30_000.0,
        "payload_leo_kg":                    30,
        "payload_gto_kg":                     0,
        "payload_escape_kg":                  0,
        "fairing_volume_m3":               0.05,
        "list_price_usd":               300_000,
        "usd_per_kg_to_leo":             10_000,
        "usd_per_kg_to_gto":             np.nan,
        "usd_per_kg_to_escape":          np.nan,
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
        "status":                        "concept",
        "launch_type":                   "maglev",
        "trl":                           2,
        "max_accel_g":                     30.0,
        "payload_leo_kg":                40_000,
        "payload_gto_kg":                15_000,
        "payload_escape_kg":             10_000,
        "fairing_volume_m3":                200,
        "list_price_usd":             1_600_000,
        "usd_per_kg_to_leo":                 40,
        "usd_per_kg_to_gto":                107,
        "usd_per_kg_to_escape":             160,
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
        "status":                        "concept",
        "launch_type":                   "airbreathing",
        "trl":                           4,
        "max_accel_g":                     3.0,
        "payload_leo_kg":                15_000,
        "payload_gto_kg":                 4_000,
        "payload_escape_kg":              2_000,
        "fairing_volume_m3":                140,
        "list_price_usd":            15_000_000,
        "usd_per_kg_to_leo":              1_000,
        "usd_per_kg_to_gto":              3_750,
        "usd_per_kg_to_escape":           7_500,
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
        "status":                        "concept",
        "launch_type":                   "chemical_rocket",
        "trl":                           2,
        "max_accel_g":                     4.0,
        "payload_leo_kg":               550_000,
        "payload_gto_kg":               200_000,
        "payload_escape_kg":            150_000,
        "fairing_volume_m3":              6_000,
        "list_price_usd":           300_000_000,
        "usd_per_kg_to_leo":                545,
        "usd_per_kg_to_gto":              1_500,
        "usd_per_kg_to_escape":           2_000,
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
        "status":                        "concept",
        "launch_type":                   "kinetic",
        "origin":                        "lunar_surface",
        "trl":                           3,
        "max_accel_g":                    1_000.0,
        "payload_leo_kg":               100_000,     # per year, to lunar escape; see notes
        "payload_gto_kg":                     0,
        "payload_escape_kg":            100_000,
        "fairing_volume_m3":               np.nan,
        "list_price_usd":             1_000_000,
        "usd_per_kg_to_leo":                 10,
        "usd_per_kg_to_gto":             np.nan,
        "usd_per_kg_to_escape":              10,
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
        "status":                        "concept",
        "launch_type":                   "tether",
        "origin":                        "lunar_surface",
        "trl":                           2,
        "max_accel_g":                      0.2,
        "payload_leo_kg":                50_000,     # per year; see notes
        "payload_gto_kg":                     0,
        "payload_escape_kg":             50_000,
        "fairing_volume_m3":               np.nan,
        "list_price_usd":               500_000,
        "usd_per_kg_to_leo":                 10,
        "usd_per_kg_to_gto":             np.nan,
        "usd_per_kg_to_escape":              10,
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
        "status":                        "concept",
        "launch_type":                   "tether",
        "trl":                           1,
        "max_accel_g":                      0.1,
        "payload_leo_kg":                20_000,     # per year; see notes
        "payload_gto_kg":                20_000,
        "payload_escape_kg":             20_000,
        "fairing_volume_m3":               np.nan,
        "list_price_usd":             2_000_000,
        "usd_per_kg_to_leo":                100,
        "usd_per_kg_to_gto":                100,
        "usd_per_kg_to_escape":             100,
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


def _apply_launch_defaults(rows: List[dict]) -> None:
    """Fill the v1.9.0 schema fields on rows that do not state them.

    Keeps a conventional expendable rocket's entry to the fields that make it
    that particular rocket, rather than restating `launch_type =
    "chemical_rocket"` twenty times.  Mutates in place, once, at import.
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


_apply_launch_defaults(LAUNCH_VEHICLES_REFERENCE)

say(f"OK  Launch vehicles reference loaded - {len(LAUNCH_VEHICLES_REFERENCE)} vehicles "
      f"({sum(1 for v in LAUNCH_VEHICLES_REFERENCE if v['status'] == 'operational')} operational, "
      f"{sum(1 for v in LAUNCH_VEHICLES_REFERENCE if v['status'] == 'development')} development, "
      f"{sum(1 for v in LAUNCH_VEHICLES_REFERENCE if v['status'] == 'concept')} concept, "
      f"{sum(1 for v in LAUNCH_VEHICLES_REFERENCE if v['status'] == 'retired')} retired)")
