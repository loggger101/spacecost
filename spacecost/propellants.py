# -*- coding: utf-8 -*-
"""Propellant reference table: 41 systems, with storage class, tankage
derivation, thruster devices and the fuel/oxidiser blend helper.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

from typing import Dict, List

import numpy as np
import pandas as pd

from ._log import say
from .units import G0_M_S2

# ─────────────────────────────────────────────────────────────────────────────
# PROPELLANT REFERENCE TABLE
# ─────────────────────────────────────────────────────────────────────────────
# Each entry describes a propellant SYSTEM as actually used.  For bipropellants
# the listed values are the COMBINED mixture (oxidiser + fuel), weighted by
# the stage's typical oxidiser-to-fuel mass ratio.  This is what matters for
# the rocket equation, since the rocket spits out the combined mass.
#
# Vacuum Isp (s) is the interplanetary-relevant value; sea-level Isp is
# lower and only matters for the first stage of a launch vehicle (already
# baked into LAUNCH_VEHICLES_REFERENCE's $/kg-to-orbit).
#
# Density (kg/L) is the bulk combined density of fuel + oxidiser at storage
# conditions, weighted by mass.  Used for tank-sizing in Module 4.
#
# Cost (USD/kg) is the COMBINED cost of mixed propellant.  Live commodity
# prices (kerosene via heating oil, methane via natural gas) fill these
# from yfinance where applicable; the rest are OTC specialty-gas quotes.

# ─── LOW-THRUST Δv PENALTY  (v1.3.0) ─────────────────────────────────────────
# The rocket equation is indifferent to thrust, but trajectories are not.  A
# high-Isp electric stage cannot perform the impulsive burns the reference Δv
# table assumes: with milli-newton thrust it spirals, and a spiral is strictly
# more expensive in Δv than the equivalent impulsive manoeuvre.
#
#   • Escaping from LEO impulsively costs ~3.2 km/s.  Spiralling out costs
#     ~7 km/s, essentially the whole LEO orbital velocity, because thrust
#     is applied against a continuously rotating velocity vector.
#   • Interplanetary low-thrust transfers land in the same territory, running
#     ~1.3-2× the impulsive Δv depending on thrust-to-mass.
#
# `dv_penalty_factor` multiplies the mission Δv when Module 4 evaluates that
# propellant.  Without it, electric propulsion wins the payload cascade on an
# impulsive Δv budget it cannot actually fly.  1.5 is a mid-range figure; it
# does not capture the OTHER low-thrust cost, which is trip time, a spiral
# adds months to years that this pipeline's duration model does not yet see.
_LOW_THRUST_DV_PENALTY = 1.5

_REF_YEAR_PROP = 2026

# ─── STORAGE CLASS AND TANKAGE MASS  (v1.9.0) ────────────────────────────────
# Until v1.9.0 this table computed `density_kg_per_L`, exported it, and nothing
# ever used it.  That is not a cosmetic gap: the mass a tank adds scales with
# the VOLUME it encloses, not with the propellant mass inside it, so leaving it
# out hands the low-density propellants a free ride.  LH2 is 0.0708 kg/L
# against kerolox at 1.015, fourteen times the tank per kilogram burnt, and
# the model was awarding hydrolox its 452 s with no volumetric penalty at all.
# It is the same failure shape as the v1.10.0 electric stage: a mass in the
# rocket equation with no line anywhere else.
#
# `storage_class` is the taxonomy, and it is what decides how a kilogram is
# actually held:
#
#   deep_cryogen      LH2 at 20 K.  Thick MLI, vapour-cooled shields, the
#                     worst boil-off of anything that flies.
#   mild_cryogen      LOX 90 K / LCH4 112 K / LAr 87 K.  One thermal system
#                     serves oxidiser and fuel, the methalox argument.
#   storable_liquid   Hypergols, hydrazine, HTP, ionic liquids.  Room
#                     temperature, indefinitely.
#   benign_liquid     Water.  Storable, non-toxic, freezes rather than boils,
#                     and the only class this pipeline can MAKE on site.
#   supercritical_gas Xe / Kr / GN2 in a COPV.  Tank mass is set by storage
#                     pressure, not by insulation.
#   sublimating_solid Iodine, PTFE, liquid-metal reservoirs.  Near-ambient
#                     pressure, so the tank is almost free; this is iodine's
#                     entire pitch.
#   solid_motor       APCP.  The "tank" is a loaded case that also takes
#                     chamber pressure and thrust.
#   propellantless    Sails and tethers.  No tank at all.
#
# ── Deriving kg of tank per litre ────────────────────────────────────────────
# A thin-walled sphere at internal pressure p has hoop stress σ = p·r/2t, so
# t = p·r/2σ and
#
#     m_tank = 4πr²·t·ρ_mat = 2πr³·p·ρ_mat/σ = 1.5 · p · V / (σ/ρ)_mat
#,
# exactly proportional to volume, independent of size.  For a low-pressure
# liquid tank the ullage pressure term alone underpredicts (bosses, baffles,
# PMDs, mounts and thrust structure are not pressure-driven), so the base
# figure is taken from flight articles rather than from the formula:
#
#     Shuttle ET          26,535 kg dry / 2,058,000 L  = 0.0129 kg/L
#     Falcon 9 stage 2    ~3,500 kg struct / 105,900 L = 0.033  kg/L
#     Centaur III         ~1,880 kg struct /  54,000 L = 0.035  kg/L
#
# 0.025 kg/L sits between the ET (which is a big dumb tank, so cheap per litre)
# and the two upper stages (which carry avionics and thrust structure in the
# figures above).  Class multipliers are then anchored one article each; see
# _STORAGE_CLASS_TANK_MULT.
#
# ⚠️  SOFT, and it errs the safe way.  Real tank mass is the pressure term
# (∝ V, exact) plus insulation and minimum-gauge terms (∝ area, so ∝ V^⅔).
# Collapsing both into ∝ V therefore OVERSTATES the penalty on a very large
# tank and understates it on a very small one.  NASA's large NTP studies get
# an LH2 tank down near 12-15% of propellant mass at ~38 t of hydrogen; this
# model gives ~53% because its stages hold tonnes, not tens of tonnes.  The
# direction is deliberate: the propellants that most want a generous tank
# model are the speculative ones, and this pipeline does not exist to
# manufacture viability for them.
_TANK_BASE_KG_PER_L = 0.025

# Burst performance factor PV/W for a flight-qualified composite-overwrapped
# pressure vessel, ~40 km (× g0 = 392 kJ/kg).  Standard COPV figure of merit;
# NASA-STD-(I)-5019 class hardware.  Burst is taken at 1.5 × operating.
_COPV_PERFORMANCE_J_PER_KG = 392_000.0

# Passive boil-off for LIQUID argon, %/day.  Derived from the LOX rate already
# in this table rather than asserted, because the whole point of the v1.10.0
# argon split is that a cryogen has to pay what a cryogen costs.
#
# The kerolox row is 0.015%/day and its own comment says why: RP-1 is storable
# and only the LOX half boils, weighted by the mix ratio.  At O/F 2.30 the LOX
# mass fraction is 2.30/3.30 = 0.697, so LOX alone is 0.015/0.697 = 0.0215%/day.
#
# Scaling that to argon at the same tank and the same MLI, boil-off is heat leak
# over the energy it takes to boil the contents, so two ratios:
#
#   heat leak        ∝ ΔT     (300 − 87.3) / (300 − 90.2)      = 1.014
#   energy to boil   ∝ ρ·h_fg  (1.141 × 213.1) / (1.395 × 161.1) = 1.082
#
# giving 0.0215 × 1.014 × 1.082 = 0.0236, rounded to 0.024%/day.  Argon boils
# slightly FASTER than oxygen: 3 K colder, and its latent heat per litre is 8%
# lower.  Over a four-year hold that is a factor of 1.41 on the return
# propellant, small next to hydrolox's 2.1, and not nothing.
_LAR_BOILOFF_PCT_PER_DAY = 0.024

# ─────────────────────────────────────────────────────────────────────────────
# THRUSTER SYSTEMS  (v1.10.0), the DEVICE, as distinct from the propellant
# ─────────────────────────────────────────────────────────────────────────────
# PROPELLANTS_REFERENCE has always been half a propellant table and half a
# propulsion-system table, `isp_vac_s`, `restartable` and `dv_penalty_factor`
# are properties of the DEVICE, not of the chemical.  What it never carried was
# anything about whether the device can be built at the size this pipeline
# flies, and that omission ran one way:
#
#     Module 4 sized an electric stage by POWER alone.  Buy enough kilowatts
#     and any entry in the table became a cargo tug.
#
# So a full cislunar run had a third of its winning missions on PULSED PLASMA
# THRUSTERS and a quarter on ELECTROSPRAY; devices that have flown, and have
# flown producing MICRONEWTONS.  EO-1's PPT was 860 µN.  LISA Pathfinder's
# colloid thrusters were 5-30 µN each.  The pipeline was asking them for ~10 N.
#
# Note the asymmetry this closes, and it is the same one the user spotted:
# LAUNCH is modelled as an integrated vehicle with a payload it can actually
# lift, while IN-SPACE propulsion was modelled as a bare specific impulse.  One
# side had a capacity limit and the other did not.
#
# Two columns fix it, and neither is a threshold; the mass does the work, the
# same way propellant tankage disqualifies low-density propellants without
# anyone naming a cutoff:
#
#   thruster_kg_per_n   Thruster-head mass per newton of thrust.  Module 4
#                       derives the thrust its mission needs (T = ṁ·ve, which
#                       is just momentum flux and owes nothing to efficiency)
#                       and multiplies.  A device that makes µN per kilogram
#                       reports thousands of tonnes of thruster and dies in the
#                       rocket equation.  No cutoff, no judgement call.
#
#   thruster_efficiency Total thrust efficiency, replacing the single global
#                       0.60 that every electric row shared.  This one is
#                       nearly as decisive as the mass: a PPT converts about
#                       8% of its input into jet power against a gridded ion
#                       thruster's 70%, so it needs ~9x the array for the same
#                       thrust, and the array is mass too.
#
# `thrust_scaling` records WHY a device lands where it does, and it is the real
# physical divide:
#
#   continuous   Thrust comes from a plasma discharge or a beam whose area you
#                can enlarge.  Scaling up means building a BIGGER device, so
#                kg/N stays roughly flat with size and lands at 6-90 kg/N
#                across every mature technology here.
#   replicated   Thrust comes from discrete emitters, needles or pulses.
#                Scaling up means building MORE devices, so kg/N is fixed by
#                the single unit and never improves: 2,500-10,000 kg/N.
#                Accion's own literature puts a cargo-scale electrospray at
#                "millions of emitters"; that sentence was already in this
#                table's notes field and nothing read it.
#
# Every figure below is thruster HEAD mass over demonstrated thrust, from a
# flight or ground article.  The PPU is separate and scales with power; see
# the "Power processing unit specific mass" ops row, because a PPU is a power
# converter and does not care what it is feeding.
#
# ⚠️  The replicated figures are deliberately GENEROUS to the technology.
# Electrospray is entered at 10,000 kg/N when ST7-DRS heads work out nearer
# 20,000-100,000; the conclusion does not depend on which end you take, and
# taking the favourable end means nobody can claim the result was engineered.
#
# ⚠️  Iodine is the judgement call in this table, and it matters because iodine
# wins most of the catalog.  Its only FLIGHT unit is ThrustMe's 1.1 mN cubesat
# thruster, which works out near 1,100 kg/N, but that is a scale artifact of a
# 1U device, not a property of iodine.  Iodine runs in Hall and gridded
# thrusters whose bodies are the same hardware xenon uses; what it genuinely
# costs is a heated feed line and corrosion-tolerant materials.  So it is
# entered as Hall-class mass with a penalty (60 against xenon Hall's 30), and
# `status` cannot express that its cargo-scale heritage is ground-test only.
# If you want to be harsh with iodine, this is the number to move, but move it
# for a reason, and record the reason.
_THRUSTER_SYSTEMS = {
    # name fragment           kg/N     η     scaling        anchor
    "Xenon  (Hall / ion)":      (54.0, 0.70, "continuous"),  # NEXT-C 12.7 kg / 236 mN, 70% total
    "Krypton  (Hall)":          (35.0, 0.45, "continuous"),  # SPT-140 body, Kr ~85% of Xe thrust and ~10 pts less efficient
    "Argon  (Hall / ion)":      (40.0, 0.40, "continuous"),  # same body again; Ar lower still
    "Argon  (Hall / ion, cryogenic)": (40.0, 0.40, "continuous"),
    "Iodine  (Hall / gridded)": (60.0, 0.45, "continuous"),  # see the iodine caveat above
    "Water  (gridded ion / ECR)": (80.0, 0.35, "continuous"),  # ECR ion; water is hard to ionise cleanly
    "Water  (electrothermal / resistojet)": (10.0, 0.75, "continuous"),  # resistojet: high thrust density, low Isp
    "Hydrazine arcjet":         ( 6.0, 0.35, "continuous"),  # MR-509 1.5 kg / 258 mN
    "Mercury ion  (RETIRED)":   (54.0, 0.65, "continuous"),  # gridded-ion class
    "Nuclear electric  (NEP, xenon)": (54.0, 0.70, "continuous"),
    "VASIMR  (argon, variable Isp)":  (53.0, 0.50, "continuous"),  # VX-200 ~300 kg / 5.7 N
    "MPD  (lithium magnetoplasmadynamic)": (40.0, 0.40, "continuous"),
    # ── Concepts.  UNANCHORED, and they are here so the guard below cannot be
    # satisfied by silence.  Both are gated out of the default search by
    # `operational_propellants_only`; if you ever ungate them, these two
    # numbers are the ones to distrust first.  Direct fusion drive is pinned to
    # Princeton's PFRC-2 sketch (a few newtons from a ~10 t engine).  For
    # antimatter there is no engineering basis whatsoever, so it is given the
    # same figures rather than anything flattering; an unanchored row should
    # never be the reason something wins.
    "Direct fusion drive":      (2_000.0, 0.50, "continuous"),
    "Antimatter-catalysed":     (2_000.0, 0.50, "continuous"),
    # ── Replicated: thrust per EMITTER, so mass is linear in thrust forever ──
    "Electrospray  (ionic liquid)": (10_000.0, 0.65, "replicated"),  # TILE-3 ~100 µN/kg-class; generous end
    "FEEP  (indium field emission)": (2_500.0, 0.60, "replicated"),  # Enpulsion IFM Nano 0.35 mN / 0.9 kg
    "PPT  (PTFE pulsed plasma)":     (5_000.0, 0.08, "replicated"),  # EO-1 PPT 860 µN / 4.9 kg; PPT efficiency is 5-13%
}


def _apply_thruster_data(df: pd.DataFrame) -> None:
    """Attach device-level columns to the propellant frame, in place.

    Chemical and propellantless rows get NaN; they are not electric, Module 4
    never sizes a power plant for them, and a number there would imply a
    constraint that does not apply.  Any ELECTRIC row missing from
    `_THRUSTER_SYSTEMS` raises rather than defaulting: a silent default is how
    a micronewton thruster got flown as a cargo tug in the first place.

    "Electric" is tested as `dv_penalty_factor > 1`, which is the SAME test
    Module 4 uses to decide whether to size a power plant (`is_electric` in
    `_evaluate_combo_at_ratio`).  Keying off `type` instead would have let
    `nuclear_electric` through; it is electric propulsion, it draws the
    penalty, and it is not spelled "electric".
    """
    kg_per_n, eff, scaling = [], [], []
    for _, row in df.iterrows():
        name = str(row["name"])
        entry = _THRUSTER_SYSTEMS.get(name)
        if entry is None:
            if float(row.get("dv_penalty_factor", 1.0) or 1.0) > 1.0:
                raise KeyError(
                    f"electric propellant {name!r} has no _THRUSTER_SYSTEMS "
                    f"entry: add one with an anchor rather than letting "
                    f"Module 4 size it on power alone"
                )
            kg_per_n.append(float("nan"))
            eff.append(float("nan"))
            scaling.append(None)
            continue
        kg_per_n.append(entry[0])
        eff.append(entry[1])
        scaling.append(entry[2])
    df["thruster_kg_per_n"]   = kg_per_n
    df["thruster_efficiency"] = eff
    df["thrust_scaling"]      = scaling


_STORAGE_CLASS_TANK_MULT = {
    # class            × base   anchor
    "storable_liquid":   1.00,  # 0.025 kg/L → NTO at 1.45 kg/L is 1.7% of propellant mass
    "benign_liquid":     0.90,  # water; no cryo insulation, no toxicity handling
    "mild_cryogen":      1.15,  # LOX at 1.141 kg/L → 2.5%; MLI but no vapour-cooled shield
    "deep_cryogen":      1.50,  # LH2; hydrolox blend lands at 10.4% vs Centaur's ~9.7% measured
    "sublimating_solid": 0.45,  # iodine at 4.93 kg/L → 0.23%; a heated reservoir, not a tank
    "solid_motor":       5.00,  # APCP at 1.80 kg/L → 6.9%; Star 48B burnout/propellant is 6.4%
    "propellantless":    0.00,
}


def _tank_kg_per_L(storage_class: str, pressure_mpa: float = 0.3) -> float:
    """kg of tankage per litre of propellant stored, by storage class.

    `pressure_mpa` is read only for `supercritical_gas`, where the tank is a
    COPV and its mass is set by storage pressure rather than by insulation.
    Everything else takes a flight-anchored multiple of _TANK_BASE_KG_PER_L.
    """
    if storage_class == "supercritical_gas":
        # 1.5·p/(PV/W) is kg per CUBIC METRE (Pa / (J/kg) = kg/m³); this table
        # quotes tankage per LITRE, so divide by 1,000.
        return 1.5 * (float(pressure_mpa) * 1e6) / _COPV_PERFORMANCE_J_PER_KG / 1_000.0
    try:
        return _TANK_BASE_KG_PER_L * _STORAGE_CLASS_TANK_MULT[storage_class]
    except KeyError:
        raise KeyError(
            f"unknown storage_class {storage_class!r}: add it to "
            f"_STORAGE_CLASS_TANK_MULT with an anchor, do not default it"
        ) from None


# Helper: combined Isp / density / cost for a fuel + oxidiser pair, weighted
# by the stage mixture ratio (oxidiser-to-fuel by mass).
def _blend(of_ratio: float, fuel: dict, ox: dict) -> dict:
    """
    Blend fuel + oxidiser into a combined-propellant dict.
    of_ratio = mass(oxidiser) / mass(fuel) at stoichiometric / stage design.
    """
    fuel_frac = 1.0 / (1.0 + of_ratio)
    ox_frac   = of_ratio / (1.0 + of_ratio)
    # combined density (mass-weighted reciprocal, volumes add)
    rho = 1.0 / (fuel_frac / fuel["density_kg_per_L"]
                 + ox_frac  / ox["density_kg_per_L"])
    cost_kg = fuel_frac * fuel["cost_usd_per_kg"] + ox_frac * ox["cost_usd_per_kg"]
    # Combined tankage.  Fuel and oxidiser sit in SEPARATE tanks at different
    # temperatures, so the two contributions are summed over their own volumes
    # rather than averaged, which is the whole reason hydrolox is punished and
    # methalox is not: LOX and LCH4 share a thermal class, LOX and LH2 do not.
    v_fuel = fuel_frac / fuel["density_kg_per_L"]
    v_ox   = ox_frac   / ox["density_kg_per_L"]
    tank_per_kg = (
        v_fuel * _tank_kg_per_L(fuel["storage_class"], fuel.get("pressure_mpa", 0.3))
        + v_ox * _tank_kg_per_L(ox["storage_class"],   ox.get("pressure_mpa", 0.3))
    )
    return {
        "density_kg_per_L":   rho,
        "ref_cost_usd_per_kg": cost_kg,
        "fuel_mass_fraction":  fuel_frac,
        "ox_mass_fraction":    ox_frac,
        "tank_kg_per_L":       tank_per_kg * rho,
    }


# Reference component prices ($/kg); these are intermediate, used only to
# build the combined propellant rows below.  Values verified May 2026
# against the cited authoritative sources.
#
#   RP-1       Haltermann Solutions / SpaceInsider, typical $2-3/kg in bulk
#   LH2        NASA contract pricing 2024-25, ~$6/kg base + handling overhead
#   LCH4       Mobius Market Research 2024, ~$400/tonne open-market liquid
#   LOX        Astronautix / aqua-calc, bulk industrial cryogen ~$0.20/kg
#   N2O4       DOD Aerospace Standard Prices FY20 reference
#   MMH        DOD Aerospace Standard Prices FY20 reference
#   Hydrazine  DOD Standard Prices FY20 ($30.5/kg) to commercial AIAA ($75.8/kg)
#   Xenon      SETS Space / EFC 2024-99.999% purity ~$10,000/kg.
#              Density: NSTAR/Dawn supercritical storage ~2.0 g/cm³
#              (NBP liquid Xe = 3.057 g/cm³ is unreachable in flight tanks).
#   Argon      SETS Space 2024, bulk industrial ~$7-15/kg.
#              Density: NBP liquid 1.395 g/cm³ (high-pressure gas ~0.5 g/cm³).
#
# v1.9.0 added `storage_class` to every component (and `pressure_mpa` to the
# supercritical ones) so tankage mass can be derived rather than guessed, plus
# the components needed by the propellants the table had been missing:
#
#   UDMH       Wikipedia / Astronautix, Proton and Long March heritage.
#              ~$80/kg; Chinese and Russian production, no Western market.
#   Aerozine-50 50/50 UDMH-hydrazine by mass, Titan / Apollo SPS.
#   HTP-98     98% hydrogen peroxide.  Bulk ~$5/kg (Evonik / Peroxide Propulsion
#              propellant-grade quotes 2024).  Cheapest storable oxidiser there is.
#   GN2        Cold gas.  Nitrogen is nearly free; the COPV is the whole cost.
#              Stored at 30 MPa, ρ ≈ 0.25 kg/L.
#   Krypton    Bulk industrial ~$300/kg (air-separation by-product; roughly 30×
#              cheaper than Xe and about 10× more abundant in air).  Stored
#              supercritical at ~18 MPa, ρ ≈ 0.55 kg/L; much worse than Xe,
#              which is why the tank term matters here.
#   Iodine     ~$60/kg technical grade.  ρ 4.93 kg/L as a SOLID at ambient
#              pressure: the densest storable electric propellant known.
#   Water      Spaceflight-grade deionised, ~$2/kg delivered.  The only entry
#              in this table an asteroid can supply.
#   ASCENT     AF-M315E hydroxylammonium-nitrate monoprop.  ~$500/kg reflects
#              pilot-scale production, not chemistry; GPIM flew ~1 kg of it.
#   APCP       Ammonium-perchlorate composite, HTPB binder + Al.  ~$15/kg for
#              the grain; the case and nozzle dominate the article cost.
#   PTFE       Teflon bar stock for pulsed-plasma thrusters, ~$25/kg.
#   EMI-BF4    Ionic liquid for electrospray, ~$2,000/kg at research volume.
#   Indium     FEEP propellant, ~$250/kg; ρ 7.31 kg/L liquid.
#   Mercury    Historic ion propellant (SERT-II, ATS-6).  ~$60/kg, ρ 13.53, 
#              still the best storage density ever flown, and banned under the
#              2013 Minamata Convention.  Present so the record is complete.
#   Lithium    MPD-thruster propellant, ~$80/kg, heated liquid reservoir.
#   Ammonia    Arcjet / resistojet working fluid, ~$1.50/kg bulk.
#   LF2        Liquid fluorine, ~$20/kg.  Highest-performing practical oxidiser
#              and completely unflyable; see the Li/F2/H2 row.
#   Al-powder  Aluminium fuel for ALICE-class metal/water propellants, ~$3/kg.
#   CO         Carbon monoxide, liquid at 81 K.  Makeable from carbonaceous
#              regolith; pairs with LOX for a fully-ISRU chemical stage.
_COMPONENTS = {
    "RP-1":      {"density_kg_per_L": 0.810, "cost_usd_per_kg":      2.50, "storage_class": "storable_liquid"},
    "LH2":       {"density_kg_per_L": 0.0708,"cost_usd_per_kg":     10.00, "storage_class": "deep_cryogen"},   # base + handling
    "LCH4":      {"density_kg_per_L": 0.422, "cost_usd_per_kg":      0.40, "storage_class": "mild_cryogen"},   # ~$400/tonne open market
    "LOX":       {"density_kg_per_L": 1.141, "cost_usd_per_kg":      0.20, "storage_class": "mild_cryogen"},
    "N2O4":      {"density_kg_per_L": 1.450, "cost_usd_per_kg":     35.00, "storage_class": "storable_liquid"},
    "MMH":       {"density_kg_per_L": 0.870, "cost_usd_per_kg":    100.00, "storage_class": "storable_liquid"},
    "Hydrazine": {"density_kg_per_L": 1.010, "cost_usd_per_kg":     75.00, "storage_class": "storable_liquid"},  # DOD ref + handling
    "Xenon":     {"density_kg_per_L": 2.000, "cost_usd_per_kg": 10_000.00, "storage_class": "supercritical_gas", "pressure_mpa": 10.0},
    # v1.10.0.  Argon used to be ONE component carrying liquid-argon density
    # (1.395 kg/L, normal boiling point 87.3 K) with the storage class of a
    # cryogen and a boil-off of zero; the row's own two comments said "liquid
    # NBP (cryogenic storage)" and "stored supercritical at ambient
    # temperature" three lines apart.  You cannot have both: 1.395 kg/L only
    # exists at 87 K, and at 87 K it boils.  The combination handed argon the
    # lightest tank of any gas in the table AND exemption from the hold-time
    # penalty every other cryogen pays, which is a free resource rather than a
    # propellant.  Split into the two real articles instead, and let Module 4's
    # per-asteroid search decide which one a mission flies.
    #
    #   ArgonSC   what has actually flown.  Every noble-gas EP system ever
    #             launched: xenon on Dawn/BepiColombo/SMART-1, krypton on
    #             Starlink v1, argon on Starlink V2, stores its propellant
    #             supercritical in a COPV at ambient temperature.  Density is
    #             derived below, not asserted.
    #   ArgonLIQ  the large-stage architecture: liquid at 87.3 K under MLI,
    #             which is how you would really feed a multi-tonne NEP stage.
    #             Studied, never flown, so the propellant row built on it is
    #             tagged `development` and the default search excludes it.
    #
    # ArgonSC density: Peng-Robinson at 293.15 K / 18 MPa (the same bottle
    # pressure as the krypton row) gives Z = 0.919 and ρ = 0.321 kg/L; a
    # generalised-compressibility reading at Tr = 1.945, Pr = 3.70 gives
    # Z ≈ 0.99 and ρ = 0.298.  0.30 is the round figure between them.
    #
    # Note the result barely moves with pressure, and that is the physics
    # rather than a coincidence: COPV mass goes as 1.5·p/(PV/W) and stored
    # density goes as p·M/(ZRT), so the tank FRACTION is ~1.5·Z·R·T/(M·(PV/W)),
    # pressure cancels and molar mass is what is left.  Argon at 30 MPa pays
    # 22.3% against 22.9% at 18 MPa.  Xenon 1.9% / krypton 12.5% / argon 22.9%
    # is just M = 131.3 / 83.8 / 39.9 read backwards, and it is the whole
    # reason a cheap propellant is not automatically a good one.
    "ArgonSC":   {"density_kg_per_L": 0.300, "cost_usd_per_kg":     10.00, "storage_class": "supercritical_gas", "pressure_mpa": 18.0},
    "ArgonLIQ":  {"density_kg_per_L": 1.395, "cost_usd_per_kg":     10.00, "storage_class": "mild_cryogen"},     # liquid at NBP 87.3 K

    # ── v1.9.0 additions ─────────────────────────────────────────────────────
    "UDMH":      {"density_kg_per_L": 0.793, "cost_usd_per_kg":     80.00, "storage_class": "storable_liquid"},
    "Aerozine50":{"density_kg_per_L": 0.903, "cost_usd_per_kg":     90.00, "storage_class": "storable_liquid"},
    "HTP-98":    {"density_kg_per_L": 1.431, "cost_usd_per_kg":      5.00, "storage_class": "storable_liquid"},
    "GN2":       {"density_kg_per_L": 0.250, "cost_usd_per_kg":      1.00, "storage_class": "supercritical_gas", "pressure_mpa": 30.0},
    "Krypton":   {"density_kg_per_L": 0.550, "cost_usd_per_kg":    300.00, "storage_class": "supercritical_gas", "pressure_mpa": 18.0},
    "Iodine":    {"density_kg_per_L": 4.930, "cost_usd_per_kg":     60.00, "storage_class": "sublimating_solid"},
    "Water":     {"density_kg_per_L": 1.000, "cost_usd_per_kg":      2.00, "storage_class": "benign_liquid"},
    "ASCENT":    {"density_kg_per_L": 1.470, "cost_usd_per_kg":    500.00, "storage_class": "storable_liquid"},
    "APCP":      {"density_kg_per_L": 1.800, "cost_usd_per_kg":     15.00, "storage_class": "solid_motor"},
    "PTFE":      {"density_kg_per_L": 2.200, "cost_usd_per_kg":     25.00, "storage_class": "sublimating_solid"},
    "EMI-BF4":   {"density_kg_per_L": 1.240, "cost_usd_per_kg":  2_000.00, "storage_class": "storable_liquid"},
    "Indium":    {"density_kg_per_L": 7.310, "cost_usd_per_kg":    250.00, "storage_class": "sublimating_solid"},
    "Mercury":   {"density_kg_per_L":13.530, "cost_usd_per_kg":     60.00, "storage_class": "storable_liquid"},
    "Lithium":   {"density_kg_per_L": 0.534, "cost_usd_per_kg":     80.00, "storage_class": "storable_liquid"},
    "Ammonia":   {"density_kg_per_L": 0.682, "cost_usd_per_kg":      1.50, "storage_class": "storable_liquid"},
    "LF2":       {"density_kg_per_L": 1.505, "cost_usd_per_kg":     20.00, "storage_class": "mild_cryogen"},
    "Al-powder": {"density_kg_per_L": 2.700, "cost_usd_per_kg":      3.00, "storage_class": "solid_motor"},
    "CO":        {"density_kg_per_L": 0.789, "cost_usd_per_kg":      1.00, "storage_class": "mild_cryogen"},
}

_kerolox    = _blend(2.30, _COMPONENTS["RP-1"],      _COMPONENTS["LOX"])
_hydrolox   = _blend(6.00, _COMPONENTS["LH2"],       _COMPONENTS["LOX"])
_methalox   = _blend(3.60, _COMPONENTS["LCH4"],      _COMPONENTS["LOX"])
_mmh_nto    = _blend(1.65, _COMPONENTS["MMH"],       _COMPONENTS["N2O4"])
_udmh_nto   = _blend(2.60, _COMPONENTS["UDMH"],      _COMPONENTS["N2O4"])
_a50_nto    = _blend(2.00, _COMPONENTS["Aerozine50"],_COMPONENTS["N2O4"])
_htp_rp1    = _blend(7.00, _COMPONENTS["RP-1"],      _COMPONENTS["HTP-98"])
_co_lox     = _blend(0.57, _COMPONENTS["CO"],        _COMPONENTS["LOX"])
_al_water   = _blend(1.00, _COMPONENTS["Al-powder"], _COMPONENTS["Water"])
# Li/F2/H2 tripropellant: Rocketdyne's 1960s test-stand mixture.  Blended in
# two steps because _blend takes a pair, lithium against fluorine first, then
# the hydrogen folded in as the "fuel" against that pair as the "oxidiser".
# 2Li + F2 → 2LiF is stoichiometric at F2/Li = 2.73; the engine ran fuel-rich
# at roughly 2.0, with hydrogen at ~8% of total mass as a low-molecular-weight
# working fluid.  Approximate; the row is gated out and the exact split moves
# Isp by a few seconds, not by a category.
_li_f2      = _blend(2.00, _COMPONENTS["Lithium"],   _COMPONENTS["LF2"])
_lifh       = _blend(11.3, _COMPONENTS["LH2"],
                     {"density_kg_per_L": _li_f2["density_kg_per_L"],
                      "cost_usd_per_kg":  _li_f2["ref_cost_usd_per_kg"],
                      "storage_class":    "mild_cryogen"})

# ─── MATURITY GATE  (v1.9.0) ─────────────────────────────────────────────────
# `status` on a propellant means exactly what it means on a launch vehicle, and
# Module 4 filters on it the same way (`operational_propellants_only`):
#
#   operational   Has flown and moved a real spacecraft.  In the default search.
#   development   Hardware exists and has been fired, but not in flight.
#   concept       Designed on paper, or demonstrated only as physics.
#   retired       Flew, and will not fly again, kept so the record is complete
#                 and so nobody re-derives it as a bright idea.
#
# Two flags matter as much as the status, because they disqualify a propellant
# from THIS mission profile regardless of how mature it is:
#
#   restartable   A return mission fires its second burn years after launch.
#                 A solid motor cannot do that, so APCP is in the table and
#                 permanently out of the search.  Documented, not silent.
#   propellantless Sails and tethers have no mass ratio, so the rocket equation
#                 says a sail can move any payload for free.  It cannot; its
#                 characteristic acceleration is ~0.1 mm/s², which is fine for a
#                 6 kg cubesat and meaningless for a hold full of ore.  Flagged
#                 so Module 4 excludes them rather than reporting infinite
#                 payload.  Sizing a sail properly needs a thrust-limited
#                 trajectory model this pipeline does not have.
#
# `isru_feed_kg_per_kg` / `isru_feed_material` generalise what used to be a
# hardcoded hydrolox-only check.  A propellant an asteroid can supply is worth
# far more than its Isp suggests, and water is not the only route: a steam
# rocket burns the water directly at 1.0 kg feed per kg propellant against
# hydrolox's 1.286, and a mass driver throws raw regolith.

PROPELLANTS_REFERENCE: List[dict] = [
    # ═════════════════════════════════════════════════════════════════════════
    # OPERATIONAL, chemical
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                  "kerolox  (RP-1 / LOX)",
        "type":                  "bipropellant",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1957,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "mild_cryogen",
        "tank_kg_per_L":         _kerolox["tank_kg_per_L"],
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.015,   # RP-1 is storable; the LOX half boils.  Weighted by the 1:2.30 mix ratio.
        "isp_vac_s":             340,
        "exhaust_vel_m_per_s":   340 * G0_M_S2,
        "density_kg_per_L":      _kerolox["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _kerolox["ref_cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _kerolox["ref_cost_usd_per_kg"] * _kerolox["density_kg_per_L"],
        "yfinance_proxy":        "heating_oil",   # RP-1 ≈ refined kerosene
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Workhorse 1st-stage propellant (Falcon 9, Atlas V kerolox).  "
                 "Vac Isp 340 s per RocketCEA / Astronautix.  Combined cost "
                 "weighted at 1:2.30 RP-1:LOX mix ratio.",
    },
    {
        "name":                  "hydrolox  (LH2 / LOX)",
        "type":                  "bipropellant",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1961,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "deep_cryogen",
        "tank_kg_per_L":         _hydrolox["tank_kg_per_L"],
        # Stoichiometric water demand for an ISRU hydrolox stage: electrolysis
        # yields 8 kg O2 per kg H2, and a 6:1 O/F stage burns 9/(1+6) kg of
        # water per kg of propellant.  This is the number Module 4 used to
        # carry as a hardcoded constant for the only ISRU propellant it knew.
        "isru_feed_kg_per_kg":   9.0 / 7.0,
        "isru_feed_material":    "water",
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.05,   # The worst case by far.  LH2 boils at 20 K and has the lowest heat of vaporisation of any propellant; even with multi-layer insulation and an active cryocooler, long-duration storage runs 0.03-0.1%/day.  This is why no flown mission has ever performed a deep-space arrival burn on hydrolox after a multi-year cruise -- Centaur is rated for hours of loiter, not years.
        "isp_vac_s":             452,
        "exhaust_vel_m_per_s":   452 * G0_M_S2,
        "density_kg_per_L":      _hydrolox["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _hydrolox["ref_cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _hydrolox["ref_cost_usd_per_kg"] * _hydrolox["density_kg_per_L"],
        "yfinance_proxy":        None,            # LH2 has no spot ticker
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Highest chemical Isp.  Vac Isp 452 s per RS-25 / RL-10 datasheets. "
                 "LH2 base price $3-6/kg (NASA contracts); bulk-handling overhead "
                 "lifts effective cost to ~$10/kg.  Used on SLS, Centaur.",
    },
    {
        "name":                  "methalox  (LCH4 / LOX)",
        "type":                  "bipropellant",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          2023,   # Zhuque-2, first methalox vehicle to orbit (Jul 2023)
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "mild_cryogen",
        "tank_kg_per_L":         _methalox["tank_kg_per_L"],
        # Sabatier from asteroid water plus carbonaceous CO2 is possible in
        # principle, but it needs a carbon source AND hydrogen AND a reactor,
        # and this pipeline prices neither the reactor nor the carbon.  Left
        # unavailable rather than credited on a maybe.
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.012,   # LCH4 boils at 112 K, close enough to LOX (90 K) that a single thermal system serves both -- the 'space-storable cryogen' argument for methalox.
        "isp_vac_s":             380,
        "exhaust_vel_m_per_s":   380 * G0_M_S2,
        "density_kg_per_L":      _methalox["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _methalox["ref_cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _methalox["ref_cost_usd_per_kg"] * _methalox["density_kg_per_L"],
        "yfinance_proxy":        "natural_gas",   # CH4 tracks NG=F (Henry Hub)
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Raptor (Starship) & BE-4 (Vulcan / New Glenn) engines.  "
                 "Vac Isp 380 s per SpaceX Raptor public data.  LCH4 ~$400/tonne "
                 "open-market per Mobius Market Research 2024.  ISRU-makeable on Mars.",
    },
    {
        "name":                  "MMH / NTO  (hypergolic)",
        "type":                  "bipropellant",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1965,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "storable_liquid",
        "tank_kg_per_L":         _mmh_nto["tank_kg_per_L"],
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,   # Storable at room temperature indefinitely.  Voyager still had usable hydrazine after 45 years.
        "isp_vac_s":             336,
        "exhaust_vel_m_per_s":   336 * G0_M_S2,
        "density_kg_per_L":      _mmh_nto["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _mmh_nto["ref_cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _mmh_nto["ref_cost_usd_per_kg"] * _mmh_nto["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Storable hypergolic — standard for deep-space manoeuvring "
                 "(OMS, RCS, OSIRIS-REx propulsion).  Vac Isp 336 s per "
                 "Astronautix N2O4/MMH datasheet.  Pricing from DOD FY20 standards.",
    },
    {
        "name":                  "Hydrazine  (monoprop)",
        "type":                  "monopropellant",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1960,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "storable_liquid",
        "tank_kg_per_L":         _tank_kg_per_L("storable_liquid"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,   # Storable indefinitely.
        "isp_vac_s":             220,
        "exhaust_vel_m_per_s":   220 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["Hydrazine"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["Hydrazine"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["Hydrazine"]["cost_usd_per_kg"]
                                 * _COMPONENTS["Hydrazine"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Attitude control + small Δv.  Cat-bed decomposition.  "
                 "Vac Isp 220 s (Astronautix Hydrazine page).  "
                 "Pricing: DOD FY20 standard $30.5/kg, commercial $75.8/kg "
                 "(AIAA 2024).  Used $75/kg conservative for aerospace.",
    },
    {
        "name":                  "Xenon  (Hall / ion)",
        "type":                  "electric",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1998,   # Deep Space 1 / NSTAR
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "supercritical_gas",
        "tank_kg_per_L":         _tank_kg_per_L("supercritical_gas", 10.0),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,   # Stored supercritical at ambient temperature; no boil-off.
        "isp_vac_s":             3_000,
        "exhaust_vel_m_per_s":   3_000 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["Xenon"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["Xenon"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["Xenon"]["cost_usd_per_kg"]
                                 * _COMPONENTS["Xenon"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "10× the Isp of chemical; low thrust ⇒ months of burn.  "
                 "Used by Dawn, BepiColombo, NEXT-C.  "
                 "SETS Space 2024: $5-12k/kg for 99.999% aerospace-grade Xe; "
                 "used $10k/kg (2023 EFC reference).",
    },
    {
        "name":                  "Argon  (Hall / ion)",
        "type":                  "electric",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          2023,   # Starlink V2 mini
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "supercritical_gas",
        "tank_kg_per_L":         _tank_kg_per_L("supercritical_gas", 18.0),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,   # Ambient-temperature COPV; nothing to boil.
        "isp_vac_s":             1_500,
        "exhaust_vel_m_per_s":   1_500 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["ArgonSC"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["ArgonSC"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["ArgonSC"]["cost_usd_per_kg"]
                                 * _COMPONENTS["ArgonSC"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Starlink-V2 thruster choice (SpaceX claims 2.4× thrust, 1.5× Isp "
                 "of their previous Kr design).  Bulk industrial $7-15/kg per "
                 "SETS Space 2024; used $10/kg midpoint.\n"
                 "v1.10.0: stored SUPERCRITICAL at 18 MPa and ambient "
                 "temperature, 0.30 kg/L, which is what has flown — no spacecraft "
                 "has ever carried cryogenic argon.  Until v1.10.0 this row took "
                 "liquid-argon density (1.395 kg/L, 87.3 K) and a boil-off of "
                 "zero at the same time, which gave it the lightest tank of any "
                 "gas here and no cryogenic hold penalty.  Honestly stored it "
                 "pays 22.9% of its own mass in COPV against krypton's 12.5% and "
                 "xenon's 1.9% — argon is the LIGHTEST noble gas, so it is the "
                 "worst of the three to bottle, and $10/kg does not buy that "
                 "back.  The cryogenic article is a separate row below.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # OPERATIONAL, chemical, added v1.9.0
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                  "UDMH / NTO  (hypergolic)",
        "type":                  "bipropellant",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1965,   # Proton-K
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "storable_liquid",
        "tank_kg_per_L":         _udmh_nto["tank_kg_per_L"],
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             318,
        "exhaust_vel_m_per_s":   318 * G0_M_S2,
        "density_kg_per_L":      _udmh_nto["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _udmh_nto["ref_cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _udmh_nto["ref_cost_usd_per_kg"] * _udmh_nto["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Proton and Long March heritage; still the most-flown storable "
                 "bipropellant by tonnage.  Vac Isp 318 s (Astronautix N2O4/UDMH) "
                 "at 2.6 O/F.  Slightly worse than MMH/NTO and considerably more "
                 "carcinogenic — present for completeness, not because it wins.",
    },
    {
        "name":                  "Aerozine-50 / NTO  (hypergolic)",
        "type":                  "bipropellant",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1964,   # Titan II / Apollo SPS
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "storable_liquid",
        "tank_kg_per_L":         _a50_nto["tank_kg_per_L"],
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             320,
        "exhaust_vel_m_per_s":   320 * G0_M_S2,
        "density_kg_per_L":      _a50_nto["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _a50_nto["ref_cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _a50_nto["ref_cost_usd_per_kg"] * _a50_nto["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "50/50 UDMH-hydrazine by mass.  Apollo Service Propulsion System "
                 "and the Titan family; the engine that had to light after eight "
                 "days in cislunar space and always did.  Vac Isp 320 s "
                 "(Astronautix AJ10-137).",
    },
    {
        "name":                  "Green monoprop  (ASCENT / AF-M315E)",
        "type":                  "monopropellant",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          2019,   # NASA GPIM
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "storable_liquid",
        "tank_kg_per_L":         _tank_kg_per_L("storable_liquid"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             235,
        "exhaust_vel_m_per_s":   235 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["ASCENT"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["ASCENT"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["ASCENT"]["cost_usd_per_kg"]
                                 * _COMPONENTS["ASCENT"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Hydroxylammonium nitrate monoprop.  Flown on NASA's Green "
                 "Propellant Infusion Mission (2019); the Swedish LMP-103S "
                 "equivalent flew earlier on PRISMA (2010).  Isp 235 s and "
                 "ρ 1.47 kg/L beat hydrazine on BOTH counts — ~50% more "
                 "density-impulse — and it is not acutely toxic, which is a "
                 "ground-handling saving this model does not price.  The $500/kg "
                 "is pilot-scale production, not chemistry.",
    },
    {
        "name":                  "HTP  (98% peroxide monoprop)",
        "type":                  "monopropellant",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1949,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "storable_liquid",
        "tank_kg_per_L":         _tank_kg_per_L("storable_liquid"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.002,   # slow catalytic self-decomposition, not boil-off; ~1%/yr in a passivated tank
        "isp_vac_s":             165,
        "exhaust_vel_m_per_s":   165 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["HTP-98"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["HTP-98"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["HTP-98"]["cost_usd_per_kg"]
                                 * _COMPONENTS["HTP-98"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Silver-screen decomposition.  Centaur RCS, Soyuz turbopump gas "
                 "generator, Black Arrow.  Cheapest propellant in this table at "
                 "~$5/kg and the lowest Isp of any liquid in it — the reason it "
                 "is here is the boil-off column: 0.002%/day is self-"
                 "decomposition, not evaporation, so unlike a cryogen the loss "
                 "does not accelerate with mission length.",
    },
    {
        "name":                  "HTP / RP-1  (peroxide bipropellant)",
        "type":                  "bipropellant",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1969,   # Black Arrow R1
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "storable_liquid",
        "tank_kg_per_L":         _htp_rp1["tank_kg_per_L"],
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.002,
        "isp_vac_s":             320,
        "exhaust_vel_m_per_s":   320 * G0_M_S2,
        "density_kg_per_L":      _htp_rp1["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _htp_rp1["ref_cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _htp_rp1["ref_cost_usd_per_kg"] * _htp_rp1["density_kg_per_L"],
        "yfinance_proxy":        "heating_oil",
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Black Arrow flew HTP/kerosene to orbit in 1971 — the only "
                 "British orbital launch.  Isp 320 s vac at 7:1 O/F, ρ 1.30 kg/L, "
                 "fully storable, and the cheapest bipropellant here.  The "
                 "combination that keeps getting rediscovered and keeps losing to "
                 "kerolox on Isp.",
    },
    {
        "name":                  "Cold gas  (GN2)",
        "type":                  "cold_gas",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1961,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "supercritical_gas",
        "tank_kg_per_L":         _tank_kg_per_L("supercritical_gas", 30.0),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             70,
        "exhaust_vel_m_per_s":   70 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["GN2"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["GN2"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["GN2"]["cost_usd_per_kg"]
                                 * _COMPONENTS["GN2"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "The simplest thruster that exists and the worst.  Isp 70 s, and "
                 "at 30 MPa the COPV masses 46% of the nitrogen it holds — the "
                 "clearest demonstration in this table of why tankage belongs in "
                 "the rocket equation.  Present as the floor of the Isp range, "
                 "not as a candidate.",
    },
    {
        "name":                  "Solid  (APCP)",
        "type":                  "solid",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1958,
        "restartable":           False,   # ← disqualifying: see notes
        "propellantless":        False,
        "storage_class":         "solid_motor",
        "tank_kg_per_L":         _tank_kg_per_L("solid_motor"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             285,
        "exhaust_vel_m_per_s":   285 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["APCP"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["APCP"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["APCP"]["cost_usd_per_kg"]
                                 * _COMPONENTS["APCP"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Star 48B / Orion 38 class kick motor.  Vac Isp 286 s, ρ 1.80 "
                 "kg/L, storable for decades, and the case masses only 6.9% of "
                 "the grain (Star 48B burnout 129 kg on 2,010 kg loaded = 6.4%, "
                 "which is what the solid_motor multiplier is anchored to).\n"
                 "restartable=False, and that is disqualifying HERE: an asteroid "
                 "return fires its second burn years after the first, and a solid "
                 "cannot be relit or throttled.  It stays in the table because "
                 "'we did not consider solids' and 'solids cannot fly this "
                 "profile' are different statements and only one of them is true.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # OPERATIONAL, electric, added v1.9.0
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                  "Krypton  (Hall)",
        "type":                  "electric",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          2019,   # Starlink v1.0
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "supercritical_gas",
        "tank_kg_per_L":         _tank_kg_per_L("supercritical_gas", 18.0),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             2_000,
        "exhaust_vel_m_per_s":   2_000 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["Krypton"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["Krypton"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["Krypton"]["cost_usd_per_kg"]
                                 * _COMPONENTS["Krypton"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "The most-flown electric propellant by unit count — every "
                 "Starlink v1.0 Hall thruster ran krypton, because Xe supply "
                 "cannot feed a constellation.  ~30× cheaper than xenon at "
                 "$300/kg, ~2/3 the Isp, and a materially worse tank: 0.55 kg/L "
                 "supercritical against xenon's 2.0 means the COPV masses 12.5% "
                 "of the propellant against xenon's 1.9%.  Whether it beats "
                 "xenon is exactly the kind of trade this table now lets the "
                 "search resolve rather than assume.",
    },
    {
        "name":                  "Iodine  (Hall / gridded)",
        "type":                  "electric",
        "status":                "operational",
        "trl":                   8,
        "first_flight":          2020,   # ThrustMe NPT30-I2 on Beihangkongshi-1
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "sublimating_solid",
        "tank_kg_per_L":         _tank_kg_per_L("sublimating_solid"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             2_000,
        "exhaust_vel_m_per_s":   2_000 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["Iodine"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["Iodine"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["Iodine"]["cost_usd_per_kg"]
                                 * _COMPONENTS["Iodine"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "First iodine electric propulsion in orbit: ThrustMe's NPT30-I2 "
                 "on Beihangkongshi-1, Nov 2020 (Rafalskyi et al., Nature 599, "
                 "2021).  Stored as a SOLID at ambient pressure, ρ 4.93 kg/L, so "
                 "the reservoir masses 0.23% of the propellant against xenon's "
                 "1.9% — by a wide margin the best storage density ever flown "
                 "outside mercury.  Cost $60/kg.  The catch is condensable "
                 "exhaust plating out on cold surfaces, which is a "
                 "contamination problem this model does not price.",
    },
    {
        "name":                  "Water  (electrothermal / resistojet)",
        "type":                  "electric",
        "status":                "operational",
        "trl":                   8,
        "first_flight":          2022,   # HYDROS-C (Tethers Unlimited), Momentus Vigoride, Pale Blue
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "benign_liquid",
        "tank_kg_per_L":         _tank_kg_per_L("benign_liquid"),
        "isru_feed_kg_per_kg":   1.0,
        "isru_feed_material":    "water",
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             190,
        "exhaust_vel_m_per_s":   190 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["Water"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["Water"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["Water"]["cost_usd_per_kg"]
                                 * _COMPONENTS["Water"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Steam.  Resistively or microwave heated, Isp 150-220 s.  Flown "
                 "by Tethers Unlimited's HYDROS-C (ISS deploy 2022), Momentus' "
                 "microwave electrothermal Vigoride, and Pale Blue's water "
                 "resistojet.\n"
                 "The point is not the Isp, which is terrible.  It is "
                 "isru_feed_kg_per_kg = 1.0: an asteroid supplies this propellant "
                 "DIRECTLY, with no electrolysis, no cryocooler and no 1.286 "
                 "stoichiometric markup.  Hydrolox needs 1.29 kg of water per kg "
                 "of propellant and a liquefaction plant; steam needs 1.00 and a "
                 "hotplate.  Whether 190 s bought that cheaply beats 452 s bought "
                 "expensively is a real question and the search now gets to "
                 "answer it per asteroid.",
    },
    {
        "name":                  "Water  (gridded ion / ECR)",
        "type":                  "electric",
        "status":                "operational",
        "trl":                   7,
        "first_flight":          2023,   # Pale Blue water ion thruster
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "benign_liquid",
        "tank_kg_per_L":         _tank_kg_per_L("benign_liquid"),
        "isru_feed_kg_per_kg":   1.0,
        "isru_feed_material":    "water",
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             900,
        "exhaust_vel_m_per_s":   900 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["Water"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["Water"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["Water"]["cost_usd_per_kg"]
                                 * _COMPONENTS["Water"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Ionise the steam instead of just heating it: Isp 800-1,000 s on "
                 "the same tank of water.  Pale Blue flew a water ion thruster in "
                 "2023; ESA and JAXA both have ECR water thrusters in "
                 "qualification.  Same ISRU story as the resistojet at ~5× the "
                 "Isp, for a much larger power plant — which this pipeline sizes "
                 "and charges, so the trade is honest.",
    },
    {
        "name":                  "Hydrazine arcjet",
        "type":                  "electric",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1993,   # Telstar 401 / A2100 MR-510
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "storable_liquid",
        "tank_kg_per_L":         _tank_kg_per_L("storable_liquid"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             600,
        "exhaust_vel_m_per_s":   600 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["Hydrazine"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["Hydrazine"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["Hydrazine"]["cost_usd_per_kg"]
                                 * _COMPONENTS["Hydrazine"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Aerojet MR-510, 600 s vac on 2 kW — flown on Lockheed A2100 "
                 "comsats since 1993 and largely displaced by Hall thrusters "
                 "since.  Sits in the gap between chemical and true electric: "
                 "3× hydrazine's Isp at ~100 mN, so it needs far less power per "
                 "newton than a Hall thruster and far less patience than an ion "
                 "engine.  Ammonia arcjets reach ~500 s on a cheaper propellant.",
    },
    {
        "name":                  "Electrospray  (ionic liquid)",
        "type":                  "electric",
        "status":                "operational",
        "trl":                   8,
        "first_flight":          2016,   # LISA Pathfinder ST7-DRS colloid thrusters
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "storable_liquid",
        "tank_kg_per_L":         _tank_kg_per_L("storable_liquid"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             2_500,
        "exhaust_vel_m_per_s":   2_500 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["EMI-BF4"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["EMI-BF4"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["EMI-BF4"]["cost_usd_per_kg"]
                                 * _COMPONENTS["EMI-BF4"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Ionic liquid (EMI-BF4) extracted electrostatically from an "
                 "emitter array — no ionisation chamber, no neutraliser "
                 "discharge, no pressurant.  Flew on LISA Pathfinder's ST7-DRS "
                 "at micronewton precision (2016); Accion's TILE flies "
                 "commercially.  Isp 2,500 s and a room-temperature liquid tank, "
                 "but thrust per emitter is microscopic — scaling to a cargo "
                 "stage means millions of emitters, which is a manufacturing "
                 "problem, not a physics one.",
    },
    {
        "name":                  "FEEP  (indium field emission)",
        "type":                  "electric",
        "status":                "operational",
        "trl":                   8,
        "first_flight":          2016,   # LISA Pathfinder / earlier GOCE caesium ion
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "sublimating_solid",
        "tank_kg_per_L":         _tank_kg_per_L("sublimating_solid"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             6_000,
        "exhaust_vel_m_per_s":   6_000 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["Indium"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["Indium"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["Indium"]["cost_usd_per_kg"]
                                 * _COMPONENTS["Indium"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Liquid indium wicked to a needle tip and field-evaporated. "
                 "ENPULSION's IFM Nano flies on hundreds of smallsats.  Isp "
                 "4,000-8,000 s — the highest of anything operational — at "
                 "ρ 7.31 kg/L in an unpressurised reservoir.  Thrust is tens of "
                 "micronewtons per emitter.  This is the high-Isp end of the "
                 "flown record, and the pipeline's power model is what stops it "
                 "running away with the answer.",
    },
    {
        "name":                  "PPT  (PTFE pulsed plasma)",
        "type":                  "electric",
        "status":                "operational",
        "trl":                   9,
        "first_flight":          1968,   # LES-6
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "sublimating_solid",
        "tank_kg_per_L":         _tank_kg_per_L("sublimating_solid"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             1_000,
        "exhaust_vel_m_per_s":   1_000 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["PTFE"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["PTFE"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["PTFE"]["cost_usd_per_kg"]
                                 * _COMPONENTS["PTFE"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "A Teflon bar ablated by a capacitor discharge — the oldest "
                 "electric propulsion in service (LES-6, 1968; EO-1, 2000). "
                 "Isp ~1,000 s, solid propellant, no tank, no valves, no feed "
                 "system at all.  Efficiency is ~10%, an order below a Hall "
                 "thruster, which is why it never scaled past attitude control.",
    },
    {
        "name":                  "Mercury ion  (RETIRED)",
        "type":                  "electric",
        "status":                "retired",
        "trl":                   9,
        "first_flight":          1970,   # SERT-II
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "storable_liquid",
        "tank_kg_per_L":         _tank_kg_per_L("storable_liquid"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             3_000,
        "exhaust_vel_m_per_s":   3_000 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["Mercury"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["Mercury"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["Mercury"]["cost_usd_per_kg"]
                                 * _COMPONENTS["Mercury"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "SERT-II (1970) and ATS-6 flew mercury ion engines.  ρ 13.53 "
                 "kg/L is still the best propellant storage density ever flown "
                 "and $60/kg is a fiftieth of xenon, so on this table's columns "
                 "alone it looks like the obvious winner.\n"
                 "It is banned.  The 2013 Minamata Convention on Mercury "
                 "prohibits it, and a 2019 attempt to fly a mercury-propelled "
                 "constellation was abandoned after the ionised-mercury plume "
                 "was shown to return to Earth's atmosphere.  status='retired' "
                 "keeps it out of the search permanently — it is here so that "
                 "the next person to notice the density has the answer already.",
    },
    {
        "name":                  "Solar sail  (photonic)",
        "type":                  "propellantless",
        "status":                "operational",
        "trl":                   8,
        "first_flight":          2010,   # IKAROS
        "restartable":           True,
        "propellantless":        True,
        "storage_class":         "propellantless",
        "tank_kg_per_L":         0.0,
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             np.inf,
        "exhaust_vel_m_per_s":   np.inf,
        "density_kg_per_L":      np.nan,
        "ref_cost_usd_per_kg":   0.0,
        "ref_cost_usd_per_L":    0.0,
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "IKAROS (2010) was the first sail to be propelled by sunlight; "
                 "LightSail 2 (2019) raised its own apogee; NEA Scout (2022) "
                 "deployed but was lost; ACS3 (2024) demonstrated composite "
                 "booms.\n"
                 "Isp is infinite, which is exactly the problem: the rocket "
                 "equation says a sail moves any payload for zero propellant, "
                 "so an unguarded model reports an unbounded result.  Real sails "
                 "run ~0.1 mm/s² of characteristic acceleration at 1 AU — fine "
                 "for a 6 kg cubesat, meaningless for a hold of ore, and falling "
                 "as 1/r² besides.  propellantless=True makes Module 4 exclude "
                 "it.  Pricing sails properly needs a thrust-limited trajectory "
                 "solver, which is the same gap that keeps the EP stage sized to "
                 "a fixed thrust duration.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # DEVELOPMENT, built and fired, not yet flown
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                  "Nuclear thermal  (LH2, NTP)",
        "type":                  "nuclear_thermal",
        "status":                "development",
        "trl":                   5,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "deep_cryogen",
        "tank_kg_per_L":         _tank_kg_per_L("deep_cryogen"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.05,   # bare LH2, no oxidiser to average against, the worst in the table
        "isp_vac_s":             900,
        "exhaust_vel_m_per_s":   900 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["LH2"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["LH2"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["LH2"]["cost_usd_per_kg"]
                                 * _COMPONENTS["LH2"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Heat hydrogen in a fission core: twice the Isp of the best "
                 "chemistry at full chemical thrust.  NERVA's NRX/XE ran on a "
                 "test stand at 825 s in 1968; DRACO targeted 900 s before being "
                 "descoped in 2025.  TRL 5 — the reactor physics is 60 years "
                 "proven and nothing has flown.\n"
                 "This row is the clearest case for the v1.9.0 tank model.  Bare "
                 "LH2 at 0.0708 kg/L pays 53% of its own mass in tankage and "
                 "0.05%/day in boil-off with no oxidiser to average against, so "
                 "a large part of the 900 s is handed straight back on a "
                 "multi-year mission.  Before v1.9.0 the model would have taken "
                 "the Isp and charged nothing for either.  The reactor's own "
                 "mass and cost are ALSO not modelled — so this row is still "
                 "optimistic, and gated out of the default search accordingly.",
    },
    {
        "name":                  "Nuclear electric  (NEP, xenon)",
        "type":                  "nuclear_electric",
        "status":                "development",
        "trl":                   4,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "supercritical_gas",
        "tank_kg_per_L":         _tank_kg_per_L("supercritical_gas", 10.0),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             5_000,
        "exhaust_vel_m_per_s":   5_000 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["Xenon"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["Xenon"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["Xenon"]["cost_usd_per_kg"]
                                 * _COMPONENTS["Xenon"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "A fission reactor driving high-power ion or Hall thrusters. "
                 "The one architecture that breaks this pipeline's binding "
                 "constraint on electric propulsion — power at distance, which "
                 "PV loses as 1/r².  Kilopower/KRUSTY ran a 1 kWe reactor in "
                 "2018; MW-class flight units are TRL 3-4.\n"
                 "⚠️  Module 4 sizes electric power off the PV row and its 1/r² "
                 "term.  A nuclear source does not scale that way, so selecting "
                 "this propellant WITHOUT teaching the power model about it "
                 "would still charge a solar array's mass.  Gated out until "
                 "that is fixed; the row exists so the gap is visible.",
    },
    {
        "name":                  "Solar thermal  (LH2)",
        "type":                  "solar_thermal",
        "status":                "development",
        "trl":                   4,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "deep_cryogen",
        "tank_kg_per_L":         _tank_kg_per_L("deep_cryogen"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.05,
        "isp_vac_s":             800,
        "exhaust_vel_m_per_s":   800 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["LH2"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["LH2"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["LH2"]["cost_usd_per_kg"]
                                 * _COMPONENTS["LH2"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Concentrate sunlight onto a hydrogen heat exchanger: NTP's Isp "
                 "without the reactor.  Ground-tested by the USAF Solar Orbit "
                 "Transfer Vehicle programme in the 1990s (Isp 700-900 s "
                 "demonstrated); never flown.  Suffers the same 1/r² starvation "
                 "as PV, so it is a near-Sun technology — which is the opposite "
                 "of where the main belt is.",
    },
    {
        "name":                  "Solar thermal steam  (water)",
        "type":                  "solar_thermal",
        "status":                "development",
        "trl":                   4,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "benign_liquid",
        "tank_kg_per_L":         _tank_kg_per_L("benign_liquid"),
        "isru_feed_kg_per_kg":   1.0,
        "isru_feed_material":    "water",
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             190,
        "exhaust_vel_m_per_s":   190 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["Water"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["Water"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["Water"]["cost_usd_per_kg"]
                                 * _COMPONENTS["Water"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Honeybee Robotics' WINE ('World Is Not Enough') mined simulant, "
                 "boiled the water and thrusted on the steam inside a vacuum "
                 "chamber in 2018 — the only end-to-end asteroid-ISRU propulsion "
                 "demonstration there has ever been.  Isp ~190 s, no electrical "
                 "conversion loss, and 1.0 kg of asteroid water per kg of "
                 "propellant.  This is the propellant the concept of a "
                 "self-refuelling mining craft is actually built on, and it was "
                 "absent from this table until v1.9.0.",
    },
    {
        "name":                  "VASIMR  (argon, variable Isp)",
        "type":                  "electric",
        "status":                "development",
        "trl":                   5,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "mild_cryogen",
        "tank_kg_per_L":         _tank_kg_per_L("mild_cryogen"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   _LAR_BOILOFF_PCT_PER_DAY,
        "isp_vac_s":             4_000,
        "exhaust_vel_m_per_s":   4_000 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["ArgonLIQ"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["ArgonLIQ"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["ArgonLIQ"]["cost_usd_per_kg"]
                                 * _COMPONENTS["ArgonLIQ"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Ad Astra's VX-200SS ran 100 hours at 80 kW in 2021.  RF-heated "
                 "plasma in a magnetic nozzle, and the headline feature is "
                 "throttleable Isp — trade thrust against efficiency in flight, "
                 "which is precisely the freedom a fixed-Isp table cannot "
                 "express.  Modelled here at a single 4,000 s point, which "
                 "understates it; capturing the variable-Isp advantage needs the "
                 "same trajectory optimiser the sails do.\n"
                 "Cryogenic argon feed, because a 100 kW-class stage moves "
                 "propellant by the tonne and no COPV is a sensible way to carry "
                 "tonnes of a gas this light.  v1.10.0: it therefore pays "
                 "cryogenic boil-off, which it was exempt from before.",
    },
    {
        "name":                  "Argon  (Hall / ion, cryogenic)",
        "type":                  "electric",
        "status":                "development",
        "trl":                   4,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "mild_cryogen",
        "tank_kg_per_L":         _tank_kg_per_L("mild_cryogen"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   _LAR_BOILOFF_PCT_PER_DAY,
        "isp_vac_s":             1_500,
        "exhaust_vel_m_per_s":   1_500 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["ArgonLIQ"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["ArgonLIQ"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["ArgonLIQ"]["cost_usd_per_kg"]
                                 * _COMPONENTS["ArgonLIQ"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "v1.10.0.  The other half of the argon split — same 1,500 s Hall "
                 "thruster as the operational row, fed from a liquid tank at "
                 "87.3 K instead of an 18 MPa bottle.  It is the architecture a "
                 "multi-tonne stage would actually want: 1.395 kg/L against "
                 "0.30 buys a 2.1% tank against 22.9%, which is the single "
                 "biggest storage swing in this table.\n"
                 "DEVELOPMENT, not operational, and the distinction is the point. "
                 "Liquid argon is routine on the ground and has never flown on a "
                 "spacecraft; no EP system has ever carried a cryogen.  Tagging "
                 "it operational would let the default search fly an article "
                 "nobody has built, which is exactly what the pre-v1.10.0 argon "
                 "row did by accident.  The honest version of that row is these "
                 "two, and the tank saving now costs what it really costs: "
                 "boil-off over a multi-year hold, on the same terms as every "
                 "other cryogen here.",
    },
    {
        "name":                  "MPD  (lithium magnetoplasmadynamic)",
        "type":                  "electric",
        "status":                "development",
        "trl":                   4,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "storable_liquid",
        "tank_kg_per_L":         _tank_kg_per_L("storable_liquid"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             4_000,
        "exhaust_vel_m_per_s":   4_000 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["Lithium"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["Lithium"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["Lithium"]["cost_usd_per_kg"]
                                 * _COMPONENTS["Lithium"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Lithium Lorentz Force Accelerator — the highest thrust density "
                 "of any electric thruster, and the only class that could plausibly "
                 "move hundreds of tonnes.  Ground-tested at Princeton and by "
                 "RIAME (Moscow) at 100+ kW; needs megawatts to be interesting, "
                 "which is why it is bracketed with NEP rather than with PV.",
    },
    {
        "name":                  "Metal / water  (ALICE, Al + H2O)",
        "type":                  "bipropellant",
        "status":                "development",
        "trl":                   3,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "solid_motor",
        "tank_kg_per_L":         _al_water["tank_kg_per_L"],
        "isru_feed_kg_per_kg":   0.5,
        "isru_feed_material":    "water",
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             210,
        "exhaust_vel_m_per_s":   210 * G0_M_S2,
        "density_kg_per_L":      _al_water["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _al_water["ref_cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _al_water["ref_cost_usd_per_kg"] * _al_water["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Nano-aluminium burnt in water — Purdue/NASA ALICE flew a "
                 "sounding rocket in 2009.  Isp only 210 s, but BOTH components "
                 "are asteroid-derivable: metallic aluminium from silicate "
                 "reduction and water from phyllosilicates.  isru_feed is 0.5 "
                 "because half the mixture is metal, which this pipeline does "
                 "not yet model refining — so the figure is a placeholder for "
                 "the water half only and the row is gated out.",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # CONCEPT, designed, or demonstrated only as physics
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name":                  "Li / F2 / H2  (tripropellant)",
        "type":                  "tripropellant",
        "status":                "concept",
        "trl":                   3,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "mild_cryogen",
        "tank_kg_per_L":         _lifh["tank_kg_per_L"],
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.04,
        "isp_vac_s":             542,
        "exhaust_vel_m_per_s":   542 * G0_M_S2,
        "density_kg_per_L":      _lifh["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _lifh["ref_cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _lifh["ref_cost_usd_per_kg"] * _lifh["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "542 s is the highest specific impulse ever MEASURED from a "
                 "chemical rocket — Rocketdyne, test stand, 1960s.  It is in "
                 "this table as the ceiling of chemistry, so that '452 s is the "
                 "best chemical Isp' is not quietly assumed.\n"
                 "It will never fly.  The exhaust is hydrogen fluoride, the "
                 "oxidiser is liquid fluorine, and the fuel is molten lithium; "
                 "the ground handling is beyond hazardous and into "
                 "unpermittable.  status='concept' at TRL 3 despite a real "
                 "firing, because engineering feasibility is not the binding "
                 "constraint here.",
    },
    {
        "name":                  "CO / LOX  (carbonaceous ISRU)",
        "type":                  "bipropellant",
        "status":                "concept",
        "trl":                   3,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "mild_cryogen",
        "tank_kg_per_L":         _co_lox["tank_kg_per_L"],
        # NOT declared ISRU-makeable, despite being the entry here most obviously
        # aimed at it.  The feed is set by the body's CARBON fraction, not by a
        # flat regolith ratio: 1 kg of propellant at O/F 0.57 is 0.637 kg of CO,
        # which is 0.274 kg of carbon, so a 3 wt% carbonaceous body owes ~9 kg of
        # rock per kg burnt, and a 1 wt% body owes 27.  Module 4 has no
        # carbon-fed ISRU path, and stating a single number here would be
        # inventing one rather than deriving it, exactly as with methalox.
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.012,
        "isp_vac_s":             260,
        "exhaust_vel_m_per_s":   260 * G0_M_S2,
        "density_kg_per_L":      _co_lox["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _co_lox["ref_cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _co_lox["ref_cost_usd_per_kg"] * _co_lox["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Carbon monoxide burnt in oxygen, both from carbonaceous "
                 "regolith or a CO2 atmosphere.  Isp ~260 s — poor — but it is "
                 "the only chemical bipropellant makeable from a C-type asteroid "
                 "without any hydrogen at all, which matters because hydrogen is "
                 "the scarce element out there, not carbon or oxygen.  Studied "
                 "extensively for Mars (Zubrin); never built.\n"
                 "The ISRU columns are deliberately null — see the comment "
                 "above them.  This is the row where 'obviously ISRU' and "
                 "'this model can price it' come apart.",
    },
    {
        "name":                  "Mass driver  (regolith reaction mass)",
        "type":                  "kinetic",
        "status":                "concept",
        "trl":                   3,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "sublimating_solid",   # raw rock in a hopper; no pressure vessel
        "tank_kg_per_L":         _tank_kg_per_L("sublimating_solid"),
        "isru_feed_kg_per_kg":   1.0,
        "isru_feed_material":    "regolith",
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             306,     # 3 km/s slug velocity / g0; see notes
        "exhaust_vel_m_per_s":   3_000,
        "density_kg_per_L":      2.000,   # loose regolith bulk density
        "ref_cost_usd_per_kg":   0.10,    # the rock is free; this is handling
        "ref_cost_usd_per_L":    0.20,
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Electromagnetically accelerate buckets of raw regolith and "
                 "throw them overboard.  O'Neill and Snow built a working "
                 "prototype at Princeton in 1977 (40 g); the concept predates "
                 "every other entry in this table as an asteroid-mining "
                 "proposal, and it was missing from it.\n"
                 "Isp is a derived equivalence, not a chemistry: a 3 km/s slug "
                 "velocity is 3,000/9.807 = 306 s.  The reaction mass is the "
                 "asteroid, so isru_feed_material='regolith' at 1.0 and the "
                 "$/kg is handling only.  What it costs is POWER, continuously, "
                 "and its thrust is a stream of discrete impulses — neither of "
                 "which this pipeline's propulsion model can express, hence "
                 "concept and gated.",
    },
    {
        "name":                  "Nuclear pulse  (Orion)",
        "type":                  "nuclear_pulse",
        "status":                "concept",
        "trl":                   2,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "solid_motor",
        "tank_kg_per_L":         _tank_kg_per_L("solid_motor"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             10_000,
        "exhaust_vel_m_per_s":   10_000 * G0_M_S2,
        "density_kg_per_L":      1.500,
        # ORDER-OF-MAGNITUDE ESTIMATE.  A pulse unit is mostly tungsten/
        # polyethylene propellant around a small fissile core, so the average
        # $/kg is nowhere near the ~$4-6M/kg of weapons-grade plutonium
        # itself, but there is no commodity price for a nuclear shaped
        # charge, and there will not be one.  $50k/kg is a placeholder that
        # keeps the row from looking cheap; do not read it as a quote.
        "ref_cost_usd_per_kg":   50_000.0,
        "ref_cost_usd_per_L":    75_000.0,
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Detonate shaped nuclear charges against a pusher plate. "
                 "Designed in full engineering detail by General Atomics "
                 "1958-1965 — Dyson and Taylor's programme produced vehicle "
                 "layouts, not sketches — and killed by the 1963 Partial Test "
                 "Ban Treaty.  Isp 10,000 s at MEGANEWTON thrust is the only "
                 "entry here that is both high-Isp and high-thrust, which is why "
                 "it keeps being revisited.  TRL 2 and permanently "
                 "unpermittable; present because 'never designed' would be false.",
    },
    {
        "name":                  "Direct fusion drive",
        "type":                  "fusion",
        "status":                "concept",
        "trl":                   2,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "supercritical_gas",
        "tank_kg_per_L":         _tank_kg_per_L("supercritical_gas", 10.0),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             10_000,
        "exhaust_vel_m_per_s":   10_000 * G0_M_S2,
        "density_kg_per_L":      0.100,
        # He-3 is quoted around $1,400-2,000 per gram, so ~$1.5M/kg, and the
        # D-He3 mix is mostly deuterium (~$1,000/kg).  ORDER-OF-MAGNITUDE
        # ESTIMATE at $1M/kg for the blend; there is no market, and world He-3
        # supply is a few kg a year from tritium decay.
        "ref_cost_usd_per_kg":   1_000_000.0,
        "ref_cost_usd_per_L":    100_000.0,
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Princeton Plasma Physics Lab's PFRC-2 field-reversed "
                 "configuration, aneutronic D-He3, studied under NASA NIAC. "
                 "Isp 10,000+ s at ~5 N/MW.  TRL 2: the confinement scheme is "
                 "under experimental test and net-positive fusion of any kind "
                 "has not been demonstrated in a flight-relevant device.",
    },
    {
        "name":                  "Antimatter-catalysed",
        "type":                  "antimatter",
        "status":                "concept",
        "trl":                   1,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "supercritical_gas",
        "tank_kg_per_L":         _tank_kg_per_L("supercritical_gas", 10.0),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     _LOW_THRUST_DV_PENALTY,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             100_000,
        "exhaust_vel_m_per_s":   100_000 * G0_M_S2,
        "density_kg_per_L":      0.100,
        # $62.5 trillion per GRAM is the figure NASA/CERN quote, which is
        # 6.25e16 USD/kg, not the 1e15 an earlier draft of this row carried.
        # The whole propellant load is not antimatter (a few micrograms
        # initiate microfission in a much larger charge), so this is the
        # antihydrogen price applied as if it were, i.e. an upper bound and
        # explicitly not a mission cost.
        "ref_cost_usd_per_kg":   6.25e16,
        "ref_cost_usd_per_L":    6.25e15,
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Antiproton-initiated microfission (Penn State AIMStar, NASA "
                 "NIAC).  The Isp column is the reason it appears in every "
                 "propulsion survey; the cost column is the reason it appears in "
                 "no mission plan.  CERN's antiproton production, scaled, prices "
                 "antihydrogen near $10^15/kg, and world annual production is "
                 "measured in nanograms.  TRL 1.  It is here to close the table "
                 "at the physical ceiling.",
    },
    {
        "name":                  "Magnetic sail / electric sail",
        "type":                  "propellantless",
        "status":                "concept",
        "trl":                   3,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        True,
        "storage_class":         "propellantless",
        "tank_kg_per_L":         0.0,
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             np.inf,
        "exhaust_vel_m_per_s":   np.inf,
        "density_kg_per_L":      np.nan,
        "ref_cost_usd_per_kg":   0.0,
        "ref_cost_usd_per_L":    0.0,
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Deflect the solar WIND rather than sunlight — Zubrin's "
                 "magsail, or Janhunen's electric sail with charged tethers. "
                 "Thrust per kilogram of hardware beats a photon sail beyond "
                 "~1 AU because solar-wind dynamic pressure falls more slowly "
                 "than the model's PV does.  ESTCube-1 (2013) and Aalto-1 "
                 "failed to deploy their tethers, so nothing has been "
                 "demonstrated in flight.  Excluded by propellantless=True for "
                 "the same reason as the photon sail.",
    },
    {
        "name":                  "Momentum-exchange tether",
        "type":                  "propellantless",
        "status":                "concept",
        "trl":                   4,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        True,
        "storage_class":         "propellantless",
        "tank_kg_per_L":         0.0,
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.0,
        "isp_vac_s":             np.inf,
        "exhaust_vel_m_per_s":   np.inf,
        "density_kg_per_L":      np.nan,
        "ref_cost_usd_per_kg":   0.0,
        "ref_cost_usd_per_L":    0.0,
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "A rotating tether catches a payload and throws it, moving "
                 "momentum between cargoes instead of expending propellant. "
                 "YES2 (2007) deployed 31.7 km of tether and reentered a "
                 "capsule; HASTOL and MXER were studied to PDR.  Genuinely "
                 "propellantless for a two-way traffic pattern, which is exactly "
                 "what a mining programme is — but it is INFRASTRUCTURE with its "
                 "own capital cost and orbit, not a propellant a spacecraft "
                 "carries, and this pipeline has no way to amortise a facility "
                 "across missions.  That is the modelling gap, not the physics.",
    },
    {
        "name":                  "Beamed laser-thermal  (H2)",
        "type":                  "beamed_energy",
        "status":                "concept",
        "trl":                   3,
        "first_flight":          None,
        "restartable":           True,
        "propellantless":        False,
        "storage_class":         "deep_cryogen",
        "tank_kg_per_L":         _tank_kg_per_L("deep_cryogen"),
        "isru_feed_kg_per_kg":   None,
        "isru_feed_material":    None,
        "dv_penalty_factor":     1.0,
        "boiloff_pct_per_day":   0.05,
        "isp_vac_s":             900,
        "exhaust_vel_m_per_s":   900 * G0_M_S2,
        "density_kg_per_L":      _COMPONENTS["LH2"]["density_kg_per_L"],
        "ref_cost_usd_per_kg":   _COMPONENTS["LH2"]["cost_usd_per_kg"],
        "ref_cost_usd_per_L":    _COMPONENTS["LH2"]["cost_usd_per_kg"]
                                 * _COMPONENTS["LH2"]["density_kg_per_L"],
        "yfinance_proxy":        None,
        "reference_year":        _REF_YEAR_PROP,
        "notes": "Leave the power plant at home and beam it: NTP's Isp with no "
                 "reactor aboard.  Kare's laser-thermal work and the 2022 "
                 "McGill/UCLA laser-thermal Mars study put Isp near 900 s.  Same "
                 "amortisation problem as the tether — the expensive part is a "
                 "ground or orbital laser array shared across missions, which "
                 "this pipeline cannot represent.",
    },
]

say(f"OK  Propellant reference loaded - {len(PROPELLANTS_REFERENCE)} fuel systems "
      f"({sum(1 for p in PROPELLANTS_REFERENCE if p['status'] == 'operational')} operational, "
      f"{sum(1 for p in PROPELLANTS_REFERENCE if p['status'] == 'development')} development, "
      f"{sum(1 for p in PROPELLANTS_REFERENCE if p['status'] == 'concept')} concept, "
      f"{sum(1 for p in PROPELLANTS_REFERENCE if p['status'] == 'retired')} retired)")
