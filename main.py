"""Print the settled findings straight from the workbook.

Everything below is read out of `data/全部实验数据.xlsx` at run time, so the
numbers in DATA_CONVENTIONS.md and README.md can always be checked against the
data rather than trusted.

    .venv/bin/python main.py
"""

from __future__ import annotations

from src import data as D


def rule(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def main() -> None:
    wb = D.load()
    print(f"source: {wb.source.name}")

    rule("Replication gaps (reported as-is, never filled)")
    gaps = D.replication_gaps(wb)
    for row in gaps.itertuples():
        sd = "SD=0 -> no t-test valid" if row.sd == 0 else f"SD={row.sd:.2f}"
        print(f"  block {row.block}  {row.construct:11} {row.cell_line:5} "
              f"@{row.dose_od:4.0f} OD   n={row.n}  mean={row.mean:.2f}  {sd}")

    rule("Convention 1 - censored intensity wells")
    censored = int(wb.reporter_intensity["censored"].sum())
    print(f"  {censored} wells read exactly 0 intensity")
    for (group, time_h), rows in wb.reporter_intensity.groupby(["group", "time_h"]):
        n_cens = int(rows["censored"].sum())
        if not n_cens:
            continue
        positive = D.reporter_summary(wb, group, float(time_h), readout="positive")
        verdict = "contradicted by block 4" if positive.mean > 0 else "genuinely dark"
        raw = ", ".join(f"{v:.0f}" for v in rows.sort_values("replicate")["intensity"])
        print(f"  {group:11} {time_h:4.0f} h  [{raw:28}]  "
              f"positive {positive.mean:5.1f} %  -> {verdict}")

    rule("Convention 2 - blocks 5 and 6 are different experiments")
    duplicated = D.block6_duplicated_constructs(wb)
    suppression = D.block6_suppression(wb)
    print(f"  block 6 ran at {suppression.mean:.3f} of block 5 "
          f"(geometric mean over {suppression.n} independently measured constructs)")
    print(f"  constructs whose block-6 ct26 row duplicates block 5: {', '.join(duplicated)}")
    print()
    for construct in D.CONSTRUCTS:
        if construct == "Blank":
            continue
        si = D.selectivity_index(wb, construct)
        print(f"  {si}")
        print(f"      {si.note}")

    rule("Chassis survival - the answer to PPT p.21")
    for construct in ("GSDMD-SsrA", "GSDMD"):
        for background, off, on in (
            ("normoxic", "有氧无酸", "有氧有酸"),
            ("hypoxic ", "无氧无酸", "无氧有酸"),
        ):
            rows = wb.growth_of(construct)
            at24 = rows[rows.time_h == 24.0]
            uninduced = at24[at24.condition == off]["od"].mean()
            induced = at24[at24.condition == on]["od"].mean()
            print(f"  {construct:11} {background}  induced/uninduced = "
                  f"{induced / uninduced:.3f}   ({induced:.3f} / {uninduced:.3f} OD)")

    print()
    for construct in ("GSDMD-SsrA", "GSDMD"):
        for condition in ("有氧有酸", "无氧有酸"):
            rows = wb.growth_of(construct)
            series = rows[rows.condition == condition].groupby("time_h")["od"].mean()
            drop = series.iloc[-1] / series.max() - 1.0
            print(f"  {construct:11} {condition}  peak -> 24 h: {drop:+.1%}")
    print("  => OD never falls under induction; the hypoxic decline is larger for the")
    print("     TAGGED strain, so it cannot be effector-driven lysis.")

    rule("The gate is lactate-dominated")
    for label, readout in (("percent positive", "positive"), ("intensity", "intensity")):
        fold = D.fold_change(
            D.reporter_summary(wb, "1% - 20mM", 24.0, readout=readout),
            D.reporter_summary(wb, "21% - 20mM", 24.0, readout=readout),
        )
        print(f"  24 h hypoxia fold, {label:16}: {fold:.2f}x")
    rows = wb.growth_of("GSDMD")
    at24 = rows[rows.time_h == 24.0]
    growth_fold = (
        at24[at24.condition == "无氧有酸"]["od"].mean()
        / at24[at24.condition == "有氧有酸"]["od"].mean()
    )
    print(f"  24 h hypoxia fold, untagged OD   : {growth_fold:.2f}x")
    print()
    for time_h in (6.0, 9.0):
        fold = D.fold_change(
            D.reporter_summary(wb, "1% - 20mM", time_h, readout="positive"),
            D.reporter_summary(wb, "21% - 20mM", time_h, readout="positive"),
        )
        print(f"  {time_h:4.0f} h hypoxia fold, percent positive: {fold:.2f}x  (onset effect)")

    rule("TAT costs selectivity (all L929 rows are from block 6)")
    normals = {c: D.selectivity_index(wb, c).normal.mean for c in
               ("GSDMD-SsrA", "GSDMD", "GSDMD-TAT")}
    for construct, value in normals.items():
        print(f"  {construct:11} L929 {value:5.2f} %")
    print(f"  TAT vs SsrA-tagged: {normals['GSDMD-TAT'] / normals['GSDMD-SsrA']:.1f}x off-target")
    print(f"  TAT vs untagged   : {normals['GSDMD-TAT'] / normals['GSDMD']:.1f}x off-target")
    five = wb.killing_block(5)
    five10 = five[five.dose_od == 10.0]
    gain = (
        five10[five10.construct == "GSDMD-TAT"]["percent"].mean()
        / five10[five10.construct == "GSDMD"]["percent"].mean()
    )
    print(f"  benefit, paired within block 5   : {gain:.2f}x on-target")

    rule("Unsettled - the SsrA decision flips sign")
    at24 = wb.growth_of("GSDMD-SsrA")
    at24 = at24[(at24.time_h == 24.0) & (at24.condition == "有氧有酸")]["od"].mean()
    un24 = wb.growth_of("GSDMD")
    un24 = un24[(un24.time_h == 24.0) & (un24.condition == "有氧有酸")]["od"].mean()
    biomass = at24 / un24
    print(f"  biomass gain from SsrA (21 % O2 + 20 mM) = {biomass:.2f}x")
    for label, block, cell_line in (("block 5", 5, "ct26"), ("block 6", 6, "ct26")):
        rows = wb.killing[
            (wb.killing.block == block)
            & (wb.killing.cell_line == cell_line)
            & (wb.killing.dose_od == 10.0)
        ]
        cost = (
            rows[rows.construct == "GSDMD"]["percent"].mean()
            / rows[rows.construct == "GSDMD-SsrA"]["percent"].mean()
        )
        net = biomass / cost
        verdict = "keep SsrA" if net > 1 else "drop SsrA"
        print(f"  potency cost, {label} paired = {cost:.2f}x  ->  net {net:.2f}x  ->  {verdict}")
    print("  => §3.4 must scan potency_ratio over [1.41, 4.70] and report both branches.")


if __name__ == "__main__":
    main()
