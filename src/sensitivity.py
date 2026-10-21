"""Module 3.5 -- global sensitivity of the tissue axis (migrated and extended).

9.23 ran Sobol on its spatial model and reported, for the tumour-vs-mucosa fold,
``K_O2_uM`` 0.427, ``n_Q`` 0.23, ``pept_basal_fraction`` 0.174. Two things are
added on migration:

1. **The gut lumen is in the model now** (module 3.1), so the analysis can ask
   what drives the *bottleneck* site rather than only the mucosa.
2. **The output is analysed on a log scale**, which is the right choice for a
   multiplicative model and makes the result far more readable.

Why log scale matters here
--------------------------
The tissue ratio is a product::

    ratio = lactate_arm x hypoxia_arm x (hypoxia_arm / density) ** n_Q x repression

On the raw scale, variance is dominated by whichever factor happens to have the
widest multiplicative range, and almost everything shows up as "interaction"
because products are nonlinear. Taking ``log10`` turns the product into a sum,
so a purely multiplicative model would have **zero interactions** and the
first-order indices would sum to 1.

That makes the analysis diagnostic rather than merely descriptive: any
interaction that survives on the log scale is a *real* coupling, not an artefact
of multiplying. There is exactly one such coupling in this model --
``n_Q`` multiplies ``log(hypoxia_arm / density)`` -- so the prediction is that
``n_Q`` should carry a modest first-order index and a much larger total-order
index. A parameter whose ``ST`` greatly exceeds its ``S1`` is one that decides
how much *everything else* matters.

Sampling ranges are declared in :data:`PROBLEM` with their provenance; the
lactate priors span this project's published values and 9.23's more generous
ones, so the analysis covers the disagreement found in module 3.1.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from SALib.analyze import sobol as sobol_analyze
from SALib.sample import sobol as sobol_sample

from . import data as D
from . import gut_lumen as GL
from . import tissue as T

#: Parameters, bounds and why those bounds.
PROBLEM: dict = {
    "num_vars": 9,
    "names": [
        "ec50_lactate_mM",
        "hill_lactate",
        "basal_lactate",
        "k_o2_percent",
        "hill_o2",
        "basal_o2",
        "n_Q",
        "lumen_density_ratio",
        "repression_fold",
    ],
    "bounds": [
        [0.5, 5.0],    # published 1.6 mM to 9.23's prior 5.0
        [1.0, 2.0],    # LldR has no reported cooperativity; 9.23 assumed 2
        [0.001, 0.20],  # 9.23's 0.0078 to the published ~1/7
        [0.3, 3.0],    # spans Hojberg 0.49 % and 9.23's 1 % prior
        [1.0, 3.0],    # around the shared n_O2 = 2
        [0.02, 0.20],  # pept basal; 9.23 fitted 0.122
        [1.0, 3.0],    # Ramalho 0.95-1.5 up through 9.23's 2.978
        [0.1, 10.0],   # luminal EcN density vs tumour -- wholly unmeasured
        [1.0, 30.0],   # native anoxic/glucose repression, each
    ],
}

OUTPUTS: tuple[str, ...] = ("colonic_mucosa", "colon_lumen_dysbiotic", "bottleneck")


def _hill(value: np.ndarray, k: np.ndarray, n: np.ndarray, basal: np.ndarray) -> np.ndarray:
    """Activating Hill with a basal floor."""
    powered = value**n
    return basal + (1.0 - basal) * powered / (k**n + powered)


def _repressing_hill(
    value: np.ndarray, k: np.ndarray, n: np.ndarray, basal: np.ndarray
) -> np.ndarray:
    """Hypoxia sensor: decreasing in oxygen."""
    return basal + (1.0 - basal) * k**n / (k**n + value**n)


def evaluate(samples: np.ndarray, wb: D.Workbook | None = None) -> dict[str, np.ndarray]:
    """Vectorised tissue ratios for a matrix of parameter vectors.

    Returns ``log10`` of the tumour-over-site ratio for each named output. A
    value of 0 means the gate is equally active at both; negative means the site
    is favoured over the tumour.
    """
    wb = wb or D.load()
    sites = GL.load_sites()
    capacities = T.measured_capacities(wb)
    target = sites.loc[GL.TARGET]
    target_density = capacities[T.SITE_CONDITION[GL.TARGET]]

    (ec50, hill_l, basal_l, k_o2, hill_o2, basal_o2, n_q, lumen_density, repression) = (
        samples[:, i] for i in range(samples.shape[1])
    )

    target_lactate = _hill(np.full_like(ec50, target.lactate_mM), ec50, hill_l, basal_l)
    target_hypoxia = _repressing_hill(
        np.full_like(k_o2, target.o2_percent), k_o2, hill_o2, basal_o2
    )

    ratios: dict[str, np.ndarray] = {}
    for site, row in sites.iterrows():
        if site == GL.TARGET:
            continue
        lactate_arm = target_lactate / _hill(
            np.full_like(ec50, row.lactate_mM), ec50, hill_l, basal_l
        )
        hypoxia_arm = target_hypoxia / _repressing_hill(
            np.full_like(k_o2, row.o2_percent), k_o2, hill_o2, basal_o2
        )

        if site in GL.LUMEN_SITES:
            density_ratio = lumen_density
        else:
            density_ratio = np.full_like(
                ec50, capacities[T.SITE_CONDITION[str(site)]] / target_density
            )

        quorum_arm = (hypoxia_arm / density_ratio) ** n_q

        repress = np.ones_like(ec50)
        if bool(row.anoxic):
            repress = repress * repression
        if bool(row.glucose_rich):
            repress = repress * repression

        ratios[str(site)] = np.log10(lactate_arm * hypoxia_arm * quorum_arm * repress)

    ratios["bottleneck"] = np.min(np.vstack(list(ratios.values())), axis=0)
    return ratios


def run(n_base: int = 1024, seed: int = 20261008, wb: D.Workbook | None = None) -> pd.DataFrame:
    """Saltelli sample, evaluate, and return first- and total-order indices."""
    wb = wb or D.load()
    samples = sobol_sample.sample(PROBLEM, n_base, calc_second_order=False, seed=seed)
    outputs = evaluate(samples, wb)

    frames = []
    for name in OUTPUTS:
        result = sobol_analyze.analyze(
            PROBLEM, outputs[name], calc_second_order=False, seed=seed, print_to_console=False
        )
        frame = pd.DataFrame(
            {
                "output": name,
                "parameter": PROBLEM["names"],
                "S1": result["S1"],
                "S1_conf": result["S1_conf"],
                "ST": result["ST"],
                "ST_conf": result["ST_conf"],
            }
        )
        frame["interaction_share"] = 1.0 - frame["S1"] / frame["ST"].replace(0, np.nan)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def top_drivers(indices: pd.DataFrame, output: str, k: int = 4) -> pd.DataFrame:
    frame = indices[indices.output == output].sort_values("ST", ascending=False)
    return frame.head(k)[["parameter", "S1", "ST", "interaction_share"]].reset_index(drop=True)


def additivity_check(indices: pd.DataFrame) -> pd.DataFrame:
    """Sum of first-order indices per output.

    Close to 1 means the log-scale model is essentially additive, i.e. the
    product structure has been fully linearised and every remaining index is a
    genuine effect. Well below 1 means real coupling remains.
    """
    rows = []
    for name in OUTPUTS:
        frame = indices[indices.output == name]
        rows.append(
            {
                "output": name,
                "sum_S1": float(frame["S1"].sum()),
                "sum_ST": float(frame["ST"].sum()),
                "residual_interaction": 1.0 - float(frame["S1"].sum()),
            }
        )
    return pd.DataFrame(rows)


def safety_probability(
    n_base: int = 1024, seed: int = 20261008, wb: D.Workbook | None = None
) -> pd.DataFrame:
    """Fraction of the sampled space in which each site stays protective.

    Not a probability in any calibrated sense -- the priors are ranges, not
    distributions. It is a coverage statement about the declared ranges.
    """
    wb = wb or D.load()
    samples = sobol_sample.sample(PROBLEM, n_base, calc_second_order=False, seed=seed)
    outputs = evaluate(samples, wb)
    rows = []
    for name, values in outputs.items():
        rows.append(
            {
                "site": name,
                "fraction_protective": float((values > 0).mean()),
                "median_log10_ratio": float(np.median(values)),
                "p05_log10_ratio": float(np.percentile(values, 5)),
            }
        )
    return pd.DataFrame(rows)
