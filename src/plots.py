"""Figures. Module 6 gets exactly one, by design.

Palette: categorical slots 1 and 2 of the reference data-viz palette
(blue ``#2a78d6``, orange ``#eb6834``). ``references/palette.md`` records that
the first three slots clear the all-pairs CVD and normal-vision gates in both
modes (worst pair CVD dE 9.2, normal-vision 24.0 in light mode); slots 1-2 are a
subset of that validated set, and neither is in the group that falls below 3:1
on the light surface, so no relief rule applies. Labels and values are drawn in
ink tokens, never in a series colour.

Static PNG output, so the interaction layer does not apply; identity is carried
by a legend plus direct labels rather than colour alone.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import immune as I
from . import sensors as S

FIGURES = Path(__file__).resolve().parent.parent / "outputs" / "figures"

#: Vector masters. Every figure is drawn once and written three ways: the PNG
#: the Word builds embed and the pixel comparisons use, and an SVG and a PDF
#: beside it for the wiki and for anything that will be printed or scaled.
#: Text is written as paths (matplotlib's ``svg.fonttype`` default), so the
#: files render identically on a machine that does not have DejaVu Sans; the
#: cost is that the text is no longer selectable, which is the right trade for
#: a figure that gets uploaded rather than edited.
VECTORS = FIGURES / "vector"

#: Raster resolution. The vector master is the thing to scale; this only has to
#: survive being placed at ~16 cm in Word.
RASTER_DPI = 300

SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#8a8980"
SERIES_1 = "#2a78d6"  # blue
SERIES_2 = "#eb6834"  # orange
GRID = "#e5e4df"


def _save(fig, path: Path) -> Path:
    """Write the raster and both vector masters, and close the figure.

    Returns the PNG path, because that is what every caller and every test
    already expects; the vector files sit in ``outputs/figures/vector`` under
    the same stem.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    VECTORS.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=RASTER_DPI, facecolor=SURFACE)
    for suffix in (".svg", ".pdf"):
        fig.savefig((VECTORS / path.stem).with_suffix(suffix), facecolor=SURFACE)
    plt.close(fig)
    return path


def _style_axes(ax) -> None:
    """Recessive grid and axes; only the left and bottom spines survive."""
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
        ax.spines[side].set_linewidth(1.0)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9, length=3, width=1.0)
    ax.grid(True, color=GRID, linewidth=0.8, alpha=0.9)
    ax.set_axisbelow(True)


def immune_feasibility(
    cascade: I.ImmuneCascade | None = None,
    path: Path | None = None,
) -> Path:
    """Module 6's single figure: what the cascade can and cannot do.

    Left: distant-lesion outcome against immune pressure, with the bistable
    window between the two thresholds. Right: the ``epsilon G = 1`` feasibility
    boundary, with the band where MSS/pMMR colorectal cancer plausibly sits.
    """
    cascade = cascade or I.ImmuneCascade()
    path = path or FIGURES / "fig6_immune_feasibility.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    guaranteed = cascade.guaranteed_eradication_pressure()
    fig, (left, right) = plt.subplots(1, 2, figsize=(11.5, 4.4), facecolor=SURFACE)

    # -- left panel ------------------------------------------------------
    pressures = np.linspace(0.0, 3.0, 601)
    escape = cascade.escape_burden(pressures)
    treatable = cascade.max_treatable_burden(pressures)
    escape_line = np.where(pressures <= guaranteed, escape, np.nan)
    treatable_line = np.where(pressures >= 1.0, treatable, np.nan)

    bistable = (pressures >= 1.0) & (pressures <= guaranteed)
    left.fill_between(
        pressures[bistable],
        treatable[bistable],
        escape[bistable],
        color=INK_MUTED,
        alpha=0.13,
        linewidth=0,
    )
    left.plot(pressures, escape_line, color=SERIES_1, linewidth=2.0, solid_capstyle="round")
    # Two segments, never joined: max-treatable jumps from the lower root to the
    # whole range at Psi*. A single polyline would draw a vertical connector
    # that reads as data.
    lens = bistable
    beyond = pressures > guaranteed
    left.plot(pressures[lens], treatable[lens], color=SERIES_2, linewidth=2.0,
              solid_capstyle="round")
    left.plot(pressures[beyond], treatable[beyond], color=SERIES_2, linewidth=2.0,
              solid_capstyle="round")

    for x, label in ((1.0, "eradication\npossible"), (guaranteed, "eradication\nguaranteed")):
        left.axvline(x, color=INK_MUTED, linewidth=1.0, linestyle=(0, (4, 3)))
        left.text(x, 1.03, label, ha="center", va="bottom", fontsize=8, color=INK_SECONDARY)

    left.plot([0.38], [0.735], marker="o", markersize=8, color=SERIES_1, clip_on=False)
    left.text(0.45, 0.715, "Escape burden", color=INK_PRIMARY, fontsize=9.5)
    left.plot([0.98], [0.325], marker="o", markersize=8, color=SERIES_2, clip_on=False)
    left.text(1.05, 0.245, "Largest burden\nstill cleared", color=INK_PRIMARY, fontsize=9.5)
    left.text(1.18, 0.50, "bistable", fontsize=8.5, color=INK_SECONDARY, style="italic")
    left.text(2.02, 0.72, "no escape state", fontsize=8.5, color=INK_SECONDARY, style="italic")

    left.set_xlim(0, 3)
    left.set_ylim(0, 1.20)
    left.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    left.set_xlabel("Immune pressure  $\\Psi$", fontsize=10, color=INK_SECONDARY)
    left.set_ylabel("Distant burden  (fraction of capacity)", fontsize=10, color=INK_SECONDARY)
    left.set_title(
        "Distant lesion outcome vs immune pressure",
        fontsize=11.5, color=INK_PRIMARY, loc="left", pad=8,
    )
    _style_axes(left)
    handles = [
        plt.Line2D([], [], color=SERIES_1, linewidth=2.0, label="Escape burden"),
        plt.Line2D([], [], color=SERIES_2, linewidth=2.0, label="Largest burden still cleared"),
    ]
    legend = left.legend(handles=handles, loc="lower right", frameon=False, fontsize=8.5)
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)

    # -- right panel -----------------------------------------------------
    gains = np.logspace(0, 2, 400)
    boundary = 1.0 / gains

    right.fill_between(gains, 1e-3, boundary, color=INK_MUTED, alpha=0.16, linewidth=0)
    right.plot(gains, boundary, color=SERIES_1, linewidth=2.0, solid_capstyle="round")
    right.axhspan(0.05, 0.20, color=SERIES_2, alpha=0.14, linewidth=0)
    right.text(
        1.25, 0.105, "MSS / pMMR\n(cold tumour)",
        fontsize=8.5, color=INK_PRIMARY, va="center",
    )
    right.text(
        2.0, 0.012, "infeasible at any pyroptotic flux\n$\\epsilon G \\leq 1$",
        fontsize=9, color=INK_SECONDARY,
    )
    right.text(
        22, 0.42, "distant control\nreachable",
        fontsize=9, color=INK_SECONDARY, ha="center",
    )

    right.set_xscale("log")
    right.set_yscale("log")
    right.set_xlim(1, 100)
    right.set_ylim(1e-2, 1.0)
    right.set_xlabel("Cascade gain  $G$", fontsize=10, color=INK_SECONDARY)
    right.set_ylabel("Immune permissiveness  $\\epsilon$", fontsize=10, color=INK_SECONDARY)
    right.set_title(
        "Feasibility boundary  $\\epsilon G = 1$",
        fontsize=11.5, color=INK_PRIMARY, loc="left", pad=8,
    )
    _style_axes(right)

    fig.text(
        0.008, 0.015,
        "Scenario only: neither G nor ε is measured for this system. "
        "Evasion scale h = %.2f." % cascade.evasion_scale,
        fontsize=8, color=INK_MUTED,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return _save(fig, path)


if __name__ == "__main__":
    print(immune_feasibility())


# -- module 3.3 / 3.1 / 4.4 figures ---------------------------------------

SERIES_3 = "#1baf7a"  # aqua, categorical slot 3


def _bar(ax, y, value, baseline, color, height=0.34):
    """A bar on a log axis, drawn from `baseline` to `value`.

    matplotlib's barh cannot anchor to a non-zero value on a log scale, so each
    bar is a thick butt-capped segment instead. Visually identical, and it keeps
    the 1.0 reference as the true baseline.
    """
    ax.hlines(
        y, min(baseline, value), max(baseline, value),
        color=color, linewidth=height * 30, capstyle="butt", zorder=3,
    )


def arm_direction(path: Path | None = None) -> Path:
    """Module 3.3: which designed arm protects which site, and where both fail."""
    from . import gut_lumen as GL
    from . import sensors as S

    path = path or FIGURES / "fig3_3_arm_direction.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    sites = GL.load_sites()
    target = sites.loc[GL.TARGET]
    lactate, hypoxia = S.LactateSensor(), S.HypoxiaSensor()

    labels, lac, hyp = [], [], []
    for site, row in sites.iterrows():
        if site == GL.TARGET:
            continue
        labels.append(row.label)
        lac.append(float(lactate(target.lactate_mM)) / float(lactate(row.lactate_mM)))
        hyp.append(float(hypoxia(target.o2_percent)) / float(hypoxia(row.o2_percent)))

    order = list(range(len(labels)))[::-1]
    fig, ax = plt.subplots(figsize=(8.6, 4.6), facecolor=SURFACE)
    ax.axvspan(0.1, 1.0, color=SERIES_2, alpha=0.08, linewidth=0, zorder=0)

    for i, idx in enumerate(order):
        for offset, value, color in ((0.19, lac[idx], SERIES_1), (-0.19, hyp[idx], SERIES_2)):
            if abs(np.log10(value)) < 0.012:
                # exactly no discrimination: a bar of zero length would read as
                # missing data, so draw a tick at the baseline instead
                ax.plot([1.0], [i + offset], marker="|", markersize=11,
                        markeredgewidth=2.5, color=color, zorder=5)
                ax.text(1.06, i + offset, "no discrimination", fontsize=8,
                        color=INK_SECONDARY, va="center", style="italic")
            else:
                _bar(ax, i + offset, value, 1.0, color)

    ax.axvline(1.0, color=INK_SECONDARY, linewidth=1.2, zorder=4)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels([labels[i] for i in order], fontsize=9.5, color=INK_PRIMARY)
    ax.set_xscale("log")
    ax.set_xlim(0.45, 30)
    ax.set_ylim(-0.75, len(labels) - 0.25)
    ax.set_xlabel("Tumour-over-site sensor activity  (log scale)", fontsize=10, color=INK_SECONDARY)
    ax.set_title(
        "Each designed arm, at each site",
        fontsize=12, color=INK_PRIMARY, loc="left", pad=10,
    )
    ax.text(0.62, len(labels) - 0.62, "anti-selective", fontsize=8.5,
            color=INK_SECONDARY, style="italic", ha="center")
    _style_axes(ax)
    ax.grid(axis="y", visible=False)
    handles = [
        plt.Line2D([], [], color=SERIES_1, linewidth=7, label="Lactate arm (lldPRD)"),
        plt.Line2D([], [], color=SERIES_2, linewidth=7, label="Hypoxia arm (pPepT)"),
    ]
    legend = ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=8.5)
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)
    # The footer states the parameters the panel is drawn at and nothing else:
    # what the picture means belongs in the legend, which is held to facts.
    fig.text(0.008, 0.015,
             f"Lactate arm: EC50 {lactate.ec50_mM:g} mM, Hill {lactate.hill:g}, "
             f"basal {lactate.basal:.3f}. "
             f"Hypoxia arm: K = {hypoxia.k_o2_percent:g} % O2, "
             f"Hill {hypoxia.hill:g}, basal {hypoxia.basal:.2f}.",
             fontsize=8, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, path)


def tissue_axis(path: Path | None = None) -> Path:
    """Module 3.1: the full tissue axis, and what native repression moves."""
    from . import tissue as T

    path = path or FIGURES / "fig3_1_tissue_axis.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    bare = T.TissueAxis().arms().set_index("site")
    repressed = (
        T.TissueAxis(anoxic_repression=10.0, glucose_repression=10.0)
        .arms()
        .set_index("site")
    )
    order = list(bare.index)[::-1]

    fig, ax = plt.subplots(figsize=(8.6, 4.6), facecolor=SURFACE)
    ax.axvspan(0.1, 1.0, color=SERIES_2, alpha=0.08, linewidth=0, zorder=0)
    for i, site in enumerate(order):
        _bar(ax, i + 0.19, repressed.loc[site, "total_ratio"], 1.0, SERIES_3)
        _bar(ax, i - 0.19, bare.loc[site, "total_ratio"], 1.0, SERIES_1)

    ax.axvline(1.0, color=INK_SECONDARY, linewidth=1.2, zorder=4)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([bare.loc[s, "label"] for s in order], fontsize=9.5, color=INK_PRIMARY)
    ax.set_xscale("log")
    ax.set_xlim(0.25, 5e3)
    ax.set_ylim(-0.75, len(order) - 0.25)
    ax.set_xlabel("Gate output, tumour over site  (log scale)", fontsize=10, color=INK_SECONDARY)
    ax.set_title("The tissue axis, with the gut lumen in it",
                 fontsize=12, color=INK_PRIMARY, loc="left", pad=10)
    _style_axes(ax)
    ax.grid(axis="y", visible=False)
    handles = [
        plt.Line2D([], [], color=SERIES_1, linewidth=7, label="Designed arms only"),
        plt.Line2D([], [], color=SERIES_3, linewidth=7, label="+ native lldPRD repression"),
    ]
    legend = ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=8.5)
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)
    fig.text(0.008, 0.015,
             f"Quorum Hill n_Q = {S.QUORUM_HILL_PLUX:g} (published); "
             "repression 10x anoxic x 10x glucose.",
             fontsize=8, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, path)


def cluster_equivalence(path: Path | None = None) -> Path:
    """Module 4.4: what it takes for clustered micro-lesions to switch on."""
    from . import multilesion as ML

    path = path or FIGURES / "fig4_4_cluster.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    field = ML.AHLField()
    counts = np.array([1, 8, 27, 64, 125, 343, 512])
    spacings = ((300.0, SERIES_1, "300 µm (touching)"),
                (1000.0, SERIES_2, "1000 µm (realistic)"),
                (2000.0, SERIES_3, "2000 µm"))

    fig, ax = plt.subplots(figsize=(8.0, 4.8), facecolor=SURFACE)
    ax.axhspan(ML.LESION_ON_UM, 1400, color=SERIES_3, alpha=0.10, linewidth=0)
    ax.axhline(ML.LESION_ON_UM, color=INK_SECONDARY, linewidth=1.0, linestyle=(0, (4, 3)))
    ax.axhline(ML.LESION_OFF_UM, color=INK_SECONDARY, linewidth=1.0, linestyle=(0, (4, 3)))

    for spacing, color, label in spacings:
        radii = []
        for n in counts:
            side = int(round(n ** (1 / 3)))
            positions = ML.cubic_lattice(side, spacing)
            radii.append(field.equivalent_isolated_radius(field.centre_in_cluster(positions, 150.0)))
        ax.plot(counts, radii, color=color, linewidth=2.0, marker="o",
                markersize=5.5, markeredgecolor=SURFACE, markeredgewidth=1.5, label=label)

    ax.text(380, ML.LESION_ON_UM + 30, f"ON band ({ML.LESION_ON_UM:.0f} µm)",
            fontsize=8.5, color=INK_SECONDARY, ha="right")
    ax.text(1.3, 116, "a single 150 µm lesion", fontsize=8.5, color=INK_SECONDARY)
    ax.annotate(
        "512 touching lesions\n= a 2.4 mm contiguous mass",
        xy=(512, 1010), xytext=(30, 1225), fontsize=8.5, color=INK_SECONDARY,
        ha="left", va="center",
        arrowprops=dict(arrowstyle="-", color=INK_MUTED, linewidth=1.0,
                        connectionstyle="arc3,rad=-0.25"),
    )
    ax.set_xscale("log")
    ax.set_xlim(0.85, 700)
    ax.set_ylim(100, 1400)
    ax.set_xticks(counts)
    ax.set_xticklabels([str(c) for c in counts])
    ax.set_xlabel("Micro-lesions in the cluster", fontsize=10, color=INK_SECONDARY)
    ax.set_ylabel("Equivalent isolated radius  (µm)", fontsize=10, color=INK_SECONDARY)
    ax.set_title("What it takes for a cluster to switch on",
                 fontsize=12, color=INK_PRIMARY, loc="left", pad=10)
    _style_axes(ax)
    legend = ax.legend(loc="upper left", frameon=False, fontsize=8.5, title="Spacing")
    legend.get_title().set_color(INK_SECONDARY)
    legend.get_title().set_fontsize(8.5)
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)
    fig.text(0.008, 0.015,
             f"{ML.LESION_OFF_UM:.0f} µm lesions on a cubic lattice. Dashed lines: the "
             f"{ML.LESION_OFF_UM:.0f} µm OFF and {ML.LESION_ON_UM:.0f} µm ON equivalent "
             "radii of the single-lesion calibration.",
             fontsize=8, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, path)


def dose_requirement(path: Path | None = None) -> Path:
    """Module 4.6's figure: the back-calculation, and what it costs in margin.

    Left: the net dose-kill curve with the requirement levels drawn across it,
    so the reader sees which targets fall inside the measured dose range.
    Right: the escalation needed as lesions get smaller, against the
    colonic-mucosa margin it consumes.
    """
    from . import dose as X

    path = path or FIGURES / "fig4_6_dose_requirement.png"
    fig, (left, right) = plt.subplots(1, 2, figsize=(11.6, 4.5), facecolor=SURFACE)

    # -- left: the curve and the requirements -----------------------------
    frame = X.net_killing(control="gfp")
    law = X.fit_power_law(control="gfp")
    grid = np.linspace(4.0, 20.0, 200)

    left.axvspan(6.0, 10.0, color=SERIES_1, alpha=0.07, linewidth=0)
    left.text(7.75, 0.062, "doses tested", fontsize=8.5, color=INK_MUTED, ha="center")

    for low, high, label, colour in (
        (0.1155, 0.6908, "human CRC", SERIES_2),
        (29.29, 50.0, "CT26", INK_SECONDARY),
    ):
        left.axhspan(low, high, color=colour, alpha=0.13, linewidth=0)
        left.text(4.3, np.sqrt(low * high), label, fontsize=8.5, color=colour, va="center")

    left.plot(grid, law.kill_percent(grid), color=SERIES_1, linewidth=1.8,
              label=f"fit, exponent {law.exponent:.2f}")
    left.errorbar(frame.dose_od, frame.net_percent, yerr=frame.se, fmt="o",
                  color=SERIES_1, markersize=6.5, markeredgecolor=SURFACE,
                  markeredgewidth=1.5, capsize=3, elinewidth=1.2, label="measured, net of gfp")

    left.set_xscale("log")
    left.set_yscale("log")
    left.set_xlim(4.0, 20.0)
    left.set_ylim(0.05, 120.0)
    left.set_xticks([5, 6, 8, 10, 15, 20])
    left.set_xticklabels(["5", "6", "8", "10", "15", "20"])
    left.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    left.set_xlabel("Dose  (OD, co-culture)", fontsize=10, color=INK_SECONDARY)
    left.set_ylabel("Net killing over 24 h  (%)", fontsize=10, color=INK_SECONDARY)
    left.set_title("Killing goes as roughly the cube of dose",
                   fontsize=12, color=INK_PRIMARY, loc="left", pad=10)
    _style_axes(left)
    legend = left.legend(loc="lower right", frameon=False, fontsize=8.5)
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)

    # -- right: escalation against margin ---------------------------------
    radii = np.array([150.0, 180.0, 200.0, 250.0, 300.0, 400.0, 600.0])
    table = X.escalation_erodes_margin(radii_um=tuple(radii))

    right.plot(table.radius_um, table.total_escalation, color=SERIES_1,
               linewidth=2.0, marker="o", markersize=5.5,
               markeredgecolor=SURFACE, markeredgewidth=1.5,
               label="dose escalation needed")
    right.plot(table.radius_um, table.mucosa_margin_left, color=SERIES_2,
               linewidth=2.0, marker="s", markersize=5.5,
               markeredgecolor=SURFACE, markeredgewidth=1.5,
               label="colonic-mucosa margin left")
    right.axhline(1.0, color=INK_MUTED, linewidth=1.0, linestyle=(0, (4, 3)))
    # Left of the escalation curve: at the right-hand end this label used to
    # sit on top of the blue markers.
    right.text(136, 1.08, "no margin", fontsize=8.5, color=INK_MUTED, ha="left")
    right.axvline(178.0, color=INK_MUTED, linewidth=1.0, linestyle=(0, (1, 3)))
    right.text(183, 0.42, "no hypoxic core\nbelow 178 µm", fontsize=8.5,
               color=INK_MUTED, ha="left", va="bottom")

    # The pass line, and the point at which the design fails it. Both values
    # come off the table rather than the prose, so the figure cannot drift.
    required = X.ENGINEERING_MARGIN_REQUIREMENT
    right.axhline(required, color=SERIES_2, linewidth=1.3, linestyle=(0, (6, 3)), zorder=2)
    right.text(632, required * 0.90, f"the {required:.0f}× margin we require",
               fontsize=9, color=SERIES_2, ha="right", va="top")

    smallest = table.iloc[int(np.argmin(table.radius_um.to_numpy()))]
    right.scatter([smallest.radius_um], [smallest.mucosa_margin_left], s=96,
                  facecolor="none", edgecolor=SERIES_2, linewidth=2.0, zorder=5)
    right.annotate(
        f"{smallest.radius_um:.0f} µm: {smallest.total_escalation:.2f}× dose,\n"
        f"{smallest.mucosa_margin_left:.2f}× margin left",
        xy=(smallest.radius_um + 4.0, smallest.total_escalation * 1.12),
        xytext=(196.0, 27.0), fontsize=9, color=INK_PRIMARY, ha="left", va="center",
        arrowprops=dict(arrowstyle="-", color=SERIES_2, linewidth=1.1,
                        shrinkA=2.0, shrinkB=6.0),
    )

    right.set_yscale("log")
    right.set_xlim(130.0, 640.0)
    right.set_ylim(0.3, 60.0)
    right.set_xlabel("Lesion radius  (µm)", fontsize=10, color=INK_SECONDARY)
    right.set_ylabel("Fold", fontsize=10, color=INK_SECONDARY)
    right.set_title("Reaching a micro-lesion spends the safety margin",
                    fontsize=12, color=INK_PRIMARY, loc="left", pad=10)
    _style_axes(right)
    legend = right.legend(loc="upper right", frameon=False, fontsize=8.5)
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)

    fig.text(0.008, 0.015,
             f"Left: fit exponent {law.exponent:.2f}, doses tested 6-10 OD; "
             "requirement bands 0.12-0.69 % (human CRC) and 29.3-50 % (CT26). "
             f"Right: escalation priced against module 3.1's "
             f"{X.COLONIC_MUCOSA_MARGIN:.2f}x mucosa margin.",
             fontsize=8, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, path)


#: Readable names for the nine sampled parameters.
PARAMETER_LABELS: dict[str, str] = {
    "repression_fold": "Native repression",
    "lumen_density_ratio": "Luminal EcN density",
    "n_Q": "Quorum Hill  $n_Q$",
    "k_o2_percent": "Oxygen sensor $K$",
    "hill_o2": "Oxygen Hill",
    "basal_o2": "pPepT basal",
    "ec50_lactate_mM": "Lactate EC50",
    "hill_lactate": "Lactate Hill",
    "basal_lactate": "lldPRD basal",
}


def sobol_drivers(indices=None, path: Path | None = None) -> Path:
    """Module 3.5's figure: what decides the margin, and where 9.23 was looking.

    Left: first- against total-order index at the bottleneck. The gap is the
    quantity of interest -- a parameter whose ST greatly exceeds its S1 governs
    how much the others matter rather than moving the output itself.
    Right: total-order index at the colonic mucosa against the bottleneck. The
    driver set swaps completely, and the two parameters that drive the real
    bottleneck are absent from the mucosa analysis entirely.
    """
    from . import sensitivity as SE

    path = path or FIGURES / "fig3_5_sobol_drivers.png"
    if indices is None:
        indices = SE.run()

    bottleneck = (
        indices[indices.output == "bottleneck"].sort_values("ST").reset_index(drop=True)
    )
    mucosa = indices[indices.output == "colonic_mucosa"].set_index("parameter")
    order = list(bottleneck["parameter"])
    labels = [PARAMETER_LABELS[name] for name in order]
    positions = np.arange(len(order))

    fig, (left, right) = plt.subplots(1, 2, figsize=(11.6, 4.8), facecolor=SURFACE)

    # -- left: S1 against ST at the bottleneck ----------------------------
    left.hlines(positions, bottleneck["S1"], bottleneck["ST"],
                color=GRID, linewidth=2.4, zorder=2)
    left.scatter(bottleneck["S1"], positions, s=52, color=SERIES_1, zorder=3,
                 edgecolor=SURFACE, linewidth=1.4, label="first order  $S_1$")
    left.scatter(bottleneck["ST"], positions, s=52, color=SERIES_2, zorder=3,
                 marker="s", edgecolor=SURFACE, linewidth=1.4, label="total order  $S_T$")

    # The annotation states the ratio and stops there; what a large ST/S1 means
    # is the legend's job, not the picture's. Computed, so it cannot drift.
    n_q = int(positions[order.index("n_Q")])
    n_q_ratio = float(bottleneck.loc[n_q, "ST"]) / float(bottleneck.loc[n_q, "S1"])
    left.annotate(
        f"$S_T$ = {n_q_ratio:.1f} × $S_1$",
        xy=(float(bottleneck.loc[n_q, "ST"]), n_q),
        xytext=(0.30, n_q - 1.75), fontsize=8.5, color=INK_SECONDARY,
        ha="left", va="center",
        arrowprops=dict(arrowstyle="-", color=INK_MUTED, linewidth=1.0,
                        connectionstyle="arc3,rad=0.25"),
    )

    left.set_yticks(positions)
    left.set_yticklabels(labels, fontsize=9)
    left.set_xlim(-0.02, 0.52)
    left.set_ylim(-0.7, len(order) - 0.3)
    left.set_xlabel("Sobol index, log-scale output", fontsize=10, color=INK_SECONDARY)
    left.set_title("What decides the bottleneck margin",
                   fontsize=12, color=INK_PRIMARY, loc="left", pad=10)
    _style_axes(left)
    left.grid(axis="y", visible=False)
    legend = left.legend(loc="lower right", frameon=False, fontsize=8.5)
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)

    # -- right: mucosa against bottleneck ---------------------------------
    height = 0.36
    right.barh(positions + height / 2, [float(mucosa.loc[n, "ST"]) for n in order],
               height=height, color=SERIES_1, zorder=3, label="colonic mucosa")
    right.barh(positions - height / 2, bottleneck["ST"],
               height=height, color=SERIES_2, zorder=3, label="bottleneck site")

    for name in ("lumen_density_ratio", "repression_fold"):
        y = int(positions[order.index(name)])
        right.text(0.012, y + height / 2, "absent from the mucosa model",
                   fontsize=8, color=INK_MUTED, va="center")

    right.set_yticks(positions)
    right.set_yticklabels(labels, fontsize=9)
    right.set_xlim(0.0, 0.82)
    right.set_ylim(-0.7, len(order) - 0.3)
    right.set_xlabel("Total-order index  $S_T$", fontsize=10, color=INK_SECONDARY)
    right.set_title("The driver set swaps between sites",
                    fontsize=12, color=INK_PRIMARY, loc="left", pad=10)
    _style_axes(right)
    right.grid(axis="y", visible=False)
    legend = right.legend(loc="lower right", frameon=False, fontsize=8.5)
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)

    fig.text(0.008, 0.015,
             "Saltelli sampling over the declared ranges, output analysed as log10 of the "
             "tumour-over-site ratio so the multiplicative model becomes additive.",
             fontsize=8, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, path)


def all_figures() -> list[Path]:
    return [
        immune_feasibility(),
        arm_direction(),
        tissue_axis(),
        cluster_equivalence(),
        dose_requirement(),
        sobol_drivers(),
    ]


def video_figures() -> list[Path]:
    """The three extra panels the presentation video needs."""
    return [
        gate_holdout(),
        lesion_floor(),
        modelling_contribution(),
    ]


# -- figures for the presentation video -----------------------------------
#
# These are narration aids, not wiki figures: the wiki page captions every PNG
# in ``outputs/figures`` and is checked for it, so video-only assets live one
# directory down.

VIDEO_FIGURES = FIGURES / "video"


def gate_holdout(path: Path | None = None) -> Path:
    """Validation layer: the AND claim restated as an out-of-sample prediction.

    Left: the four reporter corners at 24 h, as the 2x2 the gate is defined on,
    with the fully-on corner marked as the one held out. Right: predicted
    against measured for every held-out corner, at the 24 h endpoint and at the
    9 h mid-course. The endpoint lands on the identity line; mid-course does
    not, which is what gives the holdout its power.
    """
    from . import data as D
    from . import gate as G
    from . import validation as V

    path = path or VIDEO_FIGURES / "fig2_2_gate_holdout.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    wb = D.load()
    endpoint = V.gate_corner_holdout(wb, time_h=V.ENDPOINT_H)
    midcourse = V.gate_corner_holdout(wb, time_h=V.MIDCOURSE_H)

    def _by_corner(frame):
        out = {}
        for _, row in frame.iterrows():
            out[str(row["held"]).split(" ", 1)[0]] = row
        return out

    end_rows = _by_corner(endpoint)
    mid_rows = _by_corner(midcourse)

    fig, (left, right) = plt.subplots(
        1, 2, figsize=(11.5, 4.4), facecolor=SURFACE,
        gridspec_kw={"width_ratios": [1.0, 1.15]},
    )

    # -- left panel: the 2x2 the gate is defined on ----------------------
    # Rows are oxygen (aerobic on top), columns lactate. Corner keys follow
    # gate.CORNERS: A aerobic/no lactate, B hypoxic/no lactate, C aerobic +
    # lactate, D hypoxic + lactate.
    layout = {"A": (0, 1), "B": (0, 0), "C": (1, 1), "D": (1, 0)}
    for corner, (col, row) in layout.items():
        observed = float(end_rows[corner]["observed"])
        shade = 0.10 + 0.78 * (observed / 100.0)
        left.add_patch(
            plt.Rectangle(
                (col, row), 0.92, 0.92,
                facecolor=SERIES_1, alpha=shade, edgecolor=GRID, linewidth=1.2, zorder=2,
            )
        )
        label_ink = SURFACE if observed > 55.0 else INK_PRIMARY
        left.text(col + 0.46, row + 0.46, f"{observed:.1f} %",
                  ha="center", va="center", fontsize=16, color=label_ink, zorder=3)

    held = "D"
    hcol, hrow = layout[held]
    left.add_patch(
        plt.Rectangle(
            (hcol - 0.03, hrow - 0.03), 0.98, 0.98,
            facecolor="none", edgecolor=SERIES_2, linewidth=2.6, zorder=4,
        )
    )
    left.annotate(
        "held out, then predicted from\n"
        f"the other three:  {float(end_rows[held]['predicted']):.2f} %",
        xy=(hcol + 0.46, hrow - 0.05), xytext=(hcol + 0.46, -0.34),
        ha="center", va="top", fontsize=9.5, color=SERIES_2,
        arrowprops=dict(arrowstyle="-", color=SERIES_2, linewidth=1.2),
        annotation_clip=False,
    )

    left.set_xlim(-0.15, 2.05)
    left.set_ylim(-0.95, 2.30)
    left.set_xticks([0.46, 1.46])
    left.set_xticklabels(["no lactate", "+ 20 mM lactate"], fontsize=9.5)
    left.xaxis.set_ticks_position("top")
    left.xaxis.set_label_position("top")
    left.set_yticks([0.46, 1.46])
    left.set_yticklabels(["1 % O$_2$", "21 % O$_2$"], fontsize=9.5)
    left.tick_params(colors=INK_SECONDARY, length=0)
    left.set_facecolor(SURFACE)
    for side in ("top", "right", "left", "bottom"):
        left.spines[side].set_visible(False)
    left.set_title("The four corners at 24 h  (percent positive)",
                   fontsize=12, color=INK_PRIMARY, loc="left", pad=10)

    # -- right panel: predicted against measured -------------------------
    identity = np.array([0.08, 140.0])
    right.plot(identity, identity, color=INK_MUTED, linewidth=1.0, linestyle="--", zorder=2)
    right.fill_between(
        identity, identity * (1.0 - V.RATIO_TOLERANCE), identity * (1.0 + V.RATIO_TOLERANCE),
        color=INK_MUTED, alpha=0.12, linewidth=0, zorder=1,
    )

    for rows, colour, marker, label in (
        (end_rows, SERIES_1, "o", f"{V.ENDPOINT_H:.0f} h endpoint  —  4/4 pass"),
        (mid_rows, SERIES_2, "s", f"{V.MIDCOURSE_H:.0f} h mid-course  —  4/4 fail"),
    ):
        xs = [float(row["observed"]) for row in rows.values()]
        ys = [float(row["predicted"]) for row in rows.values()]
        right.scatter(xs, ys, s=62, color=colour, marker=marker, zorder=4,
                      edgecolor=SURFACE, linewidth=1.0, label=label)

    right.annotate(
        f"{float(end_rows['D']['predicted']):.2f} % predicted\n"
        f"{float(end_rows['D']['observed']):.2f} % measured",
        xy=(float(end_rows["D"]["observed"]), float(end_rows["D"]["predicted"])),
        xytext=(14.0, 118.0), fontsize=9, color=SERIES_1, ha="left",
        arrowprops=dict(arrowstyle="-", color=SERIES_1, linewidth=1.0),
    )
    right.text(0.11, 44.0, "±25 % band\n(declared before the run)",
               fontsize=8.5, color=INK_MUTED, va="center")

    right.set_xscale("log")
    right.set_yscale("log")
    right.set_xlim(0.08, 140.0)
    right.set_ylim(0.08, 220.0)
    right.set_xlabel("Measured  (% positive)", fontsize=10, color=INK_SECONDARY)
    right.set_ylabel("Predicted from the other three corners  (%)",
                     fontsize=10, color=INK_SECONDARY)
    right.set_title("Predicted against measured", fontsize=12, color=INK_PRIMARY,
                    loc="left", pad=10)
    _style_axes(right)
    legend = right.legend(loc="lower right", frameon=False, fontsize=8.5)
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)

    fig.text(0.008, 0.015,
             "Leave one corner out, predict it from the other three (multiplicative gate = "
             "additive in probit units). Tolerance +/-25 %, declared before the run.",
             fontsize=8, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, path)


def lesion_floor(path: Path | None = None) -> Path:
    """Module 3.2: the parameter-free geometric floor on what the gate can see.

    Left: the two lesions to scale -- oxygen reaches a fixed depth in from the
    perfused surface, so a lesion thinner than that depth has no hypoxic volume
    at all. Right: hypoxic volume fraction against radius, with the histology
    range the derived depth is checked against.
    """
    from . import lesion_size as L

    path = path or VIDEO_FIGURES / "fig3_2_lesion_floor.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    model = L.LesionSize()
    depth = float(model.smallest_lesion_with_a_hypoxic_core_um)
    small, large = 150.0, 400.0

    fig, (leftax, right) = plt.subplots(
        1, 2, figsize=(11.5, 4.4), facecolor=SURFACE,
        gridspec_kw={"width_ratios": [1.0, 1.2]},
    )

    # -- left panel: the two lesions, to scale ---------------------------
    for centre, radius, name in ((-470.0, small, "150 µm lesion"), (470.0, large, "400 µm lesion")):
        core = float(model.hypoxic_core_radius(radius))
        leftax.add_patch(plt.Circle((centre, 0.0), radius, facecolor=SERIES_2,
                                    alpha=0.22, edgecolor=SERIES_2, linewidth=1.4, zorder=2))
        if core > 0.0:
            leftax.add_patch(plt.Circle((centre, 0.0), core, facecolor=SERIES_1,
                                        alpha=0.85, edgecolor="none", zorder=3))
            leftax.text(centre, 0.0, f"hypoxic\ncore\n{core:.0f} µm",
                        ha="center", va="center", fontsize=9, color=SURFACE, zorder=4)
        else:
            leftax.text(centre, 0.0, "no hypoxic\nvolume at all",
                        ha="center", va="center", fontsize=9.5, color=INK_PRIMARY, zorder=4)
        leftax.text(centre, -radius - 95.0, name, ha="center", va="top",
                    fontsize=10, color=INK_SECONDARY)

    # the penetration depth, drawn on the larger lesion
    leftax.annotate(
        "", xy=(470.0 + large, 60.0), xytext=(470.0 + large - depth, 60.0),
        arrowprops=dict(arrowstyle="<->", color=INK_PRIMARY, linewidth=1.2),
    )
    leftax.text(470.0 + large - depth / 2.0, 115.0, f"O$_2$ reaches\n{depth:.0f} µm in",
                ha="center", va="bottom", fontsize=9, color=INK_PRIMARY)

    leftax.set_xlim(-800.0, 950.0)
    leftax.set_ylim(-620.0, 520.0)
    leftax.set_aspect("equal")
    leftax.axis("off")
    leftax.set_facecolor(SURFACE)
    leftax.set_title("Oxygen reaches a fixed depth in from the surface",
                     fontsize=12, color=INK_PRIMARY, loc="left", pad=10)

    # -- right panel: hypoxic fraction against radius --------------------
    radii = np.linspace(50.0, 700.0, 651)
    fraction = model.hypoxic_fraction(radii) * 100.0

    right.axvspan(160.0, 200.0, color=SERIES_2, alpha=0.16, linewidth=0, zorder=1)
    right.text(180.0, 44.0, "histology\n160–200 µm", ha="center", va="center",
               fontsize=8.5, color=SERIES_2)
    right.axvspan(50.0, depth, color=INK_MUTED, alpha=0.13, linewidth=0, zorder=1)
    right.plot(radii, fraction, color=SERIES_1, linewidth=2.2, zorder=3)
    right.axvline(depth, color=INK_PRIMARY, linewidth=1.1, linestyle=":", zorder=2)

    right.text(113.0, 26.0, "no hypoxic\ncore at all", ha="center", va="center",
               fontsize=11, color=INK_SECONDARY)
    right.annotate(f"{depth:.0f} µm", xy=(depth, 0.0), xytext=(depth + 16.0, 6.0),
                   fontsize=10, color=INK_PRIMARY, ha="left")

    right.set_xlim(50.0, 700.0)
    right.set_ylim(0.0, 52.0)
    right.set_xlabel("Lesion radius  (µm)", fontsize=10, color=INK_SECONDARY)
    right.set_ylabel("Hypoxic volume fraction  (%)", fontsize=10, color=INK_SECONDARY)
    right.set_title("A safety floor that needs no calibration",
                    fontsize=12, color=INK_PRIMARY, loc="left", pad=10)
    _style_axes(right)

    fig.text(0.008, 0.015,
             "Pure geometry: the hypoxic core is max(R - d, 0), so below the penetration depth "
             "there is no hypoxic volume to sense. Distant micro-disease needs another route.",
             fontsize=8, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, path)


def modelling_contribution(path: Path | None = None) -> Path:
    """Closing slide: what measured data went in, and what came back out.

    No equations -- this one carries the narration's last modelling beat, that
    the wet-dry connection is specific rather than decorative.
    """
    from matplotlib.patches import FancyBboxPatch

    path = path or VIDEO_FIGURES / "fig7_contribution.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        (
            "Measured, in",
            INK_SECONDARY,
            [
                "reporter, four conditions, 9 h and 24 h",
                "co-culture killing at three doses",
                "growth curves and carrying capacity",
                "published tissue oxygen and lactate",
            ],
        ),
        (
            "Modelling",
            SERIES_1,
            [
                "is the gate a product of its inputs?",
                "where else could it switch on?",
                "what size of lesion can it see?",
                "what dose does the indication need?",
                "can the immune response reach further?",
            ],
        ),
        (
            "Decisions, out",
            SERIES_2,
            [
                "kept the native lldPRD promoter",
                "abandoned the de-repressed swap",
                "178 µm floor, declared as a limit",
                "micrometastasis is not a dose problem",
                "treat early rather than larger",
            ],
        ),
    ]

    fig, ax = plt.subplots(figsize=(11.5, 4.4), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    width, gap = 3.0, 0.62
    for index, (heading, colour, lines) in enumerate(columns):
        x = index * (width + gap)
        ax.add_patch(
            FancyBboxPatch(
                (x, 0.0), width, 3.4,
                boxstyle="round,pad=0.02,rounding_size=0.12",
                facecolor=colour, alpha=0.07, edgecolor=colour, linewidth=1.3, zorder=2,
            )
        )
        ax.text(x + 0.20, 3.08, heading, fontsize=12.5, color=colour, va="center", zorder=3)
        ax.hlines(2.88, x + 0.20, x + width - 0.20, color=colour, alpha=0.35, linewidth=1.0, zorder=3)
        for line_index, line in enumerate(lines):
            y = 2.52 - 0.46 * line_index
            ax.text(x + 0.26, y, "·", fontsize=12, color=colour, va="center", zorder=3)
            ax.text(x + 0.46, y, line, fontsize=9.5, color=INK_PRIMARY, va="center",
                    zorder=3, wrap=True)
        if index < len(columns) - 1:
            ax.annotate("", xy=(x + width + gap - 0.06, 1.7), xytext=(x + width + 0.06, 1.7),
                        arrowprops=dict(arrowstyle="-|>", color=INK_MUTED, linewidth=1.6))

    ax.set_xlim(-0.2, 3 * width + 2 * gap + 0.2)
    ax.set_ylim(-0.55, 3.65)
    ax.axis("off")
    fig.text(0.008, 0.035,
             "Every input is a measurement this team made or a published value we cite; every "
             "output is a decision the project acted on, or a limit it now states.",
             fontsize=8.5, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, path)
