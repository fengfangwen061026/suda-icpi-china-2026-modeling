"""One parameter table for the whole project, and a guard rail that keeps it true.

Every number this project uses lives in the module that uses it, documented in
place with its unit and its source. That is right for the code and wrong for a
reader, who should not have to open eleven files to audit a model. So there is
also ``config/parameters.csv``.

A hand-maintained second copy of thirty numbers is normally a liability: it goes
stale the first time someone tunes a constant, and then it misleads more than it
helps. This one cannot. Every row names the thing it describes --
``sensors.EC50_LACTATE_WT``, ``dose.CT26_DOUBLING_H``, or a fitted quantity by
key -- and :func:`check` resolves each reference against the live code and
compares. ``tests/test_parameters.py`` runs that check, so the table and the
code cannot disagree without a test failing.

Reference syntax
----------------
``module.ATTRIBUTE``                  a module-level constant
``module.Class.field``                a dataclass field default
``module.MAPPING[key]``               an entry of a dict keyed by string
``module.SEQUENCE[0]``                an element of a tuple
``fitted:name``                       a value computed from the workbook; the
                                      callables are registered in :data:`FITTED`

Evidence grades extend the project's three with two that the original scheme had
no slot for:

``calibration``   fitted to team data
``scenario``      literature prior or declared assumption
``derived``       computed from other entries rather than assumed or fitted
``protocol``      a threshold this project declared before using it
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

TABLE = Path(__file__).resolve().parent.parent / "config" / "parameters.csv"

#: Relative tolerance when comparing the table against the code.
TOLERANCE: float = 5e-6

#: ``literature_prior`` is the grade `config/tissue_sites.csv` already used:
#: a value measured by somebody else on a comparable system, as distinct
#: from ``scenario``, which is a value we declared. Two sensor parameters
#: were promoted from scenario to literature_prior on 2026-10-14 when the
#: measurements were found -- see WIKI_DRAFT.md 2.5.
EVIDENCE_GRADES: tuple[str, ...] = (
    "calibration", "literature_prior", "scenario", "derived", "protocol",
)


class ParameterDriftError(RuntimeError):
    """The table and the code disagree about a value."""


def _fitted_values() -> dict[str, float]:
    """Quantities that are computed from the workbook rather than declared."""
    from . import data as D
    from . import dose as X
    from . import ssra as S

    wb = D.load()
    anchors = S.measured_anchors(wb)
    law_gfp = X.fit_power_law(wb, control="gfp")
    return {
        "dose_exponent_gfp": law_gfp.exponent,
        "dose_amplitude_gfp": law_gfp.amplitude,
        "biomass_ratio": anchors.biomass_ratio,
        "potency_ratio": anchors.potency_ratio,
        "selectivity_index": float(D.selectivity_index(wb, "GSDMD-SsrA").index),
    }


#: Resolved lazily, because loading the workbook for a table read is wasteful.
FITTED: dict[str, float] | None = None


def _fitted(name: str) -> float:
    global FITTED
    if FITTED is None:
        FITTED = _fitted_values()
    if name not in FITTED:
        raise ParameterDriftError(f"unknown fitted quantity {name!r}")
    return FITTED[name]


def resolve(reference: str) -> object:
    """Look up what a ``code_reference`` points at, in the live code."""
    if reference.startswith("fitted:"):
        return _fitted(reference.split(":", 1)[1])

    key: str | int | None = None
    if reference.endswith("]"):
        reference, raw = reference[:-1].split("[", 1)
        key = int(raw) if raw.lstrip("-").isdigit() else raw

    module_name, _, path = reference.partition(".")
    target: object = importlib.import_module(f"{__package__}.{module_name}")
    for piece in path.split("."):
        target = getattr(target, piece)
    if key is not None:
        target = target[key]  # type: ignore[index]
    return target


def load(path: Path | str = TABLE) -> pd.DataFrame:
    """The parameter table, as authored."""
    frame = pd.read_csv(path)
    missing = set(frame.evidence) - set(EVIDENCE_GRADES)
    if missing:
        raise ParameterDriftError(f"unknown evidence grade(s): {sorted(missing)}")
    if frame.symbol.duplicated().any():
        duplicated = sorted(frame.symbol[frame.symbol.duplicated()])
        raise ParameterDriftError(f"duplicate symbol(s): {duplicated}")
    return frame


@dataclass(frozen=True)
class Drift:
    """One row whose table value does not match the code."""

    symbol: str
    reference: str
    tabled: object
    in_code: object

    def __str__(self) -> str:
        return (
            f"{self.symbol} ({self.reference}): table says {self.tabled!r}, "
            f"code says {self.in_code!r}"
        )


def check(path: Path | str = TABLE) -> list[Drift]:
    """Compare every row against the code. An empty list means the table is true.

    A row with a ``value`` is compared as a scalar. A row with only ``low`` and
    ``high`` must point at a two-element sequence, and both ends are compared.
    """
    drifts: list[Drift] = []
    for _, row in load(path).iterrows():
        target = resolve(row.code_reference)
        if pd.notna(row.value):
            if not isinstance(target, (int, float, np.floating)):
                drifts.append(Drift(row.symbol, row.code_reference, row.value, target))
            elif not np.isclose(float(target), float(row.value), rtol=TOLERANCE, atol=0.0):
                drifts.append(Drift(row.symbol, row.code_reference, float(row.value), float(target)))
            continue

        if pd.isna(row.low) or pd.isna(row.high):
            drifts.append(
                Drift(row.symbol, row.code_reference, "no value and no bounds", target)
            )
            continue
        if not isinstance(target, (tuple, list)) or len(target) != 2:
            drifts.append(Drift(row.symbol, row.code_reference, (row.low, row.high), target))
            continue
        if not np.allclose(
            [float(target[0]), float(target[1])],
            [float(row.low), float(row.high)],
            rtol=TOLERANCE,
            atol=0.0,
        ):
            drifts.append(
                Drift(row.symbol, row.code_reference, (row.low, row.high), tuple(target))
            )
    return drifts


def assert_true(path: Path | str = TABLE) -> None:
    """Raise if the table has drifted from the code."""
    drifts = check(path)
    if drifts:
        joined = "\n  ".join(str(drift) for drift in drifts)
        raise ParameterDriftError(f"{len(drifts)} parameter(s) have drifted:\n  {joined}")


# -- reading the table ----------------------------------------------------


def by_group(path: Path | str = TABLE) -> dict[str, pd.DataFrame]:
    frame = load(path)
    return {name: group.reset_index(drop=True) for name, group in frame.groupby("group", sort=False)}


def evidence_census(path: Path | str = TABLE) -> pd.DataFrame:
    """How many parameters rest on team data, and how many on a declared prior.

    This is the number a reviewer wants and the project has never stated: most
    of the model is priors, and the conclusions that matter are the ones built
    to survive that.
    """
    frame = load(path)
    counts = frame.evidence.value_counts().rename_axis("evidence").reset_index(name="count")
    counts["share"] = counts["count"] / len(frame)
    return counts


def unmeasurable_this_cycle(path: Path | str = TABLE) -> pd.DataFrame:
    """Scenario-grade rows: every number no experiment in this cycle will fix."""
    frame = load(path)
    return frame[frame.evidence == "scenario"].reset_index(drop=True)


def markdown_table(group: str | None = None, path: Path | str = TABLE) -> str:
    """Emit the table as Markdown, so the wiki never holds a retyped copy."""
    frame = load(path)
    if group is not None:
        frame = frame[frame.group == group]
    lines = [
        "| Symbol | Parameter | Value | Unit | Evidence | Source |",
        "|---|---|---|---|---|---|",
    ]
    for _, row in frame.iterrows():
        if pd.notna(row.value):
            value = f"{row.value:g}"
            if pd.notna(row.low) and pd.notna(row.high):
                value += f" [{row.low:g}, {row.high:g}]"
        else:
            value = f"[{row.low:g}, {row.high:g}]"
        lines.append(
            f"| `{row.symbol}` | {row['name']} | {value} | {row.unit} | "
            f"{row.evidence} | {row.source} |"
        )
    return "\n".join(lines)
