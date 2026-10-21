"""Build `Model_Figure_Legends.docx` -- the rewritten legends for all three
modelling documents: the Model module (the wiki's seven pages), Engineering.docx
and the Description §1.5 insert.

Written to the 2026-10-20 house rule rather than to `DOC_STANDARD.md` §103's
older "this figure answers §0's n-th question" form:

  * ``Figure n.`` and the title sentence are bold, upright; the description
    that follows is neither bold nor italic.
  * The description states only what is in the image -- axes, scales, series,
    colours, bands, reference lines, printed values, held parameters -- and
    draws no conclusion from it.
  * Within the Model module figures are numbered continuously across its seven
    pages, the three summary charts included, because the module shares one
    equation numbering too (`DOC_STANDARD.md` §208: 图号连续). Engineering and
    the Description insert are separate documents and keep their own numbering.
  * Four figures appear in two or three of the documents. Their legends are
    read out of the drafts that build the Word files, so this table cannot
    drift from what is published, and the only licensed difference between two
    copies of one legend is the equation reference.

The file carries the legends, the line identifying which image each belongs to,
the six images redrawn so that nothing inside them draws a conclusion, and the
cross-document duplicate check.

    PYTHONPATH=. .venv/bin/python build_figure_legends_docx.py
"""

from __future__ import annotations

import base64
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from src.docx_vector import attach_svg, vector_pairs

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "Model_Figure_Legends.docx"
OUT_MD = OUT.with_suffix(".md")
VECTORS = ROOT / "outputs" / "figures" / "vector"
TITLE = "建模三个模块的图注（改写稿）"

HAN = "宋体"
LATIN = "Calibri"
INK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x5A, 0x5A, 0x5A)
ACCENT = RGBColor(0x1F, 0x5C, 0x3A)

#: Printable width of the page, less the margins set below.
TEXT_WIDTH = Cm(16.0)

BASE = "https://2026.igem.wiki/suda-icpi-china/model/"

#: Figures regenerated on 2026-10-21 so that nothing inside the image draws a
#: conclusion, keyed by the locator below. These are embedded in the document
#: and have to replace the assets currently on the wiki.
REDRAWN = {
    "fig3_1": ROOT / "outputs/figures/fig3_1_tissue_axis.png",
    "fig3_3": ROOT / "outputs/figures/fig3_3_arm_direction.png",
    "fig3_5": ROOT / "outputs/figures/fig3_5_sobol_drivers.png",
    "fig4_4": ROOT / "outputs/figures/fig4_4_cluster.png",
    "fig4_6": ROOT / "outputs/figures/fig4_6_dose_requirement.png",
    "fig2_2": ROOT / "outputs/figures/video/fig2_2_gate_holdout.png",
    "fig1_circuit": ROOT / "outputs/figures/fig1_circuit.png",
}

#: Every figure the repo draws now has a vector master beside its PNG, written
#: by `src/plots.py` in the same call. The Word files carry both: the PNG as the
#: fallback Word always renders, the SVG as what Word 2016+ and WPS draw from.
VECTOR_STEMS = {
    "fig3_1": "fig3_1_tissue_axis",
    "fig3_3": "fig3_3_arm_direction",
    "fig3_5": "fig3_5_sobol_drivers",
    "fig4_4": "fig4_4_cluster",
    "fig4_6": "fig4_6_dose_requirement",
    "fig2_2": "fig2_2_gate_holdout",
    "fig6_immune": "fig6_immune_feasibility",
}

#: One figure was not re-plotted but repainted, so it gets its own opening.
REDRAWN_PREFIX = {
    "fig1_circuit": "改好的图（需上传替换 wiki 上的旧图）：",
}

#: What changed inside each redrawn image, for the line above it.
REDRAWN_NOTE = {
    "fig3_1": "底注删去"
              "“Bottleneck moves from the dysbiotic lumen to the mucosa.”，"
              "只保留图所用的参数；数据未变。",
    "fig3_3": "底注删去"
              "“Structural: true for every EC50, Hill and basal.”，改为两条臂各自的参数；"
              "数据未变——逐像素比对过，wiki 上那张的缺氧臂比值与现行计算一致，"
              "原图注里“oxygen-arm ratios reflect earlier values”那句是错的。",
    "fig3_5": "左图标注"
              "“$S_T$ three times $S_1$: it sets how much the rest matters”"
              "改为只给比值“$S_T$ = 3.4 × $S_1$”；数据未变。",
    "fig4_4": "底注删去“, not micrometastases”，"
              "改为两条虚线各自是什么；图内“ON band (9.23)”里那个 9.23 是已废弃的"
              "9.23 文档编号，读者无从理解，改成“ON band (1000 µm)”。数据未变。",
    "fig4_6": "底注删去"
              "“CT26 needs 1.3-1.8x the highest dose tested…”，改为两幅图各自的参数与band；"
              "右图标注去掉“— under the line”；旧图底注的 19.6× 已更新为 21.85×，"
              "并补上 10× 要求线与 150 µm 标注点。",
    "fig1_circuit": "乳酸构件下面原来印的是“lldPDR”，操纵子与零件都是"
                    "“lldPRD”（lldP、lldR、lldD），全项目其余文档都这么写，图与自己的"
                    "图注打架。这张图是别处做的位图，仓库里没有矢量源，所以只把那一个"
                    "标签按原底色、原位置重排（`fix_circuit_label.py`），别处一个像素没动；"
                    "收到时的原图留在 outputs/figures/source/ 备查。要矢量仍得找做图的"
                    "同学导出 SVG。",
    "fig2_2": "右图标题“A prediction, not a fit”是论断，改成"
              "“Predicted against measured”；底注的“The AND logic holds at the endpoint, "
              "not mid-course.”改成只写容差。数据未变。",
}

#: The three documents share four figures. Their legends are read out of the
#: drafts that build the Word files rather than retyped here, so this table
#: cannot drift from what is actually published; `shared_legend` refuses a
#: placeholder it cannot find, and the dose legend is asserted identical in the
#: two drafts that both carry it.
ENG_DRAFT = ROOT / "ENGINEERING_DRAFT.md"
DESC_DRAFT = ROOT / "DESCRIPTION_DRAFT.md"


def shared_legend(draft: Path, placeholder: str) -> tuple[str, str]:
    """Return (title, description) of ``**Figure {#placeholder}. ...**`` in `draft`."""
    text = draft.read_text(encoding="utf-8")
    opening = f"**Figure {{#{placeholder}}}. "
    start = text.index(opening)
    block = text[start:text.index("\n\n", start)]
    title, body = block[len(opening):].split("**", 1)
    collapse = lambda part: " ".join(part.split())
    return collapse(title), collapse(body)


GATE_TITLE, GATE_BODY = shared_legend(ENG_DRAFT, "gate")
ARMS_TITLE, ARMS_BODY = shared_legend(ENG_DRAFT, "arms")
CLUSTER_TITLE, CLUSTER_BODY = shared_legend(ENG_DRAFT, "cluster")
DOSE_TITLE, DOSE_BODY = shared_legend(ENG_DRAFT, "dose")
TISSUE_TITLE, TISSUE_BODY = shared_legend(DESC_DRAFT, "tissue")

if (DOSE_TITLE, DOSE_BODY) != shared_legend(DESC_DRAFT, "dose"):
    raise SystemExit(
        "the dose legend differs between ENGINEERING_DRAFT.md and "
        "DESCRIPTION_DRAFT.md -- they are the same figure and must read the same"
    )


def with_equations(body: str, *replacements: tuple[str, str]) -> str:
    """The Model page numbers its equations; the other two documents do not.

    That is the only licensed difference between two copies of one legend, so
    it is applied here and nowhere else.
    """
    for old, new in replacements:
        if old not in body:
            raise SystemExit(f"cannot place an equation reference: {old!r}")
        body = body.replace(old, new, 1)
    return body


ARMS_BODY_MODEL = ARMS_BODY
TISSUE_BODY_MODEL = with_equations(
    TISSUE_BODY, ("at that site, on a logarithmic axis", "at that site (Eq. (11)), on a logarithmic axis"),
)
CLUSTER_BODY_MODEL = CLUSTER_BODY + " Radii are computed by Eq. (39)."
DOSE_BODY_MODEL = with_equations(
    DOSE_BODY,
    ("exponent 2.65", "exponent 2.65 (Eq. (43))"),
    ("target effect sizes", "target effect sizes (Eq. (44))"),
)

#: (locator, old number, bold head, description); locator keys REDRAWN.

PAGES_MODEL = [
    (
        "Gate Calibration",
        BASE,
        [
            (
                None,
                "top summary chart, “Gate interaction by timepoint” "
                "(currently uncaptioned)",
                "—",
                "Figure 1. Gate interaction estimate at each measurement time.",
                "Bars give the interaction term of the probit-additive gate model at "
                "6, 9 and 24 h, with standard-error whiskers and the estimate printed "
                "at each bar: +0.284 ± 0.240, +1.135 ± 0.350 and −0.011 ± 0.157. The "
                "vertical axis is the interaction term in probit units, and zero on it "
                "is exact multiplicative behaviour.",
            ),
            (
                "fig1_circuit",
                "circuit schematic under “Circuit and measured inputs”",
                "Figure 1",
                "Figure 2. The two-input AND gate.",
                "Hypoxia (Input 1) drives LuxI from pPepT, and LuxI makes the diffusible "
                "AHL that enters the integration step as Input A; lactate (Input 2) drives "
                "LuxR from the native lldPRD operon promoter, entering as Input B. The two "
                "together form the LuxR–AHL complex, which opens pLux on the effector, and "
                "the output is GSDMD-N and pyroptosis. Arrows are transcription or "
                "diffusion; the chassis drawn throughout is E. coli Nissle 1917.",
            ),
        ],
    ),
    (
        "Growth & SsrA",
        BASE + "growth-ssra/",
        [
            (
                None,
                "top summary chart, “SsrA biomass–potency decision” "
                "(currently uncaptioned)",
                "—",
                "Figure 3. Measured potency ratios against the keep-tag threshold.",
                "Bars give the untagged-over-tagged potency ratio in the three same-dose "
                "co-culture comparisons, printed at each bar: 0.888 at 6 OD, 1.062 at 8 OD "
                "and 1.414 at 10 OD. The horizontal axis is that ratio on a linear scale, "
                "and the marked line at 1.710 is the threshold of Eq. (23), the reciprocal "
                "of the measured untagged-to-tagged biomass ratio 0.585.",
            ),
        ],
    ),
    (
        "Safety",
        BASE + "safety/",
        [
            (
                "fig3_1",
                "first figure, “The tissue axis, with the gut lumen in it”",
                "Figure 2",
                f"Figure 4. {TISSUE_TITLE}",
                TISSUE_BODY_MODEL,
            ),
            (
                "fig3_3",
                "second figure, “Each designed arm, at each site”",
                "Figure 3",
                f"Figure 5. {ARMS_TITLE}",
                ARMS_BODY_MODEL,
            ),
            (
                "fig3_5",
                "third figure, “What decides the bottleneck margin” / "
                "“The driver set swaps between sites”",
                "Figure 4",
                "Figure 6. Sobol indices for the bottleneck margin and for the "
                "colonic-mucosa margin.",
                "Left: first-order (circles) and total-order (squares) indices for nine "
                "parameters, computed on log10 of the tumour-over-site ratio so that the "
                "multiplicative model becomes additive (Eq. (28)), under Saltelli sampling "
                "of the declared ranges; the grey segment is the gap between the two "
                "markers, and the annotation gives S_T = 3.4 × S_1 for the quorum Hill "
                "coefficient. Right: the same total-order index at "
                "the colonic mucosa (blue) against the bottleneck site (orange), with "
                "native repression and luminal EcN density labelled absent from the "
                "mucosa model.",
            ),
        ],
    ),
    (
        "Spatial Modeling",
        BASE + "spatial/",
        [
            (
                "fig4_4",
                "the figure, “What it takes for a cluster to switch on”",
                "Figure 5",
                f"Figure 7. {CLUSTER_TITLE}",
                CLUSTER_BODY_MODEL,
            ),
        ],
    ),
    (
        "Dose & Efficacy",
        BASE + "efficacy/",
        [
            (
                "fig4_6",
                "first figure, “Killing goes as roughly the cube of dose” / "
                "“Reaching a micro-lesion spends the safety margin”",
                "Figure 6",
                f"Figure 8. {DOSE_TITLE}",
                DOSE_BODY_MODEL,
            ),
            (
                "fig6_immune",
                "second figure, “Distant lesion outcome vs immune pressure” / "
                "“Feasibility boundary”",
                "Figure 7",
                "Figure 9. Equilibria against immune pressure, and the feasibility "
                "boundary at εG = 1.",
                "Left: steady states of Eq. (51) at h = 0.20, the escape burden (blue) and "
                "the largest burden still cleared (orange) as fractions of capacity, against "
                "immune pressure Ψ. Dashed verticals at Ψ = 1 and Ψ_crit = 1.80 bound the "
                "shaded region labelled bistable, and are labelled eradication possible and "
                "eradication guaranteed; the region to their right is labelled no escape "
                "state. Right: the εG = 1 boundary (Eq. (52)) on logarithmic axes of cascade "
                "gain G and immune permissiveness ε; the grey region below it is labelled "
                "infeasible at any pyroptotic flux, and the shaded horizontal band marks the "
                "MSS/pMMR range. Neither G nor ε is measured for this system.",
            ),
        ],
    ),
    (
        "Validation",
        BASE + "validation/",
        [
            (
                None,
                "top summary chart, “Reported internal holdouts” (currently uncaptioned)",
                "—",
                "Figure 10. Held-out predictions tested and passed, by test.",
                "Paired bars give, for each of the five internal tests, the number of "
                "held-out predictions or refits tested and the number that passed, with the "
                "count printed at each pair: 6/6 for the dose–kill holdout, 4/4 for the gate "
                "at 24 h, 0/4 for the gate at 9 h, 8/8 for the 24 h capacity forecast and "
                "6/6 for the per-construct exponent refit. The horizontal axis is the number "
                "of held-out predictions or refits.",
            ),
        ],
    ),
    (
        "Parameters & Sources",
        BASE + "parameters/",
        [],
    ),
]

#: Engineering.docx -- built from ENGINEERING_DRAFT.md, figures numbered per
#: document. Figures 2-4 are the Model module's figures reused.
PAGES_ENG = [
    (
        "Engineering.docx（全篇一套图号）",
        "model_v2/Engineering.docx ← ENGINEERING_DRAFT.md",
        [
            (
                "fig2_2",
                "Test (v1) 下，outputs/figures/video/fig2_2_gate_holdout.png",
                "Figure 1（号不变）",
                f"Figure 1. {GATE_TITLE}",
                GATE_BODY,
            ),
            (
                "fig3_3",
                "Test (v2) 下，fig3_3_arm_direction.png ——与 Model Figure 5 同一张图",
                "Figure 2（号不变）",
                f"Figure 2. {ARMS_TITLE}",
                ARMS_BODY,
            ),
            (
                "fig4_4",
                "Learn 前，fig4_4_cluster.png ——与 Model Figure 7 同一张图",
                "Figure 3（号不变）",
                f"Figure 3. {CLUSTER_TITLE}",
                CLUSTER_BODY,
            ),
            (
                "fig4_6",
                "Test 下，fig4_6_dose_requirement.png ——与 Model Figure 8、"
                "Description Figure 3 同一张图",
                "Figure 4（号不变）",
                f"Figure 4. {DOSE_TITLE}",
                DOSE_BODY,
            ),
        ],
    ),
]

#: The §1.5 insert for the wet lab's Description page. Its figure numbers
#: continue their page, which already carries one schematic as Figure 1.
PAGES_DESC = [
    (
        "Description_Modeling_Insert.docx（§1.5，接湿实验组那页的图号）",
        "model_v2/Description_Modeling_Insert.docx ← DESCRIPTION_DRAFT.md",
        [
            (
                "fig3_1",
                "fig3_1_tissue_axis.png ——与 Model Figure 4 同一张图",
                "Figure 2（号不变）",
                f"Figure 2. {TISSUE_TITLE}",
                TISSUE_BODY,
            ),
            (
                "fig4_6",
                "fig4_6_dose_requirement.png ——与 Model Figure 8、Engineering Figure 4 同一张图",
                "Figure 3（号不变）",
                f"Figure 3. {DOSE_TITLE}",
                DOSE_BODY,
            ),
        ],
    ),
]

MODULES = [
    ("一、Model 模块（wiki 七页）", PAGES_MODEL,
     "新图（已重出，需上传替换 wiki 上的旧图）："),
    ("二、Engineering 模块", PAGES_ENG,
     "新图（已重出，Engineering.docx 已重建，嵌的就是这张）："),
    ("三、Description §1.5 建模插入段", PAGES_DESC,
     "新图（已重出，Description_Modeling_Insert.docx 已重建，嵌的就是这张）："),
]

#: (figure file, where it appears, what was checked)
DUPLICATES = [
    (
        "fig3_1_tissue_axis.png",
        "Model Figure 4（Safety 页）｜Description Figure 2",
        "两处图注同文，只有 Model 那条多一个 (Eq. (11))；Description 那条原来缺"
        "“oxygen sensor constant at 0.49 % O₂”，已补齐。嵌在 "
        "Description_Modeling_Insert.docx 里的图与新图逐像素一致。",
    ),
    (
        "fig3_3_arm_direction.png",
        "Model Figure 5（Safety 页）｜Engineering Figure 2",
        "以 Engineering 那条为准统一：原 Model 图注少了“anti-selective”带与"
        "“native lldPRD repression is not included”，原 Engineering 图注少了两条臂的参数，"
        "现在都写进同一条。Engineering.docx 里原先嵌的是旧图，已重建换成新图。",
    ),
    (
        "fig4_4_cluster.png",
        "Model Figure 7（Spatial 页）｜Engineering Figure 3",
        "统一为同一条，Model 那条末尾多一句 Eq. (39)。原 Engineering 图注写的"
        "“the only cluster plotted that reaches the threshold”是读图结论，换成标注原话。"
        "Engineering.docx 已重建换成新图。",
    ),
    (
        "fig4_6_dose_requirement.png",
        "Model Figure 8（Dose & Efficacy 页）｜Engineering Figure 4｜Description Figure 3",
        "三处同文，Model 那条多 (Eq. (43))、(Eq. (44))。三条原来都没写新图里的"
        "150 µm 标注点与 21.85× 定价，已补；为守住“图注不超过 130 词”又压掉了几处冗词。"
        "Engineering 与 Description 的 docx 都已重建，嵌的图与新图逐像素一致。",
    ),
]

#: Things this table cannot fix by itself.
ADVICE = [
    "图号三处各编各的，这是对的：Engineering 与 Description 是独立文档，"
    "Model 模块是一份跨七页连排的文档。合稿时只需保证同一张图在各自文档里"
    "被正文以 (Fig. n) 点到一次。",
    "Model 模块的七页正文里一个 (Fig. n) 都没有——Engineering 与 Description "
    "已经做到了（构建会因为漏引而失败），wiki 那七页还得人工补。",
    "Model 模块若采纳本表的连排编号（Fig. 1–10），三张汇总图要一并上号；"
    "改动涉及 wiki 的 alt 文本与正文引用，建议和补 (Fig. n) 一次做完。",
    "矢量图只覆盖本仓库画的 7 张。Model 页的 fig1_circuit（Figure 2）是别处做的位图，"
    "这次只改了图里那个拼错的标签，整张图要矢量仍得找做图的同学导出 SVG；"
    "wiki 上那三张汇总图本来就是 SVG。",
    "图里的字体是 matplotlib 默认的 DejaVu Sans，发表惯例更常用 Arial/Helvetica。"
    "这台机器上有 Liberation Sans（与 Arial 等宽等距）与 Nimbus Sans（Helvetica 克隆），"
    "要换一行 rcParams 的事，但会动到全部 7 张图的外观，没有人拍板之前没动。",
    "SVG 里的文字是以路径输出的（matplotlib 的 svg.fonttype 默认），"
    "好处是任何机器上渲染都与我们看到的一致、不会被替换字体，代价是文字不可选中、"
    "不可在 AI/Inkscape 里直接改字。若合稿时需要可编辑文字，改成 svg.fonttype=\'none\' 重出，"
    "但届时要确保对方机器上装了同一款字体。",
]

#: Done in this round, recorded so the next reader does not re-raise them.
SETTLED = [
    "`DOC_STANDARD.md` §5 的图注条款已改写（原文是“图注说明这张图回答 §0 的第几问”，"
    "与现行“只陈述事实”的尺子相反）：现在写明粗体/不斜体的排法、只陈述图里有的内容、"
    "不写推断、130 词上限、同图同注只许差方程编号、图内不许有推断句、图一律出矢量。",
    "fig1_circuit 图内的 lldPDR 已改成 lldPRD，见上面 Model Figure 2 的新图；"
    "wiki 上那张要一起换掉。",
]


def style_run(run, *, size=10.5, bold=False, italic=False, color=INK):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = LATIN
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    fonts.set(qn("w:ascii"), LATIN)
    fonts.set(qn("w:hAnsi"), LATIN)
    fonts.set(qn("w:eastAsia"), HAN)
    return run


def add_para(doc, *, space_before=0, space_after=6, line=1.25, left=0.0):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    pf.left_indent = Cm(left)
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p


INTRO = (
    "覆盖 Model 模块（wiki 七页）、Engineering、Description §1.5 三处的全部图片。"
    "每张图一条图注：Figure n. 与标题句粗体不斜体，其后说明不粗不斜，"
    "只陈述图里有的内容（坐标轴、标度、系列与颜色、色带、参考线、图上标出的数值、"
    "固定住的参数），不写推断。三处共用的 4 张图用同一条图注，"
    "唯一允许的差别是方程编号（只有 Model 页给方程编号）。"
    "六张图片内部原本带推断句或失效引用，已重出，新图附在对应图注上方。"
    "本仓库画的每一张图现在都同时输出 SVG 与 PDF 矢量图，"
    "三份 Word 里嵌的是“PNG + SVG”两层，Word 2016 以上与 WPS 按矢量渲染，"
    "旧版本退回 300 dpi 的 PNG。"
)


def _data_uri(path: Path) -> str:
    """The figure inlined, vector if there is a vector of it."""
    svg = VECTORS / f"{path.stem}.svg"
    source, mime = (svg, "image/svg+xml") if svg.exists() else (path, "image/png")
    payload = base64.b64encode(source.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def write_markdown(intro: str) -> None:
    """The same table as Markdown, so it reads without Word.

    Figures are inlined as data URIs -- vector where a vector exists -- so one
    file is the whole thing. GitHub's web view strips inline images; the file
    path under each figure is there for that case.
    """
    out = [f"# {TITLE}", "", intro, "",
           "（本文件与 `Model_Figure_Legends.docx` 同源同内容，由 "
           "`build_figure_legends_docx.py` 一次写出两份。重出的图以 SVG 内嵌在本文件里，"
           "单独一个 .md 就能看图，不依赖阅读器的 Word SVG 支持；GitHub 网页版会过滤"
           "内嵌图片，那里看图请用下面给出的文件路径。）", ""]

    for module_title, pages, redrawn_prefix in MODULES:
        out += [f"## {module_title}", ""]
        for title, url, figures in pages:
            out += [f"### {title}", "", f"`{url}`", ""]
            if not figures:
                out += ["本页无图片。", ""]
                continue
            for key, locator, old, head, body in figures:
                out += [f"**{locator}**　｜　原编号：{old}", ""]
                if key in REDRAWN:
                    out += [REDRAWN_PREFIX.get(key, redrawn_prefix) + REDRAWN_NOTE[key], "",
                            f"![{REDRAWN[key].stem}]({_data_uri(REDRAWN[key])})", ""]
                if key in VECTOR_STEMS:
                    out += [f"矢量图 `outputs/figures/vector/{VECTOR_STEMS[key]}.svg`"
                            "（另有同名 `.pdf`）", ""]
                out += [f"**{head}** {body}", ""]

    out += ["## 四、三个模块之间重复的图", "",
            "共 4 张图被两处或三处共用。图片本身已核对为同一版本（与本次重出的新图"
            "逐像素一致），图注已统一。", ""]
    for figure, where, checked in DUPLICATES:
        out += [f"**{figure}**", "", where, "", checked, ""]

    out += ["## 五、修改意见（本表之外要人工做的）", ""]
    out += [f"- {item}" for item in ADVICE]
    out += ["", "### 本轮已处理", ""]
    out += [f"- {item}" for item in SETTLED]
    out += [""]

    OUT_MD.write_text("\n".join(out), encoding="utf-8")


def main() -> None:
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2.2)
        section.bottom_margin = Cm(2.2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    normal = doc.styles["Normal"]
    normal.font.name = LATIN
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), HAN)

    p = add_para(doc, space_after=2)
    style_run(p.add_run(TITLE), size=15, bold=True)
    p = add_para(doc, space_after=14)
    style_run(p.add_run(INTRO), size=9.5, color=GREY)

    for module_title, pages, redrawn_prefix in MODULES:
        p = add_para(doc, space_before=16, space_after=6)
        style_run(p.add_run(module_title), size=13, bold=True, color=ACCENT)

        for title, url, figures in pages:
            p = add_para(doc, space_before=8, space_after=1)
            style_run(p.add_run(title), size=12, bold=True)
            p = add_para(doc, space_after=8)
            style_run(p.add_run(url), size=9, color=GREY)

            if not figures:
                p = add_para(doc, space_after=10)
                style_run(p.add_run("本页无图片。"), size=9.5, color=GREY)
                continue

            for key, locator, old, head, body in figures:
                p = add_para(doc, space_after=2)
                style_run(p.add_run(f"{locator}　｜　原编号：{old}"), size=9, color=GREY)
                if key in REDRAWN:
                    p = add_para(doc, space_after=4, line=1.3)
                    style_run(p.add_run(REDRAWN_PREFIX.get(key, redrawn_prefix)
                                        + REDRAWN_NOTE[key]),
                              size=9, color=ACCENT)
                    p = add_para(doc, space_after=4)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run().add_picture(str(REDRAWN[key]), width=TEXT_WIDTH)
                if key in VECTOR_STEMS:
                    p = add_para(doc, space_after=4)
                    style_run(
                        p.add_run(
                            "矢量图：outputs/figures/vector/"
                            f"{VECTOR_STEMS[key]}.svg（另有同名 .pdf）"
                        ),
                        size=9,
                        color=GREY,
                    )
                p = add_para(doc, space_after=12, line=1.3)
                style_run(p.add_run(head + " "), size=10, bold=True)
                style_run(p.add_run(body), size=10)

    doc.add_page_break()
    p = add_para(doc, space_after=6)
    style_run(p.add_run("四、三个模块之间重复的图"), size=13, bold=True, color=ACCENT)
    p = add_para(doc, space_after=10)
    style_run(
        p.add_run(
            "共 4 张图被两处或三处共用。图片本身已核对为同一版本（与本次重出的新图"
            "逐像素一致），图注已统一。"
        ),
        size=9.5,
        color=GREY,
    )
    for figure, where, checked in DUPLICATES:
        p = add_para(doc, space_after=1)
        style_run(p.add_run(figure), size=10, bold=True)
        p = add_para(doc, space_after=2)
        style_run(p.add_run(where), size=9, color=GREY)
        p = add_para(doc, space_after=10, line=1.3)
        style_run(p.add_run(checked), size=9.5)

    p = add_para(doc, space_before=14, space_after=6)
    style_run(p.add_run("五、修改意见（本表之外要人工做的）"), size=13, bold=True,
              color=ACCENT)
    for item in ADVICE:
        p = add_para(doc, space_after=6, line=1.3, left=0.6)
        style_run(p.add_run("· " + item), size=9.5)

    p = add_para(doc, space_before=12, space_after=4)
    style_run(p.add_run("本轮已处理"), size=11, bold=True)
    for item in SETTLED:
        p = add_para(doc, space_after=6, line=1.3, left=0.6)
        style_run(p.add_run("· " + item), size=9.5, color=GREY)

    doc.save(OUT)
    attached = attach_svg(OUT, vector_pairs(ROOT / "outputs" / "figures"))
    write_markdown(INTRO)
    print(f"wrote {OUT.relative_to(ROOT)} and {OUT_MD.name} "
          f"(vector: {', '.join(attached) or 'none'})")


if __name__ == "__main__":
    main()
