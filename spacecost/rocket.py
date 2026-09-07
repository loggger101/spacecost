# -*- coding: utf-8 -*-
"""Tsiolkovsky helpers: propellant mass for a delta-v, and cost per delta-v.

Extracted verbatim from economicspace modules/transportation.py, pipeline_version 1.14.0,
commit b0b18b2de301653ee23de1bd3779867ae5b617a1 (2026-09-04).
"""

import numpy as np

from .units import G0_M_S2


# ─────────────────────────────────────────────────────────────────────────────
# ROCKET-EQUATION HELPERS
# ─────────────────────────────────────────────────────────────────────────────
# The Tsiolkovsky rocket equation gives the mass of propellant required to
# impart a given Δv to a payload:
#
#       Δv = Isp · g₀ · ln(m₀ / m_f)
#   ⇒   m_prop  =  m_payload · (exp(Δv / (Isp · g₀)) − 1)
#
# These helpers are what Module 4 will use to convert orbital geometry into
# USD.  Vectorised, accept arrays or scalars indifferently.

def propellant_mass_for_dv(
    payload_kg, delta_v_m_per_s, isp_s, g0=G0_M_S2,
):
    """
    Mass of propellant required to push `payload_kg` through `delta_v_m_per_s`
    using a stage with vacuum specific impulse `isp_s`.

    Returns the propellant mass (kg).  Vectorised over arrays.
    """
    mass_ratio = np.exp(np.asarray(delta_v_m_per_s) / (np.asarray(isp_s) * g0))
    return np.asarray(payload_kg) * (mass_ratio - 1.0)


def cost_per_dv_usd_per_kg(
    propellant_cost_usd_per_kg, isp_s, delta_v_m_per_s, g0=G0_M_S2,
):
    """
    The headline normalised metric.  Returns the USD of propellant required
    to move 1 kg of payload through `delta_v_m_per_s` using this propellant.

    This is the rocket equivalent of "fuel cost per km" for a car.
    """
    m_prop_per_kg_payload = propellant_mass_for_dv(
        1.0, delta_v_m_per_s, isp_s, g0,
    )
    return float(m_prop_per_kg_payload) * float(propellant_cost_usd_per_kg)
