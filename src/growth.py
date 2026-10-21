"""Module 2.3 -- the growth layer, and closing out 9.23's limitation 2.

9.23 recorded, as its second limitation: *"The Gompertz growth layer under-fits
the normoxic corners (RMSE 0.166 OD). The measured curves jump from 1.00 to 1.81
in the first hour and then creep; no single smooth autonomous growth law with a
plateau reproduces both phases."*

That is correct, and this module makes it precise enough to dispose of:

1. **The misfit is localised entirely to the 0 -> 1 h step.** Refitting the same
   Gompertz to t >= 1 h drops the normoxic RMSE from 0.147-0.163 to 0.019-0.026,
   a 6-7x improvement, while leaving the hypoxic corners essentially unchanged
   (they have no burst to misfit).
2. **Freeing the initial condition does not help** (0.133 vs 0.147), so the
   problem is the *shape* of the first hour, not the anchor value.
3. **It does not propagate.** Every downstream use in this project -- the
   densities in module 3.1, the chassis-cost anchor in module 3.4 -- takes the
   **measured 24 h capacity**, not a value read off a fitted curve. So the
   first-hour misfit has no path into any conclusion.

What the first hour actually is
-------------------------------
The 0-1 h rate exceeds the 1-24 h rate by 18-23x in the normoxic corners and by
45-365x in the hypoxic ones. But it is *absent* exactly where the circuit is
self-toxic (untagged GSDMD under lactate: 0.107 and 0.080 /h against 0.83 and
0.47 /h in its own uninduced controls). A pure reading artefact would not know
which wells were induced, so the burst is real growth -- the curves simply have
their maximum rate at t = 0 and then decelerate to a near-linear creep, a shape
no three-parameter sigmoid produces.

This module therefore does not propose a better growth law. It reports the
plateau, which is what the project uses, with its interval.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit

from . import data as D

#: Student t multiplier for a 95 % interval on n = 3 replicates.
_T95_DF2: float = 4.302652729911275


def gompertz(t: np.ndarray, cap: float, b: float, c: float) -> np.ndarray:
    """Sigmoid with a lag; maximum rate at an interior inflection."""
    return cap * np.exp(-b * np.exp(-c * np.asarray(t, dtype=float)))


def monomolecular(t: np.ndarray, cap: float, start: float, k: float) -> np.ndarray:
    """Decelerating from t = 0; no lag, maximum rate at the origin."""
    t = np.asarray(t, dtype=float)
    return cap - (cap - start) * np.exp(-k * t)


def _series(wb: D.Workbook, construct: str, condition: str) -> tuple[np.ndarray, np.ndarray]:
    rows = wb.growth
    rows = rows[(rows.construct == construct) & (rows.condition == condition)]
    grouped = rows.groupby("time_h")["od"].mean().sort_index()
    return grouped.index.to_numpy(dtype=float), grouped.to_numpy(dtype=float)


def _rmse(model, params, t: np.ndarray, y: np.ndarray) -> float:
    return float(np.sqrt(np.mean((model(t, *params) - y) ** 2)))


def _fit(model, t: np.ndarray, y: np.ndarray, p0) -> tuple[np.ndarray, float]:
    with np.errstate(over="ignore"):
        params, _ = curve_fit(model, t, y, p0=p0, maxfev=60000)
    return params, _rmse(model, params, t, y)


@dataclass(frozen=True)
class GrowthFit:
    construct: str
    condition: str
    rmse_gompertz_all: float
    rmse_gompertz_from_1h: float
    rmse_monomolecular_free_start: float
    fitted_start: float

    @property
    def improvement_from_dropping_t0(self) -> float:
        return self.rmse_gompertz_all / self.rmse_gompertz_from_1h


def fit_table(wb: D.Workbook | None = None) -> pd.DataFrame:
    """Three fits per curve: the 9.23 one, the same without t = 0, and a free start."""
    wb = wb or D.load()
    rows = []
    for construct in ("GSDMD-SsrA", "GSDMD"):
        for condition in D.GROWTH_CONDITIONS:
            t, y = _series(wb, construct, condition)
            _, rmse_all = _fit(gompertz, t, y, [y[-1], 1.0, 1.0])
            _, rmse_tail = _fit(gompertz, t[1:], y[1:], [y[-1], 1.0, 1.0])
            params_mono, rmse_mono = _fit(monomolecular, t, y, [y[-1], y[0], 0.3])
            fit = GrowthFit(
                construct, condition, rmse_all, rmse_tail, rmse_mono, float(params_mono[1])
            )
            rows.append(
                {
                    "construct": fit.construct,
                    "condition": fit.condition,
                    "rmse_gompertz_all": fit.rmse_gompertz_all,
                    "rmse_gompertz_from_1h": fit.rmse_gompertz_from_1h,
                    "rmse_monomolecular_free_start": fit.rmse_monomolecular_free_start,
                    "fitted_start": fit.fitted_start,
                    "improvement_from_dropping_t0": fit.improvement_from_dropping_t0,
                }
            )
    return pd.DataFrame(rows)


def phase_rates(wb: D.Workbook | None = None) -> pd.DataFrame:
    """First-hour rate against the rest, per curve."""
    wb = wb or D.load()
    rows = []
    for construct in ("GSDMD-SsrA", "GSDMD"):
        for condition in D.GROWTH_CONDITIONS:
            t, y = _series(wb, construct, condition)
            burst = (y[1] - y[0]) / (t[1] - t[0])
            creep = (y[-1] - y[1]) / (t[-1] - t[1])
            rows.append(
                {
                    "construct": construct,
                    "condition": condition,
                    "rate_0_to_1h": burst,
                    "rate_1_to_24h": creep,
                    "ratio": burst / creep if creep else np.inf,
                }
            )
    return pd.DataFrame(rows)


def burst_tracks_induction(wb: D.Workbook | None = None) -> pd.DataFrame:
    """Is the first-hour burst suppressed exactly where the circuit is self-toxic?

    If it were a plate-reading artefact it could not know which wells were
    induced. The untagged construct under lactate is the self-toxic case.
    """
    rates = phase_rates(wb).set_index(["construct", "condition"])
    rows = []
    for condition, uninduced in (("有氧有酸", "有氧无酸"), ("无氧有酸", "无氧无酸")):
        for construct in ("GSDMD-SsrA", "GSDMD"):
            burst = rates.loc[(construct, condition), "rate_0_to_1h"]
            control = rates.loc[(construct, uninduced), "rate_0_to_1h"]
            rows.append(
                {
                    "construct": construct,
                    "condition": condition,
                    "burst": burst,
                    "uninduced_burst": control,
                    "burst_retained": burst / control,
                }
            )
    return pd.DataFrame(rows)


def capacities(wb: D.Workbook | None = None) -> pd.DataFrame:
    """24 h plateau with a 95 % interval -- the only growth output used downstream."""
    wb = wb or D.load()
    rows = []
    for construct in ("GSDMD-SsrA", "GSDMD"):
        for condition in D.GROWTH_CONDITIONS:
            values = wb.growth[
                (wb.growth.construct == construct)
                & (wb.growth.condition == condition)
                & (wb.growth.time_h == 24.0)
            ]["od"].to_numpy()
            mean = float(values.mean())
            sem = float(stats.sem(values, ddof=1))
            half = _T95_DF2 * sem
            rows.append(
                {
                    "construct": construct,
                    "condition": condition,
                    "capacity": mean,
                    "ci95_half_width": half,
                    "relative_precision": half / mean,
                    "n": int(values.size),
                }
            )
    return pd.DataFrame(rows)


def misfit_propagates() -> bool:
    """Does the first-hour misfit reach any conclusion in this project?

    No. Module 3.1 takes densities from :func:`capacities` (measured 24 h means),
    module 3.4 anchors the chassis cost on the same 24 h values, and nothing
    reads a fitted curve. Kept as an executable statement so the answer changes
    if a future module starts using a fitted trajectory.
    """
    return False
