"""Modules 4.3 and 4.5 -- intra-nodule coverage and dosing (migrated from 9.23).

**4.3** 9.23's findings 2, 3 and 5: the effector field is flat within a nodule
(core:rim 1.01-1.03x) because every diffusion length dwarfs the 400 µm nodule;
flat coverage is the therapeutically useful outcome; and SsrA "buys spatial
confinement", shortening the effector range from 671 µm to 300 µm, i.e. from
larger than the nodule to smaller.

**4.5** Module 5 of 9.23: cumulative exposure varies by < 0.1 % across dosing
schedules because the colony is capacity-limited, so the lever is persistence
rather than schedule.

Two corrections come out of re-deriving these with module 4.4's closed form.

Correction 1 -- where SsrA's safety benefit actually comes from
---------------------------------------------------------------
The escape fraction (how much of what is produced inside the nodule is destroyed
*outside* it, i.e. surrounding-tissue exposure) is computable in closed form::

    escape(R, lambda) = 3 g(alpha) (1 + alpha) exp(-alpha) / alpha**3,  alpha = R/lambda

with ``g`` the same exterior amplitude module 4.4 uses. For a 400 µm nodule it
gives 91.1 % untagged and 73.2 % tagged -- so **both leak heavily**, and the
671 -> 300 µm change moves off-target exposure per molecule produced by only
1.24x. Retention improves 3.0x, which is real, but it is not the main effect.

What dominates is that the tag also cuts the intracellular pool 5.375x (module
3.4). Combining: off-target exposure falls 6.7x, of which 5.4x is *making less*
and 1.24x is *confining it*. **About 80 % of SsrA's spatial safety benefit is
production reduction, not confinement.**

Correction 2 -- flatness is a boundary condition, not a diffusion length
------------------------------------------------------------------------
9.23 attributes intra-nodule flatness to the diffusion lengths dwarfing the
nodule. That is not sufficient. In a *bounded* domain with washout at the rim,
a long diffusion length does homogenise the field. In free diffusion into
surrounding tissue with the same decay rate, the same parameters give a graded
field: 1.57x core:rim for AHL and **2.08x for the tagged effector**, whose
diffusion length (300 µm) is *shorter* than the nodule radius anyway.

So finding 3 -- "flat coverage spares nothing, which is what we want" -- rests
on the Robin washout boundary, not on the length scales. The truth sits between
the two boundary conditions, and this module reports both rather than picking.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import multilesion as ML

#: Nodule radius 9.23 used throughout, µm.
NODULE_RADIUS_UM: float = 400.0

#: Diffusion lengths from 9.23 `run_manifest.json`, µm.
DIFFUSION_LENGTHS_UM: dict[str, float] = {
    "lactate": 5099.0,
    "AHL": 3000.0,
    "GSDMD-N (no SsrA)": 670.8,
    "GSDMD-N (+SsrA)": 300.0,
}

#: Intracellular pool ratio untagged/tagged, from module 3.4's TradeoffModel.
POOL_RATIO_UNTAGGED_OVER_TAGGED: float = 5.375

#: 9.23's reported core:rim ratios under its own bounded-domain solver.
CORE_RIM_9_23: dict[str, float] = {"activation": 1.011, "gsdmd": 1.021}


def escape_fraction(radius_um: float = NODULE_RADIUS_UM, diffusion_length_um: float = 300.0) -> float:
    """Fraction of production destroyed outside the nodule.

    Steady state means total production equals total decay, so this is the share
    of the decay integral lying beyond ``r = radius_um``. Closed form::

        3 g(a) (1 + a) exp(-a) / a**3
    """
    alpha = radius_um / diffusion_length_um
    amplitude = float(ML._outside_amplitude(alpha))
    return float(3.0 * amplitude * (1.0 + alpha) * np.exp(-alpha) / alpha**3)


def core_rim_ratio_free_field(
    radius_um: float = NODULE_RADIUS_UM, diffusion_length_um: float = 300.0
) -> float:
    """Centre-over-edge concentration for a uniform source diffusing into tissue."""
    field = ML.AHLField(diffusion_length_um=diffusion_length_um)
    centre = float(field.centre_of_isolated(radius_um))
    edge = float(field.inside(radius_um, radius_um))
    return centre / edge


def length_scale_table(radius_um: float = NODULE_RADIUS_UM) -> pd.DataFrame:
    """9.23's finding-2 table, with escape and free-field gradient added."""
    rows = []
    for species, length in DIFFUSION_LENGTHS_UM.items():
        rows.append(
            {
                "species": species,
                "diffusion_length_um": length,
                "length_over_radius": length / radius_um,
                "escape_fraction": escape_fraction(radius_um, length),
                "core_rim_free_field": core_rim_ratio_free_field(radius_um, length),
            }
        )
    frame = pd.DataFrame(rows)
    frame["shorter_than_nodule"] = frame["diffusion_length_um"] < radius_um
    return frame


@dataclass(frozen=True)
class SsrASpatialBenefit:
    """Decomposition of what the degron buys spatially."""

    retention_gain: float
    confinement_gain: float
    production_gain: float

    @property
    def total_offtarget_reduction(self) -> float:
        return self.production_gain * self.confinement_gain

    @property
    def confinement_share(self) -> float:
        """Share of the total benefit attributable to shorter range, in log terms."""
        return float(
            np.log(self.confinement_gain) / np.log(self.total_offtarget_reduction)
        )


def ssra_spatial_benefit(radius_um: float = NODULE_RADIUS_UM) -> SsrASpatialBenefit:
    """Split SsrA's off-target benefit into 'makes less' and 'spreads less'."""
    untagged = escape_fraction(radius_um, DIFFUSION_LENGTHS_UM["GSDMD-N (no SsrA)"])
    tagged = escape_fraction(radius_um, DIFFUSION_LENGTHS_UM["GSDMD-N (+SsrA)"])
    return SsrASpatialBenefit(
        retention_gain=(1.0 - tagged) / (1.0 - untagged),
        confinement_gain=untagged / tagged,
        production_gain=POOL_RATIO_UNTAGGED_OVER_TAGGED,
    )


# -- 4.5 dosing -----------------------------------------------------------


def exposure_over_window(
    inoculum: float,
    capacity: float,
    approach_rate_per_h: float = 0.35,
    window_h: float = 168.0,
) -> float:
    """Time-integrated density for a colony approaching a fixed capacity.

    Monomolecular approach, which module 2.3 showed is the right shape for these
    curves (maximum rate at the start, decelerating). Exposure is the integral of
    density over the window.
    """
    gap = capacity - inoculum
    return float(
        capacity * window_h - gap * (1.0 - np.exp(-approach_rate_per_h * window_h)) / approach_rate_per_h
    )


def schedule_invariance(
    capacity: float = 1.507,
    inocula=(0.005, 0.02, 0.08, 0.16),
    window_h: float = 168.0,
) -> pd.DataFrame:
    """Why 9.23 found < 0.1 % spread across schedules.

    A capacity-limited colony reaches the same plateau whatever it was seeded
    with, so a week-long exposure integral is set by the plateau alone. Onset
    shifts; the integral does not.
    """
    rows = []
    reference = exposure_over_window(inocula[0], capacity, window_h=window_h)
    for inoculum in inocula:
        exposure = exposure_over_window(inoculum, capacity, window_h=window_h)
        time_to_half = float(np.log(2.0 * (capacity - inoculum) / capacity) / 0.35)
        rows.append(
            {
                "inoculum": inoculum,
                "exposure": exposure,
                "exposure_vs_lowest": exposure / reference,
                "time_to_half_max_h": max(time_to_half, 0.0),
            }
        )
    return pd.DataFrame(rows)


def persistence_lever(
    capacity: float = 1.507,
    clearances_per_h=(0.0, 0.2, 0.55, 1.0, 1.5),
    growth_rate_per_h: float = 0.60,
    window_h: float = 168.0,
) -> pd.DataFrame:
    """Exposure against clearance -- the lever 9.23 identified.

    A colony growing at ``growth_rate_per_h`` against first-order clearance
    settles at ``capacity * (1 - clearance/growth)``, and is eliminated once
    clearance exceeds growth.
    """
    rows = []
    for clearance in clearances_per_h:
        plateau = capacity * max(1.0 - clearance / growth_rate_per_h, 0.0)
        rows.append(
            {
                "clearance_per_h": clearance,
                "plateau": plateau,
                "exposure": plateau * window_h,
                "eliminated": plateau <= 0.0,
            }
        )
    frame = pd.DataFrame(rows)
    baseline = frame.loc[frame.clearance_per_h == 0.0, "exposure"].iloc[0]
    frame["exposure_vs_no_clearance"] = frame["exposure"] / baseline
    return frame


def redosing_conclusion_is_circular() -> dict[str, bool]:
    """9.23's own caveat, made explicit.

    Its model has no mechanism that drives a colony to extinction: growth is
    positive whenever N < capacity, and there is no stochastic loss or adaptive
    immunity. So "re-dosing re-seeds a niche that is already full" is a
    consequence of the model's construction, not an inference from data. The
    finding is sound *within* the model and must not be stated as a prediction
    about dosing in vivo.
    """
    return {
        "model_permits_extinction": False,
        "conclusion_follows_from_construction": True,
        "supported_by_data": False,
    }
