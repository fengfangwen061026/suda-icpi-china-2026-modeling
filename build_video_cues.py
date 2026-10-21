"""Assemble the presentation-video figure folder, in cue order.

Six panels are reused from the wiki figure set; three are video-only and are
rendered by ``plots.video_figures()``. Numbered copies land in
``outputs/video_cues`` so the editor has one folder in narration order.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from src import plots as P

ROOT = Path(__file__).resolve().parent
CUES = ROOT / "outputs" / "video_cues"

#: (cue number, source figure, short name for the file)
ORDER: list[tuple[int, Path, str]] = [
    (1, P.FIGURES / "fig1_circuit.png", "circuit"),
    (2, P.VIDEO_FIGURES / "fig2_2_gate_holdout.png", "and_gate_holdout"),
    (3, P.FIGURES / "fig3_3_arm_direction.png", "arms_anti_selective"),
    (4, P.FIGURES / "fig3_1_tissue_axis.png", "tissue_axis_bottleneck"),
    (5, P.VIDEO_FIGURES / "fig3_2_lesion_floor.png", "lesion_floor_178um"),
    (6, P.FIGURES / "fig4_6_dose_requirement.png", "dose_vs_margin"),
    (7, P.FIGURES / "fig4_4_cluster.png", "micrometastasis_cluster"),
    (8, P.FIGURES / "fig6_immune_feasibility.png", "immune_feasibility"),
    (9, P.VIDEO_FIGURES / "fig7_contribution.png", "contribution"),
]


def build() -> list[Path]:
    P.all_figures()
    P.video_figures()
    CUES.mkdir(parents=True, exist_ok=True)
    for stale in CUES.glob("*.png"):
        stale.unlink()
    written = []
    for number, source, name in ORDER:
        if not source.exists():
            raise FileNotFoundError(source)
        target = CUES / f"{number:02d}_{name}.png"
        shutil.copy2(source, target)
        written.append(target)
    return written


if __name__ == "__main__":
    for path in build():
        print(path.relative_to(ROOT))
