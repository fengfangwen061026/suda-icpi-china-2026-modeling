"""Module 2.2 -- is the AND gate multiplicative? Migrated from 9.23 and tightened.

9.23 noticed the right thing: read as raw fluorescence the 24 h corners give an
oxygen effect of 16.2x and a lactate effect of 170x, but a dual effect of only
227x, where a multiplicative gate predicts 16.2 x 170 = 2766x. It then argued
the assay is at its ceiling (the two lactate corners sit at 82.9 % and 97.9 %
positive) and "inverted the saturating readout" to recover 17.4x / 16.5x for
oxygen and 642x / 609x for lactate.

What that inversion actually is
-------------------------------
Reconstructed here: it is a **probit inversion**. If per-cell log-expression is
normal with condition-dependent mean ``mu`` and a common spread ``sigma``, and
the cytometry gate sits at a fixed threshold, then the positive fraction is
``p = Phi((mu - theta)/sigma)``, so

    mu = theta + sigma * probit(p)

and a fold change between two corners is ``exp(sigma * delta_z)``. Fitting
``sigma = 2.53`` reproduces 9.23's four numbers to within rounding (648x, 16.9x,
630x here against their 642x, 16.5x, 609x).

Why this module does not simply carry those numbers forward
-----------------------------------------------------------
``sigma`` is **not identifiable** from this dataset. It is the cell-to-cell
spread of expression, which needs the per-cell intensity distribution; the
workbook records only a group mean and a positive fraction. So:

* the **fold magnitudes** (17.4x, 642x) are proportional to an unmeasured
  ``sigma`` and must be reported as sigma-conditional, never as measurements;
* the **multiplicativity conclusion** does not depend on ``sigma`` at all.

A multiplicative gate means the two inputs are *additive* on ``mu``, hence
additive in probit units, hence the two-way **interaction term is zero**:

    interaction = z(D) - z(C) - z(B) + z(A)

``sigma`` scales every term equally, so it cancels from the test. That makes the
interaction test the load-bearing result and the fold numbers decoration.

Corners: ``A`` 21 % O2, ``B`` 1 % O2, ``C`` 21 % + 20 mM lactate,
``D`` 1 % + 20 mM lactate.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from . import data as D

#: Corner labels, in the order the two-way contrast uses them.
CORNERS: dict[str, str] = {
    "A": "21% -",
    "B": "1% -",
    "C": "21% - 20mM",
    "D": "1% - 20mM",
}

#: The spread that reproduces 9.23's published fold changes. NOT a measurement.
SIGMA_MATCHING_9_23: float = 2.53


def _corner_z(wb: D.Workbook, corner: str, time_h: float) -> np.ndarray:
    frame = wb.reporter_positive
    group = CORNERS[corner]
    fractions = (
        frame[(frame.group == group) & (frame.time_h == time_h)]["percent"].to_numpy() / 100.0
    )
    if np.any(fractions <= 0.0) or np.any(fractions >= 1.0):
        raise ValueError(
            f"corner {corner} at {time_h} h has a positive fraction at 0 or 1, "
            "which has no finite probit; this timepoint cannot be inverted"
        )
    return stats.norm.ppf(fractions)


@dataclass(frozen=True)
class GateTest:
    """Two-way probit analysis of one timepoint."""

    time_h: float
    oxygen_effect_no_lactate: float   # z(B) - z(A), probit units
    oxygen_effect_with_lactate: float  # z(D) - z(C)
    lactate_effect_normoxic: float     # z(C) - z(A)
    lactate_effect_hypoxic: float      # z(D) - z(B)
    interaction: float
    interaction_se: float

    @property
    def interaction_t(self) -> float:
        return self.interaction / self.interaction_se if self.interaction_se else float("nan")

    @property
    def multiplicative(self) -> bool:
        """True when the interaction is within 2 SE of zero."""
        return abs(self.interaction) <= 2.0 * self.interaction_se

    def fold(self, effect: float, sigma: float = SIGMA_MATCHING_9_23) -> float:
        """Convert a probit effect to a fold change. Depends on unmeasured sigma."""
        return float(np.exp(sigma * effect))

    def __str__(self) -> str:
        verdict = "multiplicative" if self.multiplicative else "INTERACTION PRESENT"
        return (
            f"{self.time_h:>4.0f} h  interaction {self.interaction:+.3f} "
            f"± {self.interaction_se:.3f} probit  ->  {verdict}"
        )


def gate_test(wb: D.Workbook | None = None, time_h: float = 24.0) -> GateTest:
    """Test whether the two inputs act multiplicatively at one timepoint."""
    wb = wb or D.load()
    z = {corner: _corner_z(wb, corner, time_h) for corner in CORNERS}
    means = {corner: float(values.mean()) for corner, values in z.items()}
    variance = sum(float(values.var(ddof=1)) / values.size for values in z.values())

    return GateTest(
        time_h=time_h,
        oxygen_effect_no_lactate=means["B"] - means["A"],
        oxygen_effect_with_lactate=means["D"] - means["C"],
        lactate_effect_normoxic=means["C"] - means["A"],
        lactate_effect_hypoxic=means["D"] - means["B"],
        interaction=means["D"] - means["C"] - means["B"] + means["A"],
        interaction_se=float(np.sqrt(variance)),
    )


def invertible_timepoints(wb: D.Workbook | None = None) -> list[float]:
    """Timepoints where every corner has a positive fraction strictly in (0, 1)."""
    wb = wb or D.load()
    usable = []
    for time_h in D.REPORTER_TIMES_H:
        try:
            for corner in CORNERS:
                _corner_z(wb, corner, time_h)
        except ValueError:
            continue
        usable.append(float(time_h))
    return usable


def gate_test_table(wb: D.Workbook | None = None) -> pd.DataFrame:
    """The multiplicativity test at every timepoint that can carry it."""
    wb = wb or D.load()
    rows = []
    for time_h in invertible_timepoints(wb):
        test = gate_test(wb, time_h)
        rows.append(
            {
                "time_h": test.time_h,
                "oxygen_B_minus_A": test.oxygen_effect_no_lactate,
                "oxygen_D_minus_C": test.oxygen_effect_with_lactate,
                "lactate_C_minus_A": test.lactate_effect_normoxic,
                "lactate_D_minus_B": test.lactate_effect_hypoxic,
                "interaction": test.interaction,
                "interaction_se": test.interaction_se,
                "multiplicative": test.multiplicative,
            }
        )
    return pd.DataFrame(rows)


def raw_intensity_paradox(wb: D.Workbook | None = None, time_h: float = 24.0) -> dict[str, float]:
    """The apparent sub-multiplicativity that the probit analysis resolves.

    Uses block 3 intensities. Convention 1 forbids a censored denominator, and
    at 24 h corner A is not censored in every well, so the ratio is computable
    -- but it is reported here only to show the paradox, never as the gate's
    dynamic range.
    """
    wb = wb or D.load()
    frame = wb.reporter_intensity
    means = {}
    for corner, group in CORNERS.items():
        rows = frame[(frame.group == group) & (frame.time_h == time_h)]
        means[corner] = float(rows["intensity"].mean())

    oxygen = means["B"] / means["A"]
    lactate = means["C"] / means["A"]
    dual = means["D"] / means["A"]
    return {
        "oxygen_fold": oxygen,
        "lactate_fold": lactate,
        "dual_fold": dual,
        "multiplicative_prediction": oxygen * lactate,
        "shortfall": oxygen * lactate / dual,
    }


def sigma_sensitivity(
    test: GateTest, sigmas=(1.0, 1.5, 2.0, SIGMA_MATCHING_9_23, 3.0, 4.0)
) -> pd.DataFrame:
    """How the reported fold changes move with the unidentified spread.

    The point of this table is that the folds are not measurements. The
    interaction test in :func:`gate_test` is what the data supports.
    """
    rows = []
    for sigma in sigmas:
        rows.append(
            {
                "sigma": sigma,
                "oxygen_fold_B_over_A": test.fold(test.oxygen_effect_no_lactate, sigma),
                "oxygen_fold_D_over_C": test.fold(test.oxygen_effect_with_lactate, sigma),
                "lactate_fold_C_over_A": test.fold(test.lactate_effect_normoxic, sigma),
                "lactate_fold_D_over_B": test.fold(test.lactate_effect_hypoxic, sigma),
                "matches_9_23": abs(sigma - SIGMA_MATCHING_9_23) < 1e-9,
            }
        )
    return pd.DataFrame(rows)
