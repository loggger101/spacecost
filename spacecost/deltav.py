# -*- coding: utf-8 -*-
"""Mission delta-v reference table: trajectory segments in m/s, with durations.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

from typing import List

from ._log import say

# ─────────────────────────────────────────────────────────────────────────────
# MISSION Δv REFERENCE TABLE
# ─────────────────────────────────────────────────────────────────────────────
# Typical Δv (m/s) and trip duration (yr) for each segment of a round-trip
# asteroid mining mission.  Sources: NASA NTRS, JPL design handbooks,
# Asterank's mission-design statistics.  Δv values are representative
# means; Module 4 should override per-asteroid using the orbital elements
# from Module 1 (semi_major_axis_au, eccentricity, inclination) where
# tighter accuracy is needed.

DELTA_V_REFERENCE: List[dict] = [
    {"segment": "surface  →  LEO ascent",         "dv_m_per_s":  9_400, "duration_yr": 0.001,
     "notes": "Textbook value including gravity + drag losses (NASA SP-125, "
              "Curtis 'Orbital Mechanics for Engineering Students').  "
              "Already priced into LAUNCH_VEHICLES."},
    {"segment": "LEO  →  GTO",                    "dv_m_per_s":  2_440, "duration_yr": 0.001,
     "notes": "Standard GEO transfer Δv (NASA orbital mechanics handbook)."},
    {"segment": "LEO  →  Earth escape (C3=0)",    "dv_m_per_s":  3_200, "duration_yr": 0.003,
     "notes": "C3=0 escape from 200-km LEO; same magnitude as TLI."},
    {"segment": "LEO  →  easy NEA (low-Δv class)","dv_m_per_s":  4_500, "duration_yr": 1.0,
     "notes": "Per Elvis et al. 2011 (arXiv:1105.4152): ultra-low Δv NEAs are "
              "~65 of 6699 known NEOs as of 2010 — bottom decile of accessibility."},
    {"segment": "LEO  →  average NEA",            "dv_m_per_s":  6_500, "duration_yr": 1.5,
     "notes": "Median NEA Δv per low-Δv NEA survey (arXiv:1406.5027); "
              "matches OSIRIS-REx Bennu mission profile."},
    {"segment": "LEO  →  hard NEA",               "dv_m_per_s":  8_500, "duration_yr": 2.0,
     "notes": "Upper-decile NEA (inclined or eccentric); approaches MBA territory."},
    {"segment": "LEO  →  main-belt asteroid",     "dv_m_per_s": 10_500, "duration_yr": 3.5,
     "notes": "Per Taylor et al. 2018 'Δv map of Main Belt Asteroids' "
              "(Acta Astronautica 146:73) — Hohmann transfer to ~2.7 AU."},
    {"segment": "Asteroid station-keeping",       "dv_m_per_s":    200, "duration_yr": 0.5,
     "notes": "Proximity ops, sample retrieval — OSIRIS-REx station-keeping budget."},
    {"segment": "NEA  →  Earth return (propulsive)","dv_m_per_s":  5_500, "duration_yr": 1.5,
     "notes": "Symmetric to outbound; powered Earth-return with no aerobraking."},
    {"segment": "NEA  →  Earth return (aerocap)", "dv_m_per_s":  1_500, "duration_yr": 1.5,
     "notes": "Aerocapture reduces propulsive Δv by ~4 km/s (heat-shield mass "
              "penalty captured separately under operational_costs TPS row)."},
    {"segment": "Main belt  →  Earth return",     "dv_m_per_s":  7_500, "duration_yr": 4.0,
     "notes": "Per Taylor 2018 — long cruise; favours electric propulsion."},
    {"segment": "Lunar surface  →  LEO",          "dv_m_per_s":  5_900, "duration_yr": 0.01,
     "notes": "Apollo Lunar Module ascent + plane change — reference for lunar-relay arch."},

    # ── Delivery ladder above LEO  (v1.4.0) ──────────────────────────────────
    # These price the "launch cost avoided" for material sold in space, and
    # give Module 4 the return-leg budget for a non-Earth-surface delivery.
    {"segment": "LEO  →  TLI (trans-lunar injection)", "dv_m_per_s": 3_150, "duration_yr": 0.01,
     "notes": "Apollo TLI 3.05-3.20 km/s (NASA SP-4029 / Apollo-by-the-Numbers). "
              "Effectively the same burn as LEO→Earth-escape, 50 m/s cheaper "
              "because the Moon is bound rather than at C3=0."},
    {"segment": "TLI  →  NRHO insertion",         "dv_m_per_s":    450, "duration_yr": 0.01,
     "notes": "Near-rectilinear halo orbit insertion for Gateway / Orion, "
              "~0.4-0.45 km/s (NASA Gateway NRHO trade studies, Whitley & "
              "Martinez 2016 'Options for Staging Orbits in Cis-Lunar Space'). "
              "NRHO is the cheapest usefully-stable cislunar depot orbit."},
    {"segment": "LEO  →  cislunar NRHO depot",    "dv_m_per_s":  3_600, "duration_yr": 0.02,
     "notes": "TLI + NRHO insertion.  This is the Δv that a kilogram of "
              "asteroid material delivered to NRHO AVOIDS having to be lifted "
              "through — it sets the cislunar sale price in Module 2."},

    # ── Geostationary orbit  (v1.14.0) ────────────────────────────────
    # The one destination in this table with a paying customer today: ~550
    # active satellites, and MEV-1 and MEV-2 have already docked with and
    # station-kept commercial GEO spacecraft.
    #
    # ⚠️  The plane change is the term intuition drops.  A launch from
    # Canaveral parks at 28.5 deg and GEO is equatorial, so the apogee burn
    # buys the inclination as well as the circularisation, and it is 1,836 m/s
    # rather than the 1,478 a coplanar circularisation would cost.
    {"segment": "LEO  →  GTO (perigee burn)",     "dv_m_per_s":  2_455, "duration_yr": 0.001,
     "notes": "Perigee burn from a 200-km parking orbit onto a transfer "
              "ellipse with apogee at 42,164 km: v_p(GTO) 10.239 - v_LEO "
              "7.784 km/s.  Matches the ~2.44-2.46 km/s every GTO launch "
              "quotes."},
    {"segment": "GTO  →  GEO (circularise + plane change)", "dv_m_per_s": 1_836, "duration_yr": 0.01,
     "notes": "One apogee burn doing two jobs: raise 1.597 km/s to the 3.075 "
              "km/s circular speed AND remove 28.5 deg of inclination, "
              "combined by the law of cosines rather than added.  Coplanar it "
              "would be 1,478; the 358 m/s difference is what an equatorial "
              "launch site is worth."},
    {"segment": "LEO  →  GEO depot",              "dv_m_per_s":  4_291, "duration_yr": 0.01,
     "notes": "GTO (2,455) + apogee (1,836).  This is the Δv a kilogram "
              "delivered to a GEO servicing depot AVOIDS being lifted "
              "through, and it sets the geo sale price in Module 2.  Flown as "
              "TWO stages there, and staging is worth 5.3%: 2.945 kg in LEO "
              "per kg at GEO against 3.101 single-stage."},
    {"segment": "GEO  →  Earth (deorbit to entry)", "dv_m_per_s": 1_488, "duration_yr": 0.01,
     "notes": "Lowering perigee from GEO into the atmosphere: 3.075 circular "
              "down to the 1.587 km/s apogee speed of an entry ellipse.  "
              "Twelve times the LEO deorbit burn, because the whole point of "
              "GEO is that it is a long way up."},

    # ── Lunar surface  (v1.5.0) ──────────────────────────────────────────────
    {"segment": "TLI  →  low lunar orbit (LOI)", "dv_m_per_s":    900, "duration_yr": 0.01,
     "notes": "Apollo lunar-orbit insertion, 0.9 km/s (NASA SP-4029).  Larger "
              "than NRHO insertion because LLO is a much more tightly bound "
              "orbit — which is exactly why NRHO is the cheaper depot."},
    {"segment": "NRHO  →  low lunar orbit",      "dv_m_per_s":    730, "duration_yr": 0.01,
     "notes": "Gateway-to-LLO transfer, ~0.73 km/s (Whitley & Martinez 2016). "
              "The price a cislunar depot pays to service the surface."},
    {"segment": "LLO  →  lunar surface (descent)", "dv_m_per_s": 1_870, "duration_yr": 0.001,
     "notes": "Apollo LM powered descent, 1.87 km/s including hover and "
              "terminal guidance reserve (NASA SP-4029).  No atmosphere means "
              "no aerobraking is available — every metre per second is paid "
              "for propulsively, which is why the Moon is expensive to reach "
              "despite being close."},
    {"segment": "LEO  →  lunar surface",         "dv_m_per_s":  5_920, "duration_yr": 0.02,
     "notes": "TLI (3,150) + LOI (900) + descent (1,870).  Sets the "
              "lunar-base sale price in Module 2.  Apollo's LEO-to-surface "
              "budget was ~6 km/s, which this matches."},

    # ── Mars  (v1.5.0) ───────────────────────────────────────────────────────
    {"segment": "LEO  →  trans-Mars injection",  "dv_m_per_s":  3_600, "duration_yr": 0.7,
     "notes": "Minimum-energy Hohmann TMI at a favourable opportunity; the "
              "real figure swings 3.6-4.3 km/s across the 26-month synodic "
              "cycle (NASA DRA 5.0).  The low end is used, so the delivered "
              "cost is a LOWER bound."},
    {"segment": "Mars entry  →  surface (retroprop)", "dv_m_per_s": 800, "duration_yr": 0.001,
     "notes": "Terminal propulsive descent after aeroentry and parachutes. "
              "MSL's sky-crane phase used ~0.4 km/s; Starship-class EDL "
              "estimates run 0.5-1.0 km/s for supersonic retropropulsion of a "
              "heavy lander.  Mid-range taken.  The aeroshell and parachute "
              "mass is carried separately as a landed-mass fraction — see "
              "Module 2's _MARS_LANDED_MASS_FRACTION."},
    {"segment": "Mars surface  →  low Mars orbit", "dv_m_per_s": 4_100, "duration_yr": 0.001,
     "notes": "Mars ascent including gravity and drag losses (NASA DRA 5.0 "
              "MAV sizing).  Relevant only to the downleg — shipping material "
              "OFF Mars — and it is brutal enough that nothing mined for a "
              "Mars base is worth flying home."},
    {"segment": "Low Mars orbit  →  Earth (TEI)", "dv_m_per_s": 2_100, "duration_yr": 0.7,
     "notes": "Trans-Earth injection from LMO (NASA DRA 5.0)."},

    # ── Mars orbit depot  (v1.13.0) ─────────────────────────────────────
    # The 1-sol elliptical staging orbit, 250 x 33,793 km altitude, is where
    # NASA DRA 5.0 parks a Mars vehicle.  Its period matches a sol (24.60 h
    # against 24.62), and capture only has to BIND the orbit rather than
    # circularise it.  That is the same argument NRHO wins on in cislunar
    # space, and here it is worth 1.2 km/s against low Mars orbit.
    #
    # ⚠️  These three rows are the citation home for Module 2's
    # _DELIVERY_LEGS["mars_orbit"] and Module 4's _MARS_1SOL constants.  The
    # rule stated above _DELIVERY_LEGS is that every Δv it charges appears
    # here; if you retune the depot orbit, retune it in this table first.
    {"segment": "Mars arrival  →  1-sol orbit (MOI)", "dv_m_per_s": 900, "duration_yr": 0.01,
     "notes": "Propulsive capture into the 250 x 33,793 km 1-sol orbit at a "
              "Hohmann arrival v_infinity of 2.65 km/s (NASA DRA 5.0).  The "
              "periapsis burn sqrt(v_esc^2 + v_inf^2) - v_ellipse at a radius "
              "of 3,646 km is 0.90 km/s, against 2.10 km/s to circularise "
              "into a 200-km orbit at the same arrival energy.  The saving is "
              "the apoapsis that is never brought down."},
    {"segment": "LEO  →  Mars 1-sol orbit depot", "dv_m_per_s": 4_500, "duration_yr": 0.7,
     "notes": "TMI (3,600) + MOI (900).  This is the Δv a kilogram of asteroid "
              "material delivered to a Mars-orbit depot AVOIDS being lifted "
              "through, and it sets the mars_orbit sale price in Module 2.  "
              "Nothing enters the atmosphere and nothing lands, so unlike "
              "mars_surface there is no 30% entry-survival fraction stacked "
              "on top of it."},
    {"segment": "1-sol Mars orbit  →  Earth (TEI)", "dv_m_per_s": 900, "duration_yr": 0.7,
     "notes": "Trans-Earth injection at periapsis, symmetric with MOI.  A "
              "seventh of the 6,200 m/s a kilogram on the SURFACE has to pay "
              "(4,100 ascent + 2,100 TEI from LMO), which is why material "
              "mined for a Mars-orbit depot can still route home when "
              "material landed on Mars cannot."},

    # ── Asteroid return legs by delivery destination  (v1.4.0) ───────────────
    # Reference magnitudes only; Module 4 computes these per-asteroid from the
    # actual arrival v_infinity.  Quoted here at v_inf = 3 km/s, a typical NEA
    # return, so the three architectures can be compared at a glance.
    {"segment": "NEA  →  LEO delivery (propulsive)", "dv_m_per_s": 3_626, "duration_yr": 1.5,
     "notes": "Circularising into LEO from a v_inf=3 km/s arrival hyperbola: "
              "sqrt(v_esc^2 + v_inf^2) - v_circ at 200 km.  The most expensive "
              "destination to reach propulsively — LEO sits deepest in the well "
              "of the three, which is exactly why material there is worth most "
              "per kg and costs most to deliver.  Computed by Module 4's "
              "_leo_departure_dv_km_s; excludes the asteroid-departure burn."},
    {"segment": "NEA  →  cislunar NRHO (Oberth capture)", "dv_m_per_s": 944, "duration_yr": 1.6,
     "notes": "Capture at a low perigee into an ellipse reaching lunar distance "
              "(494 m/s at v_inf=3 km/s, taking the Oberth benefit of burning "
              "deep in the well), then NRHO insertion at apogee (450 m/s). "
              "3.8x cheaper than propulsive LEO capture, and the destination "
              "is worth MORE per kg — the two effects compound.  Computed by "
              "Module 4's _cislunar_capture_dv_km_s; excludes the "
              "asteroid-departure burn.  The advantage widens as arrival "
              "energy falls: 5.6x at v_inf=1 km/s, 2.7x at 5 km/s."},
    {"segment": "NEA  →  LEO delivery (aerobraked)", "dv_m_per_s": 100, "duration_yr": 2.0,
     "notes": "Aerocapture into a high ellipse, then multi-pass aerobraking to "
              "circularise; drag does the work, so the propulsive cost is only "
              "the periapsis-raise burn out of the atmosphere.  Mars Odyssey / "
              "MRO flew this for real, saving ~1.2 km/s over ~6 months of "
              "passes (JPL).  Buys Δv with TPS mass and MONTHS of time — the "
              "duration figure carries that."},
]

say(f"OK  Mission dv reference loaded - {len(DELTA_V_REFERENCE)} trajectory segments")
