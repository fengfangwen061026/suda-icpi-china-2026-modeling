"""Module 3.3 -- can the AND gate stay OFF in the colon lumen after oral dosing?

The supervisor asked this twice: "口服后不同肠道区域的触发风险" and "正常肠道也有
低氧和乳酸吗". The 9.23 tissue axis never evaluated the lumen -- only mucosa and
well-perfused tissue -- so the question is open.

It matters more than it looks, because of a finding that is now settled from the
team's own data (``DATA_CONVENTIONS.md``): the gate is **lactate-dominated**.
Hypoxia contributes 1.18-1.33x at endpoint; lactate is necessary and nearly
sufficient. So the lumen's lactate load is close to the whole story.

The experiment that would pin the lactate sensor's EC50 will not be run this
cycle. This module therefore does not ask "what is the margin"; it asks the
inverted question, which existing data *can* answer:

    For which sensor parameters is the lumen held OFF while the tumour is ON?

The answer turns out not to need the parameters at all for two of the three
candidate safety mechanisms, because both designed sensors are monotone in their
stimulus and the lumen presents *more* of both stimuli than the tumour does.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import sensors as S

CONFIG = Path(__file__).resolve().parent.parent / "config" / "tissue_sites.csv"
TARGET = "tumour_core"
LUMEN_SITES = ("colon_lumen_healthy", "colon_lumen_faecal", "colon_lumen_dysbiotic")


def load_sites(path: Path | str = CONFIG) -> pd.DataFrame:
    sites = pd.read_csv(path)
    sites["anoxic"] = sites["anoxic"].astype(bool)
    sites["glucose_rich"] = sites["glucose_rich"].astype(bool)
    return sites.set_index("site")


# -- the parameter-free part ----------------------------------------------


@dataclass(frozen=True)
class ArmVerdict:
    """Whether one designed input arm can discriminate a site, and how."""

    site: str
    label: str
    arm: str
    target_stimulus: float
    offsite_stimulus: float
    anti_selective: bool
    wt_ratio: float | None

    def __str__(self) -> str:
        if self.anti_selective:
            verdict = "ANTI-SELECTIVE for every EC50 / Hill / basal"
        else:
            verdict = f"can discriminate; wild-type gives {self.wt_ratio:.2f}x"
        return f"  {self.arm:8} vs {self.label:28} {verdict}"


def arm_verdicts(sites: pd.DataFrame | None = None) -> list[ArmVerdict]:
    """Direction of each designed arm at each off-target site.

    This is the core result and it uses no fitted parameter. Both arms are
    monotone in their stimulus, so a site presenting at least as much stimulus
    as the tumour cannot be discriminated against by that arm, whatever its
    parameters.
    """
    sites = load_sites() if sites is None else sites
    target = sites.loc[TARGET]
    lactate_sensor = S.LactateSensor()
    verdicts: list[ArmVerdict] = []

    for site, row in sites.iterrows():
        if site == TARGET:
            continue

        anti = S.is_structurally_anti_selective(target.lactate_mM, row.lactate_mM)
        verdicts.append(
            ArmVerdict(
                site=str(site),
                label=row.label,
                arm="lactate",
                target_stimulus=float(target.lactate_mM),
                offsite_stimulus=float(row.lactate_mM),
                anti_selective=anti,
                wt_ratio=None
                if anti
                else S.lactate_discrimination(
                    target.lactate_mM, row.lactate_mM, lactate_sensor
                ),
            )
        )

        anti_o2 = S.is_structurally_anti_selective(
            S.hypoxia_stimulus(target.o2_percent), S.hypoxia_stimulus(row.o2_percent)
        )
        hypoxia = S.HypoxiaSensor()
        verdicts.append(
            ArmVerdict(
                site=str(site),
                label=row.label,
                arm="hypoxia",
                target_stimulus=S.hypoxia_stimulus(target.o2_percent),
                offsite_stimulus=S.hypoxia_stimulus(row.o2_percent),
                anti_selective=anti_o2,
                wt_ratio=None
                if anti_o2
                else float(hypoxia(target.o2_percent) / hypoxia(row.o2_percent)),
            )
        )
    return verdicts


# -- the parametric part: what would the lactate arm need? ----------------


def lactate_specification(
    offsite_lactate_mM: float,
    *,
    target_lactate_mM: float = 8.0,
    required_fold: float = 10.0,
    ec50_grid: np.ndarray | None = None,
    hill_grid: np.ndarray | None = None,
    basal: float = 0.0,
) -> pd.DataFrame:
    """Which (EC50, Hill) pairs reach ``required_fold`` discrimination.

    ``basal=0`` is deliberately the most generous case: any non-zero basal
    expression caps the achievable ratio at ``1/basal``, so a design that fails
    here fails for every real promoter. With the wild-type basal of ~1/7 the
    ceiling is 7x whatever the other parameters do.
    """
    ec50_grid = np.logspace(-1, 2.5, 120) if ec50_grid is None else ec50_grid
    hill_grid = np.array([1.0, 1.5, 2.0, 3.0, 4.0]) if hill_grid is None else hill_grid

    rows = []
    for hill in hill_grid:
        for ec50 in ec50_grid:
            sensor = S.LactateSensor(ec50_mM=ec50, hill=hill, basal=basal)
            ratio = float(sensor(target_lactate_mM) / sensor(offsite_lactate_mM))
            rows.append(
                {
                    "ec50_mM": ec50,
                    "hill": hill,
                    "ratio": ratio,
                    "meets_requirement": ratio >= required_fold,
                }
            )
    return pd.DataFrame(rows)


def minimum_ec50_for_fold(
    offsite_lactate_mM: float,
    *,
    target_lactate_mM: float = 8.0,
    required_fold: float = 10.0,
    hill: float = 1.0,
    basal: float = 0.0,
) -> float | None:
    """Smallest EC50 reaching the required fold, or ``None`` if unreachable.

    Returns ``None`` both when the site is structurally anti-selective and when
    the requirement simply cannot be met at this Hill coefficient.
    """
    grid = lactate_specification(
        offsite_lactate_mM,
        target_lactate_mM=target_lactate_mM,
        required_fold=required_fold,
        hill_grid=np.array([hill]),
        basal=basal,
    )
    feasible = grid[grid.meets_requirement]
    if feasible.empty:
        return None
    return float(feasible["ec50_mM"].min())


def basal_ceiling(basal: float) -> float:
    """Maximum discrimination any Hill sensor with this basal level can reach."""
    if basal <= 0:
        return float("inf")
    return 1.0 / basal


def max_achievable_discrimination(
    offsite_lactate_mM: float,
    *,
    target_lactate_mM: float = 8.0,
    hill: float = 1.0,
    basal: float = 0.0,
) -> float:
    """Supremum of the lactate arm's discrimination, analytically.

    For a Hill sensor, pushing EC50 far above both concentrations puts them both
    on the initial power-law stretch, where ``f ~ L**hill``. The ratio therefore
    approaches ``(L_target / L_offsite) ** hill`` from below and never exceeds
    it. A non-zero basal level caps it again at ``1 / basal``. The binding
    constraint is whichever is smaller:

        sup ratio = min( (L_t / L_off) ** hill , 1 / basal )

    So the concentration ratio between the two sites, not the sensor's midpoint,
    sets what is possible. Tuning EC50 only decides how close to that bound the
    design gets.
    """
    if offsite_lactate_mM >= target_lactate_mM:
        return 1.0
    shape = (target_lactate_mM / offsite_lactate_mM) ** hill
    return float(min(shape, basal_ceiling(basal)))


def required_hill_for_fold(
    offsite_lactate_mM: float,
    *,
    target_lactate_mM: float = 8.0,
    required_fold: float = 10.0,
) -> float | None:
    """Hill coefficient the lactate sensor would need, or ``None`` if impossible.

    Inverts :func:`max_achievable_discrimination` at zero basal:
    ``hill >= ln(required_fold) / ln(L_target / L_offsite)``.
    """
    if offsite_lactate_mM >= target_lactate_mM:
        return None
    return float(
        np.log(required_fold) / np.log(target_lactate_mM / offsite_lactate_mM)
    )


# -- the one mechanism that is not anti-selective -------------------------


@dataclass(frozen=True)
class QuorumMargin:
    """AHL accumulation needs density *and* retention; the lumen lacks retention.

    ``[AHL]_ss ~ beta_Q * f_O2 * N / (delta_Q + washout)``. In the lumen the
    hypoxia term is maximal and the EcN density after oral dosing can rival the
    tumour's, so the only term that can hold the gate OFF is washout: luminal
    transit replaces the content on a timescale of hours, whereas a colonised
    nodule retains its signal.

    This is the sole candidate safety mechanism among the designed inputs that
    is not structurally anti-selective in the lumen. It is also entirely
    unmeasured here, so it is reported as a *requirement*, not a result.
    """

    transit_time_h: float
    ahl_halflife_h: float

    @property
    def retention_ratio(self) -> float:
        """Luminal AHL steady state relative to a retentive compartment."""
        k_decay = np.log(2.0) / self.ahl_halflife_h
        k_washout = 1.0 / self.transit_time_h
        return float(k_decay / (k_decay + k_washout))


def quorum_requirement(
    transit_times_h=(1.0, 3.0, 6.0, 12.0, 24.0),
    ahl_halflife_h: float = 8.0,
) -> pd.DataFrame:
    rows = []
    for transit in transit_times_h:
        margin = QuorumMargin(transit, ahl_halflife_h)
        rows.append(
            {
                "transit_time_h": transit,
                "ahl_halflife_h": ahl_halflife_h,
                "luminal_retention": margin.retention_ratio,
                "suppression_fold": 1.0 / margin.retention_ratio,
            }
        )
    return pd.DataFrame(rows)


def required_repression_for_fold(
    *,
    required_fold: float = 10.0,
    target_lactate_mM: float = 8.0,
) -> pd.DataFrame:
    """How strong the native repression must be to hold each luminal site OFF.

    Inverts the rescue: with a de-repressed sensor the lumen/tumour
    discrimination is ``d0`` (at or below 1 in the worst sites). Applying a
    surviving-activity fraction ``r`` only in the lumen gives ``d0 / r``, so

        r <= d0 / required_fold,  i.e. repression fold >= required_fold / d0.

    This is the specification to check the native promoter's literature
    characterisation against.
    """
    sites = load_sites()
    engineered = S.LactateSensor()
    tumour = float(engineered(target_lactate_mM))

    rows = []
    for site in LUMEN_SITES:
        row = sites.loc[site]
        d0 = tumour / float(engineered(row.lactate_mM))
        rows.append(
            {
                "site": site,
                "label": row.label,
                "lactate_mM": float(row.lactate_mM),
                "derepressed_discrimination": d0,
                "required_repression_fold": required_fold / d0,
            }
        )
    return pd.DataFrame(rows)


def native_repression_rescue(
    *,
    anoxic_repression: float = 0.1,
    glucose_repression: float = 0.1,
    target_lactate_mM: float = 8.0,
) -> pd.DataFrame:
    """What the native promoter's documented repressions buy.

    **Resolved 2026-10-08.** The part is ``BBa_M36021``, documented in the
    team's own 2026-07-15 design note as "E. coli lldPRD operon promoter" --
    i.e. the *native* promoter, not an ALPaGA-style de-repressed variant. Both
    repressions are therefore retained.

    This matters because the two environments differ in exactly the two ways the
    native promoter is sensitive to:

    =================  ===================  ========================
    .                  Colon lumen          Tumour core
    =================  ===================  ========================
    oxygen             anoxic (0 %)         hypoxic but not anoxic
    glucose            dietary, proximally  depleted (Warburg)
                       glucose-rich
    =================  ===================  ========================

    So the native repressions engage in the lumen and relax in the tumour --
    supplying precisely the discrimination that neither designed arm can.

    The team's own reporter data is consistent with this: at **1 % O2** plus
    20 mM lactate the circuit reaches 97.9 % GFP-positive, its highest corner,
    so the promoter is clearly not repressed at 1 % O2. The lumen is 0 %. The
    untested gap is therefore 0 % versus 1 %, not whether the mechanism exists.

    The repression strengths remain placeholders; use
    :func:`required_repression_for_fold` for what they would need to be.
    """
    sites = load_sites()
    native = S.LactateSensor(
        anoxic_repression=anoxic_repression, glucose_repression=glucose_repression
    )
    engineered = S.LactateSensor()

    rows = []
    for site in LUMEN_SITES:
        row = sites.loc[site]
        for name, sensor in (("native (repressed)", native), ("engineered (de-repressed)", engineered)):
            lumen = float(
                sensor(row.lactate_mM, anoxic=bool(row.anoxic), glucose_rich=bool(row.glucose_rich))
            )
            tumour = float(sensor(target_lactate_mM, anoxic=False, glucose_rich=False))
            rows.append(
                {
                    "site": site,
                    "label": row.label,
                    "variant": name,
                    "lumen_activity": lumen,
                    "tumour_activity": tumour,
                    "discrimination": tumour / lumen,
                }
            )
    return pd.DataFrame(rows)


# -- the one assumption the luminal argument cannot do without -------------


def single_structural_assumption(wb: "D.Workbook | None" = None) -> dict[str, object]:
    """The project's only single point of failure, stated as a record.

    Every other open parameter in this project widens an interval. This one
    **inverts a conclusion**, and it is a binary with no data behind it.

    The luminal safety argument runs: the native lldPRD promoter keeps its
    anoxic and glucose repression, the colon lumen is anoxic and proximally
    glucose-rich, the tumour core is hypoxic but *not* anoxic and has its
    glucose consumed, so the repressions engage in the lumen and relax in the
    tumour. Everything downstream of that -- the bottleneck margin, which site
    is the bottleneck, the recommendation against a de-repressed variant --
    follows from the single binary "0 % is anoxic, 0.5 % is not".

    What the team's data does and does not say:

    * At **1 % O2** with lactate the circuit reaches its highest corner, 97.9 %
      positive. So the promoter is **not** repressed at 1 %, which is what the
      tumour side needs. That half is measured.
    * The lumen is **0 %**. Nothing in the workbook is at 0 % O2. That half is
      assumed.

    The swing is the whole argument: with the repressions the luminal sites sit
    at 23-60x, without them at 0.23-0.60x. Not a wider interval -- a sign
    change.

    The requirement is modest and that is the reason to think it holds: a 10x
    margin needs 4.4x at the healthy lumen, 9.2x at faecal level and 11.5x in
    dysbiosis, against two native repressions each reported as strong on its
    own. But "modest and reported" is not "measured here".
    """
    sites = load_sites()
    with_repression = native_repression_rescue()
    needed = required_repression_for_fold()
    repressed = with_repression[with_repression.variant == "native (repressed)"]
    derepressed = with_repression[with_repression.variant == "engineered (de-repressed)"]
    return {
        "assumption": "the colon lumen is anoxic (0 % O2) and the tumour core is not (0.5 %)",
        "form": "binary flag, not a fitted parameter",
        "measured_half": "1 % O2 + lactate is the highest reporter corner, 97.9 % positive",
        "assumed_half": "no 0 % O2 condition exists in the workbook",
        "lactate_arm_with_repression": (
            float(repressed.discrimination.min()),
            float(repressed.discrimination.max()),
        ),
        "lactate_arm_without": (
            float(derepressed.discrimination.min()),
            float(derepressed.discrimination.max()),
        ),
        "failure_mode": "sign change, not a wider interval",
        "worst_case_repression_needed": float(needed.required_repression_fold.max()),
        "is_the_only_single_point_of_failure": True,
        "experiment": "the reporter at 0 % O2 against 1 %, lldPRD-only, one plate",
        "luminal_sites": int(sites.anoxic.sum()),
    }
