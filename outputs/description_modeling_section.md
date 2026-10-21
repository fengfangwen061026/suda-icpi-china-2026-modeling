## 1.5 Modelling: What the Numbers Changed in the Design

建模段：AND 门在哪些位点仍会打开、哪些设计"改进"会破坏安全性，以及有效剂量反推。

The architecture described above is designed for preferential activation rather
than tumour-exclusive expression. That design choice raises a question the
architecture alone cannot answer: at which anatomical sites, and under which
conditions, does preferential become sufficient? We therefore built a
quantitative model of the circuit and of the environments it would meet,
calibrated on the 391 measurements this cycle's wet lab produced. Four of its
results changed the design rather than illustrating it.

Signal integration behaves multiplicatively at the endpoint, but not before it.
The interaction between the hypoxia-associated and lactate-associated arms is
zero within error at 24 h, and the factorised description predicts a held-out
input combination to within 2.2 %. At 6 and 9 h the same prediction is wrong by
up to 4.4-fold. We therefore treat the circuit as a product of its two inputs
only at the endpoint, and do not quote mid-course on/off ratios anywhere in this
project.

The tightest safety margin is at the colonic mucosa, not in the tissue next to a
tumour. Comparing gate output across tissue sites (Fig. 2), the mucosa
sits 21.85-fold below the tumour, closer than any other site on the axis. The gut lumen stays
off, but only because the native lldPRD promoter is additionally repressed by
glucose and by anoxia [6]; on the engineered inputs alone, every
luminal site we examined falls below the tumour-equivalent level.

That result argues against an apparently obvious improvement. Replacing the
native lactate promoter with a de-repressed, higher-dynamic-range variant would
raise reporter output, but it collapses luminal discrimination from 87–228-fold
to 0.87–2.28-fold. We kept the native, lower-performing promoter deliberately,
and record this as a design decision taken on quantitative grounds.

There is a lesion size below which the hypoxia-associated arm cannot contribute
at all: approximately 178 µm in radius. This follows from oxygen diffusion
geometry and contains no fitted parameters, and it falls inside the 160–200 µm
range measured histologically by Thomlinson and Gray [7], which
makes it the one quantity here that an independent measurement corroborates.

![Gate output across tissue sites](outputs/figures/fig3_1_tissue_axis.png)
**Figure 2. Modelled gate output at six tissue sites, with and without
the native lldPRD repression.** Each bar is the ratio of gate output in the
tumour core to gate output at that site, on a logarithmic axis; the vertical
line marks a ratio of 1 and the shaded band to its left marks ratios below it,
where a site's output equals or exceeds the tumour's. Blue bars are the
designed hypoxia and lactate arms alone; green bars add the native repression
of the lldPRD promoter by anoxia and by glucose, entered as 10-fold each. The
quorum Hill coefficient is held at the published value of 1 and the oxygen
sensor constant at 0.49 % O₂.

The same framework was used to ask what dose a therapeutic effect would require.
Net killing in co-culture scales as roughly the cube of dose, with a fitted
exponent of 2.65 (Fig. 3). On that relation, the effect size reported for the human
indication is reached below the lowest dose we tested, while the CT26 benchmark
requires 1.3–1.8 times the highest. The binding constraint is not potency but
what escalation costs: reaching a 150 µm micro-lesion would require 4.95 times
the dose and would leave only 4.41-fold of the mucosal margin, below the 10-fold
we set as a working requirement. Micrometastatic disease is therefore not a dose
problem, and would need to be addressed by another route.

![Dose requirement against the safety margin](outputs/figures/fig4_6_dose_requirement.png)
**Figure 3. Dose–kill relation, and the escalation and remaining margin
against lesion radius.** Left: net CT26 killing over 24 h against co-culture
dose, logarithmic axes. Points are measurements net of the GFP control with
standard-error bars, the shaded band the doses tested, the line a power-law fit
of exponent 2.65, and the horizontal bands the target effect sizes, 0.12–0.69 %
(human) and 29.3–50 % (CT26). Right: fold change against lesion radius,
logarithmic — circles the escalation that radius needs, squares the
colonic-mucosa margin left, priced on 21.85-fold. The dashed line at 10 is the
required margin, that at 1 none left, the dotted vertical at 178 µm the smallest
radius with a hypoxic core; the circled 150 µm point reads 4.95-fold dose,
4.41-fold margin left.

These analyses are computational and are calibrated on in vitro data; they
include no animal work, and several inputs are stated as intervals or declared
assumptions rather than measurements. The equations, parameter provenance,
worked substitutions and out-of-sample tests are given on the Model page, where
each assumption is marked at the point it is used.

### References (continuing the numbering of this page)

[6] Zúñiga A, Camacho M, Chang H-J, Fristot E, Mayonove P, Hani E-H, Bonnet J. An engineered lactate-responding promoter system operating in glucose-rich and anaerobic environments. *ACS Synthetic Biology* 2021; 10(12):3527–3536. doi:10.1021/acssynbio.1c00456
[7] Thomlinson RH, Gray LH. The histological structure of some human lung cancers and the possible implications for radiotherapy. *British Journal of Cancer* 1955; 9(4):539–549. doi:10.1038/bjc.1955.55
