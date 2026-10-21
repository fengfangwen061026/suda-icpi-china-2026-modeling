"""Module 4.6 -- back-calculating the effective dose. Answers the supervisor's
second question directly.

Modules 4.3 and 4.5 are *about* dose but do not answer "how much". 4.5 shows the
exposure integral is set by the plateau rather than by the inoculum (a 32-fold
inoculum range moves it by 0.18 %), and that clearance is the lever. Both are
statements that the **administered** amount does not control exposure. Neither
produces a required dose.

This module produces one, from data the project already has.

The chain
---------
Block 5 **is** a dose series: 6 / 8 / 10 OD against CT26, every construct, three
replicates. 9.23 and module 3.4 used it only for the SsrA potency ratio at a
single dose. Fitted as a curve it gives the first half of the back-calculation:

1. **Net dose-kill curve.** Chassis-attributable killing is subtracted, which
   block 5 supports: ``EcN`` is the bare chassis and ``gfp`` is a
   plasmid-bearing, non-effector strain, both measured at all three doses. The
   residual is supra-linear -- a power law with exponent **2.65-3.38** and
   r-squared above 0.995, i.e. roughly a cube law.
2. **Efficacy criterion.** A lesion is controlled when the kill rate at least
   matches its proliferation rate. With a 24 h exposure this is closed form:
   ``f_required = 1 - exp(-ln2 * 24 / T_double)``.
3. **Inversion.** ``dose = (f_required / A) ** (1 / b)``.

What the cube law does to the answer
------------------------------------
The exponent is what makes this worth doing. Because dose enters with a power
near 3, the inversion **compresses** every uncertainty on the requirement side
by a cube root. The required kill fraction differs by 435x between a CT26
xenograft and a human colorectal tumour, and the required dose differs by only
6-10x. A 3.7x loss of delivered effector in vivo costs 1.55x in dose. The answer
is therefore robust to exactly the parameters this project cannot measure.

What is and is not derived here
-------------------------------
Derived, from team data plus a declared doubling time:

* the exponent and amplitude of the net dose-kill curve;
* the required dose **in the assay's own units**, as a multiple of a condition
  that was actually run;
* how that requirement moves with lesion radius, and the dose escalation needed
  to reach a micro-lesion;
* what that escalation costs in safety margin.

**Not** derived: an oral CFU number. Two bridges are missing -- the plate count
that converts "OD in a co-culture well" to CFU per cancer cell, and the
colonisation efficiency that converts tumour CFU to swallowed CFU. Neither is in
the workbook. The module names both rather than inventing them, and reports the
requirement in a unit the team has actually realised, which is the part that
does not need them. See :func:`effective_dose_conclusion`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from . import data as D
from .sensors import QUORUM_HILL_PLUX
from . import lesion_size as L


class DoseExtrapolationError(RuntimeError):
    """Raised when an inversion would leave the measured dose range too far."""


#: The construct the team builds, and the two controls block 5 provides.
#: ``gfp`` carries a plasmid and expresses a non-effector protein, so it
#: controls for plasmid burden and for bacterial presence. ``EcN`` controls for
#: bacterial presence only. Convention 4 noted no empty-vector control for the
#: *growth* blocks; the *killing* block does have a plasmid-bearing control.
BUILT_CONSTRUCT: str = "GSDMD-SsrA"
CONTROLS: tuple[str, ...] = ("gfp", "EcN")

#: Doses in block 5, in the workbook's own units (OD of the bacterial dose).
MEASURED_DOSES: tuple[float, ...] = (6.0, 8.0, 10.0)

#: Co-culture exposure in block 5, h. The killing readout is an endpoint.
EXPOSURE_H: float = 24.0

#: CT26 subcutaneous volume doubling time, h. Fast-growing murine line.
CT26_DOUBLING_H: tuple[float, float] = (24.0, 48.0)
#: Human colorectal carcinoma volume doubling time, days. Orders of magnitude
#: slower than any xenograft; the clinical indication sits here, not above.
HUMAN_CRC_DOUBLING_D: tuple[float, float] = (100.0, 600.0)

#: How far outside the measured dose range an inversion may be reported.
#: A power law has no threshold, so extrapolating *down* is no safer than
#: extrapolating up -- both directions are bounded.
EXTRAPOLATION_LIMIT: float = 3.0

#: Fraction of tagged effector retained inside a 400 µm nodule (module 4.3:
#: 73.2 % is destroyed outside it).
NODULE_RETENTION: float = 1.0 - 0.732

#: Colonic mucosa gate-output margin from module 3.1, at quorum Hill 2.
COLONIC_MUCOSA_MARGIN: float = 21.852296

#: The fold margin this project requires of itself, declared rather than derived.
#: The loss criterion of eq. (4.6-8) demands at most 2.26x; we hold the design to
#: 10x so that the verdict does not turn on the parameters the criterion is most
#: sensitive to. Used as a pass line in modules 3.1 and 4.6 and on their figures.
ENGINEERING_MARGIN_REQUIREMENT: float = 10.0


# -- 1. the net dose-kill curve -------------------------------------------


def net_killing(
    wb: D.Workbook | None = None,
    *,
    construct: str = BUILT_CONSTRUCT,
    control: str = "gfp",
) -> pd.DataFrame:
    """Chassis-subtracted killing at each dose of block 5, with standard errors.

    Subtraction is within-block and within-dose, so convention 2 is respected:
    nothing here crosses between blocks 5 and 6.
    """
    wb = wb or D.load()
    block = wb.killing_block(5)
    rows = []
    for dose in MEASURED_DOSES:
        treated = block[(block.construct == construct) & (block.dose_od == dose)]["percent"]
        reference = block[(block.construct == control) & (block.dose_od == dose)]["percent"]
        if treated.empty or reference.empty:
            raise D.DataConventionError(
                f"block 5 has no {construct!r} or {control!r} at {dose} OD"
            )
        treated_summary = D.summarise(treated)
        control_summary = D.summarise(reference)
        se = float(
            np.sqrt(
                treated_summary.sd**2 / treated_summary.n
                + control_summary.sd**2 / control_summary.n
            )
        )
        rows.append(
            {
                "dose_od": dose,
                "raw_percent": treated_summary.mean,
                "control_percent": control_summary.mean,
                "net_percent": treated_summary.mean - control_summary.mean,
                "se": se,
                "n_treated": treated_summary.n,
                "n_control": control_summary.n,
            }
        )
    return pd.DataFrame(rows)


@dataclass(frozen=True)
class PowerLaw:
    """``net kill % = amplitude * dose ** exponent``, fitted in log-log."""

    exponent: float
    exponent_se: float
    amplitude: float
    r_squared: float
    control: str
    dose_range: tuple[float, float]

    def kill_percent(self, dose_od: float | np.ndarray) -> np.ndarray:
        return self.amplitude * np.asarray(dose_od, dtype=float) ** self.exponent

    def dose_for(self, kill_percent: float, *, strict: bool = True) -> float:
        """Invert the curve. Refuses a dose far outside the measured range.

        The curve is three points with no plateau and no threshold, so it
        carries no information about either. ``strict=False`` returns the value
        anyway, for callers that report the extrapolation alongside it.
        """
        if kill_percent <= 0.0:
            raise DoseExtrapolationError("required kill fraction must be positive")
        dose = float((kill_percent / self.amplitude) ** (1.0 / self.exponent))
        fold = self.extrapolation_fold(dose)
        if strict and fold > EXTRAPOLATION_LIMIT:
            raise DoseExtrapolationError(
                f"{kill_percent:.3g} % needs {dose:.3g} OD, which is {fold:.3g}x "
                f"outside the measured range {self.dose_range}; "
                f"the limit is {EXTRAPOLATION_LIMIT}x"
            )
        return dose

    def extrapolation_fold(self, dose_od: float) -> float:
        """How far outside the measured range a dose sits. 1.0 means inside."""
        low, high = self.dose_range
        if dose_od > high:
            return dose_od / high
        if dose_od < low:
            return low / dose_od
        return 1.0

    def inside_measured_range(self, dose_od: float) -> bool:
        return self.extrapolation_fold(dose_od) == 1.0


def fit_power_law(wb: D.Workbook | None = None, *, control: str = "gfp") -> PowerLaw:
    """Fit the net dose-kill curve of the built construct in log-log space."""
    frame = net_killing(wb, control=control)
    if (frame["net_percent"] <= 0).any():
        raise D.DataConventionError(
            f"net killing against {control!r} is non-positive at some dose; "
            "a log-log fit cannot be taken"
        )
    fit = stats.linregress(np.log(frame["dose_od"]), np.log(frame["net_percent"]))
    return PowerLaw(
        exponent=float(fit.slope),
        exponent_se=float(fit.stderr),
        amplitude=float(np.exp(fit.intercept)),
        r_squared=float(fit.rvalue**2),
        control=control,
        dose_range=(float(frame["dose_od"].min()), float(frame["dose_od"].max())),
    )


def exponent_interval(wb: D.Workbook | None = None) -> tuple[float, float]:
    """Exponent across both control choices. The spread is the control choice,
    not the fit error."""
    exponents = [fit_power_law(wb, control=c).exponent for c in CONTROLS]
    return (min(exponents), max(exponents))


# -- 2. the efficacy criterion --------------------------------------------


def required_kill_fraction(doubling_time_h: float, *, exposure_h: float = EXPOSURE_H) -> float:
    """Kill fraction over ``exposure_h`` that just matches proliferation.

    Control needs the kill rate to reach the growth rate ``r = ln2/T_double``.
    Over a window ``t`` the fraction that must be removed is
    ``1 - exp(-r t)``. Returned as a percentage, matching the assay's units.
    """
    if doubling_time_h <= 0:
        raise ValueError("doubling time must be positive")
    rate = np.log(2.0) / doubling_time_h
    return float(100.0 * (1.0 - np.exp(-rate * exposure_h)))


#: The four reference targets: the preclinical model and the clinical indication,
#: each at both ends of its reported doubling time.
TARGETS: dict[str, float] = {
    "CT26, 24 h doubling": CT26_DOUBLING_H[0],
    "CT26, 48 h doubling": CT26_DOUBLING_H[1],
    "Human CRC, 100 d doubling": HUMAN_CRC_DOUBLING_D[0] * 24.0,
    "Human CRC, 600 d doubling": HUMAN_CRC_DOUBLING_D[1] * 24.0,
}


# -- 3. the inversion ------------------------------------------------------


def dose_requirement_table(wb: D.Workbook | None = None) -> pd.DataFrame:
    """Required dose for every target, under both control choices."""
    wb = wb or D.load()
    rows = []
    for control in CONTROLS:
        law = fit_power_law(wb, control=control)
        for label, doubling in TARGETS.items():
            required = required_kill_fraction(doubling)
            dose = law.dose_for(required, strict=False)
            rows.append(
                {
                    "control": control,
                    "target": label,
                    "doubling_time_h": doubling,
                    "required_kill_percent": required,
                    "required_dose_od": dose,
                    "fold_of_highest_tested": dose / law.dose_range[1],
                    "extrapolation_fold": law.extrapolation_fold(dose),
                    "inside_measured_range": law.inside_measured_range(dose),
                }
            )
    return pd.DataFrame(rows)


def met_at_every_tested_dose(wb: D.Workbook | None = None) -> dict[str, bool]:
    """Which targets are already met at the lowest dose the team ran.

    This is the interpolation-free form of the answer. Where it is true, no
    curve and no extrapolation is needed -- the measured kill at 6 OD already
    exceeds the requirement.
    """
    wb = wb or D.load()
    verdicts: dict[str, bool] = {}
    for label, doubling in TARGETS.items():
        required = required_kill_fraction(doubling)
        achieved = min(
            float(net_killing(wb, control=c)["net_percent"].iloc[0]) for c in CONTROLS
        )
        verdicts[label] = achieved >= required
    return verdicts


def cube_law_compression(wb: D.Workbook | None = None) -> dict[str, float]:
    """How much the inversion shrinks the spread on the requirement side.

    The span of required kill fractions across all four targets, against the
    span of required doses it maps to. A power law of exponent ``b`` compresses
    by the ``b``-th root, which is why the answer survives not knowing the
    doubling time.
    """
    table = dose_requirement_table(wb)
    kill = table["required_kill_percent"]
    dose = table["required_dose_od"]
    kill_span = float(kill.max() / kill.min())
    dose_span = float(dose.max() / dose.min())
    return {
        "kill_fraction_span": kill_span,
        "dose_span": dose_span,
        "compression": kill_span / dose_span,
        "implied_exponent": float(np.log(kill_span) / np.log(dose_span)),
    }


def delivery_penalty(efficiency: float, *, exponent: float | None = None) -> float:
    """Dose multiplier that compensates a loss of delivered effector.

    In the well every molecule produced meets the cancer cells. In a nodule
    module 4.3 puts 73.2 % of the tagged effector outside it. A delivery
    efficiency ``eta`` is compensated by ``eta ** (-1/b)`` -- a cube root, so a
    large loss costs a small dose increase.
    """
    if not 0.0 < efficiency <= 1.0:
        raise ValueError("efficiency must be in (0, 1]")
    b = exponent if exponent is not None else fit_power_law().exponent
    return float(efficiency ** (-1.0 / b))


# -- 4. the dose depends on lesion radius ---------------------------------


def dose_vs_lesion_radius(
    radii_um: np.ndarray | None = None,
    *,
    reference_um: float = 400.0,
    quorum_hill: float = QUORUM_HILL_PLUX,
    exponent: float | None = None,
) -> pd.DataFrame:
    """Dose multiplier needed to hold a lesion of each radius at the reference kill.

    Gate output falls with radius (module 3.2), and killing rises as dose to the
    ``b``-th power, so the compensating dose goes as ``gate ** (-1/b)``. Below
    the oxygen penetration depth the hypoxia arm is pinned at its rim value, so
    the multiplier is large but finite -- basal expression, not zero.
    """
    if radii_um is None:
        radii_um = np.array([150.0, 180.0, 200.0, 250.0, 300.0, 400.0, 600.0, 1000.0, 2000.0])
    b = exponent if exponent is not None else fit_power_law().exponent
    axis = L.LesionSize(quorum_hill=quorum_hill)
    reference = float(axis.gate_output(reference_um))
    relative = np.asarray(axis.gate_output(radii_um), dtype=float) / reference
    return pd.DataFrame(
        {
            "radius_um": np.asarray(radii_um, dtype=float),
            "gate_relative_to_reference": relative,
            "dose_multiplier": relative ** (-1.0 / b),
            "has_hypoxic_core": np.asarray(radii_um, dtype=float)
            > axis.smallest_lesion_with_a_hypoxic_core_um,
        }
    )


def escalation_erodes_margin(
    wb: D.Workbook | None = None,
    *,
    radii_um: tuple[float, ...] = (150.0, 180.0, 250.0, 400.0),
    quorum_hill: float = QUORUM_HILL_PLUX,
) -> pd.DataFrame:
    """What a dose escalation costs in safety margin.

    Module 3.1's margins are **ratios** of gate output between sites, so raising
    the dose raises both sides and leaves them unchanged. What a ratio does not
    track is the distance to an absolute toxicity threshold. If off-target
    tolerance is set by absolute output, escalating by ``m`` consumes the
    colonic-mucosa margin to ``19.6 / m``.

    This is the joint constraint between chapters 3 and 4: the dose that reaches
    a micro-lesion is the dose that spends the safety margin.
    """
    wb = wb or D.load()
    law = fit_power_law(wb)
    size = dose_vs_lesion_radius(
        np.array(radii_um), quorum_hill=quorum_hill, exponent=law.exponent
    )
    worst = max(required_kill_fraction(d) for d in TARGETS.values())
    ct26_dose = law.dose_for(worst, strict=False)
    efficacy_multiplier = ct26_dose / law.dose_range[1]
    total = size["dose_multiplier"] * efficacy_multiplier
    return pd.DataFrame(
        {
            "radius_um": size["radius_um"],
            "size_multiplier": size["dose_multiplier"],
            "efficacy_multiplier": efficacy_multiplier,
            "total_escalation": total,
            "mucosa_margin_left": COLONIC_MUCOSA_MARGIN / total,
        }
    )


# -- 5. what counts as enough margin --------------------------------------
#
# Module 3.1 reports the tissue axis as fold ratios, and the wiki called 19.6x
# against colonic mucosa "comfortable" without saying what it is comfortable
# against. A fold is not a safety statement until it is converted into a rate
# and compared with something. These functions do that conversion, using the
# same dose-kill exponent as the efficacy side, so safety and efficacy are
# judged on one scale.

#: Colonic epithelial renewal time, days. The surface epithelium is replaced
#: from the crypt on a 3-5 day cycle. This is a *replacement cycle*, not a
#: doubling, so the rate is 1/T and not ln2/T -- unlike the tumour side, where
#: proliferation genuinely is exponential.
COLONIC_RENEWAL_D: tuple[float, float] = (3.0, 5.0)

#: The exponent to quote when the claim must not rest on the cube law. Linear
#: is the most conservative reading of how off-target exposure converts to
#: off-target loss: it credits the margin with no amplification at all.
CONSERVATIVE_EXPONENT: float = 1.0


def tolerable_offtarget_loss(
    renewal_time_h: float, *, exposure_h: float = EXPOSURE_H
) -> float:
    """Epithelial loss per exposure window that renewal replaces, in percent.

    Renewal is a replacement cycle, so the rate is ``1/T`` rather than
    ``ln2/T``. Loss below this is made good; loss above it is net denudation.
    """
    if renewal_time_h <= 0:
        raise ValueError("renewal time must be positive")
    return float(100.0 * (1.0 - np.exp(-exposure_h / renewal_time_h)))


def required_margin(
    *,
    target_kill_percent: float,
    tolerable_kill_percent: float,
    exponent: float | None = None,
) -> float:
    """Fold margin needed so the target is treated and the off-target site is not.

    Killing goes as exposure to the power ``b`` and a margin ``m`` divides
    off-target exposure by ``m``, so off-target loss is ``f_target * m**-b``.
    Requiring that to stay under what renewal replaces gives
    ``m >= (f_target / f_tolerable) ** (1/b)``.
    """
    if tolerable_kill_percent <= 0:
        raise ValueError("tolerable loss must be positive")
    b = exponent if exponent is not None else fit_power_law().exponent
    return float((target_kill_percent / tolerable_kill_percent) ** (1.0 / b))


def implied_offtarget_loss(
    margin: float, *, target_kill_percent: float, exponent: float | None = None
) -> float:
    """What a fold margin actually permits, as percent loss per 24 h.

    This is the form a reviewer can judge. "19.6x" is not a safety claim; "one
    cell in 2800 per day, against a renewal that replaces one in five" is.
    """
    if margin <= 0:
        raise ValueError("margin must be positive")
    b = exponent if exponent is not None else fit_power_law().exponent
    return float(target_kill_percent * margin ** (-b))


def margin_table(
    wb: D.Workbook | None = None,
    *,
    doubling_time_h: float = HUMAN_CRC_DOUBLING_D[0] * 24.0,
    renewal_time_d: float = 4.0,
    exponent: float | None = None,
) -> pd.DataFrame:
    """Every site's margin, restated as the off-target loss rate it permits.

    Defaults are the demanding end of the clinical indication (100 d doubling)
    and mid-range epithelial renewal. ``exponent=CONSERVATIVE_EXPONENT`` gives
    the reading that does not rely on the cube law.
    """
    from . import tissue as T

    wb = wb or D.load()
    b = exponent if exponent is not None else fit_power_law(wb).exponent
    target = required_kill_fraction(doubling_time_h)
    tolerable = tolerable_offtarget_loss(renewal_time_d * 24.0)
    axis = T.TissueAxis(anoxic_repression=10.0, glucose_repression=10.0)

    rows = []
    for _, site in axis.arms(wb).iterrows():
        margin = float(site.total_ratio)
        loss = implied_offtarget_loss(margin, target_kill_percent=target, exponent=b)
        rows.append(
            {
                "site": site.site,
                "label": site.label,
                "margin_fold": margin,
                "implied_loss_percent_24h": loss,
                "renewal_headroom": tolerable / loss,
                "above_renewal": loss > tolerable,
            }
        )
    return pd.DataFrame(rows)


def margin_requirement_is_modest(
    wb: D.Workbook | None = None, *, renewal_time_d: float = 4.0
) -> pd.DataFrame:
    """The margin the loss criterion actually demands, per target and exponent.

    It comes out below 2x everywhere, which is the point: the 19.6x the tissue
    axis delivers is not marginal against this criterion. What the criterion
    does not cover is the reason to keep the margin anyway -- see
    :func:`margin_criterion_covers_cell_loss_only`.
    """
    wb = wb or D.load()
    tolerable = tolerable_offtarget_loss(renewal_time_d * 24.0)
    fitted = fit_power_law(wb).exponent
    rows = []
    for label, doubling in TARGETS.items():
        target = required_kill_fraction(doubling)
        for name, b in (("fitted", fitted), ("conservative (linear)", CONSERVATIVE_EXPONENT)):
            rows.append(
                {
                    "target": label,
                    "exponent": name,
                    "required_kill_percent": target,
                    "tolerable_loss_percent": tolerable,
                    "required_margin_fold": required_margin(
                        target_kill_percent=target,
                        tolerable_kill_percent=tolerable,
                        exponent=b,
                    ),
                }
            )
    return pd.DataFrame(rows)


def margin_criterion_covers_cell_loss_only() -> dict[str, object]:
    """What this criterion does and does not license. Executable, so it travels.

    The criterion compares effector-driven epithelial loss with epithelial
    renewal. It says nothing about inflammation, and the effector is a pyroptosis
    executioner whose entire therapeutic rationale is that it is inflammatory --
    IL-1beta and IL-18 release is the mechanism module 6 depends on. A
    sub-lethal, sub-renewal rate of pyroptosis in colonic mucosa is therefore
    not obviously harmless, and nothing in this project bounds it.

    So the loss criterion is a **lower bound** on the margin required, not the
    requirement. It is reported because a fold with no criterion attached cannot
    be reviewed at all, not because it settles the question.
    """
    return {
        "covers": "effector-driven epithelial cell loss against crypt renewal",
        "does_not_cover": "inflammation from IL-1beta / IL-18 release",
        "why_that_matters": "the effector is a pyroptosis executioner; module 6 depends on it",
        "is_a_lower_bound_on_the_requirement": True,
        "settles_the_question": False,
        "cheapest_bound": "IL-1beta release from a colonic epithelial line at the "
        "off-target gate output, rather than at full induction",
    }


# -- 6. what the module does and does not claim ---------------------------


def effective_dose_conclusion(wb: D.Workbook | None = None) -> dict[str, object]:
    """Executable record of the module's scope, so it cannot drift in the wiki.

    The two missing bridges are named here rather than filled with a literature
    value, because both are one measurement away and neither is in the workbook.
    """
    wb = wb or D.load()
    law = fit_power_law(wb)
    table = dose_requirement_table(wb)
    human = table[table["target"].str.startswith("Human")]
    ct26 = table[table["target"].str.startswith("CT26")]
    return {
        "derived_from_team_data": True,
        "exponent_interval": exponent_interval(wb),
        "human_requirement_inside_measured_range": bool(
            human["required_dose_od"].max() <= law.dose_range[1]
        ),
        "human_fold_of_highest_tested": (
            float(human["fold_of_highest_tested"].min()),
            float(human["fold_of_highest_tested"].max()),
        ),
        "ct26_fold_of_highest_tested": (
            float(ct26["fold_of_highest_tested"].min()),
            float(ct26["fold_of_highest_tested"].max()),
        ),
        "reports_oral_cfu": False,
        "missing_bridge_1": "plate count of the co-culture well: OD -> CFU per cancer cell",
        "missing_bridge_2": "CFU/g tumour after oral gavage: tumour CFU -> swallowed CFU",
        "unit_of_the_answer": "multiple of a co-culture dose the team has run",
        "depends_on_declared_doubling_time": True,
        "doubling_time_is_compressed_by_cube_root": True,
    }
