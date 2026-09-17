# -*- coding: utf-8 -*-
"""Storage systems reference table: 20 systems across the storage domains.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

from typing import List

from ._log import say
from .operations import OPERATIONAL_COSTS_REFERENCE
from .propellants import _COPV_PERFORMANCE_J_PER_KG, _TANK_BASE_KG_PER_L

# ─────────────────────────────────────────────────────────────────────────────
# STORAGE SYSTEMS REFERENCE TABLE  (v1.9.0)
# ─────────────────────────────────────────────────────────────────────────────
# Storage was the largest unmodelled block in this pipeline.  Before v1.9.0 the
# entire treatment of it was one column, `boiloff_pct_per_day`, and a
# `density_kg_per_L` that was computed, exported, and read by nothing.  Four
# distinct things were missing, and they fail in different ways:
#
#   propellant  Tank mass scales with VOLUME, so leaving it out subsidises
#               every low-density propellant.  Now derived per propellant in
#               PROPELLANTS_REFERENCE; the rows here are the shared constants
#               that derivation rests on, plus the active-cooling option, which
#               is the only way to trade mass and power against boil-off.
#   cargo       The mined mass has to be HELD.  Ore needs restraint against the
#               return burn; volatiles need to still be there after four years
#               of cruise.  This pipeline sells water at an in-space depot and
#               has never once asked what keeps it from subliming on the way.
#   energy      A rotating body spends roughly half its time in the dark and
#               the mining rig does not stop.  Storage, not generation, is what
#               sets the power system's mass in that regime, and past ~3 AU
#               photovoltaics stop being the answer at all.
#   depot       Propellant left in orbit for someone else to collect.  The
#               entry that makes Starship's escape payload mean anything.
#
# Rows are reference data.  What Module 4 consumes has a matching entry in
# OPERATIONAL_COSTS_REFERENCE, because that is the table `_ops_value()` reads;
# this table is the taxonomy and the citations behind those numbers.

_REF_YEAR_STORAGE = 2026


# ─── FIGURES THIS TABLE MIRRORS FROM OPERATIONAL_COSTS  (v1.15.0) ────────────
# The comment above already says the rule: "What Module 4 consumes has a
# matching entry in OPERATIONAL_COSTS_REFERENCE", because that is the table
# Stage 4 reads, and `load_storage` repeats it -- add a figure here that Stage 4
# needs and you must add it there too.
#
# ⚠️  THREE FIGURES WERE OBEYING THAT RULE BY BEING TYPED TWICE.  RTG specific
# power, the eclipse fraction and the volatile containment mass each existed as
# a literal value AND a literal range in both files, agreeing only because
# nobody had edited one of them yet.  CITATIONS.md states the principle this
# breaks at the top of the file: two copies of one measurement is a defect
# waiting to happen, because one of them gets updated.
#
# So the copy in THIS file is now read from the other one.  Direction matters:
# `operational_costs` is what Stage 4 consumes and this table is the taxonomy
# and the citations behind it, so ops is the authority and storage mirrors.
#
# Renaming the ops category raises a KeyError at import rather than silently
# unlinking the two, which is the whole point of doing it by lookup instead of
# by comment.
_OPS_BY_CATEGORY = {r["category"]: r for r in OPERATIONAL_COSTS_REFERENCE}


def _mirrors_ops(category: str):
    """`(value, range_low, range_high)` for a figure OPERATIONAL_COSTS states.

    ⚠️  The two tables word their `unit` strings differently on purpose -- "W
    electric per kg" against "Watts-electric per kg of RTG" -- and that is
    presentation, not data.  Only the NUMBERS are shared, and only the numbers
    are mirrored here.
    """
    row = _OPS_BY_CATEGORY[category]
    return row["value"], row["range_low"], row["range_high"]


# Unpacked at module level rather than called inline, so the three rows below
# stay readable as a table and the link is visible in one place.
_RTG_W_PER_KG    = _mirrors_ops("RTG specific power")
_ECLIPSE_FRAC    = _mirrors_ops("Eclipse / night-side dark fraction")
_VOLATILE_HOLDUP = _mirrors_ops("Volatile cargo containment")

STORAGE_REFERENCE: List[dict] = [
    # ── PROPELLANT STORAGE ───────────────────────────────────────────────────
    {
        "name":            "Low-pressure liquid propellant tank",
        "domain":          "propellant",
        "unit":            "kg of tank per litre of propellant",
        "value":           _TANK_BASE_KG_PER_L,
        "range_low":       0.013,
        "range_high":      0.035,
        "status":          "operational",
        "trl":             9,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "The base figure every non-pressurised storage class in "
                 "PROPELLANTS_REFERENCE multiplies.  Bracketed by three flight "
                 "articles: Shuttle ET 0.0129 kg/L (big dumb tank, cheap per "
                 "litre), Falcon 9 stage 2 ~0.033, Centaur III ~0.035 (the last "
                 "two include thrust structure and avionics mounts).  Derivation "
                 "and the ∝V-vs-∝V^⅔ caveat are at _TANK_BASE_KG_PER_L.",
    },
    {
        "name":            "COPV burst performance factor",
        "domain":          "propellant",
        "unit":            "J per kg (PV/W)",
        "value":           _COPV_PERFORMANCE_J_PER_KG,
        "range_low":       250_000,
        "range_high":      600_000,
        "status":          "operational",
        "trl":             9,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "~40 km × g0.  Sets tank mass for every supercritical-gas "
                 "propellant: m/V = 1.5·p_operating/(PV/W).  This is why xenon "
                 "at 10 MPa pays 1.9% of its mass in tankage and krypton at "
                 "18 MPa pays 12.5% — the cheaper propellant needs the heavier "
                 "bottle, and the trade did not exist in this model before.",
    },
    {
        "name":            "Multi-layer insulation (passive)",
        "domain":          "propellant",
        "unit":            "kg per m² of tank surface",
        "value":           1.2,
        "range_low":       0.5,
        "range_high":      3.0,
        "status":          "operational",
        "trl":             9,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "60-layer aluminised-Mylar blanket, the passive baseline behind "
                 "every boiloff_pct_per_day figure in the propellant table. "
                 "Carried inside the storage-class tank multipliers rather than "
                 "as a separate area term, because this pipeline never computes "
                 "a tank's surface area — only its volume.",
    },
    {
        "name":            "Zero-boil-off cryocooler (20 K)",
        "domain":          "propellant",
        "unit":            "W electrical input per W lifted at 20 K",
        "value":           80.0,
        "range_low":       50.0,
        "range_high":      150.0,
        "status":          "development",
        "trl":             5,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "Reverse-turbo-Brayton.  Carnot at 20 K against a 300 K reject "
                 "is 14 W/W and real machines run 15-25% of Carnot, so 50-150 "
                 "W/W.  NASA's ZBO and eCryo programmes have run 20 K coolers on "
                 "the ground; nothing has flown on a propellant tank.\n"
                 "This is the row that turns boil-off from a fact into a CHOICE: "
                 "spend array mass and power, keep the hydrogen.  Module 4 does "
                 "not offer that choice yet — it applies boiloff_pct_per_day "
                 "passively — so hydrolox is charged the full 0.05%/day with no "
                 "option to buy it down.  That is conservative for hydrolox and "
                 "it is a known gap, not a modelling decision.",
    },
    {
        "name":            "Cryocooler specific mass (20 K)",
        "domain":          "propellant",
        "unit":            "kg per W lifted at 20 K",
        "value":           5.0,
        "range_low":       2.0,
        "range_high":      15.0,
        "status":          "development",
        "trl":             5,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "Cold head, compressor, recuperator and radiator.  Pairs with "
                 "the row above: a tank leaking 20 W needs ~100 kg of machine "
                 "and ~1.6 kW of electrical power to hold it at zero boil-off, "
                 "and the array for that 1.6 kW is another ~27 kg at 1 AU and "
                 "~240 kg at 3 AU.  Which is why zero-boil-off is a near-Sun "
                 "answer and passive tolerance is the far one.",
    },
    {
        "name":            "Vapour-cooled shield",
        "domain":          "propellant",
        "unit":            "fraction of passive boil-off removed",
        "value":           0.40,
        "range_low":       0.25,
        "range_high":      0.60,
        "status":          "operational",
        "trl":             8,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "Route the boil-off gas through a shield on its way overboard "
                 "and it intercepts heat that would have boiled more.  Free in "
                 "power, cheap in mass, and it only works while something is "
                 "already boiling.  Flown on ground and airborne cryogenic "
                 "systems; the 0.05%/day hydrolox figure already assumes a "
                 "good passive stack including this.",
    },

    # ── CARGO / ORE CONTAINMENT ──────────────────────────────────────────────
    {
        "name":            "Bulk ore restraint (bag / hopper)",
        "domain":          "cargo",
        "unit":            "kg of containment per kg of ore",
        "value":           0.15,
        "range_low":       0.08,
        "range_high":      0.30,
        "status":          "development",
        "trl":             4,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "Tankage, primary structure and cargo restraint for loose "
                 "regolith.  This is the number Module 4 carries as "
                 "`return_structure_frac_of_payload`, recorded here so the "
                 "cargo side of storage has a citation of its own.  Real cargo "
                 "spacecraft run 0.4:1 to 2:1 payload-to-structure; 0.15 is "
                 "aggressive and assumes dense ore in a body-mounted hopper "
                 "rather than a pressurised hold.  Before v1.10.0 it was zero "
                 "and the cascade happily loaded 125 t of ore into a 500 kg can.",
    },
    {
        "name":            "Volatile cargo containment (water ice)",
        "domain":          "cargo",
        "unit":            "kg of containment per kg of volatile cargo",
        # Mirrored from OPERATIONAL_COSTS "Volatile cargo containment".
        "value":           _VOLATILE_HOLDUP[0],
        "range_low":       _VOLATILE_HOLDUP[1],
        "range_high":      _VOLATILE_HOLDUP[2],
        "status":          "development",
        "trl":             4,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "Water sold at a depot has to still be water on arrival.  In "
                 "vacuum at 1 AU, exposed ice in sunlight sits well above its "
                 "sublimation threshold and is simply gone; shaded and blanketed "
                 "it is stable for decades.  So the cost is a sealed, shaded "
                 "hold — heavier than an ore hopper, far lighter than a cryogen "
                 "tank, and no active power.\n"
                 "✅  MODELLED as of Module 4 v1.14.0, through the "
                 "'Volatile cargo containment' OPERATIONAL_COSTS row — this "
                 "table is not one Module 4 loads, which is why the figure sat "
                 "here unread for two releases while the pipeline priced water "
                 "at every in-space destination and charged nothing to keep it "
                 "through a four-year cruise.  It was not a rounding term: the "
                 "best cislunar missions run ~88% water by mass, so the "
                 "commodity carrying the result was the one flying free.",
    },
    {
        "name":            "Sintered / consolidated cargo",
        "domain":          "cargo",
        "unit":            "Wh per kg of ore consolidated",
        "value":           350,
        "range_low":       150,
        "range_high":      800,
        "status":          "concept",
        "trl":             3,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "Melt or sinter the concentrate into billets and the restraint "
                 "problem mostly goes away — a solid block needs mounts, not a "
                 "hopper, and it cannot migrate under thrust or leak dust into "
                 "mechanisms.  Trades containment mass for processing energy at "
                 "a body where power is the binding constraint.  Studied for "
                 "lunar regolith (microwave sintering); not demonstrated on "
                 "asteroid material.",
    },
    {
        "name":            "Dust mitigation and seals",
        "domain":          "cargo",
        "unit":            "kg per kg of mining hardware",
        "value":           0.08,
        "range_low":       0.03,
        "range_high":      0.20,
        "status":          "development",
        "trl":             5,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "Regolith fines are the failure mode that ended Apollo's "
                 "surface EVAs early and jammed InSight's mole.  In microgravity "
                 "the dust does not settle at all — Hayabusa2's impactor "
                 "experiment showed ejecta persisting for hours.  Labyrinth "
                 "seals, electrodynamic screens and bellows on every joint. "
                 "Folded into the mining-rig recurring rate in this pipeline "
                 "rather than charged separately; listed so it is visible.",
    },

    # ── ONBOARD ENERGY STORAGE ───────────────────────────────────────────────
    {
        "name":            "Li-ion battery (system level)",
        "domain":          "energy",
        "unit":            "Wh per kg",
        "value":           130,
        "range_low":       90,
        "range_high":      200,
        "status":          "operational",
        "trl":             9,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "Cells reach 250-300 Wh/kg; packaging, harness, cell balancing "
                 "and thermal roughly halve it at the system level.  Already "
                 "inside the 60 W/kg 'Power system specific mass' row rather "
                 "than added to it — that row is explicitly PV + PMAD + battery "
                 "+ structure, which is why it is 60 W/kg against ROSA's ~150 "
                 "W/kg at the wing.",
    },
    {
        "name":            "Regenerative fuel cell",
        "domain":          "energy",
        "unit":            "Wh per kg",
        "value":           400,
        "range_low":       250,
        "range_high":      700,
        "status":          "development",
        "trl":             5,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "Electrolyse water in the light, run it back through a fuel "
                 "cell in the dark.  3× a battery's energy density and it gets "
                 "better the longer the dark period, because tank mass and "
                 "converter mass are separate — which is the opposite of a "
                 "battery.  For a mining rig on a rotating body it is the "
                 "obvious architecture, and it stores the one consumable the "
                 "asteroid itself supplies.  Studied by NASA for lunar night "
                 "survival; not flown.",
    },
    {
        "name":            "Flywheel energy storage",
        "domain":          "energy",
        "unit":            "Wh per kg",
        "value":           100,
        "range_low":       40,
        "range_high":      180,
        "status":          "development",
        "trl":             6,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "Unlimited cycle life and it doubles as a momentum wheel, which "
                 "a rotating-body operation needs anyway.  NASA G2 flywheel ran "
                 "on the ground at 60,000 rpm; the ISS flight unit was cancelled. "
                 "Energy density is no better than lithium, so it only wins where "
                 "cycle count or attitude control dominates.",
    },
    {
        "name":            "Eclipse / night-side power fraction",
        "domain":          "energy",
        "unit":            "fraction of mission time without sunlight",
        # Mirrored from OPERATIONAL_COSTS "Eclipse / night-side dark fraction".
        "value":           _ECLIPSE_FRAC[0],
        "range_low":       _ECLIPSE_FRAC[1],
        "range_high":      _ECLIPSE_FRAC[2],
        "status":          "operational",
        "trl":             9,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "A rig anchored to a rotating body is in shadow about half the "
                 "time — typical asteroid rotation periods run 2-20 h, so the "
                 "dark period is hours, not the 35 minutes of a LEO eclipse. "
                 "Sizing storage for it roughly DOUBLES the power system for a "
                 "given continuous draw.\n"
                 "✅  MODELLED as of Module 4 v1.14.0, through the "
                 "'Eclipse / night-side dark fraction', 'Energy storage usable "
                 "specific energy' and 'Power-system row baseline dark period' "
                 "OPERATIONAL_COSTS rows.  Module 4 now installs "
                 "[(1−f) + f/η]/(1−f) = 2.11× the continuous draw and adds the "
                 "storage the body's OWN rotation period demands, less what the "
                 "60 W/kg row already carries.  Radioisotope plants are exempt "
                 "and the EP array is exempt — one is flat with time, the other "
                 "is in permanent sunlight.",
    },
    {
        "name":            "RTG specific power",
        "domain":          "energy",
        "unit":            "W-electric per kg",
        # Mirrored from OPERATIONAL_COSTS "RTG specific power".
        "value":           _RTG_W_PER_KG[0],
        "range_low":       _RTG_W_PER_KG[1],
        "range_high":      _RTG_W_PER_KG[2],
        "status":          "operational",
        "trl":             9,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "GPHS-RTG: 290 We at 56 kg = 5.2 W/kg (Cassini, New Horizons). "
                 "MMRTG: 110 We at 45 kg = 2.4 W/kg (Curiosity, Perseverance) — "
                 "worse, because it is designed to work in an atmosphere too. "
                 "Flat with heliocentric distance, which is the entire point: "
                 "at 1 AU the 60 W/kg solar row beats it twelve times over, at "
                 "3 AU solar falls to 6.7 W/kg and they cross, and past ~3.2 AU "
                 "nuclear wins outright.  The pipeline's catalog runs well past "
                 "3 AU.",
    },
    {
        "name":            "Fission surface power (Kilopower class)",
        "domain":          "energy",
        "unit":            "W-electric per kg",
        "value":           6.7,
        "range_low":       0.7,
        "range_high":      15.0,
        "status":          "development",
        "trl":             5,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "KRUSTY demonstrated a 1 kWe uranium-molybdenum reactor with "
                 "Stirling conversion in 2018 — the first new US space reactor "
                 "test in decades.  A 10 kWe flight unit is designed around "
                 "~1,500 kg, so 6.7 W/kg, and unlike an RTG it scales: the "
                 "reactor mass is dominated by shielding and radiator, not by "
                 "fuel.  The only power source in this table that could run a "
                 "hundred-kilowatt beneficiation plant at 3 AU.",
    },

    # ── IN-SPACE PROPELLANT DEPOTS ───────────────────────────────────────────
    {
        "name":            "Orbital propellant depot (cryogenic)",
        "domain":          "depot",
        "unit":            "% of stored mass lost per day",
        "value":           0.03,
        "range_low":       0.01,
        "range_high":      0.10,
        "status":          "development",
        "trl":             5,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "A depot beats a spacecraft tank on boil-off for one geometric "
                 "reason: heat leak scales with area and capacity with volume, "
                 "so a big tank leaks proportionally less.  It can also afford "
                 "the cryocooler and the sunshade that a departure stage cannot. "
                 "Nothing has flown; SpaceX's propellant-transfer demonstration "
                 "is the nearest thing in progress.",
    },
    {
        "name":            "Depot refuelling flights to escape",
        "domain":          "depot",
        "unit":            "tanker launches per fully-fuelled departure",
        "value":           12,
        "range_low":       8,
        "range_high":      16,
        "status":          "development",
        "trl":             4,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "SpaceX's own range for filling a Starship in LEO before a "
                 "high-energy departure.  Carried on the vehicle row as "
                 "`tanker_flights_for_escape` and charged by Module 4 from "
                 "v1.9.0.  Before that, Starship's 27 t to escape — which is "
                 "larger than its GTO payload precisely BECAUSE it assumes "
                 "refuelling — was priced at a single $90M launch.  The vehicle "
                 "row had said so in prose since v1.4.0.",
    },
    {
        "name":            "In-space propellant transfer loss",
        "domain":          "depot",
        "unit":            "fraction of transferred mass lost per transfer",
        "value":           0.03,
        "range_low":       0.01,
        "range_high":      0.08,
        "status":          "development",
        "trl":             4,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "Chill-down of the receiving tank, residuals in the transfer "
                 "line, and ullage settling.  Cryogenic transfer in microgravity "
                 "has been done at small scale (Robotic Refueling Mission, "
                 "storables) and never at stage scale.  Not modelled by Module 4 "
                 "— tanker flights are charged, transfer losses are not.",
    },
    {
        "name":            "ISRU propellant depot (asteroid water)",
        "domain":          "depot",
        "unit":            "USD per kg of propellant delivered to depot",
        "value":           50.0,
        "range_low":       20.0,
        "range_high":      200.0,
        "status":          "concept",
        "trl":             3,
        "reference_year":  _REF_YEAR_STORAGE,
        "notes": "The endpoint the whole pipeline points at: water mined, "
                 "electrolysed or simply boiled, and left in orbit for the next "
                 "vehicle.  Carried as `isru_processing_usd_per_kg` in Module 4, "
                 "where it prices the ISRU return propellant a mission makes for "
                 "ITSELF.  Selling propellant to a third party is a different "
                 "market with a different depth, and Module 2 does not price it "
                 "— the in-space demand ceilings cover materials, not fuel.",
    },
]

say(f"OK  Storage reference loaded - {len(STORAGE_REFERENCE)} systems "
      f"({len({s['domain'] for s in STORAGE_REFERENCE})} domains)")
