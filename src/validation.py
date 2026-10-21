"""The validation layer. Until now it was empty, and said so.

The project's evidence grades are `calibration` (fitted to team data),
`scenario` (literature prior or declared assumption) and `validation`
(tested against data the fit never saw). The third was empty, because there is
no second dataset and there never will be for this cycle.

But held-out prediction does not need a second dataset. It needs a fit that is
denied part of the first one and then asked to produce the part it was denied.
Four such tests exist in the workbook as it stands, and all four bear on
conclusions the project actually uses:

1. **The dose-kill curve** is fitted on two doses and asked for the third.
2. **The gate's AND logic** is the strongest of the four. The multiplicative
   claim says the four reporter corners carry no interaction, which means any
   one corner is determined by the other three. So each corner is held out and
   predicted. At the 24 h endpoint the prediction lands on the observation; at
   9 h it does not, which is the same timepoint the interaction test rejects.
   The claim and its boundary are both reproduced *out of sample*.
3. **The 24 h carrying capacity** -- the quantity every downstream module takes
   as measured -- is forecast from timepoints up to 12 h.
4. **The exponent of the dose-kill curve** is refitted on five constructs that
   the headline fit never used.

None of this makes the model externally validated. It is internal cross
validation, and it cannot detect an error shared by the whole workbook. What it
does rule out is a fit that only reproduces the points it was given, which is
the failure mode three-point curves and four-corner designs are prone to.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from . import data as D
from . import dose as X
from . import gate as G
from . import growth as GR

#: A held-out prediction passes when it lands within this fraction of the
#: observation. Declared up front so the tolerance is not chosen afterwards.
RATIO_TOLERANCE: float = 0.25

#: ...and within this many standard errors, where an SE exists.
SE_TOLERANCE: float = 2.0

#: Timepoints up to here are allowed to forecast the 24 h plateau.
FORECAST_CUTOFF_H: float = 12.0

#: The corner the gate's AND claim is really about, and the one it is not.
ENDPOINT_H: float = 24.0
MIDCOURSE_H: float = 9.0


@dataclass(frozen=True)
class HeldOut:
    """One prediction of data the fit was denied."""

    test: str
    held: str
    predicted: float
    observed: float
    standard_errors: float | None = None

    @property
    def ratio(self) -> float:
        return self.predicted / self.observed if self.observed else float("nan")

    @property
    def passed(self) -> bool:
        within_ratio = abs(self.ratio - 1.0) <= RATIO_TOLERANCE
        if self.standard_errors is None:
            return within_ratio
        return within_ratio and abs(self.standard_errors) <= SE_TOLERANCE

    def __str__(self) -> str:
        mark = "pass" if self.passed else "FAIL"
        tail = "" if self.standard_errors is None else f", {self.standard_errors:+.2f} SE"
        return (
            f"{self.test} | held {self.held}: predicted {self.predicted:.4g}, "
            f"observed {self.observed:.4g} ({self.ratio:.3f}x{tail}) -> {mark}"
        )


def _frame(results: list[HeldOut]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "test": r.test,
                "held": r.held,
                "predicted": r.predicted,
                "observed": r.observed,
                "ratio": r.ratio,
                "standard_errors": r.standard_errors,
                "passed": r.passed,
            }
            for r in results
        ]
    )


# -- 1. the dose-kill curve ------------------------------------------------


def dose_curve_leave_one_out(wb: D.Workbook | None = None) -> pd.DataFrame:
    """Fit the power law on two doses, predict the third. Both controls."""
    wb = wb or D.load()
    results: list[HeldOut] = []
    for control in X.CONTROLS:
        frame = X.net_killing(wb, control=control)
        doses = frame["dose_od"].to_numpy()
        kills = frame["net_percent"].to_numpy()
        errors = frame["se"].to_numpy()
        for index in range(len(doses)):
            train = [j for j in range(len(doses)) if j != index]
            fit = stats.linregress(np.log(doses[train]), np.log(kills[train]))
            predicted = float(np.exp(fit.intercept) * doses[index] ** fit.slope)
            results.append(
                HeldOut(
                    test=f"dose-kill curve, net of {control}",
                    held=f"{doses[index]:.0f} OD",
                    predicted=predicted,
                    observed=float(kills[index]),
                    standard_errors=float((predicted - kills[index]) / errors[index]),
                )
            )
    return _frame(results)


# -- 2. the gate corners ---------------------------------------------------

#: Each corner, and the three that determine it when the interaction is zero.
#: z(D) = z(C) + z(B) - z(A), and the three rearrangements.
_CORNER_RULES: dict[str, tuple[str, str, str]] = {
    "A": ("C", "B", "D"),
    "B": ("D", "A", "C"),
    "C": ("D", "A", "B"),
    "D": ("C", "B", "A"),
}


def gate_corner_holdout(
    wb: D.Workbook | None = None, time_h: float = ENDPOINT_H
) -> pd.DataFrame:
    """Hold out one reporter corner; predict it from the other three.

    Under the multiplicative gate the four corners are additive in probit units,
    so three of them determine the fourth. This is the AND claim restated as a
    prediction. Predictions are reported as percent positive, the readout's own
    units, after inverting the probit.
    """
    wb = wb or D.load()
    z = {corner: G._corner_z(wb, corner, time_h) for corner in G.CORNERS}
    means = {corner: float(values.mean()) for corner, values in z.items()}
    errors = {
        corner: float(values.std(ddof=1) / np.sqrt(values.size)) for corner, values in z.items()
    }

    results: list[HeldOut] = []
    for held, (first, second, third) in _CORNER_RULES.items():
        predicted_z = means[first] + means[second] - means[third]
        se = float(
            np.sqrt(
                errors[first] ** 2 + errors[second] ** 2 + errors[third] ** 2 + errors[held] ** 2
            )
        )
        results.append(
            HeldOut(
                test=f"gate corners at {time_h:.0f} h",
                held=f"{held} ({G.CORNERS[held]})",
                predicted=float(stats.norm.cdf(predicted_z) * 100.0),
                observed=float(stats.norm.cdf(means[held]) * 100.0),
                standard_errors=float((predicted_z - means[held]) / se) if se else None,
            )
        )
    return _frame(results)


def gate_corner_holdout_table(wb: D.Workbook | None = None) -> pd.DataFrame:
    """Every invertible timepoint, so the pass and the failure both show."""
    wb = wb or D.load()
    frames = [gate_corner_holdout(wb, time_h=t) for t in G.invertible_timepoints(wb)]
    return pd.concat(frames, ignore_index=True)


def and_logic_holds_at_the_endpoint_only(wb: D.Workbook | None = None) -> dict[str, bool]:
    """The claim the wiki makes, as an out-of-sample result.

    The endpoint prediction must land and the mid-course one must not. A model
    that passed everywhere would mean the holdout has no power.
    """
    wb = wb or D.load()
    endpoint = gate_corner_holdout(wb, time_h=ENDPOINT_H)
    midcourse = gate_corner_holdout(wb, time_h=MIDCOURSE_H)
    return {
        "endpoint_predicts_held_out_corners": bool(endpoint["passed"].all()),
        "midcourse_does_not": bool(not midcourse["passed"].all()),
        "holdout_has_power": bool(endpoint["passed"].all() and not midcourse["passed"].all()),
    }


# -- 3. the carrying capacity ---------------------------------------------


def capacity_forecast(
    wb: D.Workbook | None = None, *, cutoff_h: float = FORECAST_CUTOFF_H
) -> pd.DataFrame:
    """Forecast the 24 h plateau from timepoints at or below ``cutoff_h``.

    The fit starts at 1 h, which is module 2.3's conclusion: the 0 -> 1 h burst
    is real growth that no three-parameter sigmoid reproduces, so including it
    corrupts the fit rather than informing it.
    """
    wb = wb or D.load()
    results: list[HeldOut] = []
    for construct in ("GSDMD-SsrA", "GSDMD"):
        for condition in sorted(set(wb.growth.condition)):
            times, values = GR._series(wb, construct, condition)
            train = (times >= 1.0) & (times <= cutoff_h)
            parameters, _ = GR._fit(
                GR.gompertz, times[train], values[train], (values.max() * 1.2, 2.0, 0.3)
            )
            predicted = float(GR.gompertz(np.array([24.0]), *parameters)[0])
            observed = float(values[times == 24.0][0])
            results.append(
                HeldOut(
                    test=f"24 h capacity from t <= {cutoff_h:.0f} h",
                    held=f"{construct}, {condition}",
                    predicted=predicted,
                    observed=observed,
                )
            )
    return _frame(results)


def capacity_forecast_bias(wb: D.Workbook | None = None) -> float:
    """Mean forecast ratio. Above 1 means the Gompertz overshoots the plateau."""
    return float(capacity_forecast(wb)["ratio"].mean())


def biomass_ratio_survives_the_forecast(wb: D.Workbook | None = None) -> pd.DataFrame:
    """The SsrA decision's anchor, rebuilt from held-out forecasts.

    Module 3.4 keeps the degron because the potency it costs is less than the
    biomass it buys, and the biomass ratio is the untagged 24 h OD over the
    tagged one under induction. The forecast overshoots both strains by about
    the same factor, so the **ratio** is reproduced far better than either
    plateau -- which is the quantity the decision rests on.
    """
    wb = wb or D.load()
    forecast = capacity_forecast(wb).set_index("held")
    rows = []
    for condition in ("有氧有酸", "无氧有酸"):
        tagged = forecast.loc[f"GSDMD-SsrA, {condition}"]
        untagged = forecast.loc[f"GSDMD, {condition}"]
        rows.append(
            {
                "condition": condition,
                "forecast_ratio": untagged["predicted"] / tagged["predicted"],
                "observed_ratio": untagged["observed"] / tagged["observed"],
                "error_percent": abs(
                    untagged["predicted"] / tagged["predicted"]
                    - untagged["observed"] / tagged["observed"]
                )
                / (untagged["observed"] / tagged["observed"])
                * 100.0,
            }
        )
    return pd.DataFrame(rows)


# -- 4. the exponent, on constructs the headline fit never used ------------


def cross_construct_exponents(wb: D.Workbook | None = None) -> pd.DataFrame:
    """Refit the dose-kill exponent separately for every construct in block 5.

    The headline fit uses ``GSDMD-SsrA`` net of a control. These are raw fits on
    each construct's own three doses, so five of the six are data the headline
    number never saw. What generalises is the sign of the curvature, not the
    point value: killing is supra-linear in dose for every construct, including
    the two that carry no effector at all.
    """
    wb = wb or D.load()
    block = wb.killing_block(5)
    doses = np.array(X.MEASURED_DOSES)
    rows = []
    for construct in D.CONSTRUCTS:
        means = np.array(
            [
                block[(block.construct == construct) & (block.dose_od == dose)]["percent"].mean()
                for dose in doses
            ]
        )
        if np.any(~np.isfinite(means)) or np.any(means <= 0.0):
            continue
        fit = stats.linregress(np.log(doses), np.log(means))
        rows.append(
            {
                "construct": construct,
                "exponent": float(fit.slope),
                "r_squared": float(fit.rvalue**2),
                "carries_effector": "GSDMD" in construct,
                "used_in_headline_fit": construct == X.BUILT_CONSTRUCT,
                "supra_linear": bool(fit.slope > 2.0),
            }
        )
    return pd.DataFrame(rows)


# -- the layer, as a whole -------------------------------------------------


def validation_summary(wb: D.Workbook | None = None) -> pd.DataFrame:
    """One row per test, with what it would have falsified."""
    wb = wb or D.load()
    dose = dose_curve_leave_one_out(wb)
    endpoint = gate_corner_holdout(wb, time_h=ENDPOINT_H)
    midcourse = gate_corner_holdout(wb, time_h=MIDCOURSE_H)
    capacity = capacity_forecast(wb)
    constructs = cross_construct_exponents(wb)
    return pd.DataFrame(
        [
            {
                "test": "dose-kill curve, leave one dose out",
                "n": len(dose),
                "passed": int(dose["passed"].sum()),
                "worst_ratio": float(dose["ratio"].sub(1.0).abs().max() + 1.0),
                "would_have_falsified": "module 4.6's back-calculated dose",
            },
            {
                "test": f"gate corners at {ENDPOINT_H:.0f} h, leave one corner out",
                "n": len(endpoint),
                "passed": int(endpoint["passed"].sum()),
                "worst_ratio": float(endpoint["ratio"].sub(1.0).abs().max() + 1.0),
                "would_have_falsified": "the AND-logic claim",
            },
            {
                "test": f"gate corners at {MIDCOURSE_H:.0f} h (expected to fail)",
                "n": len(midcourse),
                "passed": int(midcourse["passed"].sum()),
                "worst_ratio": float(midcourse["ratio"].sub(1.0).abs().max() + 1.0),
                "would_have_falsified": "nothing -- this is the holdout's power check",
            },
            {
                "test": f"24 h capacity from t <= {FORECAST_CUTOFF_H:.0f} h",
                "n": len(capacity),
                "passed": int(capacity["passed"].sum()),
                "worst_ratio": float(capacity["ratio"].sub(1.0).abs().max() + 1.0),
                "would_have_falsified": "every density in modules 3.1 and 3.4",
            },
            {
                "test": "dose-kill exponent, refit per construct",
                "n": len(constructs),
                "passed": int(constructs["supra_linear"].sum()),
                "worst_ratio": float("nan"),
                "would_have_falsified": "the cube law, hence 4.6's robustness argument",
            },
        ]
    )


def validation_layer_is_no_longer_empty(wb: D.Workbook | None = None) -> dict[str, object]:
    """Executable record of what the layer now contains, and what it still lacks."""
    wb = wb or D.load()
    summary = validation_summary(wb)
    held_out = int(summary["n"].sum())
    gate = and_logic_holds_at_the_endpoint_only(wb)
    return {
        "held_out_predictions": held_out,
        "is_empty": held_out == 0,
        "external_dataset": False,
        "kind": "internal cross validation, one workbook",
        "holdout_has_power": gate["holdout_has_power"],
        "cannot_detect": "an error shared by the whole workbook",
        "capacity_forecast_bias": capacity_forecast_bias(wb),
    }
