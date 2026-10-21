"""Ingest of `data/全部实验数据.xlsx`, with the 2026-10-08 data conventions enforced.

The workbook holds six blocks. Nothing here imputes, drops or rescales a
measured value; the conventions are expressed as metadata and as guard rails,
so that a downstream analysis cannot silently repeat the two mistakes that the
2026-10-08 audit found in the 9.23 write-up:

1. Block 3 (fluorescence intensity) records an undetected well as ``0``. Those
   zeros are genuine measurements -- "no fluorescence detected" -- but they are
   left-censored at the instrument's limit of detection, so they cannot be used
   as the denominator of a fold change. Block 4 (percent positive) resolves the
   same wells above zero, which is how we know the readout is censored rather
   than truly null. ``reporter_intensity`` therefore carries a ``censored``
   flag, and :func:`fold_change` refuses a censored denominator.

2. Blocks 5 and 6 are different experiments: block 5 is the dose series on the
   cancer line, block 6 the normal-vs-cancer comparison at 10 OD only. Block 6
   runs an order of magnitude lower than block 5, so a ratio that takes its
   numerator from one block and its denominator from the other is inflated.
   :func:`selectivity_index` pairs strictly within block 6, and flags the two
   constructs whose block-6 cancer row duplicates block 5.

See ``DATA_CONVENTIONS.md`` for the reasoning and the numbers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "全部实验数据.xlsx"

#: Growth conditions, as labelled in blocks 1-2, mapped to (O2 %, lactate mM).
GROWTH_CONDITIONS: dict[str, tuple[float, float]] = {
    "有氧无酸": (21.0, 0.0),
    "有氧有酸": (21.0, 20.0),
    "无氧无酸": (1.0, 0.0),
    "无氧有酸": (1.0, 20.0),
}

#: Reporter groups, as labelled in blocks 3-4, mapped to (O2 %, lactate mM).
REPORTER_GROUPS: dict[str, tuple[float, float]] = {
    "21% -": (21.0, 0.0),
    "1% -": (1.0, 0.0),
    "21% - 20mM": (21.0, 20.0),
    "1% - 20mM": (1.0, 20.0),
}

#: Constructs, in the column order used by blocks 5-6.
CONSTRUCTS: tuple[str, ...] = (
    "Blank",
    "EcN",
    "gfp",
    "gfp-TAT",
    "GSDMD-SsrA",
    "GSDMD",
    "GSDMD-TAT",
)

TIMES_H: tuple[float, ...] = (0.0, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0, 24.0)
REPORTER_TIMES_H: tuple[float, ...] = (3.0, 6.0, 9.0, 24.0)
DOSES_OD: tuple[float, ...] = (6.0, 8.0, 10.0)


class DataConventionError(RuntimeError):
    """Raised when an analysis asks for a quantity the data cannot support."""


@dataclass(frozen=True)
class Workbook:
    """Every measured value in the workbook, tidied, nothing imputed.

    ``growth``             construct, condition, o2_percent, lactate_mM, time_h,
                           replicate, od  -- blocks 1 (GSDMD-SsrA) and 2 (GSDMD).
    ``reporter_intensity`` group, o2_percent, lactate_mM, time_h, replicate,
                           intensity, censored -- block 3.
    ``reporter_positive``  same keys, ``percent`` -- block 4.
    ``killing``            block, construct, cell_line, dose_od, replicate,
                           percent -- blocks 5 (ct26 dose series) and 6
                           (L929 vs ct26 at 10 OD).
    """

    growth: pd.DataFrame
    reporter_intensity: pd.DataFrame
    reporter_positive: pd.DataFrame
    killing: pd.DataFrame
    source: Path

    # -- convenience views -------------------------------------------------

    def growth_of(self, construct: str) -> pd.DataFrame:
        return self.growth[self.growth.construct == construct]

    def killing_block(self, block: int) -> pd.DataFrame:
        return self.killing[self.killing.block == block]


def _cell(ws, row: int, col: int):
    return ws.cell(row=row, column=col).value


def _find_block_row(ws, prefix: str) -> int:
    """Row index of the block whose first column starts with ``prefix``."""
    for row in range(1, ws.max_row + 1):
        value = _cell(ws, row, 1)
        if isinstance(value, str) and value.strip().startswith(prefix):
            return row
    raise DataConventionError(f"block {prefix!r} not found in sheet")


def _growth_block(ws, title_row: int, construct: str, label_offset: int) -> list[dict]:
    """Blocks 1-2: four conditions, each a label row then three replicate rows."""
    rows: list[dict] = []
    for index, (condition, (o2, lactate)) in enumerate(GROWTH_CONDITIONS.items()):
        label_row = title_row + label_offset + 4 * index
        found = _cell(ws, label_row, 2)
        if not (isinstance(found, str) and found.strip() == condition):
            raise DataConventionError(
                f"{construct}: expected condition {condition!r} at row {label_row}, "
                f"found {found!r} -- the sheet layout has shifted"
            )
        for replicate in range(1, 4):
            data_row = label_row + replicate
            for time_index, time_h in enumerate(TIMES_H):
                value = _cell(ws, data_row, 3 + time_index)
                if value is None:
                    continue
                rows.append(
                    {
                        "construct": construct,
                        "condition": condition,
                        "o2_percent": o2,
                        "lactate_mM": lactate,
                        "time_h": time_h,
                        "replicate": replicate,
                        "od": float(value),
                    }
                )
    return rows


def _reporter_block(ws, title_row: int, value_name: str) -> list[dict]:
    """Blocks 3-4: four groups of three replicate columns, four timepoints."""
    rows: list[dict] = []
    for group_index, (group, (o2, lactate)) in enumerate(REPORTER_GROUPS.items()):
        base_col = 3 + 3 * group_index
        header = _cell(ws, title_row, base_col)
        if not (isinstance(header, str) and header.strip() == group):
            raise DataConventionError(
                f"reporter block at row {title_row}: expected group {group!r} in "
                f"column {base_col}, found {header!r}"
            )
        for time_index, time_h in enumerate(REPORTER_TIMES_H):
            data_row = title_row + 1 + time_index
            for replicate in range(1, 4):
                value = _cell(ws, data_row, base_col + replicate - 1)
                if value is None:
                    continue
                rows.append(
                    {
                        "group": group,
                        "o2_percent": o2,
                        "lactate_mM": lactate,
                        "time_h": time_h,
                        "replicate": replicate,
                        value_name: float(value),
                    }
                )
    return rows


def _killing_rows(ws, title_row: int, block: int, labels: list[tuple[str, float, int]]) -> list[dict]:
    """Blocks 5-6: seven constructs of three replicate columns.

    ``labels`` gives, per data row, the (cell_line, dose_od, row_offset).
    """
    rows: list[dict] = []
    for construct_index, construct in enumerate(CONSTRUCTS):
        base_col = 3 + 3 * construct_index
        header = _cell(ws, title_row, base_col)
        if not (isinstance(header, str) and header.strip() == construct):
            raise DataConventionError(
                f"killing block {block}: expected construct {construct!r} in "
                f"column {base_col}, found {header!r}"
            )
        for cell_line, dose_od, offset in labels:
            data_row = title_row + offset
            for replicate in range(1, 4):
                value = _cell(ws, data_row, base_col + replicate - 1)
                if value is None:
                    continue  # a replicate that was not run stays absent
                rows.append(
                    {
                        "block": block,
                        "construct": construct,
                        "cell_line": cell_line,
                        "dose_od": dose_od,
                        "replicate": replicate,
                        "percent": float(value),
                    }
                )
    return rows


def load(path: Path | str = DEFAULT_PATH) -> Workbook:
    """Read the workbook. Raises if the sheet layout is not the expected one."""
    path = Path(path)
    ws = load_workbook(path, data_only=True).worksheets[0]

    growth = _growth_block(ws, _find_block_row(ws, "1."), "GSDMD-SsrA", label_offset=2)
    growth += _growth_block(ws, _find_block_row(ws, "2."), "GSDMD", label_offset=1)

    intensity = _reporter_block(ws, _find_block_row(ws, "3."), "intensity")
    positive = _reporter_block(ws, _find_block_row(ws, "4."), "percent")

    killing = _killing_rows(
        ws,
        _find_block_row(ws, "5."),
        block=5,
        labels=[("ct26", dose, 1 + i) for i, dose in enumerate(DOSES_OD)],
    )
    killing += _killing_rows(
        ws,
        _find_block_row(ws, "6."),
        block=6,
        labels=[("L929", 10.0, 1), ("ct26", 10.0, 2)],
    )

    intensity_df = pd.DataFrame(intensity)
    # Convention 1: an intensity of exactly 0 is "not detected", i.e. left-censored
    # at the instrument LOD. It is kept as a measurement and flagged, never dropped.
    intensity_df["censored"] = intensity_df["intensity"] == 0.0

    return Workbook(
        growth=pd.DataFrame(growth),
        reporter_intensity=intensity_df,
        reporter_positive=pd.DataFrame(positive),
        killing=pd.DataFrame(killing),
        source=path,
    )


# -- guard rails -----------------------------------------------------------


@dataclass(frozen=True)
class Summary:
    """Mean, SD and n of one group, with the censoring state carried along."""

    mean: float
    sd: float
    n: int
    n_censored: int = 0

    @property
    def any_censored(self) -> bool:
        return self.n_censored > 0

    def __str__(self) -> str:
        tail = f", {self.n_censored} <LOD" if self.any_censored else ""
        return f"{self.mean:.3g} ± {self.sd:.3g} (n={self.n}{tail})"


def summarise(values: pd.Series | np.ndarray, n_censored: int = 0) -> Summary:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        raise DataConventionError("cannot summarise an empty group")
    sd = float(array.std(ddof=1)) if array.size > 1 else 0.0
    return Summary(float(array.mean()), sd, int(array.size), n_censored)


def reporter_summary(wb: Workbook, group: str, time_h: float, *, readout: str = "positive") -> Summary:
    """Summarise one reporter group. ``readout`` is ``"positive"`` or ``"intensity"``."""
    if readout == "positive":
        frame = wb.reporter_positive
        column = "percent"
        rows = frame[(frame.group == group) & (frame.time_h == time_h)]
        return summarise(rows[column])
    if readout == "intensity":
        frame = wb.reporter_intensity
        rows = frame[(frame.group == group) & (frame.time_h == time_h)]
        return summarise(rows["intensity"], n_censored=int(rows["censored"].sum()))
    raise DataConventionError(f"unknown readout {readout!r}")


def fold_change(numerator: Summary, denominator: Summary, *, what: str = "fold change") -> float:
    """Ratio of two group means, refused when the denominator is censored.

    Convention 1: block 3 records undetected wells as 0. A group containing one
    is left-censored, so the true mean is unknown and bounded above -- the ratio
    would be an unbounded lower bound masquerading as a point estimate. Use the
    percent-positive readout (block 4) for OFF-state folds instead.
    """
    if denominator.any_censored:
        raise DataConventionError(
            f"{what}: the denominator has {denominator.n_censored} well(s) below the "
            "limit of detection, so this ratio is unbounded. Use the percent-positive "
            "readout (block 4) for OFF-state fold changes."
        )
    if denominator.mean == 0.0:
        raise DataConventionError(f"{what}: denominator mean is zero")
    return numerator.mean / denominator.mean


def block6_duplicated_constructs(wb: Workbook, *, tolerance: float = 0.02) -> tuple[str, ...]:
    """Constructs whose block-6 ct26 row reproduces block 5 at 10 OD.

    Block 6 ran an order of magnitude below block 5 for every construct it
    measured independently. Two constructs instead match block 5 replicate for
    replicate, so their block-6 cancer row is almost certainly block 5's data
    carried across. Their selectivity index would pair a block-5 numerator with
    a block-6 denominator, which is what inflated the 11.4x figure in the 9.23
    write-up. They are detected here rather than hard-coded.
    """
    duplicated: list[str] = []
    for construct in CONSTRUCTS:
        five = wb.killing[
            (wb.killing.block == 5)
            & (wb.killing.construct == construct)
            & (wb.killing.dose_od == 10.0)
        ].set_index("replicate")["percent"]
        six = wb.killing[
            (wb.killing.block == 6)
            & (wb.killing.construct == construct)
            & (wb.killing.cell_line == "ct26")
        ].set_index("replicate")["percent"]
        shared = five.index.intersection(six.index)
        if len(shared) < 2:
            continue
        if float(five.loc[shared].mean()) == 0.0:
            continue  # the blank is zero in both blocks; not informative
        relative = np.abs(five.loc[shared] - six.loc[shared]) / five.loc[shared].abs()
        if bool((relative <= tolerance).all()):
            duplicated.append(construct)
    return tuple(duplicated)


def block6_suppression(wb: Workbook) -> Summary:
    """Geometric-mean ratio of block 6 ct26 to block 5 at 10 OD, independents only.

    Quantifies how much lower block 6 ran. Used to say what a duplicated
    construct's block-6 value would plausibly have been.
    """
    duplicated = set(block6_duplicated_constructs(wb))
    ratios: list[float] = []
    for construct in CONSTRUCTS:
        if construct in duplicated or construct == "Blank":
            continue
        five = wb.killing[
            (wb.killing.block == 5)
            & (wb.killing.construct == construct)
            & (wb.killing.dose_od == 10.0)
        ]["percent"].mean()
        six = wb.killing[
            (wb.killing.block == 6)
            & (wb.killing.construct == construct)
            & (wb.killing.cell_line == "ct26")
        ]["percent"].mean()
        if five and six:
            ratios.append(float(six) / float(five))
    logs = np.log(ratios)
    return Summary(float(np.exp(logs.mean())), float(np.exp(logs.std(ddof=1))), len(ratios))


@dataclass(frozen=True)
class SelectivityIndex:
    """ct26 / L929 killing for one construct, paired inside block 6."""

    construct: str
    cancer: Summary
    normal: Summary
    index: float
    trustworthy: bool
    note: str

    def __str__(self) -> str:
        mark = "" if self.trustworthy else "  [NOT USABLE]"
        return (
            f"{self.construct}: ct26 {self.cancer} / L929 {self.normal} "
            f"= {self.index:.2f}x{mark}"
        )


def selectivity_index(wb: Workbook, construct: str) -> SelectivityIndex:
    """Selectivity index for one construct, strictly paired within block 6.

    Convention 2: blocks 5 and 6 are different experiments, so a ratio may never
    mix them. Constructs whose block-6 cancer row duplicates block 5 are
    returned with ``trustworthy=False``.
    """
    rows = wb.killing[(wb.killing.block == 6) & (wb.killing.construct == construct)]
    if rows.empty:
        raise DataConventionError(f"{construct!r} is not in block 6")
    cancer = summarise(rows[rows.cell_line == "ct26"]["percent"])
    normal = summarise(rows[rows.cell_line == "L929"]["percent"])

    if normal.mean == 0.0:
        return SelectivityIndex(
            construct, cancer, normal, float("nan"), False,
            "L929 killing is zero in every replicate; the ratio is undefined",
        )

    duplicated = block6_duplicated_constructs(wb)
    if construct in duplicated:
        note = (
            "block-6 ct26 row duplicates block 5 at 10 OD, so this pairs a block-5 "
            "numerator with a block-6 denominator and is inflated; do not report it"
        )
        return SelectivityIndex(construct, cancer, normal, cancer.mean / normal.mean, False, note)

    note = "paired within block 6"
    if normal.n < 3 or cancer.n < 3:
        note += f"; incomplete replication (n={normal.n} normal, n={cancer.n} cancer)"
    if normal.sd == 0.0 and normal.n > 1:
        note += "; L929 replicates are identical (SD = 0), so no t-test is valid here"
    return SelectivityIndex(construct, cancer, normal, cancer.mean / normal.mean, True, note)


def replication_gaps(wb: Workbook) -> pd.DataFrame:
    """Every killing group measured with fewer than three replicates."""
    grouped = (
        wb.killing.groupby(["block", "construct", "cell_line", "dose_od"])["percent"]
        .agg(n="count", mean="mean", sd=lambda s: s.std(ddof=1) if len(s) > 1 else np.nan)
        .reset_index()
    )
    return grouped[grouped.n < 3].reset_index(drop=True)
