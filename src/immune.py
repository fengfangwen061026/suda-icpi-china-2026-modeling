"""Module 6 -- the pyroptosis-immunity-distant-killing cascade, minimally.

Module 4.4 established that the quorum arm makes this a *nodule detector*: a
cluster of micro-lesions does not reach the ON band, and dispersing a burden is
strictly worse than compacting it. So direct colonisation cannot address
disseminated disease, and whatever distant effect the project claims has to come
through the immune cascade the PPT describes:

    GSDMD pore -> IL-1beta / IL-18 -> DC maturation -> CTL -> distant lesion

This is the least constrained part of the project, so it is kept deliberately
small. Four states collapse onto **two dimensionless numbers**, and the module
reports feasibility boundaries rather than predicted efficacy.

The cascade
-----------
::

    dA/dt = Phi - delta_A A                        antigen + IL-1b/IL-18 signal
    dD/dt = a_D A/(K_A + A) - delta_D D            DC maturation, saturating
    dT/dt = a_T epsilon D - delta_T T              CTL priming, suppressed by epsilon
    dM/dt = r M (1 - M/K) - k T M/(h + M)          distant lesion

``epsilon`` in (0, 1] is the immunosuppression factor. It matters here more than
anywhere: the project explicitly targets **pMMR/MSS** colorectal cancer, which
its own design note describes as low-immunogenicity, poorly infiltrated and
immunosuppressive -- a "cold tumour". The one mechanism that must carry distant
control is therefore operating in its worst setting. Converting cold to hot is
exactly the stated rationale for pyroptosis, so the question this module asks is
how much pyroptotic flux that conversion needs.

Reduction
---------
At steady state the upstream chain collapses. With ``x = Phi / (delta_A K_A)``
the normalised pyroptotic flux, define the **immune pressure number**

    Psi = epsilon * G * x / (1 + x),    G = (k / (r h)) (a_T / delta_T)(a_D / delta_D)

and let ``h`` be the evasion scale as a fraction of carrying capacity. Setting
``K = 1`` (burden relative to capacity) and ``r = 1`` (time in units of 1/r),
the distant lesion obeys

    dM/dt = M [ (1 - M) - h Psi / (h + M) ]

so the whole cascade enters through ``Psi`` alone. Two consequences are
structural, not fitted:

1. ``x/(1+x) < 1`` always, so **``epsilon G > 1`` is a hard feasibility
   ceiling**. If the cold-tumour-adjusted cascade gain is below 1, no amount of
   pyroptosis achieves distant control.
2. Above it, the required flux is ``x_min = 1 / (epsilon G - 1)``, which
   diverges as ``epsilon G -> 1+``.

Evidence class: **scenario_only** throughout. Neither ``G`` nor ``epsilon`` is
measured here and no validation is possible with the available data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ImmuneCascade:
    """The reduced distant-lesion model, parameterised by ``h`` alone.

    ``h`` is the burden at which immune killing is half-saturated, as a fraction
    of carrying capacity. Small ``h`` means killing saturates early, i.e. a
    large lesion evades a fixed CTL pool more easily.
    """

    evasion_scale: float = 0.2

    # -- feasibility -----------------------------------------------------

    @staticmethod
    def immune_pressure(
        normalised_flux: float | np.ndarray,
        *,
        epsilon: float = 1.0,
        gain: float = 5.0,
    ) -> float | np.ndarray:
        """``Psi = epsilon G x / (1 + x)``."""
        x = np.asarray(normalised_flux, dtype=float)
        out = epsilon * gain * x / (1.0 + x)
        return float(out) if out.ndim == 0 else out

    @staticmethod
    def is_feasible(*, epsilon: float, gain: float) -> bool:
        """Whether distant control is reachable at *any* pyroptotic flux."""
        return epsilon * gain > 1.0

    @staticmethod
    def required_flux(*, epsilon: float, gain: float) -> float:
        """``x_min = 1/(epsilon G - 1)``, or infinity when infeasible."""
        product = epsilon * gain
        if product <= 1.0:
            return float("inf")
        return 1.0 / (product - 1.0)

    # -- outcomes --------------------------------------------------------

    def guaranteed_eradication_pressure(self) -> float:
        """``Psi`` above which eradication happens from *any* initial burden.

        Below it but above 1 the system is bistable: a small distant lesion is
        cleared, a large one still escapes.
        """
        h = self.evasion_scale
        return 1.0 + (1.0 - h) ** 2 / (4.0 * h)

    def escape_burden(self, pressure: float | np.ndarray) -> float | np.ndarray:
        """Stable non-zero burden the distant lesion settles at.

        Roots of ``M^2 - (1 - h)M + h(Psi - 1) = 0``; the upper root is the
        stable escape state. Returns 0 when no positive equilibrium exists,
        i.e. above :meth:`guaranteed_eradication_pressure`.
        """
        h = self.evasion_scale
        psi = np.asarray(pressure, dtype=float)
        disc = (1.0 - h) ** 2 - 4.0 * h * (psi - 1.0)
        upper = np.where(disc >= 0.0, ((1.0 - h) + np.sqrt(np.maximum(disc, 0.0))) / 2.0, 0.0)
        out = np.maximum(upper, 0.0)
        return float(out) if out.ndim == 0 else out

    def max_treatable_burden(self, pressure: float | np.ndarray) -> float | np.ndarray:
        """Largest initial burden that is still cleared, for ``Psi > 1``.

        This is the unstable (lower) root -- the basin boundary of ``M = 0``.
        Zero below ``Psi = 1``; the whole range above guaranteed eradication.
        """
        h = self.evasion_scale
        psi = np.asarray(pressure, dtype=float)
        disc = (1.0 - h) ** 2 - 4.0 * h * (psi - 1.0)
        lower = ((1.0 - h) - np.sqrt(np.maximum(disc, 0.0))) / 2.0
        out = np.where(psi <= 1.0, 0.0, np.where(disc >= 0.0, lower, 1.0))
        return float(out) if out.ndim == 0 else out

    def burden_reduction(self, pressure: float | np.ndarray) -> float | np.ndarray:
        """Fractional reduction of the escape burden relative to no immunity."""
        untreated = self.escape_burden(0.0)
        return 1.0 - self.escape_burden(pressure) / untreated

    # -- trajectories, for the one figure --------------------------------

    def growth_rate(self, burden: float, pressure: float) -> float:
        h = self.evasion_scale
        return float(burden * ((1.0 - burden) - h * pressure / (h + burden)))


def containment_curve(
    cascade: ImmuneCascade | None = None,
    pressures: np.ndarray | None = None,
) -> pd.DataFrame:
    """Distant burden and treatability across immune pressure."""
    cascade = cascade or ImmuneCascade()
    if pressures is None:
        pressures = np.linspace(0.0, 6.0, 121)
    return pd.DataFrame(
        {
            "immune_pressure": pressures,
            "escape_burden": cascade.escape_burden(pressures),
            "burden_reduction": cascade.burden_reduction(pressures),
            "max_treatable_burden": cascade.max_treatable_burden(pressures),
            "eradication_possible": pressures > 1.0,
            "eradication_guaranteed": pressures >= cascade.guaranteed_eradication_pressure(),
        }
    )


def cold_tumour_penalty(
    epsilons=(1.0, 0.5, 0.2, 0.1, 0.05),
    gains=(2.0, 5.0, 10.0, 30.0),
) -> pd.DataFrame:
    """Required pyroptotic flux as immunosuppression deepens.

    ``epsilon = 1`` is an immunologically permissive tumour; MSS/pMMR CRC sits
    at the low end, which is where the project's own target population is.
    """
    rows = []
    for gain in gains:
        for epsilon in epsilons:
            rows.append(
                {
                    "cascade_gain": gain,
                    "epsilon": epsilon,
                    "effective_gain": epsilon * gain,
                    "feasible": ImmuneCascade.is_feasible(epsilon=epsilon, gain=gain),
                    "required_normalised_flux": ImmuneCascade.required_flux(
                        epsilon=epsilon, gain=gain
                    ),
                }
            )
    return pd.DataFrame(rows)


def feasibility_boundary(gains: np.ndarray | None = None) -> pd.DataFrame:
    """The ``epsilon G = 1`` curve: the minimum suppression a gain can tolerate."""
    if gains is None:
        gains = np.logspace(0, 2, 60)
    return pd.DataFrame({"cascade_gain": gains, "min_epsilon": 1.0 / gains})


def local_vs_distant_split(
    local_kill_fraction: float,
    cascade: ImmuneCascade | None = None,
    *,
    epsilon: float = 0.2,
    gain: float = 10.0,
    normalised_flux: float = 1.0,
    distant_share_of_burden: float = 0.3,
) -> dict[str, float]:
    """The supervisor's question 6: local versus distant contribution.

    ``local_kill_fraction`` is what the circuit achieves at the primary lesion,
    measurable from block 5. The distant part is whatever the cascade removes of
    the disseminated share. Both are reported; the distant number is
    scenario-only and must never be presented as a prediction.
    """
    cascade = cascade or ImmuneCascade()
    pressure = ImmuneCascade.immune_pressure(
        normalised_flux, epsilon=epsilon, gain=gain
    )
    distant_reduction = float(cascade.burden_reduction(pressure))
    local_share = 1.0 - distant_share_of_burden

    local_removed = local_kill_fraction * local_share
    distant_removed = distant_reduction * distant_share_of_burden
    total = local_removed + distant_removed
    return {
        "immune_pressure": float(pressure),
        "local_removed": local_removed,
        "distant_removed": distant_removed,
        "total_removed": total,
        "distant_contribution_share": distant_removed / total if total else 0.0,
        "eradication_possible": bool(pressure > 1.0),
    }
