# -*- coding: utf-8 -*-
"""Fairing volumes for the launch table: every figure derived from a cited drawing.

`fairing_volume_m3` is the USABLE payload envelope under the fairing -- the
volume a spacecraft may occupy -- not the fairing's outer volume.  Until
pipeline_version 1.17.0 it was typed on 39 of the 76 launch rows with no source
and blank on the other 37, and a consumer that fills a blank with a default
(economicspace Stage 4 used 100 m3) was pricing a third of the table on a
number nobody had chosen.

Every row now takes its volume from here, and `fairing_basis` says how:

    guide       the manufacturer's user's guide draws the usable envelope with
                its dimensions printed; the volume is that drawing revolved
                about the vehicle axis (`envelope_m3`).
    published   the manufacturer states the usable volume as a number.
    estimate    only the fairing's OUTER diameter and length are published;
                the volume is that cylinder times `FAIRING_FILL_RATIO`, the
                median envelope-to-outer-cylinder ratio of the guide rows below
                that print both.  Derived, never typed.
    none        no usable volume, envelope or outer length is published (or
                the row has no fairing at all); the column is NaN and the
                reason is in the row's notes.

HOW A DRAWING BECOMES A VOLUME.  An envelope is a list of (height, diameter)
points up the vehicle axis, in metres, from the drawing's own datum (the
separation or interface plane it is dimensioned from).  Consecutive points are
joined by straight lines and the outline is revolved: each pair is a frustum,
two points at one height are a step.  A nose drawn as a circular arc with a
printed radius is followed along the arc (`_arc`, `_tangent_ogive`); a cone
drawn with a printed half-angle takes its top diameter from the angle.  Where a
drawing does not print the diameter at the very top, the outline is closed to
a point, which can only under-count.  Access-door notches and "negotiable"
or "specific allocation" zones are left out: the envelope is what a customer
may use without asking.

Two guides also print a total, and the method reproduces both, which is the
check that the geometry is being read right: New Glenn's 458 m3 (Blue Origin
Payload User's Guide Rev C, Fig 5-2) and SLS Block 1B's 621 m3 (NASA ESD 30000
Fig 6-7).  Both are asserted at import.
"""

import math
import statistics
from typing import Dict, List, Sequence, Tuple

from ._log import say

Profile = List[Tuple[float, float]]


# ─────────────────────────────────────────────────────────────────────────────
# GEOMETRY
# ─────────────────────────────────────────────────────────────────────────────
_ARC_STEPS = 64     # chords per drawn arc; a chord only ever cuts inside an arc


def envelope_m3(profile: Sequence[Tuple[float, float]]) -> float:
    """Volume of `profile` revolved about the axis: (height m, diameter m) points."""
    total = 0.0
    for (z0, d0), (z1, d1) in zip(profile, profile[1:]):
        if z1 < z0:
            raise ValueError(f"envelope heights must not decrease: {z0} then {z1}")
        total += math.pi * (z1 - z0) / 12.0 * (d0 * d0 + d0 * d1 + d1 * d1)
    return total


def _arc(z0: float, d0: float, z1: float, d1: float, rho: float) -> Profile:
    """Points on the circular arc of radius `rho` from (z0, d0) to (z1, d1),
    bulging away from the axis, as a nose drawn with a printed radius does."""
    r0, r1 = d0 / 2.0, d1 / 2.0
    dz, dr = z1 - z0, r1 - r0
    chord = math.hypot(dz, dr)
    if chord > 2.0 * rho:
        raise ValueError(f"no arc of radius {rho} spans a chord of {chord:.3f}")
    offset = math.sqrt(rho * rho - chord * chord / 4.0)
    nz, nr = dr / chord, -dz / chord            # normal to the chord ...
    if nr > 0:
        nz, nr = -nz, -nr                       # ... on the axis side
    cz, cr = (z0 + z1) / 2.0 + nz * offset, (r0 + r1) / 2.0 + nr * offset
    a0, a1 = math.atan2(r0 - cr, z0 - cz), math.atan2(r1 - cr, z1 - cz)
    return [(cz + rho * math.cos(a0 + (a1 - a0) * i / _ARC_STEPS),
             2.0 * (cr + rho * math.sin(a0 + (a1 - a0) * i / _ARC_STEPS)))
            for i in range(_ARC_STEPS + 1)]


def _tangent_ogive(z0: float, d0: float, rho: float, z1: float) -> Profile:
    """A tangent ogive of radius `rho` rising from a cylinder of diameter `d0`
    at height `z0`, followed up to height `z1`."""
    r0 = d0 / 2.0
    out = []
    for i in range(_ARC_STEPS + 1):
        x = (z1 - z0) * i / _ARC_STEPS
        out.append((z0 + x, 2.0 * (math.sqrt(rho * rho - x * x) + r0 - rho)))
    return out


def _cone_top(d0: float, height: float, half_angle_deg: float) -> float:
    """Top diameter of a cone section drawn with a printed half-angle."""
    return d0 - 2.0 * height * math.tan(math.radians(half_angle_deg))


def _cylinder_m3(diameter: float, length: float) -> float:
    return math.pi / 4.0 * diameter * diameter * length


# ─────────────────────────────────────────────────────────────────────────────
# ENVELOPES DRAWN IN A USER'S GUIDE
# ─────────────────────────────────────────────────────────────────────────────
# Each entry: (profile, citation).  Every number in a profile is printed on the
# cited figure, in millimetres or inches there and metres here.

_FALCON = (
    [(0.0, 4.5725), (6.6796, 4.5725)]
    + _tangent_ogive(6.6796, 4.5725, 6.8189, 11.3635)[1:],
    "SpaceX Falcon User's Guide (Sep 2021), Fig 12-5, payload static envelope "
    "of the standard fairing: 4,572.5 mm to ST 6,679.6, then a tangent ogive "
    "of R 6,818.9 to ST 11,363.5 (the R 771.9 nose cap above it is left out)",
)

_VULCAN = (
    # Stations in inches, datum the 1575 PAF interface at LV STA 2596.66.
    [(0.0, 4.877), (6.6040, 4.648), (9.3980, 3.632), (12.8016, 0.838)],
    "ULA Vulcan Launch Systems User's Guide (Oct 2023), Fig 4.3.1-1, static "
    "payload envelope of the 15.5-m PLF, the standard offering (s4.3); "
    "negotiable zones excluded",
)

_SOYUZ_ST = (
    # Above the Fregat interface.  The 3,720 -> 3,800 mm step is taken at the
    # printed 980 mm mark.
    [(0.310, 3.72), (0.980, 3.72), (0.980, 3.80), (5.370, 3.80),
     (7.530, 2.68)],
    "Arianespace Soyuz CSG User's Manual Issue 2 (Mar 2012), Fig 5.3.1a, ST "
    "fairing volume -- the fairing flown commercially from Baikonur and "
    "Vostochny as well as Kourou; the 'specific volume allocation' in the nose "
    "is excluded",
)

_DELTA_IV_5M_19 = (
    [(0.0, 4.572), (10.988, 4.572), (15.715, 1.322)],
    "Boeing Launch Services, Delta IV Technical Summary, 'Delta IV Payload "
    "Fairing Envelopes': Heavy, 5-m composite fairing, 19.1 m (1194-5 PAF)",
)

ENVELOPES: Dict[str, Tuple[Profile, str]] = {
    "Falcon 9 (reusable)":                 _FALCON,
    "Falcon 9 (expendable)":               _FALCON,
    "Falcon Heavy (reusable side cores)":  _FALCON,
    "Falcon Heavy (expendable)":           _FALCON,
    "SLS Block 1": (
        _DELTA_IV_5M_19[0],
        "NASA SLS Mission Planner's Guide ESD 30000 Rev A (Dec 2018) s6.2.1: "
        "a Block 1 cargo flight takes the 5-m class composite fairing and "
        "refers to the Delta IV User's Guide for it -- a reference "
        "configuration that has never flown; envelope from "
        + _DELTA_IV_5M_19[1],
    ),
    "Atlas V 551": (
        [(0.0, 4.572), (4.8882, 4.572), (6.2123, 4.1336), (7.5363, 3.4742),
         (8.8603, 2.5842), (10.1844, 0.0)],
        "ULA Atlas V Launch Services User's Guide Rev 11 (Mar 2010), Fig 6-4, "
        "5-m Short static payload envelope; 500-series performance is quoted "
        "with the 5-m Short PLF (s2.5.2.2)",
    ),
    "Vulcan Centaur VC2":                  _VULCAN,
    "Vulcan Centaur VC4":                  _VULCAN,
    "Vulcan Centaur VC6":                  _VULCAN,
    "New Glenn": (
        [(0.0, 1.6256), (0.2032, 1.6256), (0.2032, 6.35), (6.5862, 6.35),
         (10.7239, 6.2281), (13.2639, 5.4508), (15.8039, 3.9065),
         (17.8359, 2.1336)],
        "Blue Origin New Glenn Payload User's Guide Rev C (Oct 2018), "
        "Fig 5-2, standard capacity standard payload volume (the guide states "
        "458 m3)",
    ),
    "Electron": (
        [(0.0, 1.070), (0.5661, 1.070), (0.717, 1.0421), (0.868, 0.9922),
         (1.0189, 0.930), (1.1699, 0.8554), (1.3208, 0.7679),
         (1.4718, 0.667), (1.6227, 0.5523), (1.7737, 0.423), (1.9246, 0.0)],
        "Rocket Lab Electron Payload User's Guide 7.0, 'Standard Fairing' "
        "envelope (p26)",
    ),
    "Alpha": (
        [(0.0, 1.6), (0.38, 2.0), (2.88, 2.0)]
        + _tangent_ogive(2.88, 2.0, 2.0, 4.48)[1:],
        "Firefly Alpha Payload User's Guide v2.0 (Aug 2019), Fig 8: 1.6 m "
        "rising to 2 m over 0.38 m, 2 m for 2.5 m, then an ogive of R 2 m "
        "for 1.6 m",
    ),
    "Minotaur IV": (
        [(0.0, 2.055), (2.877, 2.055), (4.401, 1.334), (5.277, 0.0)],
        "Northrop Grumman Minotaur IV/V/VI User's Guide Release 2.5 "
        "(Nov 2025), Fig 5.1.1.1-1, dynamic envelope of the standard 92-in "
        "fairing with the 38-in PAF",
    ),
    "Soyuz-2.1a":                          _SOYUZ_ST,
    "Soyuz-2.1b":                          _SOYUZ_ST,
    "Proton-M": (
        [(0.0, 3.81), (5.898, 3.81), (10.174, 1.25), (11.416, 0.128)],
        "ILS Proton Mission Planner's Guide LKEB-9812-1990 Rev 7 (Jul 2009), "
        "Fig E.1-1b, payload envelope under the PLF-BR-15255 fairing with "
        "the 937VB-1168 adapter",
    ),
    "Ariane 6 (A62)": (
        [(0.0, 4.6), (5.0, 4.6), (6.125, 4.33), (8.142, 3.45),
         (9.042, 2.89), (10.142, 2.33), (11.815, 0.0)],
        "Arianespace Ariane 6 User's Manual Issue 2 Rev 0 (Feb 2021), "
        "Fig 5.3.1a, usable volume under the short fairing (A62 only)",
    ),
    "Ariane 6 (A64)": (
        [(0.0, 4.6), (5.943, 4.6), (6.113, 4.7), (10.150, 4.7),
         (10.150, 4.6), (11.185, 4.6), (14.327, 3.45), (15.227, 2.89),
         (16.327, 2.33), (18.0, 0.0)],
        "Arianespace Ariane 6 User's Manual Issue 2 Rev 0 (Feb 2021), "
        "Fig 5.3.1b, usable volume under the long fairing; the 'usable volume "
        "extension, subject to specific analysis' is excluded",
    ),
    "Vega C": (
        [(0.0, 3.05), (3.914, 3.05)] + _arc(3.914, 3.05, 6.203, 1.0, 4.226)[1:],
        "Arianespace Vega C User's Manual Issue 0 Rev 0 (May 2018), "
        "Fig 5.3.1.a, usable volume with the VAMPIRE 937 adapter",
    ),
    "Long March 2C": (
        [(0.0, 3.0), (3.605, 3.0), (5.805, 1.823)],
        "CALT LM-2C User's Manual (Issue 1999), ch. 4, Fig 4-2a, two-stage "
        "fairing static envelope with the 1194A interface",
    ),
    "Long March 3B/E": (
        [(0.0, 3.65), (4.610, 3.65), (6.110, _cone_top(3.65, 1.5, 15.0)),
         (6.670, 2.323)],
        "CGWIC LM-3A Series Launch Vehicle User's Manual (Issue 2011), "
        "Fig 4-5b, 4000F fairing static envelope (the LM-3BE's 5,500 kg GTO "
        "is quoted with the 4000F, s3.5.2.1); the 15 deg section's top "
        "diameter is taken from its printed angle",
    ),
    "Ceres-1": (
        [(0.0, 1.4), (1.4, 1.4), (2.5, 1.0)],
        "Galactic Energy, Ceres-1 (谷神星一号) Launch Vehicle User's Manual "
        "(2023), s05 fairing and payload envelope figure",
    ),
    "Pallas-1": (
        [(0.0, 3.8), (4.913, 3.8), (7.800, 2.0)],
        "Galactic Energy, Pallas-1 (智神星一号) User's Manual (2023), "
        "Fig 6(b), payload envelope under the 4,200 mm fairing; the "
        "von Karman nose is taken along its chord",
    ),
    "Delta IV Heavy":                      _DELTA_IV_5M_19,
    "H-IIA 204": (
        [(0.0, 3.7), (5.8, 3.7), (10.23, _cone_top(3.7, 4.43, 18.0))],
        "MHI H-IIA User's Manual YET04001 Ver. 4.0, Fig 4.5-2, usable volume "
        "of the Model 4S fairing (H2A204's 5,950 kg standard GTO is quoted "
        "with the 4S, Table 2.1-1); the 18 deg cone's top diameter is taken "
        "from its printed angle",
    ),
    "Pegasus XL": (
        [(0.0, 1.168), (1.110, 1.168)]
        + _arc(1.110, 1.168, 2.138, 0.726, 2.692)[1:],
        "Northrop Grumman Pegasus User's Guide Release 8.2 (Sep 2020), "
        "Fig 5-2, payload fairing dynamic envelope with the 38-in "
        "separation system",
    ),
    "Ariane 5 ECA": (
        [(0.0, 4.57), (5.767, 4.57), (10.039, 4.48), (12.089, 3.65),
         (12.959, 3.10), (14.089, 2.55), (15.589, 1.013)],
        "Arianespace Ariane 5 User's Manual Issue 5 Rev 1 (Jul 2011), "
        "Annex 5, Fig A5.1, usable volume beneath the fairing in single "
        "launch",
    ),
    "Vega": (
        [(0.0, 2.363), (0.449, 2.363), (0.449, 2.307), (3.180, 2.307)]
        + _arc(3.180, 2.307, 5.965, 0.536, 6.183)[1:],
        "Arianespace Vega User's Manual Issue 4 (Apr 2014), Fig 5.3.2a, "
        "usable volume inside the Vega fairing",
    ),
    "Space Shuttle": (
        # 180 in x 720 in.
        [(0.0, 4.572), (18.288, 4.572)],
        "NASA NSTS 21492, Space Shuttle Program Payload Bay Payload User's "
        "Guide, s4.0: maximum payload dimensions 720 in long by 180 in in "
        "diameter, 'a volume of 10,600 cubic feet'.  The same sentence's "
        "'306.6 m3' and '18.46 m' disagree with its own inches and cubic "
        "feet; the inches are used",
    ),
    "Starship (projected)": (
        [(0.0, 8.0), (8.0, 8.0), (9.0, 7.70), (10.0, 7.36), (11.0, 6.98),
         (12.0, 6.54), (13.0, 6.08), (14.0, 5.56), (15.0, 5.02),
         (16.0, 4.40), (17.24, 3.60)],
        "SpaceX Starship Users Guide Rev 1.0 (Mar 2020), Fig 4, payload "
        "dynamic envelope, radii printed at 1 m stations",
    ),
    "Neutron": (
        [(0.0, 4.7915), (4.5632, 4.7915), (4.5632, 5.5799),
         (6.3187, 5.5799), (9.1698, 3.7067), (11.6497, 0.0)],
        "Rocket Lab Neutron Payload User's Guide v1.0 (Jan 2025), Fig 13, "
        "payload accommodation; the nose is taken along its chords",
    ),
    "SLS Block 1B (Cargo)": (
        # From the 1.60 m minimum payload-adapter height, where NASA's volume
        # is measured; the drawing is dimensioned from the EUS interface.
        [(1.60, 7.5), (11.46, 7.5)] + _arc(11.46, 7.5, 18.11, 1.75, 9.14)[1:],
        "NASA SLS Mission Planner's Guide ESD 30000 Rev A (Dec 2018), "
        "Fig 6-7, composite 8.4 m PLF short concept, which states a maximum "
        "payload available volume of 621 m3",
    ),
    "Skylon / SABRE": (
        # A U-section bay, taken as the circle of its printed deployed-payload
        # radius over the mean of its 13.0 m top and 11.402 m floor.
        [(0.0, 4.70), (12.201, 4.70)],
        "Reaction Engines SKYLON Users' Manual Rev 1, Fig 13, payload "
        "envelope: 2,350 mm maximum radius, 13,000 mm long with 10 deg end "
        "clearances of 799 mm at the floor.  The polygonal section is "
        "approximated by that circle",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# VOLUMES THE MANUFACTURER STATES AS A NUMBER
# ─────────────────────────────────────────────────────────────────────────────
_FT3 = 0.0283168466

PUBLISHED: Dict[str, Tuple[float, str]] = {
    "LVM3 (GSLV Mk III)": (
        110.0,
        "VSSC (ISRO), GSLV MkIII vehicle specifications: 'Heat Shield (Payload "
        "Fairing) Diameter 5.0 m, PLF Usable Volume 110m3'",
    ),
    "Gravity-1": (
        100.0,
        "Orienspace, via Tencent News 2023-11-22: the 4.2 m fairing 'has 100 "
        "cubic metres of payload space'.  This reads as the fairing's "
        "interior rather than a keep-in envelope: it is about 1.6x the median "
        "guide envelope for a fairing of this size",
    ),
    "Saturn V": (
        round(3230 * _FT3, 2),
        "Douglas SM-47274, Saturn V Payload Planner's Guide (Nov 1965), prime "
        "payload configuration 'A': the spacecraft/LEM adapter volume that "
        "flew, 'about 3,230 cubic feet' when the LEM is not carried",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# ONLY THE OUTSIDE OF THE FAIRING IS PUBLISHED
# ─────────────────────────────────────────────────────────────────────────────
# (outer diameter m, outer length m, citation)
OUTER_ONLY: Dict[str, Tuple[float, float, str]] = {
    "Angara A5": (
        4.35, 17.705,
        "RussianSpaceWeb (A. Zak), Angara-5: the 14S746 fairing first flown "
        "19 Jun 2025, 17.705 m long and 4.35 m in diameter; no usable "
        "envelope is published",
    ),
    "H3 (24L)": (
        5.2, 16.4,
        "Kawasaki Heavy Industries, H3 payload fairings: type L, 16.4 m by "
        "5.2 m; no usable envelope is published",
    ),
    "H3 (30)": (
        5.2, 10.4,
        "Kawasaki Heavy Industries, H3 payload fairings: type S (the H3-30S "
        "fairing), 10.4 m by 5.2 m; no usable envelope is published",
    ),
    "Long March 2D": (
        3.35, 6.983,
        "CGWIC, LM-2D technical data: fairing diameter 3.35 m, fairing "
        "length 6.983 m",
    ),
    "Long March 5": (
        5.2, 12.267,
        "Standard LM-5 fairing, 5.2 m by 12.267 m, as quoted from CALT's "
        "design office (Sohu, 2024-05-06); the 18.5 m and 20.5 m (5B) "
        "fairings are optional",
    ),
    "Long March 10B": (
        5.2, 12.5,
        "Tencent News 2026-07-13: the LM-10B's short fairing is 5.2 m by "
        "12.5 m, carried over from the LM-5; an 18.5 m fairing is optional",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# NOTHING TO DERIVE FROM
# ─────────────────────────────────────────────────────────────────────────────
NOT_PUBLISHED: Dict[str, str] = {
    "Spectrum":
        "Isar Aerospace gives its payload user's guide only on request",
    "PSLV-XL":
        "ISRO/VSSC publish the 3.2 m heat-shield diameter only",
    "GSLV Mk II":
        "ISRO publishes the 3.4 m and 4 m fairing diameters only",
    "SSLV":
        "NSIL publishes the 2.1 m fairing diameter only",
    "Nuri (KSLV-II)":
        "KARI publishes no fairing envelope or length",
    "Long March 4C":
        "CNSA publishes the 2.9, 3.35 and 3.8 m fairing diameters only",
    "Long March 6A":
        "SAST publishes the 3.8 and 4.2 m fairing diameters; its 4.2 m "
        "fairing's length is given only as 'nearly 4 m' plus 'about 5 m'",
    "Long March 7":
        "the two-stage LM-7 this row's LEO figure describes flies Tianzhou, "
        "which has no payload fairing; the LM-7A's 4.2 m fairing has no "
        "published length",
    "Long March 8A":
        "CASC publishes the 5.2 m fairing diameter only",
    "Long March 12":
        "CASC publishes the 4.2 and 5.2 m fairing diameters only",
    "Kuaizhou-1A":
        "ExPace publishes the 1.2 and 1.4 m fairing diameters only",
    "Kuaizhou-11":
        "ExPace publishes the 2.2 m fairing diameter only",
    "Kinetica-1":
        "CAS Space publishes the 2.65 and 3.35 m fairing diameters only",
    "Kinetica-2":
        "CAS Space publishes the fairing diameter only",
    "Jielong-3":
        "China Rocket publishes the 2.9 and 3.35 m fairing diameters only",
    "Zhuque-2E":
        "LandSpace publishes the 3.35 m fairing diameter only",
    "Zhuque-3":
        "LandSpace publishes the 5.2 m fairing diameter only",
    "New Glenn 9x4":
        "Blue Origin has given the 8.7 m diameter; no envelope or length has "
        "been published that could be read",
    "Terran R":
        "Relativity has published the fairing diameter only",
    "Nova":
        "Stoke Space has published no fairing envelope",
    "Eclipse (MLV)":
        "Firefly has published the 5.4 m diameter only",
    "Tianlong-3":
        "Space Pioneer has published no fairing envelope or length",
    "Long March 10":
        "CASC has published no fairing envelope for the three-core vehicle",
    "Long March 9":
        "CASC roadmap figures give no fairing envelope",
    "Soyuz-5":
        "RSC Energia has published no fairing envelope",
    "Epsilon S":
        "JAXA has not published the Epsilon S fairing envelope; the Epsilon "
        "User's Manual (2018) envelope is the older vehicle's",
    "Hyperbola-3":
        "i-Space has published the 5.2 m fairing diameter only",
    "SpinLaunch Orbital":
        "SpinLaunch has published no payload volume for the orbital vehicle",
    "Light-gas gun (orbital)":
        "a gun launcher is a projectile, not a fairing; no source gives a "
        "payload volume",
    "StarTram (maglev)":
        "the StarTram studies give no cargo-vehicle payload volume",
    "Sea Dragon":
        "the 1962 Aerojet study gives no payload bay dimensions",
    "Lunar mass driver":
        "a mass driver throws bulk material in buckets; it has no fairing, "
        "and its payload columns are annual throughput",
    "Lunar space elevator":
        "a tether climber has no fairing, and its payload columns are "
        "annual throughput",
    "Earth space elevator":
        "a tether climber has no fairing, and its payload columns are "
        "annual throughput",
}


# ─────────────────────────────────────────────────────────────────────────────
# THE FILL RATIO, DERIVED FROM THE GUIDE ROWS THAT PRINT BOTH
# ─────────────────────────────────────────────────────────────────────────────
# (guide row, outer diameter m, outer length m, where the outer size is printed)
_CALIBRATION: Tuple[Tuple[str, float, float, str], ...] = (
    ("Falcon 9 (reusable)", 5.2, 13.2, "Falcon User's Guide (May 2025) p16"),
    ("Proton-M", 4.35, 15.255, "PMPG Fig E.1-1b (PLF-BR-15255)"),
    ("Long March 3B/E", 4.0, 9.561, "LM-3A Series User's Manual s4.4"),
    ("Long March 2C", 3.35, 8.368, "LM-2C User's Manual ch. 4"),
    ("Atlas V 551", 5.4, 20.7, "Atlas V User's Guide 5-m PLF table (p26)"),
    ("Vulcan Centaur VC2", 5.4, 15.5, "Vulcan User's Guide s4.3"),
    ("H-IIA 204", 4.07, 12.0, "H-IIA User's Manual Table 1.3-1, Fig 4.5-2"),
    ("Alpha", 2.2, 5.0, "Alpha Payload User's Guide v2.0 p12"),
    ("Electron", 1.2, 2.5, "Electron Payload User's Guide 7.0 p12"),
    ("Ceres-1", 1.6, 5.0, "Ceres-1 User's Manual s05, 'about 5 m'"),
)

_ENVELOPE_M3: Dict[str, float] = {n: envelope_m3(p) for n, (p, _) in ENVELOPES.items()}

FILL_RATIOS: Dict[str, float] = {
    name: _ENVELOPE_M3[name] / _cylinder_m3(d, l)
    for name, d, l, _ in _CALIBRATION
}

# The median, so one fairing that also encloses an upper stage (Atlas V's 5-m
# fairing covers the Centaur) cannot drag every estimate with it.
FILL_RATIO_RANGE = (min(FILL_RATIOS.values()), max(FILL_RATIOS.values()))
FAIRING_FILL_RATIO = statistics.median(FILL_RATIOS.values())


# ─────────────────────────────────────────────────────────────────────────────
# THE PER-ROW RESULT
# ─────────────────────────────────────────────────────────────────────────────
def _round(v: float) -> float:
    """Three significant figures: the precision a drawing read this way earns."""
    if v <= 0 or not math.isfinite(v):
        return v
    return float(f"{v:.3g}")


def _build() -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    groups = (ENVELOPES, PUBLISHED, OUTER_ONLY, NOT_PUBLISHED)
    for name in {n for g in groups for n in g}:
        if sum(name in g for g in groups) != 1:
            raise ValueError(f"fairing source for {name!r} is stated twice")
    for name, (_, cite) in ENVELOPES.items():
        out[name] = {"volume": _round(_ENVELOPE_M3[name]), "basis": "guide",
                     "source": cite}
    for name, (vol, cite) in PUBLISHED.items():
        out[name] = {"volume": _round(vol), "basis": "published",
                     "source": cite}
    for name, (d, l, cite) in OUTER_ONLY.items():
        out[name] = {
            "volume": _round(FAIRING_FILL_RATIO * _cylinder_m3(d, l)),
            "basis": "estimate",
            "source": (f"{cite}.  Estimated as that cylinder x "
                       f"{FAIRING_FILL_RATIO:.3f}, the median usable-envelope "
                       f"fill of the guide-drawn fairings (range "
                       f"{FILL_RATIO_RANGE[0]:.2f}-{FILL_RATIO_RANGE[1]:.2f})"),
        }
    for name, why in NOT_PUBLISHED.items():
        out[name] = {"volume": float("nan"), "basis": "none",
                     "source": f"no usable volume: {why}"}
    return out


FAIRINGS: Dict[str, dict] = _build()


def _check_against_published_totals() -> None:
    """The two guides that print a total must come back from their drawing."""
    for name, stated in (("New Glenn", 458.0), ("SLS Block 1B (Cargo)", 621.0)):
        got = _ENVELOPE_M3[name]
        if abs(got / stated - 1.0) > 0.005:
            raise ValueError(
                f"{name}: envelope drawing gives {got:.1f} m3 against the "
                f"{stated:.0f} m3 its guide states; the profile is misread")


_check_against_published_totals()

say(f"OK  Fairing volumes derived - "
    f"{sum(f['basis'] == 'guide' for f in FAIRINGS.values())} from guide drawings, "
    f"{sum(f['basis'] == 'published' for f in FAIRINGS.values())} published, "
    f"{sum(f['basis'] == 'estimate' for f in FAIRINGS.values())} estimated, "
    f"{sum(f['basis'] == 'none' for f in FAIRINGS.values())} unpublished; "
    f"fill ratio {FAIRING_FILL_RATIO:.3f}")
