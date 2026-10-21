# BBa_26FA7L94 零件页 — 建模组可提交材料

> 目标奖项：**Best New Composite Part**（General Bio Engineering，选报制）
> 零件页：<https://registry.igem.org/parts/bba-26fa7l94>
> 本文件 2026-10-21 立。英文段落可直接粘到 Registry 的 Documentation 分节；
> 中文是给合稿会的说明，**不要粘**。

---

## 0. 评委到底按什么打分

官方 Special Awards 页（competition.igem.org/judging/awards/special）对
**Best New Composite Part** 给的是四条 ballot question，1–6 分制：

1. Registry 上的文档比得上 `BBa_25LG0OCK` / `BBa_25IWB2F9` / `BBa_25LK9WHI` 吗？
2. 团队是否证明了零件按预期工作？—— **"modeling data can be acceptable"**
3. 对社区有用吗？
4. 这个 composite part 被表征得有多好？—— **"experimentally measured or modeled"**

两条里明写建模可以算证据。**第 4 条是建模组的主战场**，第 3 条是我们最有东西可给
的一条（§2 D 节）。

另外两点格式要求：

- Standard URL 一栏是 **None，评委只看 Registry 零件页本身**。写在 wiki Model 页上的
  东西**不计入这个奖**。2025 Judge Handbook：*"All part-related documentation must be
  on the iGEM Registry on a Part's respective part page."* 所以建模材料必须**在零件页
  上重述一遍**，不能只放链接。
- 这是**选报**奖（每队最多选 3 个额外奖项进 Gold 评审，两张清单各至少 1 个）。
  判断题：要不要用掉一个额外名额在这上面 —— 见 §5。

### 对标件长什么样

`BBa_25LG0OCK`（XJTLU-Science-China 2025，去年的获奖对标件）的 Documentation 有
**7 个分节**：Design ×1、Experiment ×2、Characterisation ×3、Application ×1。

我们现在有 **5 个分节**：Design / Experiment / Characterisation / Application /
Discussion，各 1 个。**Characterisation 只有 1 节，而对标件有 3 节** —— 这正好是
建模能补的地方，也正好对上第 4 条 ballot question。

> 注：对标件**没有**建模分节，但 Registry 的分节类型里**有一个专门的
> `Dry-lab modelling`（optional）**：
>
> > *Processes used to model it in silico.*
> > **Useful to include:** Versions of software and libraries used, derivations of
> > equations, and GitHub or GitLab links.
>
> 所以建模材料分两种挂法，**不要混**：
> - **结果**（倍数、阈值、预测）→ 挂 `Characterisation`，吃第 4 条 ballot。
> - **方法与可复现性**（软件版本、方程推导、代码仓库）→ 挂 `Dry-lab modelling`，
>   见 §2 E 节。这一节是**对标件完全没有**的，填满就是净加分。

---

## 1. 范围判断：哪些模块属于这一页

这个 composite part 是 **传感 + 逻辑层**，到 `pLux` 为止，**不含 GSDMD-N-SsrA**
（看页面 Construct：`K1123000→B0034→C0061→B0015` + `K822000→B0034→C0062→B0015`
+ `R0062`）。

| 模块 | 内容 | 放这一页？ |
|---|---|---|
| — | 软件版本 / 方程推导 / 代码仓库 | ✅ **E 节，`Dry-lab modelling` 专用** |
| 2.2 | AND 门是不是乘性的（实测标定） | ✅ **核心** — 对第 2 条 ballot |
| VALIDATION | 留出法外样本预测 | ✅ **核心** — 对第 4 条 ballot |
| 3.1 | 组织轴：各位点门输出倍数 | ✅ 传递函数 |
| 3.2 | 178 µm 几何底线 | ✅ 零参数硬指标 |
| 3.3 | 结肠腔反向选择 + 设计警告 | ✅ **对社区最有用的一节** |
| 3.5 | Sobol：余量方差由谁支配 | ✅ 压缩成两句 |
| 4.4 | 群感是体积积分器不是双稳开关 | ✅ 这是对本零件的表征 |
| 2.3 | 生长层 | ❌ 底层前提，不是本零件的性质 |
| 3.4 | SsrA 标签 | ❌ 效应蛋白，不在本零件里 |
| 4.3/4.5 | 瘤内空间覆盖、给药方案 | ❌ 同上 |
| 4.6 | 反推有效剂量 | ❌ 同上 |
| 6 | 焦亡–免疫级联 | ❌ 同上 |

**不要把 Model 页整体搬过来。** 第 4 条问的是"**这个** composite part 表征得多好"，
掺进效应蛋白和剂量的内容只会稀释。后五个模块属于 GSDMD 零件页和 wiki Model 页。

---

## 2. 可直接粘的英文分节

### A 节 — 建议 tag：**Characterisation**
**标题：** `Model-Based Characterisation: the Gate Is Multiplicative at Endpoint`

> This composite part is an AND gate on two environmental inputs. We tested that
> claim directly, rather than assuming it, against the 2 × 2 factorial
> fluorescence dataset this cycle's wet lab produced (391 measurements).
>
> Read as raw intensity, the double-input corner reaches only 226.6-fold over the
> fully-off corner, against 2768-fold expected from the product of the two
> single-input responses. That 12.2-fold shortfall looks like genuine
> sub-multiplicative behaviour, and it is not: two of the lactate corners sit at
> 82.9 % and 97.9 % of the readout's dynamic range. A probit (log-normal)
> inversion onto the latent expression scale removes the shortfall completely.
>
> On the latent scale, the interaction term at 24 h is
>
> **I = −0.011 ± 0.157** — zero within error.
>
> This is the one result here that depends on no unmeasured parameter: the
> inversion's width σ cancels out of the interaction test algebraically. Within
> each input the single-input responses are also internally consistent to better
> than 1 %. **At 24 h the part behaves as an AND gate.**
>
> At 9 h the same part is significantly *super*-multiplicative:
> **I = +1.135 ± 0.350** (t = 3.24, 8 d.f., p ≈ 0.01). The multiplicative
> description is therefore an **endpoint** property. Teams reusing this part
> should not quote mid-course on/off ratios from it, and we do not quote any.
>
> **Caveat we ask reusers to respect.** The single-input fold-changes recovered by
> the inversion (hypoxia ≈ 17.4-fold, lactate ≈ 642-fold) depend exponentially on
> σ, and swing over three orders of magnitude across a plausible σ range (lactate
> 12.9-fold to 27 660-fold). We report them as **σ-conditional**, not as
> measurements. Turning them into measurements needs no new experiment — only the
> single-cell fluorescence distribution, which already exists in the raw flow
> cytometry files.

### B 节 — 建议 tag：**Characterisation**
**标题：** `Out-of-Sample Validation of the Gate Model (Hold-Out)`

> A model fitted to all of the data cannot be wrong about any of it. We therefore
> refitted with parts of the dataset withheld and predicted the withheld values:
> **28 hold-out predictions across four protocols, 24 passing and 4 failing by
> design** as a discrimination check.
>
> The test that bears on this part directly is leave-one-corner-out on the gate's
> four input corners at 24 h. **All four corners are predicted from the other
> three; worst-case ratio 1.022-fold, and the fully-on corner is predicted to
> within 0.05 percentage points.** This upgrades the AND claim from a fit to an
> out-of-sample prediction.
>
> The same protocol run at 9 h fails 4 out of 4 (worst 4.447-fold). That is the
> correct outcome and the reason we trust the 24 h pass: the 9 h interaction is
> real, and the protocol rejects it rather than waving it through.
>
> **Scope, stated plainly.** This is internal cross-validation on a single
> workbook. It is not validation against an independent dataset, and it cannot
> detect a systematic error common to the whole workbook.

### C 节 — 建议 tag：**Characterisation**
**标题：** `Predicted Transfer Function Across Tissue Environments and Lesion Sizes`

> With the endpoint gate model calibrated and validated above, we evaluated the
> part's expected output across the anatomical sites it would actually meet, and
> across lesion size.
>
> **Site selectivity.** Gate output factorises into a lactate arm, a hypoxia arm,
> a quorum arm and native promoter repression. Against the tumour site, the
> tightest normal site is the **colonic mucosa at 21.85-fold below tumour** — not
> the tissue adjacent to a tumour, which is where we had expected the bottleneck.
> Whether that margin exists at all depends on native repression: without it the
> bottleneck becomes the dysbiotic colonic lumen at **0.231-fold**, i.e. the gate
> inverts and prefers the lumen. See the Design section for what follows from
> that.
>
> **A parameter-free size floor.** A lesion of radius below **178 µm** contains no
> hypoxic volume at all, so the hypoxia arm cannot leave its basal level for
> *any* parameter set. This bound is pure geometry and uses no fitted parameter —
> the hardest single number we can offer a reuser.
>
> **The quorum arm is a volume integrator, not a switch.** Clusters of small
> lesions sharing one AHL pool do cooperate (1.3–3.9-fold at realistic ≥1 mm
> spacing), but no realistic cluster crosses the single-lesion threshold: 125
> lesions at realistic spacing reach only a 303 µm equivalent, and the first ON
> cluster needs **8³ = 512 tangent lesions spanning 2.1 mm** — by then it is a
> tumour, which the single-lesion model already calls ON. Dispersing a given
> burden is always weaker than aggregating it (0.84–0.95-fold). Practically:
> **this receiver shows no hysteresis and no sharp threshold.** Teams expecting
> LuxI/LuxR bistability from this architecture should not.
>
> **Where the remaining uncertainty sits.** Global (Sobol) sensitivity over the
> declared parameter ranges puts **81 % of the bottleneck's variance on two
> parameters**: the native repression fold (S_T = 0.457) and the lumen bacterial
> density ratio (0.355). The safety margin holds across **73.9 % of the declared
> parameter space**, and every failure in the remaining 26.1 % is a lumen
> failure, never a tissue-site failure.

### D 节 — 建议 tag：**Design**
**标题：** `Reuse Guidance, and One Design Warning`

> Anyone reusing this part should read this section before changing the lactate
> arm.
>
> **Neither designed input arm can keep this part off in the colonic lumen.** The
> normal colon lumen is simultaneously hypoxic and lactate-rich, so both designed
> inputs read it as target-like. This is structural, not parametric — it follows
> from the gate's form and holds for every value of every EC50, Hill coefficient
> and basal level. Under dysbiosis, where luminal lactate can reach 12.5 times
> the intratumoural concentration, the gate **actively selects against** the
> intended site.
>
> **The lactate arm cannot be fixed by tuning.** Its discrimination has an
> analytic ceiling set by the concentration ratio and the basal level, *not* by
> EC50: for the wild-type promoter the ceiling is 1/b_L = **7-fold**. Reaching
> 10-fold discrimination in the faecal scenario would require a Hill coefficient
> n_L ≥ 4.9, and LldR is non-cooperative. That number is not available at any
> EC50.
>
> **What does keep it off is the native promoter's own repression.** The lldPRD
> promoter carries native anaerobic and glucose repression. The gate needs only
> about **11.5-fold** of it, and each of the two native repressions is
> individually described as strong — so the margin is comfortable. AHL washout
> contributes only 1.5–2.9-fold (colonic transit is slow) and is secondary.
>
> **⚠️ Design warning: do not substitute a de-repressed lldPRD variant.** In a
> tumour-facing assay the native promoter looks like a defect — it under-performs
> under hypoxia, and removing the repression is an obvious-looking improvement.
> It is in fact the only mechanism keeping this part off in the gut lumen, and
> removing it flips the sign of the part's selectivity rather than widening an
> interval.
>
> **The one experiment that would settle it.** This is the single point of
> failure in our safety argument, and one plate closes it: lldPRD-only reporter,
> 0 % versus 1 % O₂. We flag it here rather than claiming it is resolved.

### E 节 — tag：**Dry-lab modelling**
**标题：** `In Silico Methods, Equations and Code`

> 这一节是**照着 Registry 那条提示逐项填的**：software/library versions ·
> derivations of equations · GitHub or GitLab link。下面每个数字都是 2026-10-21
> 实测的，不是估的。

> **Software.** All modelling for this part was done in **Python 3.13.5** with
> pinned versions: `numpy 2.5.3`, `scipy 1.18.1`, `pandas 3.0.6`,
> `matplotlib 3.11.2`, `openpyxl 3.1.5`, `SALib 1.6.0`, `pytest 9.1.1`. No
> commercial or closed-source tool is used anywhere in the pipeline, and no step
> requires a GUI — the whole analysis is one command.
>
> **Equations and their derivations.** Every equation in the project is derived
> and numbered once, in a single table (`EQUATIONS.md`, **70 numbered
> equations**, format `(chapter.section-index)`). Each entry carries the
> equation, its symbol definitions, an evidence grade, and the file and function
> that evaluates it — so any number on this page can be traced to the code that
> produced it. Module documents cite equation numbers and never re-derive them.
> The equations behind this part specifically are §2.2 (probit inversion and the
> multiplicativity criterion), §3.1 (the factorised tissue transfer function),
> §3.2 (the hypoxic-volume geometry giving the 178 µm floor), §3.3 (the
> parameter-free lumen inversion result), §3.5 (Sobol decomposition) and §4.4
> (the linear AHL superposition, closed-form because LuxI is not under pLux).
>
> **Parameters are not inline numbers.** All 36 parameters live in a single CSV
> with value, unit, range, source and evidence grade; `src/parameters.py` checks
> that table row-by-row against the constants actually used in the code, and the
> test suite fails on any drift. Tissue environments are a second table (7 sites,
> each with O₂ and lactate values, upper and lower bounds, literature source and
> evidence grade). This is why we can state which numbers are measured, which are
> literature priors, and which are scenario assumptions.
>
> **Code and tests.** ~6 400 lines of analysis code across 20 modules, with
> ~4 100 lines of tests: **390 tests pass, 2 skipped, in 3.1 s.** The tests are
> not smoke tests — they pin the audited value of each reported number, assert
> the closed-form solutions against independent numerical integration (agreement
> to 1 × 10⁻⁴ for the spatial model), and encode the claims we are *not* allowed
> to make as executable assertions (for example `misfit_propagates() -> False`).
>
> **Reproducing everything on this page:**
> ```bash
> pip install -r requirements.txt
> python -m pytest tests/ -q      # 390 passed, 2 skipped
> python main.py                  # regenerates every figure and table
> ```
>
> **Repository:** `<GitLab URL — 见 §4 第 2 条，发布前必须填上>`

> ⚠️ 如果合稿会觉得分节太多，**可以把 A 节的方法段（probit 反演怎么做的）并进 E 节**,
> A 节只留交互项结果。但 A 节的结论必须留在 `Characterisation`——第 4 条 ballot
> 看的是那里。

---

## 3. 配图

`outputs/figures/wiki_upload/` 里有 5 张 SVG + `fig1_circuit.png`（**fig1 没有 SVG**，
要么补生成，要么用 `outputs/figures/vector/` 下的版本），图注在
`Model_Figure_Legends.docx`。Registry 的分节正文支持图片上传，走 SVG。
**注意：所有图内的推断句已于 2026-10-21 从 `src/plots.py` 拿掉，必须用重新生成的新图**
（旧图还带 "Bottleneck moves from…" 这类句子）。

| 图 | 用在 | 说明 |
|---|---|---|
| `fig1_circuit` | A 节开头 | 两条传感臂汇成 AND 门 |
| `fig3_1_tissue_axis` | C 节「Site selectivity」 | 与 wiki Model 页 Figure 4 **同图**，图注必须一字不差 |
| `fig3_3_arm_direction` | D 节开头 | 两条臂在肠腔反向 |
| `fig3_5_sobol_drivers` | C 节末 | 只给比值，不给 "$S_T$ three times $S_1$" |
| `fig4_4_cluster` | C 节「volume integrator」 | 图内 "ON band (9.23)" 已改成 "ON band (1000 µm)" |

`fig4_6_dose_requirement` 与 `fig6_immune_feasibility` **不要放这一页**（见 §1）。

---

## 4. 零件号的事，以及一件必须做的事

### 4.1 零件清单的出入 —— 已决定：以湿实验组已上传的为准

页面上有两处对不齐（**Source** 列 `BBa_M36021`、**Construct** 图画 `BBa_K822000`；
低氧臂页面写 `BBa_K1123000` 而建模用 `pPepT`）。**2026-10-21 决定不再纠结**，零件号
一律以湿实验组已经上传到 Registry 的为准，建模组不提改动要求。

**这不影响上面任何一节**，原因是：

1. **A–E 五节一个 BBa 号都没引。** 低氧臂一律写 `the hypoxia-responsive arm` /
   `FNR-family oxygen regulation`，不点启动子名（与 `DESCRIPTION_DRAFT.md` 同一
   策略）；模型的 $K_{O_2}=0.49\%$ 取自 Højberg et al. *AEM* 1999，是 FNR 家族实测
   值，`pPepT` 和 `K1123000` 都在这个家族里，怎么定都不打架。
2. **D 节只说 `lldPRD`，那是天然操纵子的名字，不是零件号。** `BBa_M36021` 是
   `BBa_K822000` 的 332 bp 衍生件，**两个候选都是 lldPRD 启动子**，而"厌氧 + 葡萄糖
   抑制"是这段启动子区本身的性质。若实际用的是更完整的 `K822000`，天然抑制只会
   **不少于**我们建模时假设的量 —— 结论方向不变，余量只会更宽。

所以 D 节那句设计警告照原样粘即可。**唯一要守的纪律：粘的时候不要手痒把 BBa 号加
回去。**

### 4.2 代码根本没进版本控制

`model_v2/` 下**只有 `.gitignore`，没有 `.git`** —— 整个建模仓库从来没初始化过。
而 `Dry-lab modelling` 那条提示明写要 **GitHub or GitLab links**，E 节结尾那行现在
是空的。

要做的事，按顺序：

1. `git init` + 首次提交。**现有 `.gitignore` 只排了 `.venv/`、`__pycache__/`、
   `*.pyc`、`.pytest_cache/`，没有排 `data/`** —— 也就是说照现状一提交，
   `data/全部实验数据.xlsx`（全队这一轮唯一的原始数据）就会一起公开。
   **这个要先问队里**：公开它对第 3 条 ballot 是加分（可复现），但那是湿实验组的
   数据，不是建模组能单方面决定的。
2. 推到 **iGEM 自己的 GitLab**（`gitlab.igem.org`，每队有仓库）。用 iGEM GitLab 而
   不是 GitHub 的好处：评委点得进去、不依赖个人账号、和 wiki 同源。
3. 补一个 `LICENSE`。零件页本身已经是 **CC BY 4.0**，代码配 MIT 或 Apache-2.0 都行,
   但**必须有**——没 license 的仓库等于"不可复用"，直接打第 3 条 ballot
   （useful to the community）的脸。
4. 把 URL 填回 E 节。

> 这一条不解决，E 节就只能交三分之二。而 E 节恰恰是对标件没有、我们能拿满的一节。

---

## 5. 要不要用掉一个选报名额

**建议：报。** 理由：

- 第 2 条和第 4 条 ballot 明写建模可作证据，而我们在这个零件上**同时**有实测标定
  （A 节）、外样本验证（B 节）、预测性传递函数（C 节）—— 这三件事很少有队伍对
  **同一个** composite part 全部做到。
- 第 3 条（对社区有用）我们有 D 节这个**反直觉的设计警告**。这类"别照着明显的方向
  改"的结论对 Registry 的价值远高于再一条表征曲线，而且它只能靠建模得出。
- 补 3 个 Characterisation 分节后，文档体量与 `BBa_25LG0OCK` 的 7 节相当。

**老版指引提醒**：判断表上这个奖只填**一个**零件号，评委只看第一个。

---

## 6. 不能写的话

- 不写中程（6 h / 9 h）的 on/off 倍数 —— `MODULE_2_2 §7.4`。
- 17.4× / 642× **必须**带 σ-conditional 标注，不能当测量值 —— `MODULE_2_2 §7.3`。
- 不写"独立数据集验证"，只写"内部交叉验证，单一工作簿" —— `MODULE_VALIDATION §7.4`。
- 22–910× 与 14–6891× 是**同一个** $n_Q$ 跨度，**不得并列成两份独立证据**
  —— `MODULE_3_2 §7.3`。
- 不写"再给药无用"（推论是循环的）—— `MODULE_4_3_4_5 §7.4`。本页反正不涉及剂量。
- 不写安全性"已解决"：D 节末尾那块板没做，单点失效仍然开着 —— `MODULE_3_3 §6.1`。
