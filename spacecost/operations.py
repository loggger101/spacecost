# -*- coding: utf-8 -*-
"""Operational cost reference table: the per-mission-year and per-kg lines.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

from typing import List

from ._log import say
from .config import CONFIG

# ─────────────────────────────────────────────────────────────────────────────
# OPERATIONAL COSTS REFERENCE TABLE
# ─────────────────────────────────────────────────────────────────────────────
# Fixed and recurring overhead.  Each row's `notes` field carries an
# inline citation; representative anchors include NASA OIG audit IG-24-015
# (SLS), the OSIRIS-REx mission cost breakdown (Planetary Society / NASA),
# NASA DSN Mission Operations & Communications Services catalog 820-100-H,
# Gallagher / Plane Talking 2024 space-insurance market update, the
# Damodaran NYU Stern industry cost-of-capital tables, and the Mars 2020 /
# Perseverance autonomy program for the autonomous-control NRE anchor.
#
# Mission profile: every line item here assumes an UNCREWED autonomous
# mining spacecraft (v1.2.4+).  No crew costs anywhere in the table.

_REF_YEAR_OPS = 2026

OPERATIONAL_COSTS_REFERENCE: List[dict] = [
    {
        "category":         "Spacecraft development (NRE)",
        "unit":             "USD per program",
        "value":            588_500_000,        # OSIRIS-REx actual
        "range_low":        100_000_000,
        "range_high":     2_000_000_000,
        "notes": "Anchor: OSIRIS-REx spacecraft development = $588.5M actual "
                 "(Planetary Society / NASA budget breakdown).  Discovery-class "
                 "deep-space platform.  Range covers SmallSat ($100M) → flagship ($2B+).",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Mining payload recurring cost",
        "unit":             "USD per kg of mining hardware",
        "value":            300_000,
        "range_low":        100_000,
        "range_high":     1_000_000,
        "notes": "Burdened recurring hardware cost for deep-space-rated mining "
                 "equipment.  Anchor: Aerospace Corp Small Mission Cost Model "
                 "and NASA NICM bracket recurring deep-space hardware at "
                 "$100k-$1M/kg.  Asteroid-mining rigs trend mid-range due to "
                 "regolith-contact mechanisms.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Return capsule recurring cost",
        "unit":             "USD per kg of return-capsule dry mass",
        "value":            150_000,
        "range_low":         50_000,
        "range_high":       400_000,
        "notes": "v1.3.0.  Was previously billed at the mining-payload rate "
                 "($300k/kg), which over-prices it: a sample-return capsule is "
                 "structure + TPS frame + parachute + beacon, with no "
                 "regolith-contact mechanisms, no manipulator, no power or "
                 "propulsion system, and no science payload.  Stardust and the "
                 "OSIRIS-REx SRC are the heritage.  Half the mining-rig rate; "
                 "range spans a bare capsule to one with active thermal and "
                 "guided entry.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Berthing adapter recurring cost",
        "unit":             "USD per kg of delivery-vehicle dry mass",
        "value":             60_000,
        "range_low":         30_000,
        "range_high":       150_000,
        "notes": "v1.4.0.  In-space delivery (LEO / cislunar depot) replaces the "
                 "re-entry capsule with a passive berthing adapter + cargo "
                 "carrier: structure, latches, grapple fixture, RF beacon.  No "
                 "TPS, no parachute, no guided-entry GNC, no flotation or "
                 "beacon-for-recovery.  Priced well under the $150k/kg re-entry "
                 "capsule rate and near the low end of the NICM/SSCM recurring "
                 "bracket, since it is the simplest deep-space-rated structure "
                 "in the catalog.  Heritage: Cygnus PCM, Dragon trunk, the "
                 "passive half of the NASA Docking System.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Surface lander recurring cost",
        "unit":             "USD per kg of lander dry mass",
        "value":            200_000,
        "range_low":        100_000,
        "range_high":       500_000,
        "notes": "v1.5.0.  Delivering to a lunar or Mars SURFACE base needs a "
                 "lander, not a berthing adapter: throttleable descent "
                 "engines, landing legs, terminal guidance and hazard "
                 "avoidance, plus the GNC to fly it.  More capable than the "
                 "$150k/kg re-entry capsule (which is passive after entry) "
                 "and less than the $300k/kg regolith-contact mining rig.  "
                 "Heritage: Apollo LM descent stage, and the CLPS landers "
                 "(Intuitive Machines Nova-C, Astrobotic Peregrine, Blue "
                 "Moon MK1).  A Mars lander carries the TPS row on top, "
                 "because it has to survive entry as well as land.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Depot berthing & handover operations",
        "unit":             "USD per delivery",
        "value":            2_000_000,
        "range_low":          500_000,
        "range_high":       8_000_000,
        "notes": "v1.4.0.  In-space counterpart to 'Sample recovery operations'. "
                 "Rendezvous-and-proximity-operations support, depot crew or "
                 "robotic-arm time, cargo survey and handover.  Far cheaper than "
                 "an Earth recovery campaign: no search aircraft, no ships, no "
                 "range clearance, no clean-room convoy.  Scaled from ISS "
                 "visiting-vehicle berthing ops rather than the $15M OSIRIS-REx "
                 "UTTR recovery.  ESTIMATE — no commercial depot exists yet.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Heat shield / TPS for Earth return",
        "unit":             "USD per kg of TPS mass",
        "value":             50_000,
        "range_low":         20_000,
        "range_high":       150_000,
        "notes": "Flight-rated PICA-X / AVCOAT-class TPS material + manufacturing. "
                 "Required for the aerocapture-return Δv segment.  NOTE: NASA / "
                 "SpaceX have not published a per-kg PICA-X cost; figure is an "
                 "engineering estimate.  Stardust / OSIRIS-REx capsule heritage "
                 "(see NTRS 20140005558 for material data).",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Propellant tank recurring cost",
        "unit":             "USD per kg of tank dry mass",
        "value":              6_000,
        "range_low":          3_000,
        "range_high":        25_000,
        "notes": "v1.10.0.  Module 3 has derived tank MASS per propellant since "
                 "v1.9.0 (tank_kg_per_L) and Module 4 has flown it through the "
                 "rocket equation since then — but nothing ever priced it, so "
                 "the tank paid its launch $/kg and cost nothing to build.  That "
                 "is the same mass-without-a-price asymmetry as the free "
                 "electric-propulsion stage, just smaller.\n"
                 "Derived from Centaur III, the closest flight article: ~1,880 kg "
                 "of stage structure, ~$30M for the stage against ~$20M for the "
                 "RL10 it carries, so ~$10M of structure ≈ $5,300/kg.  Rounded "
                 "up to $6,000 and quoted as a LOWER BOUND, consistent with the "
                 "rest of this table: Centaur is a mature production article and "
                 "a deep-space tank holding propellant for four years needs "
                 "insulation Centaur does not carry.  The upper end of the range "
                 "is where a one-off, long-duration cryogenic tank plausibly "
                 "lands.\n"
                 "It is deliberately the CHEAPEST hardware rate here — below the "
                 "$60k/kg passive berthing adapter — because a tank is the "
                 "simplest article in the mission: no mechanisms, no docking "
                 "interface, no re-entry.  Do not read its small effect as a "
                 "reason to drop it; the point of the line is that every "
                 "kilogram in the mass cascade has one.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Mission operations",
        "unit":             "USD per mission-year",
        "value":             31_400_000,        # OSIRIS-REx $283M / 9 yr
        "range_low":         15_000_000,
        "range_high":       100_000_000,
        "notes": "Anchor: OSIRIS-REx prime ops = $283M over 9 yr = $31.4M/yr "
                 "(NASA / Planetary Society).  Ground team + mission control + planning. "
                 "Range covers SmallSat ($15M) → flagship ($100M+).",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Deep Space Network time",
        "unit":             "USD per DSN hour (34-m dish)",
        "value":            1_530,              # FY09 $1057 × 1.45 CPI
        "range_low":        1_000,
        "range_high":       4_000,
        "notes": "DSN aperture fee for 34-m antenna.  NASA Mission Operations "
                 "and Communications Services (MOCS) cited $1057/hr in FY09; "
                 "CPI-adjusted to 2026 ≈ $1530/hr.  70-m apertures ~$4k/hr. "
                 "Authoritative current rates: dse.jpl.nasa.gov/ext/ calculator.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "FAA Part 450 licensing compliance",
        "unit":             "USD per program",
        "value":            2_500_000,
        "range_low":        1_000_000,
        "range_high":       5_000_000,
        "notes": "FAA does not charge an application fee; cost is internal "
                 "engineering + legal + safety-case work for 14 CFR Part 450 "
                 "compliance (FAA.gov / Congress.gov R48582).  First-of-kind "
                 "re-entry missions (asteroid sample return) trend upper-end. "
                 "v1.4.0: this row is the LAUNCH + RE-ENTRY figure; a mission "
                 "delivering to an in-space depot never re-enters and carries "
                 "the launch-only row below instead.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "FAA Part 450 licensing (launch only)",
        "unit":             "USD per program",
        "value":            1_200_000,
        "range_low":          600_000,
        "range_high":       2_500_000,
        "notes": "v1.4.0.  Part 450 covers launch AND re-entry as separately "
                 "licensed activities (14 CFR 450.1).  A mission that delivers "
                 "to LEO or a cislunar depot performs no re-entry, so it drops "
                 "the re-entry safety case, the debris-casualty-expectation "
                 "analysis for the landing footprint, and the range/airspace "
                 "coordination that dominate the first-of-kind sample-return "
                 "figure.  Roughly half the combined licence, which is where "
                 "routine launch-only Part 450 compliance sits.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Third-party liability insurance",
        "unit":             "USD per launch",
        "value":            1_500_000,
        "range_low":          500_000,
        "range_high":       3_000_000,
        "notes": "FAA-mandated Maximum Probable Loss coverage — statute caps at "
                 "$500M third-party / $100M US-government per 14 CFR Part 450. "
                 "Premium covers ground/air harm; distinct from payload insurance.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Launch insurance",
        "unit":             "percent of launch+payload value",
        "value":           10.0,                # 2024 market post-Intelsat 33e loss
        "range_low":        5.0,
        "range_high":      15.0,
        "notes": "Market rate per Plane Talking (Gallagher) Q1 2024 — premiums "
                 "rose from ~6% (early 2023) to ~10% post-Intelsat 33e loss. "
                 "First-of-kind vehicles at upper end.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Communications relay & data downlink",
        "unit":             "USD per Mbit returned",
        "value":            50,
        "range_low":        10,
        "range_high":       200,
        "notes": "Ka-band; relevant only for high-rate science / 3-D maps.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Power system (solar + battery)",
        "unit":             "USD per Watt-end-of-life",
        "value":            800,
        "range_low":        500,
        "range_high":     1_500,
        "notes": "Burdened recurring cost for a deep-space PV+battery train.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Power system specific mass",
        "unit":             "Watts per kg of power system, at 1 AU",
        "value":            60,
        "range_low":        30,
        "range_high":      150,
        "notes": "v1.4.0.  SYSTEM-level, not array-level: photovoltaic wing + "
                 "PMAD + battery + deployment structure.  ROSA / iROSA "
                 "roll-out arrays demonstrate ~150 W/kg at the wing (NASA "
                 "ROSA flight demo, ISS iROSA 2021+), but batteries, "
                 "regulation and structure roughly halve that at the system "
                 "level.  60 W/kg is "
                 "mid-range for a deep-space PV train.  Scales as 1/r^2 with "
                 "heliocentric distance — Module 4 applies that per asteroid, "
                 "which is why main-belt targets are punished so hard once "
                 "processing power is modelled.\n"
                 "v1.11.0: this row USED to claim it also covered 'power "
                 "through eclipse and through the night side of a rotating "
                 "body', and that claim has been removed because it was not "
                 "true and could not be.  A specific mass cannot express a "
                 "sizing factor, and the storage duration it implies is a LEO "
                 "eclipse, not an asteroid night — see 'Power-system row "
                 "baseline dark period', which names what this figure really "
                 "carries so Module 4 can charge the increment above it.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Electric thruster + PPU specific mass",
        "unit":             "kg per kW of input electrical power",
        "value":            8,
        "range_low":        5,
        "range_high":       15,
        "notes": "v1.6.0.  Thruster, power-processing unit, gimbals, xenon/argon "
                 "feed system, tankage and thermal — NOT the solar array, which "
                 "is carried separately by the 'Power system specific mass' row "
                 "and scales 1/r^2.  NASA NEXT-C: 7 kW thruster ~13.5 kg + PPU "
                 "~34 kg ≈ 7 kg/kW.  Gateway AEPS: 12.5 kW Hall, similar class. "
                 "8 kg/kW allows for feed system and structure.\n"
                 "⚠️  SUPERSEDED for Module 4 v1.12.0 and retained as the "
                 "fallback for a stale catalog.  Lumping thruster and PPU into "
                 "one per-kW figure is what let a micronewton device be sized "
                 "as a cargo tug: buy the kilowatts and you got the thrust.  "
                 "They scale on different quantities — a PPU is a power "
                 "converter (kg/kW, the row below) and a thruster head makes "
                 "momentum (kg/N, per technology, in _THRUSTER_SYSTEMS).",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Power processing unit specific mass",
        "unit":             "kg per kW of input electrical power",
        "value":            4.7,
        "range_low":        3.0,
        "range_high":       8.0,
        "notes": "v1.10.0.  The PPU alone, split out of the combined row above. "
                 "NASA NEXT-C: 34.5 kg of PPU at 7.4 kW = 4.66 kg/kW.  A PPU "
                 "converts bus power to the discharge and does not care what it "
                 "is feeding, so it is the half of the old 8 kg/kW that really "
                 "does scale with POWER.  The other half — the thruster head — "
                 "scales with THRUST and is per-technology, because that is "
                 "exactly where a pulsed plasma thruster and a gridded ion "
                 "engine stop being interchangeable.  Together they reproduce "
                 "NEXT-C: 4.7 x 7.4 + 54 x 0.236 = 47.5 kg against 47.2 kg "
                 "measured (12.7 kg thruster + 34.5 kg PPU).",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Electric propulsion system recurring cost",
        "unit":             "USD per kW of input electrical power (thruster + PPU)",
        "value":            1_500_000,
        "range_low":          500_000,
        "range_high":       3_000_000,
        "notes": "v1.8.2.  Recurring cost of the electric PROPULSION train — "
                 "thruster, power-processing unit, gimbals, feed system, "
                 "thermal.  NOT the solar array, which is priced separately "
                 "off the 'Power system (solar + battery)' row at $/W and is "
                 "far cheaper per kilogram.\n"
                 "Anchor: a NASA NEXT-C flight string is a 7 kW gridded-ion "
                 "thruster plus PPU at roughly 47 kg, procured in the "
                 "$10-15M-per-string class as a flight article — call it "
                 "$1.5-2M/kW.  High-power Hall systems buy down from there: "
                 "Psyche's SPT-140 strings and Gateway's 12.5 kW AEPS are "
                 "cheaper per kilowatt than NEXT-C, which is why the range "
                 "runs down to $500k/kW and why the figure should be expected "
                 "to fall if multi-hundred-kW deep-space EP is ever built.\n"
                 "SOFT: no multi-hundred-kW deep-space electric stage has "
                 "flown, and this pipeline sizes some missions at 300 kW — "
                 "six times the largest article yet built.  Extrapolating a "
                 "per-kW price that far is a judgement, not a quote.  It is "
                 "here because the alternative was worse: before v1.8.2 the "
                 "electric stage entered the rocket equation as mass and "
                 "appeared in NO cost line at all, so a 14-tonne, 309 kW "
                 "propulsion system was free and electric propulsion won on "
                 "hardware nobody had to buy.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Electric propulsion efficiency",
        "unit":             "fraction of input power converted to jet power",
        "value":            0.60,
        "range_low":        0.45,
        "range_high":       0.72,
        "notes": "v1.6.0.  Total efficiency (anode × mass-utilisation × PPU). "
                 "Hall thrusters run 0.50-0.60; gridded ion (NEXT) reaches "
                 "0.65-0.70 at high specific impulse.  Sets thrust for a given "
                 "power: T = 2·η·P / (Isp·g0), which is what makes low-thrust "
                 "trip time computable at all.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Water liberation energy (bound water)",
        "unit":             "Watt-hours per kg of water extracted",
        "value":            2_500,
        "range_low":        1_000,
        "range_high":       5_000,
        "notes": "v1.6.0.  C/B/D-type 'ice' is not ice — it is water bound into "
                 "phyllosilicates, and getting it out means heating the rock "
                 "past dehydroxylation, not melting a cube.  Arithmetic for a "
                 "10 wt% hydrated body, per kg of WATER recovered: heat 10 kg "
                 "of rock from ~200 K to ~700 K at c_p ≈ 800 J/kg·K = 4.0 MJ; "
                 "dehydroxylation enthalpy of serpentine ≈ 250 kJ/kg of rock "
                 "= 2.5 MJ; vaporise and capture 1 kg of water = 2.26 MJ. "
                 "Total ≈ 8.8 MJ/kg = 2,440 Wh/kg.  Matches the 1-3 kWh/kg "
                 "range in the asteroid-ISRU literature (Colorado School of "
                 "Mines / NASA ISRU studies).  Charged ON TOP of the generic "
                 "beneficiation row, which covers mechanical separation only.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "RTG (radioisotope power)",
        "unit":             "USD per Watt-electric",
        "value":            500_000,
        "range_low":        200_000,
        "range_high":     1_000_000,
        "notes": "Pu-238 supply-constrained (NASA / DOE target 1.5 kg/yr production "
                 "by 2026).  Historical Russian Pu-238 ~$2.5M/kg; with 6-8% RTG "
                 "conversion efficiency a 50-W RTG costs ~$1M just in fuel "
                 "(Space.com / NASA NIAC).  Only used past ~3 AU when PV starves.\n"
                 "v1.9.0: this row existed from v1.2.0 and NOTHING READ IT.  A "
                 "3.5 AU target flew a photovoltaic array starved by 1/r² with "
                 "no nuclear alternative anywhere in the model, which is the "
                 "reason main-belt bodies were punished as hard as they were. "
                 "Module 4 now picks whichever of PV and RTG is lighter for the "
                 "target's heliocentric distance and pays the corresponding "
                 "rate — this one, or the $800/W solar row.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "RTG specific power",
        "unit":             "Watts-electric per kg of RTG",
        "value":            5.0,
        "range_low":        2.4,
        "range_high":       5.5,
        "notes": "v1.9.0.  The nuclear counterpart to 'Power system specific "
                 "mass', and the reason it is a separate row: this one does NOT "
                 "scale with heliocentric distance.\n"
                 "GPHS-RTG (Cassini, New Horizons, Galileo): 290 We at 56 kg = "
                 "5.2 W/kg.  MMRTG (Curiosity, Perseverance): 110 We at 45 kg = "
                 "2.4 W/kg, worse because it is qualified to run in an "
                 "atmosphere as well as vacuum.  5.0 W/kg takes the "
                 "deep-space-only design.\n"
                 "The crossover against the 60 W/kg-at-1-AU solar row is at "
                 "sqrt(60/5) = 3.46 AU: inside that, PV is lighter per watt; "
                 "outside it, nothing beats a radioisotope.  RTGs cost ~625× "
                 "more per watt ($500k vs $800), so the model buys the smallest "
                 "one that does the job, which is exactly how real outer-planet "
                 "missions are sized.  Supply is the real constraint and it is "
                 "NOT priced here: DOE Pu-238 production runs ~1.5 kg/yr, "
                 "enough for roughly one flagship RTG a year for the entire "
                 "world, so any programme flying more than a couple of these "
                 "does not have a cost problem, it has an allocation problem.",
        "reference_year":   _REF_YEAR_OPS,
    },
    # ── Eclipse and night-side operation  (v1.11.0) ──────────────────────────
    # Three rows that together let Module 4 stop assuming the sun never sets on
    # the processing plant.  They were derivable from STORAGE_REFERENCE before
    # this release and unreachable, because Module 4 loads operational_costs.csv
    # and does not load storage_systems.csv, which is exactly why the "⚠️  Not
    # modelled" note on the storage row survived a release that was looking for
    # unread columns.
    {
        "category":         "Eclipse / night-side dark fraction",
        "unit":             "fraction of the time a surface rig sees no sun",
        "value":            0.50,
        "range_low":        0.35,
        "range_high":       0.55,
        "notes": "v1.11.0.  A rig anchored to a rotating body stands on a "
                 "surface that is lit half the time, by geometry — the same "
                 "0.50 STORAGE_REFERENCE has carried since v1.9.0, moved here "
                 "so Module 4 can actually read it.  Ranges below 0.5 for a "
                 "high-latitude or near-polar emplacement on a body with "
                 "obliquity, above it for an equatorial site with local "
                 "horizon shadowing.\n"
                 "This is a SIZING factor, not a specific mass, and that is why "
                 "no W/kg figure can absorb it: to deliver P continuously "
                 "through a dark fraction f you must INSTALL "
                 "P·[(1−f) + f/η_rt]/(1−f) of generating capacity, because the "
                 "sunlit hours have to run the load and recharge the store as "
                 "well.  At f = 0.50 and η_rt = 0.90 that is 2.11×.\n"
                 "The alternative architecture is to mine at half duty cycle "
                 "and take twice the stay time instead; Module 4 sizes the "
                 "storage rather than halving the duty, which is the choice "
                 "that leaves mission duration comparable across bodies.\n"
                 "Does NOT apply to a radioisotope source — an RTG's output is "
                 "flat — and does not apply to the electric-propulsion array, "
                 "which is in interplanetary cruise and in permanent sunlight.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Energy storage usable specific energy",
        "unit":             "usable Watt-hours per kg of storage system",
        "value":            104,
        "range_low":         70,
        "range_high":       160,
        "notes": "v1.11.0.  130 Wh/kg at the system level (STORAGE_REFERENCE "
                 "'Li-ion battery (system level)': cells reach 250-300 Wh/kg "
                 "and packaging, harness, balancing and thermal roughly halve "
                 "it) × 0.80 depth of discharge = 104 Wh/kg USABLE.  DoD is "
                 "folded in here rather than carried as a fourth row because "
                 "a consumer that forgets to apply it silently oversizes the "
                 "mission by 25%, and this table's job is to hand Module 4 the "
                 "number it should divide by.\n"
                 "A regenerative fuel cell (400 Wh/kg, TRL 5) is the obvious "
                 "architecture for a multi-hour dark period and would cut this "
                 "term by ~4×; it is not taken, because nothing has flown one "
                 "and this row is the operational choice.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Energy storage round-trip efficiency",
        "unit":             "fraction of stored energy recovered",
        "value":            0.90,
        "range_low":        0.80,
        "range_high":       0.95,
        "notes": "v1.11.0.  Charge and discharge losses through the cells and "
                 "the regulator.  Li-ion cells alone run 0.92-0.96 round trip; "
                 "0.90 takes the loss through PMAD as well.  This is the term "
                 "that makes the array oversize worse than the naive 1/(1−f): "
                 "the energy that goes through the store has to be generated "
                 "twice over, once for the load and once for the loss.  At "
                 "f = 0.50 it is the difference between 2.00× and 2.11×.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Power-system row baseline dark period",
        "unit":             "hours of darkness already covered by the 60 W/kg row",
        "value":            0.58,
        "range_low":        0.0,
        "range_high":       1.2,
        "notes": "v1.11.0.  The deduction that stops Module 4 double-charging "
                 "the battery.  'Power system specific mass' is 60 W/kg "
                 "SYSTEM-level against ROSA's ~150 W/kg at the wing, and part "
                 "of that 2.5× is a battery — so some storage is already paid "
                 "for and only the INCREMENT above it is new.\n"
                 "0.58 h is the standard LEO eclipse (35 min of a ~92 min "
                 "orbit), which is the storage duration a conventional "
                 "deep-space PV train is specified against.  Arithmetic: 0.58 h "
                 "of 1 W at 104 Wh/kg usable is 0.0056 kg/W, against the row's "
                 "own 1/60 = 0.0167 kg/W of total plant — a third of it, which "
                 "is why deducting it matters rather than being a nicety.\n"
                 "⚠️  The 'Power system specific mass' row's own notes claim it "
                 "covers 'power through eclipse and through the night side of a "
                 "rotating body'.  It cannot cover both: an asteroid with a "
                 "10 h rotation is dark for 5 h, roughly 9× the LEO figure, and "
                 "no single specific mass can be right for both duty cycles. "
                 "That contradiction is the argon failure in a new place — a "
                 "reference row asserting two incompatible states at once — and "
                 "this row resolves it by naming which of the two the 60 W/kg "
                 "figure actually is.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Volatile cargo containment",
        "unit":             "kg of containment per kg of volatile cargo",
        "value":            0.05,
        "range_low":        0.03,
        "range_high":       0.12,
        "notes": "v1.11.0.  Water sold at a depot has to still be water when it "
                 "arrives.  Exposed ice in sunlight at 1 AU sits far above its "
                 "sublimation threshold and is simply gone over a multi-year "
                 "cruise; shaded, sealed and blanketed it is stable for "
                 "decades.  So the charge is a sealed shaded hold — no power, "
                 "no cryocooler, but real mass.\n"
                 "Carried in STORAGE_REFERENCE since v1.9.0 with '⚠️  NOT "
                 "modelled in Module 4' on it, and duplicated here because that "
                 "table is not one Module 4 loads.  It is INCREMENTAL to the "
                 "0.15 ore-restraint fraction Module 4 already flies as "
                 "`return_structure_frac_of_payload`: the hopper holds the "
                 "cargo, the seal and shade keep the volatile fraction of it "
                 "from leaving.  That reading is what makes the storage row's "
                 "own 'heavier than an ore hopper' true at a value below 0.15.\n"
                 "Charged on WATER only, which is what the citation covers. "
                 "Carbon and organics are refractory at these temperatures and "
                 "ride in the hopper like rock.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Drilling / excavation energy",
        "unit":             "Watt-hours per kg of regolith extracted",
        "value":            200,
        "range_low":         50,
        "range_high":       500,
        "notes": "Range derived from Zacny et al. (NIAC studies on asteroid / "
                 "lunar regolith excavation) — loose regolith ≲50 Wh/kg, "
                 "consolidated rock ≳500 Wh/kg.  Pairs with the power-system "
                 "row to size mining rig (kg-extracted per installed-kW-hr).",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Beneficiation / on-site processing energy",
        "unit":             "Watt-hours per kg of refined product",
        "value":            500,
        "range_low":        100,
        "range_high":     2_000,
        "notes": "Magnetic / electrostatic / thermal concentration to ~50% purity. "
                 "Lunar / asteroid ISRU literature (NASA Money-Mass-ematics 2023). "
                 "Trades in-flight energy for a much smaller return-mass × prop bill.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Autonomous mining control & AI (NRE)",
        "unit":             "USD per program",
        "value":            200_000_000,
        "range_low":         50_000_000,
        "range_high":       500_000_000,
        "notes": "Pipeline assumes fully UNCREWED autonomous mining — no life "
                 "support, no crew habitat.  This line item captures the "
                 "one-time NRE for autonomous regolith-assessment vision, "
                 "sample-collection control logic, station-keeping autonomy, "
                 "and remote-fault-recovery software.  Anchor: Mars 2020 / "
                 "Perseverance autonomy stack ≈ $150M of $2.4B program; "
                 "asteroid mining trends upper end of range due to longer "
                 "Earth-spacecraft light-time (decisions must be local) and "
                 "novel regolith-contact mechanics.  Treated as in addition "
                 "to the bus 'Spacecraft development (NRE)' line above.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Sample recovery operations",
        "unit":             "USD per recovery",
        "value":             15_000_000,
        "range_low":          5_000_000,
        "range_high":        30_000_000,
        "notes": "Search-and-recovery teams, helicopters / ships, clean-room transport, "
                 "range coverage.  Modelled on OSIRIS-REx UTTR landing (Sept 2023). "
                 "NOTE: NASA has not published a standalone recovery-ops figure; "
                 "$15M is an order-of-magnitude estimate from the broader $283M / 9 yr "
                 "operations envelope — refine with project-specific data when available.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Launch vehicle reliability",
        "unit":             "probability of a successful launch",
        "value":            0.97,
        "range_low":        0.90,
        "range_high":       0.99,
        "notes": "v1.7.0.  Falcon 9 has flown >99% success over 300+ flights; "
                 "a first-flight or low-cadence vehicle sits near 0.90.  0.97 "
                 "is a fleet-representative figure for an operational booster "
                 "on a high-value payload.  Distinct from launch insurance, "
                 "which replaces the HARDWARE on failure — it does not "
                 "replace the revenue the mission would have earned.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Spacecraft mean time between failures",
        "unit":             "years of deep-space operation",
        "value":            30,
        "range_low":        15,
        "range_high":       60,
        "notes": "v1.7.0.  Exponential survival: P = exp(-T/MTBF).  Anchors "
                 "span the record — Voyager 1/2 past 45 years, New Horizons "
                 "19+, Dawn 11 (ended on hydrazine exhaustion, not failure), "
                 "against Akatsuki's orbit-insertion loss and Hayabusa's "
                 "near-total systems failure at 4 years.  30 years puts a "
                 "5-year mission at 85% survival, which matches the broad "
                 "deep-space record.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Mining system first-of-kind success probability",
        "unit":             "probability the rig works as designed",
        "value":            0.85,
        "range_low":        0.70,
        "range_high":       0.95,
        "notes": "v1.8.1.  Probability the excavation and beneficiation chain "
                 "works once it arrives — separate from the spacecraft "
                 "surviving the trip.  Counted from the actual flight record "
                 "of regolith-contact mechanisms rather than from the "
                 "failures alone, which is what v1.7.0's 0.75 did and it was "
                 "unfairly harsh:\n"
                 "  SUCCEEDED (10): Apollo 15-17 drills and scoops; Luna 16 / "
                 "20 / 24 drills; Stardust aerogel; Phoenix arm (sticky soil "
                 "delayed delivery but it worked); Curiosity drill (feed "
                 "mechanism failed 2016, recovered by feed-extended drilling); "
                 "Hayabusa2 sampler and SCI impactor, both touchdowns clean; "
                 "OSIRIS-REx TAGSAM, 121.6 g against a 60 g requirement; "
                 "Perseverance coring drill; Chang'e 5 and 6 drill + scoop.\n"
                 "  PARTIAL (1): Hayabusa — the projectile never fired, but "
                 "contact dust was still collected and returned.\n"
                 "  FAILED (2): Philae's harpoon pyrotechnics; InSight's HP3 "
                 "mole, which could not get purchase in Martian regolith.\n"
                 "That is 11/13 = 0.85 counting Hayabusa as the success it "
                 "ultimately was, or 10/13 = 0.77 counting it as a loss.  "
                 "0.85 is taken because Hayabusa did return its sample.\n"
                 "The honest caveat is that NONE of these is sustained "
                 "mining — they are one-shot or short-campaign collections of "
                 "grams to kilograms, not a rig moving 200 kg/day for years "
                 "with no maintenance.  0.85 is therefore the demonstrated "
                 "mechanism rate, and the sustained-operation risk on top of "
                 "it is carried by the spacecraft MTBF term rather than "
                 "double-counted here.  Grows with flight heritage — see "
                 "'Mining reliability growth exponent'.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Mining reliability growth exponent",
        "unit":             "Duane / AMSAA growth parameter (alpha)",
        "value":            0.30,
        "range_low":        0.10,
        "range_high":       0.60,
        "notes": "v1.9.0.  Reliability is not static across a programme — it "
                 "grows as failure modes are found and designed out.  The "
                 "Duane model has failure probability fall as n^(-alpha) with "
                 "cumulative production, and MIL-HDBK-189 puts alpha at "
                 "0.3-0.6 for an ACTIVE reliability-growth programme (one that "
                 "root-causes every anomaly and feeds fixes back) against "
                 "0.1-0.2 for passive fielding.  0.30 is the bottom of the "
                 "active band — appropriate for hardware that flies once every "
                 "few years, where each mission is a slow, expensive lesson "
                 "and there is no test fleet to accelerate the learning.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Mining system mature success probability",
        "unit":             "asymptotic ceiling on rig success probability",
        "value":            0.95,
        "range_low":        0.85,
        "range_high":       0.99,
        "notes": "v1.9.0.  Growth is asymptotic, not unbounded — no amount of "
                 "flight heritage makes a machine that grinds rock in vacuum "
                 "certain to work.  0.95 is where mature, high-cycle "
                 "spacecraft MECHANISMS sit: solar-array and antenna "
                 "deployments run ~97-99% across the fleet record, and a "
                 "continuously-operating excavator is harder than a one-shot "
                 "deployment.  Without this ceiling the Duane curve would "
                 "eventually promise certainty, which no mechanism earns.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Mining rig service life",
        "unit":             "years of operation before wear-out",
        "value":            15,
        "range_low":        5,
        "range_high":       30,
        "notes": "v1.7.0.  Caps how many missions one rig can actually serve, "
                 "which the old flat amortisation ignored — you cannot spread "
                 "a rig across 100 missions of 2 years each.  Bounded by "
                 "abrasive wear on regolith-contact mechanisms, thermal "
                 "cycling and radiation, not by propellant.  ISS-class "
                 "hardware is rated 15-30 years; a machine chewing rock is at "
                 "the low end.  Whatever life is left when the programme ends "
                 "is credited back as terminal value.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Mining rig maximum trips",
        "unit":             "mining campaigns before wear-out",
        "value":            5,
        "range_low":        2,
        "range_high":       12,
        "notes": "v1.12.0.  The SECOND half of rig service life, and the half "
                 "that was missing: 'Mining rig service life' above is a "
                 "CALENDAR bound, and calendar time is not what wears out a "
                 "machine that cuts rock.  Duty cycles are.  A rig sitting idle "
                 "between campaigns ages slowly; one digging continuously eats "
                 "cutting surfaces, seals and bearings on unweathered, angular, "
                 "never-water-rounded regolith.  Module 4 took min(years/stay) "
                 "alone, so at a short stay one rig served 12 consecutive "
                 "campaigns on the strength of a number that only ever said it "
                 "would not corrode meanwhile.  ⚠️  JUDGEMENT, and there is no "
                 "flight heritage for it — nothing has ever mined an asteroid "
                 "twice.  Bracketed from the two nearest analogues, which "
                 "disagree in the useful direction.  TERRESTRIAL: mobile mining "
                 "plant reaches major overhaul near 15,000-25,000 operating "
                 "hours (~2-3 yr of continuous duty, i.e. ~2 campaigns at this "
                 "model's ~1.25 yr stay) and survives 2-3 rebuilds before the "
                 "frame is retired — but every one of those rebuilds happens in "
                 "a workshop, and there is no workshop at an asteroid.  FLIGHT: "
                 "every regolith-contact mechanism ever flown was single-"
                 "campaign by design or failed inside one — TAGSAM fired once, "
                 "Philae's harpoons did not fire, InSight's mole never buried "
                 "itself, and Curiosity's drill lost its feed mechanism partway "
                 "through its first decade.  5 is therefore already the "
                 "optimistic reading of both: rebuild-interval life, achieved "
                 "un-rebuilt.  range_low 2 is one overhaul interval; "
                 "range_high 12 restores the pre-v1.12.0 behaviour, where the "
                 "calendar bound was the only bound.  Set Module 4's "
                 "`model_rig_trip_limit = False` for that exactly.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Rig salvage fraction",
        "unit":             "fraction of remaining book value recoverable",
        "value":            0.50,
        "range_low":        0.00,
        "range_high":       0.80,
        "notes": "v1.7.0.  A part-worn rig parked on a specific asteroid is "
                 "worth something to whoever goes there next and nothing to "
                 "anyone else — an illiquid, location-locked asset with a "
                 "market of approximately one buyer.  Half of remaining book "
                 "value is a deliberately unheroic haircut.  Set 0.0 to "
                 "model abandonment.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "In-space processing plant throughput",
        "unit":             "kg processed per year per kg of plant",
        "value":            100,
        "range_low":        20,
        "range_high":       500,
        "notes": "v1.7.0.  Sizes the refinery that turns raw asteroid feedstock "
                 "into something a depot can actually build with.  Terrestrial "
                 "smelters run 1,000x their own mass per year; 100x is a heavy "
                 "derating for microgravity, no convection, no gravity-fed "
                 "materials handling and full autonomy.  Combined with the "
                 "$300k/kg recurring hardware rate this sets the capital "
                 "charge per kg refined.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Cost of capital (WACC)",
        "unit":             "annualised fraction",
        "value":            0.10,
        "range_low":        0.075,             # Boeing 7.5% floor
        "range_high":       0.15,
        "notes": "Boeing 7.5% / Howmet 8.3% WACC (ValueInvesting.io 2026) as the "
                 "industrial floor; asteroid-mining ventures carry a startup risk "
                 "premium to ~10-15% (Damodaran NYU Stern industry tables).  "
                 "A 7-yr mission at 10% WACC ⇒ ~1.95× capital multiplier on Day-1 spend. "
                 "Module 4 should compound this across mission_duration_yr.",
        "reference_year":   _REF_YEAR_OPS,
    },
    {
        "category":         "Contingency reserve",
        "unit":             "percent of total mission cost",
        "value":            CONFIG.contingency_fraction * 100,
        "range_low":        15.0,
        "range_high":       50.0,
        "notes": "Industry-standard; first-of-kind missions carry the upper end.",
        "reference_year":   _REF_YEAR_OPS,
    },
]

say(f"OK  Operational costs reference loaded - "
      f"{len(OPERATIONAL_COSTS_REFERENCE)} categories")
