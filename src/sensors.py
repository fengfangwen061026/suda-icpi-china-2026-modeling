"""The two designed input sensors, written so their *direction* can be reasoned about.

The circuit is `pPepT -> LuxI -> AHL` and `lldPRD -> LuxR`, with `pLux` driving the
effector. Both designed inputs are therefore *activated* by their stimulus:

* ``lactate_sensor``  -- lldPRD/LldR, monotonically **increasing** in lactate
* ``hypoxia_sensor``  -- pPepT/FNR,  monotonically **decreasing** in oxygen

Monotonicity is the whole point of this module. It means a site's gate output can
be bounded without knowing any sensor parameter, which is what
``src/gut_lumen.py`` uses to reach a parameter-free conclusion.

Parameter status
----------------
``EC50_LACTATE_WT`` and ``HILL_LACTATE_WT`` are the only values here taken from a
measurement of this part family; everything else is a declared prior. The team's
own reporter data cannot identify any of them: it has two oxygen levels and two
lactate levels, which locate neither a midpoint nor a Hill coefficient (the same
limitation the 9.23 spec recorded in its identifiability section). The lactate
gradient experiment that would fix it will not be run this cycle.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: Wild-type lldPRD/LldR L-lactate biosensor, EC50 in mM.
#: Zuniga, Camacho, Chang, Fristot, Mayonove, Hani & Bonnet, ACS Synth. Biol.
#: 10(12):3527-3536, 2021 -- the ALPaGA paper. Rebuilding the wild-type lldPRD
#: biosensor of Goers et al. (Biotechnol. Bioeng. 114:1290, 2017) on a low-copy
#: plasmid, they report "~7 fold change ... with a half maximal effective
#: concentration (EC50) of ~1.6 mM".
#: NB: the EC50 is the WILD-TYPE promoter's. ALPaGA itself is a different,
#: engineered part (EC50 ~110 uM) that we did not build -- see module 3.3.
EC50_LACTATE_WT: float = 1.6
#: No cooperativity is reported for LldR; a single-site Hill is the default.
HILL_LACTATE_WT: float = 1.0
#: ~7-fold dynamic range implies a basal fraction of roughly 1/7 of maximum.
BASAL_LACTATE_WT: float = 1.0 / 7.0


@dataclass(frozen=True)
class LactateSensor:
    """lldPRD/LldR. Increasing in lactate.

    ``anoxic_repression`` and ``glucose_repression`` are the native promoter's
    documented repressions, expressed as the fraction of activity surviving.
    The ALPaGA engineering effort existed precisely to remove them, so which
    value applies depends on which part the team actually built -- see
    ``README.md``, module 3.3.
    """

    ec50_mM: float = EC50_LACTATE_WT
    hill: float = HILL_LACTATE_WT
    basal: float = BASAL_LACTATE_WT
    anoxic_repression: float = 1.0
    glucose_repression: float = 1.0

    def __call__(
        self,
        lactate_mM: float | np.ndarray,
        *,
        anoxic: bool = False,
        glucose_rich: bool = False,
    ) -> float | np.ndarray:
        lactate = np.asarray(lactate_mM, dtype=float)
        occupancy = lactate**self.hill / (self.ec50_mM**self.hill + lactate**self.hill)
        activity = self.basal + (1.0 - self.basal) * occupancy
        if anoxic:
            activity = activity * self.anoxic_repression
        if glucose_rich:
            activity = activity * self.glucose_repression
        return activity if activity.ndim else float(activity)


#: pLux quorum Hill coefficient.
#: Ramalho, Meyer, Muckl, Kapsner, Gerland & Simmel, PLoS ONE 11(1):e0145829,
#: 2016 fit the pLux dose response at four resolutions and get n = 0.97+-0.08
#: (bulk), 0.95+-0.2 (microfluidic chemostat), 1.2+-0.3 and 1.5+-0.6
#: (single-cell), and report that earlier quantitative analyses of the AHL/pLux
#: system "typically resulted in Hill exponents around n = 1-1.5".
#: 9.23 used 2.0, which is above that whole range. We take the published
#: centre and sweep 0.95-1.5; module 3.1 reports both. See WIKI_DRAFT.md 2.5.
QUORUM_HILL_PLUX: float = 1.0

#: FNR-family half-maximal oxygen, % O2 in the gas phase.
#: Hojberg, Schnider, Winteler, Sorensen & Haas, Appl. Environ. Microbiol.
#: 65(9):4085-4093, 1999: an ANR-dependent promoter run in an oxystat reaches
#: half-maximal induction at ~5e2 Pa against an air reading of 210e2 Pa, i.e.
#: 500/101325 = 0.49 % O2, and the authors state the dose response "closely
#: resembles that found for E. coli promoters which are activated by the FNR
#: protein".
#: 9.23 used 1.0 %, which is twice this and is not sourced to a measurement.
#: Module 3.1 reports both; see WIKI_DRAFT.md 2.5.
K_O2_PERCENT_FNR: float = 0.49


@dataclass(frozen=True)
class HypoxiaSensor:
    """pPepT/FNR. Decreasing in oxygen, so maximal in an anoxic lumen."""

    k_o2_percent: float = K_O2_PERCENT_FNR
    hill: float = 2.0
    basal: float = 0.05

    def __call__(self, o2_percent: float | np.ndarray) -> float | np.ndarray:
        o2 = np.asarray(o2_percent, dtype=float)
        repression = self.k_o2_percent**self.hill / (
            self.k_o2_percent**self.hill + o2**self.hill
        )
        activity = self.basal + (1.0 - self.basal) * repression
        return activity if activity.ndim else float(activity)


def lactate_discrimination(
    lactate_target_mM: float,
    lactate_offsite_mM: float,
    sensor: LactateSensor | None = None,
) -> float:
    """Ratio of lactate-arm activity at the target over an off-target site.

    A value below 1 means the arm is *anti*-selective: it reports the off-target
    site more strongly than the tumour.
    """
    sensor = sensor or LactateSensor()
    return float(sensor(lactate_target_mM) / sensor(lactate_offsite_mM))


def is_structurally_anti_selective(stimulus_target: float, stimulus_offsite: float) -> bool:
    """True when no tuning of an activated sensor can prefer the target site.

    Both designed sensors are monotone in their stimulus. So if an off-target
    site presents at least as much stimulus as the tumour does, then
    ``f(target) / f(offsite) <= 1`` for **every** EC50, Hill coefficient and
    basal level. The conclusion is structural rather than parametric, which is
    what lets module 3.3 reach a verdict without the lactate gradient
    experiment that will not be run.

    Pass oxygen as its *hypoxia* stimulus (i.e. lower O2 = more stimulus) by
    negating it, or use :func:`hypoxia_stimulus`.
    """
    return stimulus_offsite >= stimulus_target


def hypoxia_stimulus(o2_percent: float) -> float:
    """Monotone transform making 'more hypoxic' mean 'more stimulus'."""
    return -float(o2_percent)
