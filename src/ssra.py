"""Module 3.4 -- SsrA as a post-translational safety valve.

The supervisor's question was whether the degron is "a sufficient safety valve or
only an auxiliary one" (`SsrA 是足够的安全阀，还是只是辅助？`), and what the
effector's half-life in normal tissue actually is.

Three things are settled here, two of them from the team's own data:

1. **Keep the tag.** The decision reduces to a closed form: keep it iff the
   potency it costs is less than the biomass it buys. It is, but only by 21 %.
2. **Half-life in normal tissue is ~2 h** with the tag, ~8.7 h without.
3. **The degron amplifies the promoter's selectivity** rather than merely
   damping output, because ClpXP saturates. That part is structural, not fitted.

The 9.23 module carried this as an unresolved 3.3x spread in the potency cost.
It is not unresolved: the high end came from pairing a block-5 numerator with a
block-6 denominator, which ``DATA_CONVENTIONS.md`` convention 2 forbids for
exactly the reason it forbade the 11.4x selectivity index. See
:func:`measured_anchors`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import data as D

#: Natural turnover of untagged GSDMD-N in EcN, 1/h (dilution + proteolysis).
DELTA_NATURAL: float = 0.08
#: Degradation added by the SsrA tag as built, 1/h.
DELTA_BUILT: float = 0.35
#: Condition in which the circuit is induced and the chassis cost is visible.
INDUCED_CONDITION: str = "有氧有酸"
UNINDUCED_CONDITION: str = "有氧无酸"


@dataclass(frozen=True)
class Anchors:
    """The two measured states the trade-off is anchored to."""

    biomass_ratio: float          # untagged / tagged 24 h OD, induced
    potency_ratio: float          # untagged / tagged per-OD killing
    potency_ratio_source: str
    rejected_potency_ratio: float | None
    rejection_reason: str | None


def measured_anchors(wb: D.Workbook | None = None) -> Anchors:
    """Read both anchors from the workbook, applying convention 2.

    The potency ratio must pair two constructs measured in the *same* block.
    Block 5 measures both at 10 OD, so it qualifies. Block 6's apparent ratio
    does not: its GSDMD cancer row duplicates block 5, so dividing it by block
    6's independently measured GSDMD-SsrA mixes two experiments that differ by
    an order of magnitude overall.
    """
    wb = wb or D.load()

    at24 = wb.growth[wb.growth.time_h == 24.0]
    tagged = at24[(at24.construct == "GSDMD-SsrA") & (at24.condition == INDUCED_CONDITION)]
    untagged = at24[(at24.construct == "GSDMD") & (at24.condition == INDUCED_CONDITION)]
    biomass_ratio = float(untagged["od"].mean() / tagged["od"].mean())

    duplicated = D.block6_duplicated_constructs(wb)

    def ratio(block: int) -> float:
        rows = wb.killing[
            (wb.killing.block == block)
            & (wb.killing.cell_line == "ct26")
            & (wb.killing.dose_od == 10.0)
        ]
        return float(
            rows[rows.construct == "GSDMD"]["percent"].mean()
            / rows[rows.construct == "GSDMD-SsrA"]["percent"].mean()
        )

    rejected, reason = None, None
    if "GSDMD" in duplicated:
        rejected = ratio(6)
        reason = (
            "block 6's GSDMD cancer row duplicates block 5, so this ratio pairs a "
            "block-5 numerator with a block-6 denominator -- the same cross-block "
            "error that inflated the 11.4x selectivity index"
        )

    return Anchors(
        biomass_ratio=biomass_ratio,
        potency_ratio=ratio(5),
        potency_ratio_source="block 5, both constructs measured at 10 OD",
        rejected_potency_ratio=rejected,
        rejection_reason=reason,
    )


# -- the decision, in closed form -----------------------------------------


def potency_ratio_by_dose(wb: D.Workbook | None = None) -> pd.DataFrame:
    """The potency cost at each dose of block 5, with the decision at each.

    The ratio is not constant across the dose series and is not significant at
    n = 3 (the 9.23 statistics put p = 0.24 at 10 OD). Reporting all three doses
    is what makes the conclusion robust rather than resting on one anchor.
    """
    wb = wb or D.load()
    anchors = measured_anchors(wb)
    crossover = crossover_potency_ratio(anchors.biomass_ratio)

    rows = []
    for dose in D.DOSES_OD:
        sel = wb.killing[(wb.killing.block == 5) & (wb.killing.dose_od == dose)]
        untagged = sel[sel.construct == "GSDMD"]["percent"]
        tagged = sel[sel.construct == "GSDMD-SsrA"]["percent"]
        ratio = float(untagged.mean() / tagged.mean())
        rows.append(
            {
                "dose_od": dose,
                "untagged_percent": float(untagged.mean()),
                "tagged_percent": float(tagged.mean()),
                "n_untagged": int(untagged.size),
                "potency_ratio": ratio,
                "crossover": crossover,
                "keep_tag": ratio < crossover,
                "margin": crossover / ratio,
            }
        )
    return pd.DataFrame(rows)


def crossover_potency_ratio(biomass_ratio: float) -> float:
    """Potency cost at which keeping the tag stops paying.

    Delivered exposure is ``viability x potency``. Removing the tag multiplies
    potency by ``r`` and multiplies biomass by ``biomass_ratio``, so

        delivery(tagged) / delivery(untagged) = 1 / (biomass_ratio * r)

    which exceeds 1 exactly when ``r < 1 / biomass_ratio``. **Keep the tag iff
    the potency it costs is less than the biomass it buys.** No functional form
    is assumed: the result follows from the two measured ratios alone.
    """
    return 1.0 / biomass_ratio


def keep_tag_margin(anchors: Anchors) -> float:
    """How much better keeping the tag is, as a factor. Below 1 means drop it."""
    return crossover_potency_ratio(anchors.biomass_ratio) / anchors.potency_ratio


def decision_scan(
    anchors: Anchors, potency_ratios: np.ndarray | None = None
) -> pd.DataFrame:
    """Delivered-exposure ratio across a range of potency costs."""
    if potency_ratios is None:
        potency_ratios = np.linspace(1.0, 5.0, 81)
    crossover = crossover_potency_ratio(anchors.biomass_ratio)
    return pd.DataFrame(
        {
            "potency_ratio": potency_ratios,
            "delivery_tagged_over_untagged": crossover / potency_ratios,
            "keep_tag": potency_ratios < crossover,
        }
    )


# -- tag strength as a continuous knob ------------------------------------


@dataclass(frozen=True)
class TradeoffModel:
    """Steady-state pool, chassis viability and export, as functions of tag strength.

    ``pool(delta) = (d_nat + d_built) / (d_nat + delta)`` -- the intracellular
    GSDMD-N pool, normalised to 1 at the tag strength actually built.

    ``viability(delta) = exp(-lam * pool)`` -- an exponential because two
    measured states can identify exactly one free parameter; a Hill form would
    need a midpoint and a coefficient the data cannot separate.

    ``potency(delta) = pool / (k_export + pool)`` -- saturating because export
    across the outer membrane, not the size of the pool, limits delivery.
    """

    delta_natural: float = DELTA_NATURAL
    delta_built: float = DELTA_BUILT
    lam: float = 0.0
    k_export: float = 1.0

    @classmethod
    def from_anchors(cls, anchors: Anchors) -> "TradeoffModel":
        base = cls()
        pool_untagged = base.pool(0.0)
        lam = -np.log(anchors.biomass_ratio) / (pool_untagged - 1.0)
        r = anchors.potency_ratio
        if r <= 1.0:
            raise ValueError(
                f"potency ratio {r:.2f} <= 1: the data says the tag costs no potency "
                "at this dose, so the saturating-export form has no free parameter to "
                "identify. Use the closed-form decision instead -- it needs no "
                "functional assumption."
            )
        if r >= pool_untagged:
            raise ValueError(
                f"potency ratio {r:.2f} exceeds the pool ratio {pool_untagged:.2f}; "
                "removing the tag cannot raise killing by more than it raises the pool"
            )
        k_export = pool_untagged * (r - 1.0) / (pool_untagged - r)
        return cls(base.delta_natural, base.delta_built, float(lam), float(k_export))

    def pool(self, delta: float | np.ndarray) -> float | np.ndarray:
        return (self.delta_natural + self.delta_built) / (self.delta_natural + delta)

    def viability(self, delta: float | np.ndarray) -> float | np.ndarray:
        return np.exp(-self.lam * self.pool(delta))

    def potency(self, delta: float | np.ndarray) -> float | np.ndarray:
        pool = self.pool(delta)
        return pool / (self.k_export + pool)

    def delivery(self, delta: float | np.ndarray) -> float | np.ndarray:
        return self.viability(delta) * self.potency(delta)

    def optimum_delta(self, grid: np.ndarray | None = None) -> float:
        grid = np.linspace(0.0, 2.0, 4001) if grid is None else grid
        return float(grid[np.argmax(self.delivery(grid))])

    def curve(self, grid: np.ndarray | None = None) -> pd.DataFrame:
        grid = np.linspace(0.0, 1.5, 301) if grid is None else grid
        built = self.delivery(self.delta_built)
        return pd.DataFrame(
            {
                "delta_ssra": grid,
                "pool": self.pool(grid),
                "viability": self.viability(grid),
                "potency": self.potency(grid),
                "delivery": self.delivery(grid),
                "delivery_vs_built": self.delivery(grid) / built,
            }
        )


def half_life_h(delta: float) -> float:
    """Effector half-life at a given total first-order turnover rate."""
    return float(np.log(2.0) / delta)


def half_life_table() -> pd.DataFrame:
    """The supervisor's question: what is the half-life in normal tissue?"""
    rows = [
        ("untagged", DELTA_NATURAL, "natural turnover only"),
        ("SsrA as built", DELTA_NATURAL + DELTA_BUILT, "tag active, ClpXP unsaturated"),
        ("double SsrA (2x tag)", DELTA_NATURAL + 2 * DELTA_BUILT, "hypothetical"),
    ]
    return pd.DataFrame(
        [
            {"variant": name, "delta_total_per_h": d, "half_life_h": half_life_h(d), "note": note}
            for name, d, note in rows
        ]
    )


# -- why the degron is more than a damper ---------------------------------


@dataclass(frozen=True)
class ClpXPCapacity:
    """ClpXP is a finite enzyme, so the degron's strength depends on its load.

    Degradation is Michaelis-Menten, ``v = vmax * P / (km + P)``, giving an
    *effective* first-order rate ``k_eff(P) = vmax / (km + P)`` that falls as
    the pool grows. So the same tag degrades hard in normal tissue, where the
    only substrate is promoter leak, and is outrun in the tumour, where the gate
    is open.

    The consequence is the useful part: the final protein ratio between tumour
    and normal tissue **exceeds** the promoter's transcription ratio. The degron
    amplifies selectivity instead of merely scaling both sites down. This is a
    structural property of saturable degradation, not a fitted result -- but
    ``vmax`` and ``km`` for this substrate in EcN are unknown, so the module
    reports the *window* they must fall in rather than a predicted fold.
    """

    vmax: float   # µM/h, ClpXP capacity for this substrate
    km: float     # µM
    gamma: float = 0.35  # 1/h, growth dilution

    def steady_state(self, production: float) -> float:
        """Solve ``production = vmax*P/(km+P) + gamma*P`` for P >= 0."""
        a = self.gamma
        b = self.gamma * self.km + self.vmax - production
        c = -production * self.km
        disc = b * b - 4 * a * c
        return float((-b + np.sqrt(disc)) / (2 * a))

    def effective_rate(self, pool: float) -> float:
        return float(self.vmax / (self.km + pool))

    def amplification(self, leak_production: float, induced_production: float) -> float:
        """Protein-level tumour/normal ratio divided by the transcription ratio.

        A value above 1 means the degron sharpened the promoter's discrimination.
        """
        p_norm = self.steady_state(leak_production)
        p_tum = self.steady_state(induced_production)
        transcription_ratio = induced_production / leak_production
        return float((p_tum / p_norm) / transcription_ratio)


def capacity_window(leak_production: float, induced_production: float) -> tuple[float, float]:
    """ClpXP capacity must sit between the leak rate and the induced rate.

    Below the leak rate the degron is saturated everywhere and protects nothing;
    above the induced rate it is unsaturated everywhere and merely scales both
    sites down without amplifying. Useful amplification requires

        leak_production < vmax < induced_production.
    """
    return (leak_production, induced_production)


def amplification_scan(
    leak_production: float = 1.0,
    induced_production: float = 100.0,
    km: float = 1.0,
    gamma: float = 0.35,
    vmax_grid: np.ndarray | None = None,
) -> pd.DataFrame:
    if vmax_grid is None:
        vmax_grid = np.logspace(-1, 3, 120)
    rows = []
    for vmax in vmax_grid:
        cap = ClpXPCapacity(vmax=float(vmax), km=km, gamma=gamma)
        rows.append(
            {
                "vmax": float(vmax),
                "in_window": leak_production < vmax < induced_production,
                "amplification": cap.amplification(leak_production, induced_production),
                "normal_half_life_h": half_life_h(
                    cap.effective_rate(cap.steady_state(leak_production)) + gamma
                ),
                "tumour_half_life_h": half_life_h(
                    cap.effective_rate(cap.steady_state(induced_production)) + gamma
                ),
            }
        )
    return pd.DataFrame(rows)
