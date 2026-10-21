"""The parameter table, and the guard rail that keeps it honest.

A second copy of thirty numbers is only safe if something fails when it drifts.
That something is `test_the_table_matches_the_code`.
"""

from __future__ import annotations

import pytest

from src import parameters as P


@pytest.fixture(scope="module")
def table():
    return P.load()


# -- the guard rail --------------------------------------------------------


def test_the_table_matches_the_code():
    """Every row resolved against the live code. No drift allowed."""
    drifts = P.check()
    assert drifts == [], "\n".join(str(drift) for drift in drifts)


def test_the_guard_rail_catches_drift(tmp_path, table):
    """The check must be able to fail, or it proves nothing."""
    tampered = table.copy()
    row = tampered.index[tampered.symbol == "K_O2"][0]
    tampered.loc[row, "value"] = 99.0
    path = tmp_path / "parameters.csv"
    tampered.to_csv(path, index=False)

    drifts = P.check(path)
    assert len(drifts) == 1
    assert drifts[0].symbol == "K_O2"
    with pytest.raises(P.ParameterDriftError, match="K_O2"):
        P.assert_true(path)


def test_interval_rows_are_checked_at_both_ends(tmp_path, table):
    tampered = table.copy()
    row = tampered.index[tampered.symbol == "T_renew"][0]
    tampered.loc[row, "high"] = 9.0
    path = tmp_path / "parameters.csv"
    tampered.to_csv(path, index=False)
    assert [drift.symbol for drift in P.check(path)] == ["T_renew"]


def test_a_row_with_neither_value_nor_bounds_is_rejected(tmp_path, table):
    tampered = table.copy()
    row = tampered.index[tampered.symbol == "n_Q"][0]
    tampered.loc[row, ["value", "low", "high"]] = [None, None, None]
    path = tmp_path / "parameters.csv"
    tampered.to_csv(path, index=False)
    assert [drift.symbol for drift in P.check(path)] == ["n_Q"]


# -- the reference syntax --------------------------------------------------


def test_every_reference_form_resolves():
    from src import sensors as S

    assert P.resolve("sensors.EC50_LACTATE_WT") == S.EC50_LACTATE_WT
    assert P.resolve("sensors.HypoxiaSensor.k_o2_percent") == S.HypoxiaSensor().k_o2_percent
    assert P.resolve("spatial.DIFFUSION_LENGTHS_UM[AHL]") == 3000.0
    assert P.resolve("dose.CT26_DOUBLING_H") == (24.0, 48.0)
    assert P.resolve("dose.CT26_DOUBLING_H[0]") == 24.0
    assert P.resolve("fitted:biomass_ratio") == pytest.approx(0.5847, abs=1e-3)


def test_an_unknown_fitted_key_is_refused():
    with pytest.raises(P.ParameterDriftError, match="unknown fitted quantity"):
        P.resolve("fitted:not-a-quantity")


# -- the table's own integrity --------------------------------------------


def test_symbols_are_unique_and_grades_are_known(table):
    assert not table.symbol.duplicated().any()
    assert set(table.evidence) <= set(P.EVIDENCE_GRADES)


def test_duplicate_symbols_are_refused(tmp_path, table):
    doubled = table.iloc[[0, 0]]
    path = tmp_path / "parameters.csv"
    doubled.to_csv(path, index=False)
    with pytest.raises(P.ParameterDriftError, match="duplicate symbol"):
        P.load(path)


def test_unknown_evidence_grade_is_refused(tmp_path, table):
    tampered = table.copy()
    tampered.loc[tampered.index[0], "evidence"] = "vibes"
    path = tmp_path / "parameters.csv"
    tampered.to_csv(path, index=False)
    with pytest.raises(P.ParameterDriftError, match="unknown evidence grade"):
        P.load(path)


def test_every_row_carries_a_source_and_a_use(table):
    for column in ("source", "used_for", "unit", "name"):
        assert table[column].notna().all(), f"{column} is incomplete"
    # units may legitimately be one character ("h", "d"); prose may not
    for column in ("source", "used_for", "name"):
        assert (table[column].astype(str).str.len() > 10).all(), f"{column} is too terse"


def test_every_row_is_either_a_value_or_an_interval(table):
    has_value = table.value.notna()
    has_bounds = table.low.notna() & table.high.notna()
    assert (has_value | has_bounds).all()


def test_bounds_bracket_the_value_where_both_are_given(table):
    both = table[table.value.notna() & table.low.notna() & table.high.notna()]
    assert len(both) >= 6
    assert (both.low <= both.value).all()
    assert (both.value <= both.high).all()


# -- what the census says --------------------------------------------------


def test_the_model_is_mostly_priors():
    """The number a reviewer wants and the project had never stated."""
    census = P.evidence_census().set_index("evidence")
    assert census.loc["scenario", "share"] > 0.5
    assert census.loc["calibration", "count"] >= 5


def test_the_calibrated_parameters_are_the_decisive_ones(table):
    """Everything the project actually decided on is fitted to team data."""
    calibrated = set(table[table.evidence == "calibration"].symbol)
    assert {"b_dose", "r_biomass", "r_potency", "SI"} <= calibrated


def test_scenario_rows_are_listed_for_the_limitations_section(table):
    scenario = P.unmeasurable_this_cycle()
    assert len(scenario) == int((table.evidence == "scenario").sum())
    # The lumen scenario parameters are still ours to declare; 5.2 lists them.
    assert {"L_AHL", "O2_core"} <= set(scenario.symbol)


def test_the_two_sensor_drivers_carry_a_published_measurement(table):
    """n_Q and K_O2 were promoted from scenario on 2026-10-14.

    They are the two parameters the Sobol analysis puts first, so the grade
    they carry is the single most load-bearing claim in the census. If either
    is ever edited back to a declared value, 2.5 stops being true.
    """
    graded = dict(zip(table.symbol, table.evidence))
    assert graded["n_Q"] == "literature_prior"
    assert graded["K_O2"] == "literature_prior"
    values = dict(zip(table.symbol, table.value))
    assert values["n_Q"] == pytest.approx(1.0)
    assert values["K_O2"] == pytest.approx(0.49)


# -- the wiki never holds a retyped copy ----------------------------------


def test_markdown_table_covers_every_row(table):
    rendered = P.markdown_table()
    assert rendered.count("\n") == len(table) + 1
    for symbol in table.symbol:
        assert f"`{symbol}`" in rendered


def test_markdown_table_can_be_filtered(table):
    rendered = P.markdown_table(group="Quorum")
    assert "`n_Q`" in rendered
    assert "`EC50_lac`" not in rendered


def test_interval_only_rows_render_as_intervals():
    rendered = P.markdown_table(group="Targets")
    assert "[100, 600]" in rendered
    assert "[3, 5]" in rendered
