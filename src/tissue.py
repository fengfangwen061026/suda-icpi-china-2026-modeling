"""Module 3.1 -- the tissue axis, with the gut lumen in it.

9.23 reported the headline safety numbers as "22-910x vs colonic mucosa" and
"47-2465x vs well-perfused tissue". Two things change on migration:

1. **The range is not a measurement range.** It is almost entirely the span of
   ``n_Q``, the quorum Hill coefficient, which nothing in the dataset
   identifies and which 9.23's own Sobol analysis flagged as the second-largest
   driver of the mucosa fold. Reported here as an explicit sweep.
2. **The site list was incomplete.** Module 3.3 added the colon lumen, which is
   where oral dosing actually puts the bacteria, and both designed arms are
   anti-selective there. Folding those sites in changes the story the tissue
   axis tells.

The gate, arm by arm
--------------------
Total gate output at a site, relative to the tumour core, is the product of
three arms plus whatever the native promoter's repressions contribute::

    ratio(site) = lactate_arm x hypoxia_arm x quorum_arm x repression

* **lactate arm** ``f_L(L_tumour) / f_L(L_site)`` -- :mod:`src.sensors`
* **hypoxia arm** ``f_O2(C_tumour) / f_O2(C_site)`` -- :mod:`src.sensors`
* **quorum arm** -- ``Q ~ f_O2 x N``, so the arm's argument is the hypoxia
  ratio divided by the density ratio, raised to ``n_Q``
* **repression** -- 1 everywhere except the anoxic, glucose-rich lumen

Bacterial density is **measured**, not assumed: each site is assigned the
carrying capacity its own oxygen and lactate condition produced in the growth
block of the workbook. Following 9.23, every site is evaluated at its own
capacity, which is deliberately the worst case for safety -- it assumes EcN
colonises healthy tissue as well as it colonises tumour.

The power-law assumption
------------------------
The quorum arm is treated as ``(Q/K_Q)**n_Q``, i.e. the tumour is taken to sit
*below* the quorum threshold. This is not free: if the tumour were saturated,
the arm would contribute no selectivity at all, and neither 9.23's tissue folds
nor its lesion-size turn-on (14-6891x) could arise. Both of its own findings
therefore require sub-saturation, so the assumption is inherited rather than
invented. It is declared, not fitted.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import data as D
from .sensors import QUORUM_HILL_PLUX
from . import gut_lumen as GL
from . import sensors as S

#: Growth condition whose measured carrying capacity stands in for each site's
#: bacterial density. Chosen by the site's own oxygen and lactate levels.
SITE_CONDITION: dict[str, str] = {
    "tumour_core": "无氧有酸",
    "tumour_rim": "有氧有酸",
    "colonic_mucosa": "有氧无酸",
    "well_perfused": "有氧无酸",
    "colon_lumen_healthy": "无氧无酸",
    "colon_lumen_faecal": "无氧有酸",
    "colon_lumen_dysbiotic": "无氧有酸",
}

#: 9.23's published tissue folds, for the migration comparison.
PUBLISHED_9_23: dict[str, tuple[float, float]] = {
    "colonic_mucosa": (22.3, 909.6),
    "well_perfused": (47.1, 2464.5),
}

#: 9.23's two circuit calibrations, read from its `outputs/calibration.json`.
#: They share every fixed prior and differ almost entirely in ``n_Q`` -- which
#: is why its headline "22-910x" is a quorum-Hill span, not a measurement range.
CALIBRATION_9_23: dict[str, dict[str, float]] = {
    "dynamic_fit": {"n_Q": 1.0, "K_Q": 13.05},
    "endpoint_matched": {"n_Q": 2.978, "K_Q": 353.3},
}


def sensors_9_23() -> tuple[S.LactateSensor, S.HypoxiaSensor]:
    """The sensor priors 9.23 actually used, for the comparison.

    From its `calibration.json`: ``EC50_L = 5.0 mM``, ``n_L = 2.0``,
    ``lld_basal = 0.0078``, ``K_O2 = 10 uM``, ``n_O2 = 2.0``,
    ``pept_basal = 0.122``. Its own parameter table calls 50 uM "~5 % O2", so
    10 uM is 1 % O2 -- identical to this project's hypoxia prior.

    The lactate priors are **not** identical: they are considerably more
    favourable than the published characterisation of the part that was
    actually chosen. See :func:`prior_comparison`.
    """
    return (
        S.LactateSensor(ec50_mM=5.0, hill=2.0, basal=0.0078),
        S.HypoxiaSensor(k_o2_percent=1.0, hill=2.0, basal=0.122),
    )


def sensors_published() -> tuple[S.LactateSensor, S.HypoxiaSensor]:
    """This project's defaults: the published wild-type lldPRD characterisation."""
    return S.LactateSensor(), S.HypoxiaSensor()


def measured_capacities(wb: D.Workbook | None = None) -> dict[str, float]:
    """24 h carrying capacity per growth condition, from the workbook.

    Calibration-grade: these are measured, unlike every transport and tissue
    parameter in this module.
    """
    wb = wb or D.load()
    at24 = wb.growth[(wb.growth.time_h == 24.0) & (wb.growth.construct == "GSDMD-SsrA")]
    return {
        condition: float(at24[at24.condition == condition]["od"].mean())
        for condition in D.GROWTH_CONDITIONS
    }


@dataclass(frozen=True)
class TissueAxis:
    """Gate output at each site relative to the tumour core."""

    quorum_hill: float = QUORUM_HILL_PLUX
    lumen_density_ratio: float = 1.0
    """Lumen EcN density as a multiple of the tumour's. Scenario, not measured."""
    anoxic_repression: float = 1.0
    glucose_repression: float = 1.0
    """Fold repression of the native promoter. 1.0 disables them; module 3.3
    confirmed the built part (BBa_M36021) retains both."""
    use_9_23_priors: bool = False

    def arms(self, wb: D.Workbook | None = None) -> pd.DataFrame:
        wb = wb or D.load()
        sites = GL.load_sites()
        capacities = measured_capacities(wb)
        lactate, hypoxia = sensors_9_23() if self.use_9_23_priors else sensors_published()

        target = sites.loc[GL.TARGET]
        target_density = capacities[SITE_CONDITION[GL.TARGET]]
        target_lactate = float(lactate(target.lactate_mM))
        target_hypoxia = float(hypoxia(target.o2_percent))

        rows = []
        for site, row in sites.iterrows():
            if site == GL.TARGET:
                continue
            lactate_arm = target_lactate / float(lactate(row.lactate_mM))
            hypoxia_arm = target_hypoxia / float(hypoxia(row.o2_percent))

            density = capacities[SITE_CONDITION[str(site)]]
            if site in GL.LUMEN_SITES:
                density = target_density * self.lumen_density_ratio
            density_ratio = density / target_density

            quorum_argument = hypoxia_arm / density_ratio
            quorum_arm = quorum_argument**self.quorum_hill

            # Repression lowers the gate at that site, so it *raises* the
            # tumour-over-site ratio by the same factor.
            repression = 1.0
            if bool(row.anoxic):
                repression *= self.anoxic_repression
            if bool(row.glucose_rich):
                repression *= self.glucose_repression

            rows.append(
                {
                    "site": site,
                    "label": row.label,
                    "is_lumen": site in GL.LUMEN_SITES,
                    "lactate_arm": lactate_arm,
                    "hypoxia_arm": hypoxia_arm,
                    "density_ratio": density_ratio,
                    "quorum_arm": quorum_arm,
                    "repression": repression,
                    "total_ratio": lactate_arm * hypoxia_arm * quorum_arm * repression,
                }
            )
        frame = pd.DataFrame(rows)
        frame["protective"] = frame["total_ratio"] > 1.0
        return frame


def quorum_hill_sweep(
    hills=(1.0, 1.5, 2.0, 3.0, 4.0),
    wb: D.Workbook | None = None,
    **kwargs,
) -> pd.DataFrame:
    """The tissue axis across the unidentified quorum Hill coefficient.

    This is what 9.23's "22-910x" actually was.
    """
    wb = wb or D.load()
    frames = []
    for hill in hills:
        frame = TissueAxis(quorum_hill=hill, **kwargs).arms(wb)
        frame.insert(0, "quorum_hill", hill)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def published_comparison(wb: D.Workbook | None = None, **kwargs) -> pd.DataFrame:
    """Does the reconstructed axis span 9.23's published folds?"""
    sweep = quorum_hill_sweep(wb=wb, **kwargs)
    rows = []
    for site, (low, high) in PUBLISHED_9_23.items():
        values = sweep[sweep.site == site]["total_ratio"]
        rows.append(
            {
                "site": site,
                "published_low": low,
                "published_high": high,
                "reconstructed_low": float(values.min()),
                "reconstructed_high": float(values.max()),
                "published_range_covered": bool(
                    values.min() <= low and values.max() >= high
                ),
            }
        )
    return pd.DataFrame(rows)


def lumen_density_sweep(
    ratios=(0.1, 0.3, 1.0, 3.0, 10.0),
    quorum_hill: float = QUORUM_HILL_PLUX,
    with_repression: bool = True,
    repression_fold: float = 10.0,
    wb: D.Workbook | None = None,
) -> pd.DataFrame:
    """How the lumen verdict moves with the one parameter nobody has measured."""
    wb = wb or D.load()
    strength = repression_fold if with_repression else 1.0
    rows = []
    for ratio in ratios:
        axis = TissueAxis(
            quorum_hill=quorum_hill,
            lumen_density_ratio=ratio,
            anoxic_repression=strength,
            glucose_repression=strength,
        )
        frame = axis.arms(wb)
        for _, row in frame[frame.is_lumen].iterrows():
            rows.append(
                {
                    "lumen_density_ratio": ratio,
                    "site": row.site,
                    "label": row.label,
                    "total_ratio": row.total_ratio,
                    "protective": row.total_ratio > 1.0,
                }
            )
    return pd.DataFrame(rows)


def weakest_link(wb: D.Workbook | None = None, **kwargs) -> pd.Series:
    """The site with the smallest tumour-over-site ratio -- the safety bottleneck."""
    frame = TissueAxis(**kwargs).arms(wb)
    return frame.loc[frame["total_ratio"].idxmin()]


def prior_comparison(wb: D.Workbook | None = None, quorum_hill: float = QUORUM_HILL_PLUX) -> pd.DataFrame:
    """9.23's lactate priors against the published characterisation of the part.

    The part built is ``BBa_M36021``, the native E. coli lldPRD promoter, whose
    published wild-type biosensor has ``EC50 ~ 1.6 mM``, no reported
    cooperativity, and a ~7-fold dynamic range (basal ~ 1/7). 9.23 instead used
    ``EC50 = 5 mM``, ``n_L = 2``, basal 0.0078 -- all three shifted toward
    better discrimination, none of them anchored to this part.

    The oxygen priors agree (``K_O2`` 10 uM = 1 % O2, ``n_O2`` 2).
    """
    wb = wb or D.load()
    published = TissueAxis(quorum_hill=quorum_hill, use_9_23_priors=False).arms(wb)
    legacy = TissueAxis(quorum_hill=quorum_hill, use_9_23_priors=True).arms(wb)
    merged = published.merge(legacy, on=["site", "label", "is_lumen"], suffixes=("_pub", "_923"))
    merged["lactate_arm_inflation"] = merged["lactate_arm_923"] / merged["lactate_arm_pub"]
    merged["total_inflation"] = merged["total_ratio_923"] / merged["total_ratio_pub"]
    return merged[
        [
            "label",
            "is_lumen",
            "lactate_arm_pub",
            "lactate_arm_923",
            "lactate_arm_inflation",
            "total_ratio_pub",
            "total_ratio_923",
            "total_inflation",
        ]
    ]


def calibration_span(wb: D.Workbook | None = None) -> pd.DataFrame:
    """Tissue folds under 9.23's own two calibrations, which differ only in n_Q."""
    wb = wb or D.load()
    frames = []
    for variant, values in CALIBRATION_9_23.items():
        frame = TissueAxis(quorum_hill=values["n_Q"], use_9_23_priors=True).arms(wb)
        frame.insert(0, "variant", variant)
        frame.insert(1, "n_Q", values["n_Q"])
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def critical_lumen_density(
    site: str = "colon_lumen_dysbiotic",
    *,
    quorum_hill: float = QUORUM_HILL_PLUX,
    repression_fold: float = 1.0,
    wb: D.Workbook | None = None,
) -> float:
    """Luminal EcN density, relative to the tumour's, at which the gate tips.

    Below it the quorum arm holds the lumen OFF; above it the gate is more
    active in the lumen than in the tumour. Solving
    ``lac * hyp * (hyp/d)**n * R = 1`` gives

        d_crit = hyp * (lac * hyp * R) ** (1/n)

    so the margin that repression buys scales as ``R ** (1/n_Q)`` -- a strong
    repression is worth less when the quorum arm is steep.
    """
    wb = wb or D.load()
    frame = TissueAxis(quorum_hill=quorum_hill).arms(wb).set_index("site")
    row = frame.loc[site]
    repression = repression_fold**2 if repression_fold != 1.0 else 1.0
    base = float(row.lactate_arm) * float(row.hypoxia_arm) * repression
    return float(row.hypoxia_arm) * base ** (1.0 / quorum_hill)
