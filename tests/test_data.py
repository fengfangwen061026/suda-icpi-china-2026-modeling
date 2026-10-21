"""The 2026-10-08 audit, pinned as tests.

Every number asserted here was derived from the workbook during the audit. If
the sheet is edited or replaced, these fail loudly rather than letting a stale
conclusion survive.
"""

from __future__ import annotations

import math

import pytest

from src import data as D


@pytest.fixture(scope="module")
def wb() -> D.Workbook:
    return D.load()


# -- the sheet is the one we audited --------------------------------------


def test_shapes(wb):
    # 2 constructs x 4 conditions x 3 replicates x 8 timepoints
    assert len(wb.growth) == 2 * 4 * 3 * 8
    # 4 groups x 4 timepoints x 3 replicates
    assert len(wb.reporter_intensity) == 4 * 4 * 3
    assert len(wb.reporter_positive) == 4 * 4 * 3
    # block 5: 7 x 3 doses x 3, less the one GSDMD @ 8 OD replicate never run
    assert len(wb.killing_block(5)) == 7 * 3 * 3 - 1
    # block 6: 7 x 2 lines x 3, less the one GSDMD-TAT / L929 replicate never run
    assert len(wb.killing_block(6)) == 7 * 2 * 3 - 1


def test_replication_gaps_are_exactly_the_two_known_ones(wb):
    gaps = D.replication_gaps(wb)
    found = {(int(r.block), r.construct, r.cell_line, float(r.dose_od)) for r in gaps.itertuples()}
    assert found == {
        (5, "GSDMD", "ct26", 8.0),
        (6, "GSDMD-TAT", "L929", 10.0),
    }


# -- convention 1: intensity zeros are left-censored ----------------------


def test_nineteen_censored_intensity_wells(wb):
    assert int(wb.reporter_intensity["censored"].sum()) == 19


def test_sixteen_of_nineteen_censored_wells_are_contradicted_by_the_positive_readout(wb):
    """The reason we call them censored rather than null.

    A well reading exactly 0 intensity while its own group resolves 2-32 % GFP
    positive cannot be a true zero; it is below the intensity LOD. Only the 3 h
    21 % O2 group is zero on both readouts, i.e. genuinely dark.
    """
    contradicted, consistent = 0, []
    for (group, time_h), rows in wb.reporter_intensity.groupby(["group", "time_h"]):
        censored = int(rows["censored"].sum())
        if censored == 0:
            continue
        positive = D.reporter_summary(wb, group, float(time_h), readout="positive")
        if positive.mean > 0:
            contradicted += censored
        else:
            consistent.append((group, float(time_h), censored))

    assert contradicted == 16
    assert consistent == [("21% -", 3.0, 3)]


def test_fold_change_refuses_a_censored_denominator(wb):
    on = D.reporter_summary(wb, "1% - 20mM", 24.0, readout="intensity")
    off = D.reporter_summary(wb, "21% -", 24.0, readout="intensity")
    assert off.any_censored
    with pytest.raises(D.DataConventionError, match="limit of detection"):
        D.fold_change(on, off, what="ON/OFF intensity")


def test_fold_change_allowed_on_the_positive_readout(wb):
    on = D.reporter_summary(wb, "1% - 20mM", 24.0, readout="positive")
    off = D.reporter_summary(wb, "21% -", 24.0, readout="positive")
    assert D.fold_change(on, off) == pytest.approx(97.87 / 5.43, rel=1e-3)


# -- convention 2: never pair across blocks 5 and 6 -----------------------


def test_the_two_duplicated_constructs_are_detected(wb):
    assert D.block6_duplicated_constructs(wb) == ("GSDMD", "GSDMD-TAT")


def test_block6_ran_an_order_of_magnitude_below_block5(wb):
    suppression = D.block6_suppression(wb)
    assert suppression.n == 4
    assert suppression.mean == pytest.approx(0.131, abs=0.002)


def test_the_built_construct_has_a_usable_selectivity_index(wb):
    si = D.selectivity_index(wb, "GSDMD-SsrA")
    assert si.trustworthy
    assert si.cancer.mean == pytest.approx(4.767, abs=0.001)
    assert si.normal.mean == pytest.approx(1.433, abs=0.001)
    assert si.index == pytest.approx(3.326, abs=0.001)


@pytest.mark.parametrize("construct", ["GSDMD", "GSDMD-TAT"])
def test_the_inflated_indices_are_refused(wb, construct):
    si = D.selectivity_index(wb, construct)
    assert not si.trustworthy
    assert "duplicates block 5" in si.note


def test_the_eleven_fold_figure_is_what_we_are_refusing(wb):
    """Guards the specific number that the 9.23 write-up reported."""
    si = D.selectivity_index(wb, "GSDMD")
    assert si.index == pytest.approx(11.4, abs=0.1)
    assert not si.trustworthy


def test_tat_raises_off_target_killing_within_block6(wb):
    """A comparison that is valid: all three L929 rows come from block 6."""
    tagged = D.selectivity_index(wb, "GSDMD-SsrA").normal.mean
    untagged = D.selectivity_index(wb, "GSDMD").normal.mean
    tat = D.selectivity_index(wb, "GSDMD-TAT").normal.mean
    assert tat / tagged == pytest.approx(7.0, abs=0.1)
    assert tat / untagged == pytest.approx(5.1, abs=0.1)


# -- the growth findings ---------------------------------------------------


def _endpoint(wb, construct: str, condition: str) -> float:
    rows = wb.growth
    rows = rows[
        (rows.construct == construct) & (rows.condition == condition) & (rows.time_h == 24.0)
    ]
    return float(rows["od"].mean())


def test_lactate_alone_saturates_the_self_toxicity(wb):
    """The untagged strain ends at the same OD with lactate alone as with both inputs."""
    lactate_only = _endpoint(wb, "GSDMD", "有氧有酸")
    both_inputs = _endpoint(wb, "GSDMD", "无氧有酸")
    assert lactate_only == pytest.approx(1.380, abs=0.001)
    assert both_inputs == pytest.approx(1.380, abs=0.001)
    assert lactate_only == pytest.approx(both_inputs, abs=0.001)
    # and it is not a floor: hypoxia alone reaches higher
    assert _endpoint(wb, "GSDMD", "无氧无酸") == pytest.approx(1.707, abs=0.001)


def test_the_built_construct_keeps_its_chassis(wb):
    """Induced / uninduced biomass, within each oxygen background."""
    normoxic = _endpoint(wb, "GSDMD-SsrA", "有氧有酸") / _endpoint(wb, "GSDMD-SsrA", "有氧无酸")
    hypoxic = _endpoint(wb, "GSDMD-SsrA", "无氧有酸") / _endpoint(wb, "GSDMD-SsrA", "无氧无酸")
    assert normoxic == pytest.approx(0.903, abs=0.002)
    assert hypoxic == pytest.approx(0.962, abs=0.002)
    # the untagged strain pays far more in the normoxic background
    untagged = _endpoint(wb, "GSDMD", "有氧有酸") / _endpoint(wb, "GSDMD", "有氧无酸")
    assert untagged == pytest.approx(0.478, abs=0.002)


def test_no_lysis_in_any_induced_condition(wb):
    """OD never falls in a lactate condition, so the effector does not burst the chassis."""
    for construct in ("GSDMD-SsrA", "GSDMD"):
        for condition in ("有氧有酸", "无氧有酸"):
            rows = wb.growth
            series = (
                rows[(rows.construct == construct) & (rows.condition == condition)]
                .groupby("time_h")["od"]
                .mean()
                .sort_index()
            )
            drop = series.iloc[-1] / series.max() - 1.0
            if condition == "有氧有酸":
                assert drop == pytest.approx(0.0, abs=1e-9), (construct, condition)
            else:
                # hypoxic stationary decline affects the tagged strain MORE, so it
                # cannot be effector-driven lysis
                assert drop > -0.09, (construct, condition)
    tagged_drop = _series_drop(wb, "GSDMD-SsrA", "无氧有酸")
    untagged_drop = _series_drop(wb, "GSDMD", "无氧有酸")
    assert tagged_drop < untagged_drop


def _series_drop(wb, construct: str, condition: str) -> float:
    rows = wb.growth
    series = (
        rows[(rows.construct == construct) & (rows.condition == condition)]
        .groupby("time_h")["od"]
        .mean()
        .sort_index()
    )
    return float(series.iloc[-1] / series.max() - 1.0)


def test_hypoxia_adds_little_at_endpoint_on_three_readouts(wb):
    """The claim that the gate is lactate-dominated, from three independent readouts."""
    positive = D.fold_change(
        D.reporter_summary(wb, "1% - 20mM", 24.0, readout="positive"),
        D.reporter_summary(wb, "21% - 20mM", 24.0, readout="positive"),
    )
    intensity = D.fold_change(
        D.reporter_summary(wb, "1% - 20mM", 24.0, readout="intensity"),
        D.reporter_summary(wb, "21% - 20mM", 24.0, readout="intensity"),
    )
    growth = _endpoint(wb, "GSDMD", "无氧有酸") / _endpoint(wb, "GSDMD", "有氧有酸")
    assert positive == pytest.approx(1.18, abs=0.01)
    assert intensity == pytest.approx(1.33, abs=0.01)
    assert growth == pytest.approx(1.00, abs=0.01)
    assert max(positive, intensity, growth) < 1.5


def test_hypoxia_does_accelerate_onset(wb):
    """It is a rate effect, not a switch: the mid-course fold is much larger."""
    for time_h, expected in ((6.0, 3.4), (9.0, 3.4)):
        fold = D.fold_change(
            D.reporter_summary(wb, "1% - 20mM", time_h, readout="positive"),
            D.reporter_summary(wb, "21% - 20mM", time_h, readout="positive"),
        )
        assert fold == pytest.approx(expected, abs=0.1)
