# Engineering｜工程循环（中英对照审稿版）

> **⚠️ 本对照版已过期（2026-10-20）**
>
> 英文稿已于 2026-10-20 **整体重写**：范围从"全队 Engineering"收窄为
> **建模组 Engineering**，循环从 6 轮改为 7 轮（框架迭代 / AND 门留出 /
> 组织位点 / 多病灶 / 剂量 / 数据层 / 开放项），湿实验的克隆与共培养不再
> 写成我们做的。**下面的中文对应的是旧版英文稿，不要据此审稿。**
>
> 新英文稿：[`ENGINEERING_DRAFT.md`](ENGINEERING_DRAFT.md)。
> 等新结构定稿后再重译；重译后删掉本块，`tests/test_engineering.py`
> 的覆盖检查会自动重新生效。

> **审稿说明（本文件不上线，只供队内审）**
>
> * 上线的是英文稿 [`ENGINEERING_DRAFT.md`](ENGINEERING_DRAFT.md)。
>   **本文件是它的对照版**：英文段落在上，中文译文在下，以 `◆` 开头。
>   审的时候请**对着英文审**，中文只是帮你快速读懂——要改的是英文那一句。
> * 标题用 `英文｜中文` 的形式。纯数字表格只译表头，散文表格另附中文表。
> * **中文稿不参与上线页的构建**，`build_engineering_html.py` 只读英文稿。所以改了
>   英文稿之后，这份中文要手动跟一次；两边数字不一致时**以英文稿和代码为准**。
>   （`tests/test_engineering.py` 会检查这份对照版是否还覆盖英文稿的每个数字、
>   每个段落、每个标题——漏跟会让测试失败。）
> * **想在浏览器里看**：`.venv/bin/python build_bilingual_html.py` →
>   `engineering_bilingual.html`（自包含，图片内嵌，双击即可打开）。中文段会带
>   左侧竖线、浅一号字，和英文区分开。
> * 术语按仓库既有译法：chassis=底盘，degron=降解标签，gut lumen=肠腔，
>   anoxic=厌氧（0% O₂）／hypoxic=低氧，discrimination=判别力，
>   counter-selective=反选择，left-censored=左截断，CPP=细胞穿膜肽。

---

## How we engineered｜我们是怎么做工程迭代的

Our project asks an engineered probiotic — *E. coli* Nissle 1917 — to carry a
pore-forming effector, GSDMD-NT, and to release its activity **in a colorectal
tumour and essentially nowhere else**. Two things make that hard, and both are
engineering problems rather than discovery problems:

◆ 本项目要让一株工程化益生菌——*E. coli* Nissle 1917——携带成孔效应蛋白 GSDMD-NT，
并且**只在结直肠肿瘤里、基本不在别处**释放它的活性。有两件事让这件事很难，而它们
都是**工程问题，不是发现问题**：

1. **The effector is toxic to its own chassis.** A pore-former does not know
   which membrane it is in.
2. **"Tumour" is not a signal.** It has to be decomposed into inputs a cell can
   actually measure, and the combination has to be rare outside a tumour —
   including in the gut lumen, where an orally delivered probiotic spends most
   of its life.

◆ 1. **效应蛋白对自己的底盘有毒。** 成孔蛋白不知道自己正在打穿哪一张膜。
◆ 2. **"肿瘤"不是一个信号。** 它必须被拆成细菌真正测得到的输入，而且这些输入的
组合在肿瘤之外必须罕见——**包括肠腔**，口服递送的益生菌一生中大部分时间待在那里。

We ran six engineering cycles against those two problems. Four closed in the
wet lab, one closed in silico and changed a build decision before we spent money
on it, and one is open — we state its entry condition and the single plate that
would close it, rather than claiming it is finished.

◆ 围绕这两个问题，我们跑了**六轮工程循环**。四轮在湿实验里收口，一轮在计算里收口
并且**在我们花钱之前就改掉了一个构建决定**，还有一轮是开着的——对这一轮我们写清楚
它成立的前提、以及**一块板**就能定案的那个实验，而不是假装它已经做完了。

| # | Cycle | What it decided | Status |
|---|---|---|---|
| 1 | Containing the effector | Keep the `SsrA` degron | ✅ Closed |
| 2 | Making the trigger tumour-specific | Replace constitutive `luxR` drive with a lactate sensor | ✅ Closed |
| 3 | Where else does the gate open? | **Do not** de-repress the lactate sensor | ✅ Closed (in silico) |
| 4 | Delivery vs. selectivity | Drop the `TAT` cell-penetrating peptide | ✅ Closed |
| 5 | How much do we need? | Dose target set; micrometastasis is not a dose problem | ✅ Closed |
| 6 | Anoxia vs. hypoxia at the sensor | Entry condition stated, one plate would close it | ⏳ Open |

◆ 对照表：

| # | 循环 | 定下了什么 | 状态 |
|---|---|---|---|
| 1 | 把效应蛋白关住 | 保留 `SsrA` 降解标签 | ✅ 已收口 |
| 2 | 让触发条件真正指向肿瘤 | 驱动 `luxR` 的组成型启动子换成乳酸传感器 | ✅ 已收口 |
| 3 | 这个门还会在哪里打开？ | **不要**去掉乳酸传感器的抑制 | ✅ 已收口（计算） |
| 4 | 递送 vs. 选择性 | 去掉 `TAT` 细胞穿膜肽 | ✅ 已收口 |
| 5 | 到底需要多大剂量？ | 定下剂量目标；微转移灶不是剂量问题 | ✅ 已收口 |
| 6 | 传感器处：厌氧还是低氧？ | 前提已写明，一块板就能定案 | ⏳ 开放中 |

🖼 **Figure 1.** The final circuit. Hypoxia drives `LuxI` from `pPepT`, producing
AHL; lactate drives `LuxR` from the native `lldPRD` operon promoter
(`BBa_M36021`); only the LuxR–AHL complex opens `pLux`, which drives
`GSDMD-NT-SsrA`. Chassis is *E. coli* Nissle 1917; backbone `pWSK29`.
Two of the elements shown are not in the circuit we first specified: the
`SsrA` degron arrived through Cycle 1, and `BBa_M36021` replaced a constitutive
promoter through Cycle 2.

◆ **图 1.** 最终线路。低氧经 `pPepT` 驱动 `LuxI` 产生 AHL；乳酸经天然 `lldPRD`
操纵子启动子（`BBa_M36021`）驱动 `LuxR`；只有 LuxR–AHL 复合物才能打开 `pLux`，
后者驱动 `GSDMD-NT-SsrA`。底盘是 *E. coli* Nissle 1917，骨架是 `pWSK29`。
图上有**两个元件不在我们最初的设计里**：`SsrA` 降解标签来自循环 1，`BBa_M36021`
在循环 2 里替换掉了一个组成型启动子。

---

## Cycle 1 — The effector kills the factory｜循环 1 — 效应蛋白把工厂杀了

### Design｜设计

Our first circuit put `GSDMD-NT` straight under `pLux`. The predicted failure
mode was immediate and was raised in our own lab before any iGEM construct
existed: a colleague working on a related pore-forming effector found it lysed
the host wall and membrane during normal transcription and translation, killing
the producer **before enough protein accumulated to detect** — no clear soluble
or secreted band on a Western blot. That is a technical deadlock, not a tuning
problem: every improvement to expression makes it worse.

◆ 我们最初的线路直接把 `GSDMD-NT` 挂在 `pLux` 下面。预期的失效模式立刻就出现了，
而且是在任何 iGEM 构建体存在之前、在我们自己实验室里被提出来的：一位做相近成孔
效应蛋白的同学发现，它在正常转录翻译过程中就会裂解宿主的细胞壁和细胞膜，**在目的
蛋白积累到可检测之前就把生产者杀死**——Western blot 上跑不出清晰的可溶或分泌条带。
这是一个**技术死锁，不是调参问题**：任何提高表达的改进都只会让它更糟。

We specified three candidate containment strategies and the engineering
principle each one relies on:

◆ 我们列了三条候选的"关住它"的策略，以及每条各自依赖的工程原理：

| Strategy | Principle | Cost if it fails |
|---|---|---|
| **A** Periplasmic/secreted export (`PelB`) + tumour-specific MMP-2 cleavable linker | Keep the effector *inactive and outside the cytoplasm* until a tumour protease matures it | Precursor matures early → chassis dies anyway |
| **B** C-terminal cell-penetrating peptide (`TAT`) | Keep N-terminal specificity, add active entry into the target cell | CPP is not selective — see Cycle 4 |
| **C** C-terminal `SsrA` degron | Let the chassis' own `ClpXP` protease clear whatever leaks | Degradation also eats the therapeutic output |

◆ 对照表：

| 策略 | 原理 | 失败的代价 |
|---|---|---|
| **A** 周质／分泌表达（`PelB`）+ 肿瘤特异的 MMP-2 可切割连接子 | 让效应蛋白**无活性地待在胞质之外**，直到被肿瘤蛋白酶成熟化 | 前体提前成熟 → 底盘照样死 |
| **B** C 端接细胞穿膜肽（`TAT`） | 保住 N 端特异性，另外加一条主动进入靶细胞的路 | 穿膜肽本身没有选择性——见循环 4 |
| **C** C 端接 `SsrA` 降解标签 | 让底盘自己的 `ClpXP` 蛋白酶去清掉漏出来的那部分 | 降解同时也会吃掉治疗用的产物 |

Strategy C is 11 codons and needs no new protease, no new linker chemistry and
no assumption about tumour MMP-2 levels, so it was the cheapest to test. Its
obvious objection — *a degron will throw away the product you want* — is exactly
what a Test can settle.

◆ 策略 C 只有 11 个密码子，不需要新的蛋白酶、不需要新的连接子化学、也不需要对肿瘤
MMP-2 水平做任何假设，所以**它是最便宜的那个可测项**。而针对它最明显的反对意见
——*降解标签会把你想要的产物一起扔掉*——恰恰是一个 Test 就能了结的问题。

### Build｜构建

`pWSK29` backbone, Golden Gate assembly with `BsaI` (`GGTCTC`) and T4 ligase.
Assembly products were transformed into `DH5α` first for selection, colony PCR,
diagnostic digestion and full-insert sequencing, and only sequence-confirmed
plasmids were moved into `EcN1917` for functional work. We deliberately kept
**plasmid validation and chassis validation as separate stages** so that a
cloning failure could never be misread as a biological result.

◆ `pWSK29` 骨架，用 `BsaI`（`GGTCTC`）+ T4 连接酶做 Golden Gate 组装。组装产物先
转化 `DH5α` 做筛选、菌落 PCR、诊断性酶切和全插入片段测序，**只有测序确认过的质粒**
才导入 `EcN1917` 做功能验证。我们**刻意把"质粒验证"和"底盘验证"分成两个阶段**，
这样一次克隆失败绝不会被误读成一个生物学结果。

The pair that matters for this cycle:

◆ 这一轮真正关键的是下面这一对：

* `pLux → GSDMD-NT-SsrA` (the construct we intend to ship)
* `pLux → GSDMD-NT` (identical plasmid, identical promoter, identical RBS,
  identical ORF — **differing only by the 11-codon `SsrA` tag**)

◆ · `pLux → GSDMD-NT-SsrA`（我们打算最终采用的构建体）
◆ · `pLux → GSDMD-NT`（同一质粒、同一启动子、同一 RBS、同一开放阅读框——
**只差那 11 个密码子的 `SsrA` 标签**）

That pairing was a design choice in the build, and it is what makes the test
interpretable. `SsrA` acts **post-translationally**, so both strains synthesise
the effector at the same rate and differ only in the accumulated pool.
Consequently plasmid burden and metabolic cost of production **cancel between
the two arms**, and we did not need an empty-vector control to attribute a
growth difference to the protein itself.

◆ 这个配对是**构建阶段的一个设计选择**，也正是它让后面的测试可解释。`SsrA` 是
**翻译后**起作用的，所以两株菌合成效应蛋白的速率完全相同，**只有累积池不同**。
于是质粒负担和生产的代谢成本**在两臂之间自动抵消**——我们因此**不需要空载体对照**
就能把生长差异归因到蛋白本身。

### Test｜测试

Growth curves, OD<sub>600</sub>, 0–24 h, n = 3, in a 2 × 2 design: ± 20 mM
lactate (induction) × aerobic / anaerobic background. Biomass retained at 24 h,
compared **within** an oxygen background:

◆ 生长曲线，OD<sub>600</sub>，0–24 h，n = 3，2 × 2 设计：±20 mM 乳酸（诱导）×
有氧／无氧背景。24 h 保留的生物量，**在同一氧背景内**比较：

| 24 h biomass retained on induction | Aerobic | Anaerobic |
|---|---|---|
| **`GSDMD-NT-SsrA`** (shipped construct) | **90.3 %** | **96.2 %** |
| `GSDMD-NT` (untagged) | 47.8 % | 80.9 % |

◆ 表头中文：诱导后 24 h 保留的生物量｜有氧背景｜无氧背景；
行：**`GSDMD-NT-SsrA`（实际采用）** vs `GSDMD-NT`（无标签）。

🖼 **Figure 2.** Growth curves for both constructs across the four conditions,
n = 3, mean ± SD. The 21 % O₂ + lactate panel is the one to look at: the untagged
arm flattens at OD ≈ 1.38 while the tagged arm reaches ≈ 2.36. Retained-biomass
percentages are computed from the plotted wells, not quoted. Note that the
workbook's "anaerobic" background is 1 % O₂ — it contains no 0 % condition
anywhere, which is what Cycle 6 is about.

◆ **图 2.** 两个构建体在四种条件下的生长曲线，n = 3，均值 ± SD。**要看的是
"21 % O₂ + 乳酸"那一格**：无标签那臂在 OD ≈ 1.38 就平了，带标签那臂到了 ≈ 2.36。
图上的保留生物量百分比是**从画出来的这些孔现算的**，不是抄的。注意工作簿里的
"无氧"背景其实是 **1 % O₂**——里面**任何地方都没有 0 % 条件**，这正是循环 6 要讲的事。

### Learn｜学到了什么

**The degron does not cost us the product — it buys us the producer.** Keeping
the tag more than doubles retained biomass under aerobic induction (90.3 % vs
47.8 %). Three further things came out of this cycle that we did not expect:

◆ **降解标签并没有让我们损失产物——它买回了生产者。** 保留标签让有氧诱导下的保留
生物量翻了一倍不止（90.3 % 对 47.8 %）。这一轮还额外得到三件我们没预料到的事：

1. **OD never falls under induction.** Both arms sit at 0.0 % decline in the
   aerobic + lactate condition. The only decline anywhere is in anoxia, and it
   is *larger in the tagged strain* (−7.9 % vs 0.0 %) — i.e. it is anaerobic
   stationary-phase decay, unrelated to the effector. **EcN is a surviving
   producer, not a suicide vector.** We had been asked to model a two-subpopulation
   lysing culture; the data say that model has no referent, so we did not build it.

◆ 1. **诱导条件下 OD 从不下降。** 在"有氧 + 乳酸"条件下两臂的下降幅度都是 0.0 %。
唯一出现下降的地方是低氧，而且**是带标签那株降得更多**（−7.9 % 对 0.0 %）——也就是说
那是**低氧稳定期衰减，与效应蛋白无关**。**EcN 是一个存活的生产者，不是自杀式载体。**
原本有人要求我们建一个"两亚群裂解"的模型；数据说这个模型**没有对应物**，所以我们没建。

2. **A reverse argument strengthens the attribution.** `ClpXP` proteolysis itself
   consumes ATP. The tagged strain pays that extra energetic bill **and still
   grows better**. That rules out "metabolic burden of expression" as the
   explanation for the untagged strain's collapse.

◆ 2. **有一个反向论证进一步加强了归因。** `ClpXP` 降解本身是耗 ATP 的。带标签那株
**多付了这笔能量账，却还长得更好**。这就排除了"表达的代谢负担"这个解释——它解释不了
无标签那株为什么崩掉。

3. **The tag is a selectivity *amplifier*, not just a mop.** `ClpXP` is a finite
   enzyme, so degradation follows Michaelis–Menten kinetics and the effective
   first-order clearance rate $v_\text{max}/(K_m + P)$ **falls as the substrate pool
   grows**. In normal tissue only leak-level substrate exists, `ClpXP` is far
   from saturated and clearance is fast; in a tumour the gate is open, `P ≫ K_m`,
   the protease is swamped and production outruns it. So protein-level
   selectivity *exceeds* promoter-level transcriptional selectivity.

◆ 3. **这个标签是选择性的*放大器*，不只是一块抹布。** `ClpXP` 是一个**有限的酶**，
所以降解遵循米氏动力学，等效的一阶清除速率 $v_\text{max}/(K_m + P)$
**随底物池增大而下降**。在正常组织里只有泄漏级别的底物，`ClpXP` 远未饱和、清除很快；
在肿瘤里门是开的，`P ≫ K_m`，蛋白酶被打满、生产跑赢了降解。于是**蛋白层面的选择性
超过了启动子层面的转录选择性**。

**Honest boundary on point 3.** `v_max` and `K_m` for EcN `ClpXP` against this
substrate are unmeasured. We therefore do **not** report an amplification factor
as a prediction. We report the **structural requirement** instead:

◆ **第 3 条的诚实边界。** EcN 的 `ClpXP` 对这个底物的 `v_max` 和 `K_m` **都没测过**。
所以我们**不把放大倍数当成预测来报**，而是报那个**结构性要求**：

$$\text{leak production rate} \;<\; v_\text{max} \;<\; \text{induced production rate}$$

◆ （泄漏产率 < $v_\text{max}$ < 诱导产率）

and label the amplification table "illustrative, not predictive". Stating the
window a parameter must fall in is a usable engineering result; inventing the
parameter is not.

◆ 并且把那张放大倍数表明确标成"**演示，而非预测**"。**说清楚一个参数必须落在哪个
窗口里，是一个可用的工程结论；凭空编出这个参数，不是。**

**Residual limitation, stated rather than hidden.** The ± `SsrA` pairing cannot
separate *pore-forming activity* from the generic proteostatic load of any
accumulated protein. An inactivated point mutant would settle it. It does not
affect the `SsrA` decision, so we did not block on it.

◆ **残留的局限，写出来而不是藏起来。** ±`SsrA` 这个配对**分不开**"成孔活性"和
"任何蛋白累积都会带来的通用蛋白稳态负荷"。一个失活点突变体可以定案。但它不影响
`SsrA` 这个决策本身，所以我们没有卡在这里。

**→ Fed into Design:** `SsrA` retained in the shipped construct. Strategy A
(`PelB` + MMP-2 linker) was shelved rather than killed, because it addresses
release rather than containment — which is still our highest-priority open
question. Strategy B went forward to Cycle 4 and did not survive it.

◆ **→ 回流到设计：** 最终构建体保留 `SsrA`。策略 A（`PelB` + MMP-2 连接子）是
**搁置而不是否掉**，因为它解决的是**释放**而不是**关住**——而释放至今仍是我们
优先级最高的开放问题。策略 B 进入了循环 4，并且**没能活着出来**。

---

## Cycle 2 — "Tumour" is not a signal｜循环 2 — "肿瘤"不是一个信号

### Design (v1)｜设计（第一版）

The first gate we specified was **hypoxia AND cell density**:

◆ 我们最初定的门是**低氧 AND 菌密度**：

```
pPepT  → LuxI          (hypoxia input → AHL synthesis)
J23114 → LuxR          (constitutive)
pLux   → reporter      (NanoLuc or sfGFP, standing in for GSDMD-NT)
```

◆ （`pPepT → LuxI`：低氧输入 → 合成 AHL；`J23114 → LuxR`：组成型；
`pLux → 报告基因`：NanoLuc 或 sfGFP，先替代 GSDMD-NT）

Reporter-first was deliberate: prove the logic with a quantifiable, non-toxic
output before putting a pore-former downstream of it. We planned a four-corner
test (hypoxia/normoxia × high/low density, n ≥ 3) and an oxygen ladder for
`pPepT` alone (<0.1 %, 0.1–0.5 %, 1 %, 2 %, ambient), with NanoLuc as primary
read-out — luminescence has no photobleaching and better linearity than GFP —
and Western blot against GFP as an orthogonal identity check.

◆ **"先上报告基因"是刻意的**：在把一个成孔蛋白挂到下游之前，先用一个**可定量、
无毒**的输出把逻辑证出来。我们计划了四角点实验（低氧／常氧 × 高／低密度，n ≥ 3），
以及单独测 `pPepT` 的氧梯度（<0.1 %、0.1–0.5 %、1 %、2 %、常氧），**主读出用
NanoLuc**——发光没有光漂白、线性也比 GFP 好——再用抗 GFP 的 Western blot 做一个
正交的身份核验。

### Learn (before Build — the cheap kind)｜学到了什么（在构建之前——便宜的那种）

Reviewing this design against the delivery route killed it on paper. The
intended route is oral. **The colonic lumen is strictly anoxic and carries
~10¹¹ CFU/g of commensals.** Both of the v1 inputs — low oxygen and high
bacterial density — are therefore *more* true in the gut lumen than in a tumour.
A hypoxia-AND-density gate is not a tumour detector; it is a colon detector.

◆ 把这版设计拿去对照**给药途径**，它在纸面上就死了。预期途径是**口服**。
**结肠腔是严格厌氧的，并且带着约 10¹¹ CFU/g 的共生菌。** 于是第一版的两个输入
——低氧、高菌密度——**在肠腔里比在肿瘤里更成立**。一个"低氧 AND 密度"的门
**不是肿瘤探测器，而是结肠探测器**。

This is the cycle we would most like a reader to notice, because it cost one
meeting instead of one cloning run.

◆ **这是我们最希望读者注意到的一轮**，因为它的代价是**一次会议，而不是一次克隆**。

### Design (v2)｜设计（第二版）

Replace the constitutive drive on `luxR` with a **lactate-sensing promoter**,
making lactate a third, genuinely tumour-associated input:

◆ 把 `luxR` 上的组成型驱动换成**乳酸感应启动子**，让乳酸成为第三个、
真正与肿瘤相关的输入：

```
pPepT        → LuxI              (hypoxia)
BBa_M36021   → LuxR              (lactate; E. coli lldPRD operon promoter)
pLux         → GSDMD-NT-SsrA     (AND of the two arms, via LuxR–AHL)
```

◆ （`BBa_M36021` 即 *E. coli* `lldPRD` 操纵子启动子；`pLux` 经 LuxR–AHL
实现两臂的 AND）

`J23114` was kept in the kit as a constitutive control and module-diagnostic
tool rather than discarded. We also wrote down, before ordering, the in-silico
checks this swap forces: internal `BsaI` sites in every fragment and the
backbone, `LldR` binding sites in the final `BBa_M36021` sequence, and —
critically — **whether EcN's endogenous `LldR` is present, expressed and
functional**, since `BBa_M36021`'s lactate response depends on that regulatory
background and we might need to supply `lldR` in trans.

◆ `J23114` **没有丢掉**，而是留在 kit 里作为组成型对照和模块诊断工具。我们还在
**下单之前**就把这次替换强制要求的 in-silico 检查写了下来：每个片段和骨架内部的
`BsaI` 位点、最终 `BBa_M36021` 序列里的 `LldR` 结合位点，以及——**最关键的**
——**EcN 内源的 `LldR` 是否存在、是否表达、是否有功能**，因为 `BBa_M36021` 的乳酸
响应依赖这个调控背景，必要时我们可能得**额外反式提供 `lldR`**。

### Build｜构建

Constructs carrying the reporter under the two-input gate, assembled and
sequence-verified as in Cycle 1.

◆ 把报告基因挂在双输入门下的构建体，按循环 1 的流程组装并测序确认。

### Test｜测试

Four corners at 20 mM lactate: 21 % / 1 % O₂ × ± lactate, n = 3, sampled at
3, 6, 9 and 24 h, with **two independent read-outs** — GFP intensity and GFP⁺
fraction (positive rate).

◆ 在 20 mM 乳酸下测四个角点：21 % / 1 % O₂ × ±乳酸，n = 3，在 3、6、9、24 h 取样，
用**两个相互独立的读出**——GFP 强度，以及 GFP⁺ 比例（发光率）。

| 24 h | 21 % O₂, − lactate | 1 % O₂, − lactate | 21 % O₂, + lactate | 1 % O₂, + lactate |
|---|---|---|---|---|
| GFP⁺ fraction | 5.4 % | 31.7 % | 82.9 % | **97.9 %** |

◆ 表头中文：24 h｜21 % O₂ 无乳酸｜1 % O₂ 无乳酸｜21 % O₂ 加乳酸｜1 % O₂ 加乳酸；
行名：GFP⁺ 比例。

🖼 **Figure 3.** Four-corner induction at 3/6/9/24 h, both read-outs, n = 3,
mean ± SD. A hollow marker on the intensity panel means that point's mean
includes a well recorded as `0` — a measurement at the detection limit, not a
true zero. The two read-outs disagree about those wells, which is what forced
the conventions in Learn 3.

◆ **图 3.** 四角点在 3/6/9/24 h 的诱导情况，两个读出，n = 3，均值 ± SD。强度那一格
里**空心的点**表示这个均值里含有记为 `0` 的孔——那是**检测下限处的测量值，不是真零**。
两个读出在这些孔上**互相矛盾**，这正是下面"学到了什么"第 3 条那些约定的由来。

### Learn｜学到了什么

**1 · Lactate is the necessary and nearly sufficient input; hypoxia is an
accelerator, not a gatekeeper.** Three mutually independent read-outs agree on
how much low oxygen adds *on top of* saturating lactate at the 24 h endpoint:

◆ **1 · 乳酸是必要且几乎充分的输入；低氧只是加速器，不是守门人。** 三个相互独立的
读出对"在乳酸饱和的基础上低氧还能再加多少"给出一致的答案（24 h 终点）：

| Read-out | Increment from 21 % → 1 % O₂ |
|---|---|
| GFP⁺ fraction, 82.9 % → 97.9 % | **1.18×** |
| GFP intensity, 253,571 → 337,332 | **1.33×** |
| Untagged-strain endpoint OD, 1.380 → 1.380 | **1.00×** |

◆ 表头中文：读出｜21 % → 1 % O₂ 带来的增量；
三行依次为：GFP⁺ 比例、GFP 强度、无标签菌的终点 OD。

The OD read-out is the strictest of the three: the untagged strain lands on
exactly 1.380 under *lactate-only* and under *both inputs*, and that is not a
floor — hypoxia-only reaches 1.707. Mid-course, hypoxia does accelerate
measurably (3.4× on positive rate at both 6 h and 9 h), which is a kinetic
effect, not an endpoint-selectivity effect.

◆ OD 这个读出是三者中最严的：无标签菌在**"只有乳酸"**和**"两个输入全开"**两种条件下
**都精确落在 1.380**，而且**这不是地板**——"只有低氧"能到 1.707。在中程，低氧确实
有可测的加速作用（6 h 和 9 h 的发光率倍数都是 3.4×），但那是**动力学效应，不是终点
选择性效应**。

This retired an earlier internal claim of a "16–17× oxygen effect". That figure
came from inverting a latent variable out of saturated read-outs — the most
model-dependent of the available estimates — and we replaced it with the three
direct measurements above.

◆ 这一条**作废了我们内部早先"氧效应 16–17×"的说法**。那个数字是从饱和读出里**反演
一个潜变量**得来的——是所有可得估计里**最依赖模型假设**的一个——我们用上面三个
**直接测量**把它替换掉了。

**2 · The gate factorises at the endpoint, and only at the endpoint.** The
two-way interaction term is zero within error at 24 h, and the factorised gate
predicts any held-out corner to within **2.2 %**. At 6 and 9 h the same
prediction is wrong by up to **4.4×**.

◆ **2 · 这个门在终点可以因子化，而且只在终点可以。** 24 h 时双因素交互项**在误差内
为零**，因子化后的门能把**任意一个留出角点**预测到 **2.2 %** 以内。而在 6 h 和 9 h，
同样的预测**最大会错 4.4 倍**。

**→ Fed into Design and into the modelling:** the whole safety analysis is
licensed to treat the gate as a product of its two arms, **and** we wrote an
explicit prohibition against extrapolating mid-course ON/OFF ratios. One
convenience and one restriction, from the same experiment.

◆ **→ 回流到设计与建模：** 整条安全性论证**被授权**把门当作两臂的乘积来处理，
**同时**我们写下了一条明确的禁令：**不许外推中程的 ON/OFF 倍数**。同一个实验，
给了我们一个便利和一个约束。

**3 · Measurement conventions, forced on us by the data.** 19 wells in the
intensity read-out recorded `0`. Those are real measurements ("no fluorescence
detected"), but they are left-censored at the instrument's detection limit, and
**16 of the 19 are contradicted by the positive-rate read-out on the same
sample** — intensity 0 while 2–32 % of cells scored GFP⁺. So: zeros stay in the
mean, zeros may **never** be a denominator (our `fold_change()` raises an error
if they are), OFF-state ON/OFF ratios are always taken from the positive-rate
read-out, and groups containing a censored well are reported as their three raw
values rather than as mean ± SD. `[40433, 32134, 0]` has an 88 % CV and a
bimodal distribution; `± SD` would tell the reader it is Gaussian noise, which
it is not.

◆ **3 · 被数据逼出来的测量约定。** 强度读出里有 **19 个孔记为 `0`**。它们是真实测量
（"没检测到荧光"），但它们在仪器检测下限处**左截断**，而且 **19 个里有 16 个被同一
样品的发光率读出证伪**——强度为 0，而同组解析出 2–32 % 的细胞是 GFP⁺。所以：
**0 保留在均值里**；**0 绝不能做分母**（我们的 `fold_change()` 遇到这种情况会直接
抛错）；OFF 态的 ON/OFF 倍数**一律取发光率读出**；**含截断孔的组列出三个原始值，
不写 `mean ± SD`**。`[40433, 32134, 0]` 的 CV 是 88 %、分布是双峰的，写 `± SD`
会让读者以为那是高斯噪声——它不是。

---

## Cycle 3 — Where else does the gate open? (a modelling cycle)｜循环 3 — 这个门还会在哪里打开？（一轮建模循环）

iGEM's own description of the engineering cycle notes that it applies to the
development of models in the Design stage. This cycle produced a **build
decision** — it stopped us ordering a part — without any new DNA.

◆ iGEM 自己对工程循环的说明里写明：**这个循环同样适用于 Design 阶段里模型自身的
开发**。这一轮**没有任何新 DNA**，却产出了一个**构建决定**——它拦住了我们去订一个元件。

### Design｜设计

Cycle 2 told us lactate dominates the gate. That immediately raises the question
Cycle 2 could not answer, because no lactate gradient and no 0 % O₂ condition
exists in our data: **at which non-tumour sites are both inputs simultaneously
true?** We built a tissue-site model — oxygen and lactate with upper and lower
bounds, a literature source and an evidence grade per site — and scored the gate
at each site. The previous cycle's site list had no gut lumen in it at all;
adding it was the point.

◆ 循环 2 告诉我们**乳酸主导这个门**。这立刻引出一个循环 2 回答不了的问题——因为我们
的数据里**既没有乳酸梯度，也没有 0 % O₂ 条件**：**在哪些非肿瘤位点，两个输入会同时
为真？** 我们建了一个组织位点模型——每个位点都有氧和乳酸的上下界、文献来源和证据
等级——并在每个位点给这个门打分。**上一轮的位点表里根本没有肠腔；把它加进去才是
重点。**

| Site | Lactate | Source |
|---|---|---|
| Healthy rectal lumen | L-lactate 0.5 mM [0–1.6]; D-lactate 0.1 mM [0–0.8] | Crit Care 2006, PMC1794470 |
| Healthy faeces | < 5 mM (absorbed by epithelium or consumed by lactate-utilisers) | Duncan et al., AEM 2004 |
| Tumour (model value) | 8 mM | project parameter table |
| **Ulcerative colitis / short bowel (dysbiosis)** | **up to 100 mM** | Mayeur et al., PLoS ONE 2013; Hove & Mortensen 1994 |

◆ 对照表：

| 位点 | 乳酸 | 来源 |
|---|---|---|
| 健康直肠腔 | L-乳酸 0.5 mM [0–1.6]；D-乳酸 0.1 mM [0–0.8] | Crit Care 2006, PMC1794470 |
| 健康粪便 | < 5 mM（被肠上皮吸收，或被耗乳酸菌消耗） | Duncan et al., AEM 2004 |
| 肿瘤（模型用值） | 8 mM | 项目参数总表 |
| **溃疡性结肠炎／短肠综合征（菌群失调）** | **可达 100 mM** | Mayeur et al., PLoS ONE 2013；Hove & Mortensen 1994 |

### Build / Test｜构建／测试

Analytic, then numerical. Both input arms are monotone functions of their own
stimulus, so the lactate arm's discriminating power has a closed-form ceiling:

◆ 先解析，再数值。两条输入臂都是各自刺激的**单调函数**，所以乳酸臂的判别力有一个
**闭式上限**：

$$\text{discrimination} \;\le\; \min\!\left(\left(\frac{L_\text{target}}{L_\text{off-target}}\right)^{n},\; \frac{1}{\text{basal}}\right)$$

◆ （判别力 ≤ min( (靶点乳酸/脱靶乳酸)^n , 1/基础表达 )）

Wild-type `lldPRD` has basal expression of about 1/7, so **the lactate arm cannot
discriminate better than 7×, for any Hill coefficient and any EC50.**

◆ 野生型 `lldPRD` 的基础表达约为 1/7，所以**乳酸臂的判别力上限就是 7×——
对任何 Hill 系数、任何 EC50 都成立。**

### Learn｜学到了什么

**1 · On the designed arms alone, the gut lumen is not protected.** The colonic
lumen is **anoxic (0 % O₂)** while a tumour core is merely **hypoxic (≈0.5 %)**,
so the hypoxia arm is *counter-selective* at all three luminal sites. Under
dysbiosis, where luminal lactate can reach 12× the tumour value, **both arms are
counter-selective at once.** Scored on the designed arms, all three luminal
sites fall **below 1.0**. This is structural: it holds for any EC50, any Hill
coefficient, any basal rate.

◆ **1 · 只靠设计的那两条臂，肠腔是守不住的。** 结肠腔是**厌氧（0 % O₂）**，而肿瘤
核心只是**低氧（≈0.5 %）**，所以**低氧臂在三个肠腔位点全部反选择**。在菌群失调情景
下，肠腔乳酸可达肿瘤值的 12 倍，于是**两条臂同时反选择**。按设计臂打分，三个肠腔
位点**全部低于 1.0**。**这是结构性的**：任意 EC50、任意 Hill 系数、任意基础表达都如此。

**2 · The safety argument survives — because of a property of the part we had
not been crediting.** `BBa_M36021` is the *native* `E. coli lldPRD` operon
promoter, and our own 2026-07-15 design note says so explicitly. Native means
its **anaerobic repression and glucose repression are intact**. The colonic lumen
is anoxic and, proximally, glucose-rich; a tumour core is hypoxic-but-not-anoxic
and glucose-depleted by the Warburg effect. So the repression **engages in the
lumen and releases in the tumour**, giving 87–228× luminal discrimination where
the designed arms alone give 0.87–2.28×. The worst-case site needs only ≈12-fold
repression.

◆ **2 · 安全性论证有救——靠的是这个元件身上一个我们之前没给它记功的性质。**
`BBa_M36021` 是**天然的** *E. coli* `lldPRD` 操纵子启动子，我们自己 2026-07-15 的
设计说明里就是这么写的。**天然**意味着它的**厌氧抑制和葡萄糖抑制都还在**。结肠腔
厌氧、而且近端富糖；肿瘤核心**低氧但不厌氧**，并且被 Warburg 效应耗尽了葡萄糖。
所以**抑制在肠腔启动、在肿瘤松开**，把肠腔判别力从单靠设计臂的 0.87–2.28×
抬到 **87–228×**。最苛刻的位点**只需要约 12 倍抑制**。

**3 · 🔴 This reversed a planned optimisation.** Our July route-map contained the
line *"replace with a lactate sensor optimised for hypoxic, glucose-rich
conditions"* — i.e. swap in a de-repressed variant to raise intratumoural
expression. **That would discard the only mechanism holding the colonic lumen
off**, dropping luminal discrimination from 87–228× back to 0.87–2.28×. We
rejected that optimisation. This is the clearest case in the project of a model
changing a build decision rather than decorating one.

◆ **3 · 🔴 这一条推翻了一项既定的优化计划。** 我们 7 月的路线图里有这么一句：
*"更换经过低氧、富糖条件优化的乳酸传感元件"*——也就是换一个**去抑制变体**来提高
瘤内表达。**那会把唯一能关住结肠腔的机制一起扔掉**，判别力从 87–228× 掉回
0.87–2.28×。**我们否决了这项优化。** 这是全项目中**模型改变构建决定**（而不是给
构建决定做装饰）最清楚的一个例子。

**4 · The mucosal margin, converted into a rate rather than quoted as a fold.**
A 19.6× mucosal margin is not by itself a safety statement. Off-target exposure
is divided by the margin, killing scales as exposure^b, and colonic epithelium
turns over in 3–5 days (22.1 % daily repair — note that is `1/T`, not `ln2/T`).
Carried through, 19.6× implies epithelial loss of 2.6 × 10⁻⁴ %/24 h, i.e.
**1/85,800 of the renewal rate**; even with amplification removed entirely
(b = 1) it is still 1/629. Inverted, the loss criterion alone needs only 2.3×
margin.
⚠️ **But that criterion covers cell loss only, not inflammation** — the effector
is a pyroptosis executioner, and IL-1β/IL-18 are precisely what our immune
module depends on. So this is a **lower bound** on the margin required, not a
verdict that the margin is sufficient.

◆ **4 · 把黏膜余量换算成速率，而不是当成一个倍数来引用。** **19.6× 的黏膜余量本身
不是一句安全性陈述。** 脱靶暴露被余量除、杀伤 ∝ 暴露^b、结肠上皮 3–5 天置换一次
（每日修复 22.1 %——注意这是 `1/T`，不是 `ln2/T`）。一路算下去，19.6× 意味着上皮
损失 2.6 × 10⁻⁴ %/24h，也就是**更新率的 1/85,800**；**即使把放大完全拿掉（b = 1），
仍然是 1/629**。反过来看，单就损失判据而言**只需要 2.3 倍余量**。
◆ ⚠️ **但这个判据只覆盖细胞损失，不覆盖炎症**——效应蛋白是**焦亡的执行者**，
而 IL-1β／IL-18 恰恰正是我们免疫模块所依赖的东西。所以这是所需余量的**下界**，
**不是"余量够了"的判决**。

---

## Cycle 4 — Delivery vs. selectivity: the `TAT` peptide｜循环 4 — 递送 vs. 选择性：`TAT` 肽

### Design｜设计

Strategy B from Cycle 1. Our highest-priority open question is how GSDMD-NT
leaves the chassis and reaches a tumour cell at all. A C-terminal
cell-penetrating peptide was the literature-supported answer: CPPs are reported
to carry cargo as large as p53 across membranes by non-receptor-mediated routes,
and fusing at the C-terminus leaves the N-terminal pore-forming domain
unobstructed.

◆ 这是循环 1 里的策略 B。我们**优先级最高的开放问题**是：GSDMD-NT 究竟**怎么离开
底盘、怎么到达肿瘤细胞**。C 端接细胞穿膜肽是文献支持的答案：有报道称 CPP 能通过
非受体介导的途径把**大到 p53 这种量级的货物**带过膜，而且融合在 C 端不会挡住
**N 端的成孔结构域**。

### Build｜构建

Four constructs, so that the peptide's contribution could be separated from the
effector's: `gfp`, `gfp-TAT`, `GSDMD-NT`, `GSDMD-NT-TAT`, alongside
`GSDMD-NT-SsrA` and a bare `EcN` control.

◆ 做了四个构建体，**好把肽的贡献和效应蛋白的贡献分开**：`gfp`、`gfp-TAT`、
`GSDMD-NT`、`GSDMD-NT-TAT`，另外还有 `GSDMD-NT-SsrA` 和裸 `EcN` 对照。

### Test｜测试

Two co-culture blocks. A dose series against CT26 colorectal carcinoma cells
(6 / 8 / 10 OD, n = 3), and a normal-cell comparison at 10 OD only
(L929 fibroblasts vs CT26, n = 3).

◆ 两个共培养区块。一个是对 CT26 结直肠癌细胞的剂量序列（6 / 8 / 10 OD，n = 3），
另一个是只在 10 OD 做的正常细胞对比（L929 成纤维细胞 vs CT26，n = 3）。

🖼 **Figure 4.** Killing of CT26 vs L929 at 10 OD for every construct, measured
within one experiment, n = 3 unless marked, mean ± SD. The `TAT` constructs are
labelled in orange; their L929 bar is the whole story. `†` marks a construct
whose cancer-cell row duplicates the dose block well-for-well, so no selectivity
index is drawn for it. `GSDMD-NT-TAT` against L929 has n = 2 and both wells read
exactly 10.0, so it carries no error bar and no test.

◆ **图 4.** 10 OD 下每个构建体对 CT26 和 L929 的杀伤，**都在同一次实验内测得**，
除标注外 n = 3，均值 ± SD。`TAT` 构建体的标签是橙色的；**它们的 L929 那根柱子就是
全部故事**。`†` 标记的构建体，其癌细胞那一行与剂量区块**逐孔重复**，所以**不给它画
选择性指数**。`GSDMD-NT-TAT` 对 L929 只有 n = 2，而且两个孔都恰好读到 10.0，
所以它**没有误差棒、也没有检验**。

### Learn｜学到了什么

**`TAT` must be dropped.** The normal-cell row was all measured within one
experiment, so constructs are directly comparable there:

◆ **`TAT` 必须去掉。** 正常细胞那一行全部是在同一次实验内测的，所以**构建体之间
可以直接比较**：

| Construct | L929 killing at 10 OD |
|---|---|
| `GSDMD-NT-SsrA` | 1.43 ± 0.49 % |
| `GSDMD-NT` | 1.97 ± 0.15 % |
| **`GSDMD-NT-TAT`** | **10.00 %** (n = 2) |

◆ 表头中文：构建体｜10 OD 下对 L929 的杀伤率。

`TAT` raises off-target killing **7.0×** relative to the shipped construct
(5.1× relative to untagged), while the benefit it buys — measured within the
dose block, where the pairing is valid — is only **1.33×** (22.33 % → 29.63 %).
A 7-fold selectivity cost for a 1.33-fold potency gain fails on any weighting.

◆ `TAT` 把脱靶杀伤相对最终构建体抬高了 **7.0 倍**（相对无标签版是 5.1 倍），
而它换来的收益——在剂量区块内部配对测得、那里的配对才是有效的——**只有 1.33 倍**
（22.33 % → 29.63 %）。**用 7 倍的选择性代价换 1.33 倍的效力，在任何权重下都不划算。**

**And the mechanism of the cost is visible in the controls.** `gfp-TAT` kills
8.37 % at 10 OD, **2.0× `gfp`'s 4.23 %** — more than half of `GSDMD-NT-SsrA`'s
15.80 %. A GFP construct has no pore-forming domain, so **a large fraction of a
`TAT` construct's killing comes from the peptide itself, not from the effector.**
That is indiscriminate membrane damage wearing a delivery label.

◆ **而且这笔代价的机理在对照里就看得见。** `gfp-TAT` 在 10 OD 下杀伤 8.37 %，
是 `gfp` 的 4.23 % 的 **2.0 倍**——**超过了 `GSDMD-NT-SsrA` 那 15.80 % 的一半**。
GFP 构建体**根本没有成孔结构域**，所以**`TAT` 构建体的杀伤有很大一部分来自肽本身，
而不是来自效应蛋白。** 那是**挂着"递送"标签的无差别膜损伤**。

**→ Fed into Design:** no CPP in the shipped construct. Release/export remains
our top open question, and Cycle 1's Strategy A (`PelB` + MMP-2-cleavable
linker) is the surviving candidate precisely because its selectivity comes from a
*tumour-restricted protease*, not from a constitutively promiscuous peptide.

◆ **→ 回流到设计：** 最终构建体里**不放 CPP**。释放／外排仍然是我们最靠前的开放
问题，而循环 1 的策略 A（`PelB` + MMP-2 可切割连接子）之所以是**幸存的候选**，
正是因为**它的选择性来自一个肿瘤受限的蛋白酶**，而不是来自一个**组成型地见谁都
穿**的肽。

**A limitation we have to flag on this cycle:** `GSDMD-NT-TAT` against L929 has
n = 2 and both values are exactly 10.0, so the standard deviation is 0 and **no
t-test is possible.** We report it as n = 2 and borrow a pooled SD from the other
constructs where a test is needed. We did not impute the third well.

◆ **这一轮必须声明的一个局限：** `GSDMD-NT-TAT` 对 L929 只有 n = 2，而且两个值
**恰好都是 10.0**，所以标准差为 0、**没有 t 检验可做**。我们**照实标注 n = 2**，
需要做检验时从其他构建体借一个合并标准差。**我们没有去填补第三个孔。**

---

## Cycle 5 — How much do we need?｜循环 5 — 到底需要多大剂量？

### Design｜设计

The dose question had never been asked as an engineering specification, only as
a potency comparison. We reframed it: **what fraction of a lesion must be
cleared per day for the lesion not to grow**, and what dose delivers that?

◆ 剂量这个问题以前**从来没有被当成一条工程指标来问**，只被当成效力比较。我们把它
重新表述为：**每天必须清除病灶的多大比例，病灶才不会长大**，以及**什么剂量能做到
这一点**？

### Build / Test｜构建／测试

The dose block (6 / 8 / 10 OD, n = 3) was already there — it had previously been
mined only for a single-point potency ratio. It also carries a **plasmid control**
(`gfp`: plasmid-bearing, expressing a non-effector protein), so the chassis
contribution can be subtracted; at 10 OD the chassis accounts for 27 % of the
raw reading.

◆ 剂量区块（6 / 8 / 10 OD，n = 3）**本来就在那里**——此前只被用来取一个单点的效力
比值。而且它**带有质粒对照**（`gfp`：带质粒、表达一个非效应蛋白），所以**底盘的贡献
可以被扣掉**；在 10 OD 时底盘占原始读数的 **27 %**。

### Learn｜学到了什么

**1 · Killing follows a near-cubic dose law.** Killing ∝ dose^b with
b = 2.65–3.38, r² > 0.995.

◆ **1 · 杀伤服从一条接近立方的剂量律。** 杀伤 ∝ 剂量^b，b = 2.65–3.38，r² > 0.995。

**2 · The criterion is closed-form and assumes no dose–response shape.**
Controlling a lesion requires clearing, in 24 h, a fraction

◆ **2 · 判据是闭式的，而且不假设任何剂量—响应形式。** 控制住一个病灶，要求在 24 h
内清除如下比例：

$$f \;=\; 1 - \exp\!\left(-\frac{\ln 2 \cdot 24}{T_\text{doubling}}\right)$$

| Target | 24 h clearance needed | Dose required (relative to 10 OD) |
|---|---|---|
| CT26 (24–48 h doubling) | 29–50 % | **1.30 – 1.76×** ❌ needs scaling up |
| **Human CRC (100–600 d doubling)** | **0.12 – 0.69 %** | **0.18 – 0.43×** ✅ **already met** |

◆ 对照表：

| 靶标 | 24 h 需清除 | 所需剂量（相对 10 OD） |
|---|---|---|
| CT26（倍增 24–48 h） | 29–50 % | **1.30 – 1.76×** ❌ 需要上调 |
| **人结直肠癌（倍增 100–600 天）** | **0.12 – 0.69 %** | **0.18 – 0.43×** ✅ **已满足** |

**The human half does not depend on the fit at all:** the measured net killing at
6 OD is 2.97 % against a requirement of 0.69 % — a direct comparison, exceeding
it 4.3×. **All three measured doses satisfy the clinical indication.** CT26
doubles two orders of magnitude faster than human CRC, so "the dose is
insufficient in mice" does not imply insufficiency in humans; it means the mouse
model is the harder target.

◆ **人这一半完全不依赖拟合：** 6 OD 下实测净杀伤 **2.97 %**，而需求是 **0.69 %**
——这是**直接比较**，超出 4.3 倍。**三个实测剂量全部满足临床适应症的需求。**
CT26 的倍增比人结直肠癌**快两个数量级**，所以"在小鼠身上剂量不够"**并不蕴含**
在人身上不够；它只说明**小鼠模型是苛刻得多的靶子**。

**3 · The cubic law takes the cube root of every unknown.** A 600-fold spread in
doubling time becomes a 9.9-fold spread in required dose; the 3.7-fold delivery
loss from spatial coverage needs only 1.64-fold dose compensation. **This
back-calculation is least sensitive to its most uncertain parameter** — which is
the opposite of the usual situation and worth saying out loud.

◆ **3 · 立方律把每一个未知量都开了三次方根。** 倍增时间跨 600 倍 → 所需剂量只跨
**9.9 倍**；空间覆盖带来的 3.7 倍递送损失**只需要 1.64 倍剂量来补偿**。
**这个反推对它最不确定的那个参数最不敏感**——这和通常的情况正好相反，**值得明说**。

**4 · Micrometastasis is not a dose problem, and that redirected the project.**
We had planned a 2D axisymmetric finite-difference model for clustered lesions.
It turned out to be unnecessary — and the reason is an architectural fact nobody
had stated: **`LuxI` sits on `pPepT`, not on `pLux`, so there is no AHL
autoinduction feedback.** The steady state is therefore *linear*, superposition
is exact, and summing closed-form single-sphere solutions over any 3D arrangement
is more accurate than a 2D numerical approximation. A corollary: **the
quorum-sensing module is a colonised-volume integrator, not a bistable switch** —
no hysteresis, no switch-like transition, a graded response.

◆ **4 · 微转移灶不是剂量问题，而这件事改变了项目方向。** 我们原计划给成簇病灶写一个
二维轴对称有限差分模型。**结果发现没必要**——原因是一个**此前没人说过的架构事实**：
**`LuxI` 挂在 `pPepT` 上，而不是挂在 `pLux` 上，所以 AHL 没有自诱导正反馈。**
于是稳态方程是**线性**的，**叠加原理精确成立**，把闭式单球解在任意三维排布上加起来
**比二维数值近似更准**。一个推论：**群体感应模块是"定植体积积分器"，不是双稳开关**
——无滞后、无突变式切换、响应是渐变的。

Equivalent isolated radius for clustered 150 µm micro-lesions, against our own
150 µm OFF → 1000 µm ON bracket:

◆ 150 µm 微病灶成簇之后的**等效孤立半径**，对照我们自己的 150 µm OFF → 1000 µm ON
区间：

| Spacing | 13 lesions | 125 lesions |
|---|---|---|
| 300 µm (touching) | 333 µm | **652 µm** |
| 1000 µm (realistic) | 207 µm | 303 µm |
| 2000 µm | 173 µm | 201 µm |

◆ 表头中文：间距｜13 个病灶｜125 个病灶；首行"300 µm（相切）"、
次行"1000 µm（真实间距）"。

**None reaches 1000 µm.** Reaching it would take 512 touching lesions — a
continuous 2.4 mm mass, which is no longer a micrometastasis. And dispersal is
always *worse* than aggregation (0.84–0.95× equivalent/equal-volume), because
self-contribution scales as a² while neighbour contribution scales as a³/d.

◆ **没有一个达到 1000 µm。** 要达到需要 **512 个相切病灶**——那是一个连续的 2.4 mm
团块，**已经不是微转移灶了**。而且**分散永远不如聚集**（等效/等体积 = 0.84–0.95×），
因为**自身贡献 ∝ a²，而邻居贡献 ∝ a³/d**。

> ✅ **Safety side:** the lesion-size cut-off survives extension to multiple
> lesions, and gets harder.
> ⚠️ **Efficacy side:** this circuit cannot clear true micrometastases. Distal
> killing can only come from the immune cascade — which is why our immune module
> is not optional decoration but the only mechanism that addresses disseminated
> disease.

◆ ✅ **安全侧：** 病灶尺寸阈值**经得起多病灶扩展**，而且结论更硬。
◆ ⚠️ **效力侧：** 这条线路**清不掉真正的微转移灶**。远端杀伤**只能来自免疫级联**
——所以我们的免疫模块**不是可选的点缀，而是唯一能回答播散性疾病的机制**。

**5 · One safety statement in this cycle has an independent confirmation.** The
lesion diameter below which the hypoxia arm cannot fire for *any* parameter set
is ≈178 µm. It is pure geometry with zero fitted parameters, and it lands inside
the 160–200 µm bracket Thomlinson & Gray measured histologically in 1955 — the
only parameter in the project that an independent measurement confirms.

◆ **5 · 这一轮里有一条安全性陈述拿到了独立确认。** 低于这个病灶直径，低氧臂
**对任何参数组都点不着**——这个直径是 **≈178 µm**。它是**纯几何、零拟合参数**，
而且**正好落在 Thomlinson & Gray 1955 年组织学测得的 160–200 µm 区间内**——这是
**全项目唯一一个被独立测量确认的参数**。

---

## Cycle 6 — Open: anoxia vs. hypoxia at the lactate sensor｜循环 6 — 开放中：乳酸传感器处的厌氧 vs. 低氧

We are reporting this cycle unfinished because the alternative is to overstate
Cycle 3.

◆ 我们**照"未完成"来报这一轮**，因为另一个选择是**把循环 3 说过头**。

### Design｜设计

Cycle 3's safety conclusion rests on one assumption: that native `lldPRD`
anaerobic repression is engaged at 0 % O₂ (gut lumen) and released at ~1 % O₂
(tumour core). **This is the single structural assumption in the project**, and it
is not in the same class as our other open parameters:

◆ 循环 3 的安全性结论**压在一个假设上**：天然 `lldPRD` 的厌氧抑制**在 0 % O₂
（肠腔）启动、在约 1 % O₂（肿瘤核心）松开**。**这是全项目唯一的结构性假设**，
而且**它和我们其他的开放参数不是一类东西**：

> Every other unmeasured parameter only widens an interval.
> **This one changes a sign.**

◆ **其他未定参数只是把区间撑宽。这一条会让结论变号。**

With repression, the three luminal sites score 23–60×. Without it, **0.23–0.60×**.
That also flips which element is the bottleneck, and flips the "do not swap the
promoter" recommendation of Cycle 3.

◆ 有抑制时，三个肠腔位点打分 **23–60×**；没有抑制时是 **0.23–0.60×**。
随之翻掉的还有**"瓶颈是哪个元件"**，以及循环 3 那条**"不要换启动子"**的建议。

* **The measured half:** 1 % O₂ + lactate is the highest corner (97.9 %), so the
  sensor is *not* repressed at 1 % — which is what the tumour side requires.
* **The unmeasured half:** our workbook contains **no 0 % O₂ condition at all.**
* **Why we nonetheless think it holds** (neither reason is a measurement): the
  required repression is modest (4.4× / 9.2× / 11.5× at the three sites), and the
  switching range of FNR-type oxygen regulation is 0–1 % — exactly the interval
  separating the two sites.

◆ · **已测的那一半：** "1 % O₂ + 乳酸"是最高角点（97.9 %），所以传感器在 1 % 下
**没有被抑制**——这正是肿瘤侧所需要的。
◆ · **未测的那一半：** 我们的工作簿里**根本没有任何 0 % O₂ 条件**。
◆ · **我们仍然认为它成立的理由**（两条都不是测量）：所需抑制**很温和**
（三个位点分别是 4.4× / 9.2× / 11.5×），而 FNR 型氧调控的**切换区间恰好是 0–1 %**
——正是分开这两个位点的那个区间。

### Build / Test — specified, not yet run｜构建／测试 — 已指定，尚未执行

> **One plate closes it: `lldPRD`-only reporter, 0 % vs 1 % O₂.**

◆ **一块板就能定案：只带 `lldPRD` 的报告构建体，0 % 对 1 % O₂。**

This is also the parameter our global sensitivity analysis independently flagged
as the most valuable and cheapest to measure (`repression_fold`, S<sub>T</sub> =
0.457 at the bottleneck). A fuller lactate gradient (`lldPRD`-only at
0/0.5/2/5/10/20 mM) remains the single most valuable experiment we could run;
the wet lab could not schedule it in this cycle, so Cycle 3 was deliberately
written to ask *where must the parameter lie* rather than to depend on it.

◆ 这**同时也是**我们全局灵敏度分析**独立标出来**的"最该测、又最便宜"的那个参数
（`repression_fold`，在瓶颈处 S<sub>T</sub> = 0.457）。更完整的乳酸梯度
（只带 `lldPRD`，0/0.5/2/5/10/20 mM）仍然是**我们能做的最有价值的单个实验**；
实验组在本轮排不上，所以**循环 3 是刻意写成"反问参数必须落在哪里"，而不是依赖它。**

---

## What we got wrong, and how we caught it｜我们错在哪，以及怎么抓到的

Two of our own results reversed under checking, and we think a reader should
weigh these more heavily than the ones that went our way.

◆ 我们自己有两个结果**在复核中被推翻**。我们认为读者**应当给这两条比那些"顺我们
意"的结论更高的权重**。

**1 · We withdrew a selectivity index we had already published internally.**
We had reported a selectivity index of **11.4×** for untagged `GSDMD-NT`. It is
wrong, and it was caught by our own consistency checking rather than by anyone
objecting. The dose block and the normal-cell block are **two different
experiments** — the latter reads an order of magnitude lower overall (geometric
mean ratio 0.131 across the four constructs independently measured in both). An
11.4× index built from a numerator at dose-block level and a denominator at
normal-cell-block level is inflated by roughly 7.6×. Ratios may not cross blocks.

◆ **1 · 我们撤回了一个已经在内部发布过的选择性指数。** 我们曾经报过无标签
`GSDMD-NT` 的选择性指数是 **11.4×**。**它是错的**，而且是**被我们自己的一致性检查
抓到的**，不是被谁质疑出来的。剂量区块和正常细胞区块是**两次不同的实验**——后者
整体低一个数量级（在两个区块里都独立测过的那四个构建体，比值的几何均值是 0.131）。
一个**分子取自剂量区块水平、分母取自正常细胞区块水平**的 11.4× 指数，大约被虚高了
**7.6 倍**。**比值不得跨区块。**

While checking this we found something else: in the normal-cell block, the CT26
rows for `GSDMD-NT` and `GSDMD-NT-TAT` are **well-for-well identical** to the
dose block, ratios 1.003 and 1.001, matching to the first decimal across all
three replicates. In a genuine independent experiment that is impossible; it is
almost certainly a copy-paste during table assembly. Our code **detects** this
rather than hard-coding it (2 % tolerance), and flags those constructs'
selectivity indices as untrustworthy.

◆ 在查这件事的时候我们还发现了另一件事：在正常细胞区块里，`GSDMD-NT` 和
`GSDMD-NT-TAT` 的 CT26 行与剂量区块**逐孔相同**，比值分别是 1.003 和 1.001，
三个复孔**一一对应到小数点后一位**。在一次真正独立的实验里**这是不可能的**；
几乎可以肯定是**制表时复制粘贴**过去的。我们的代码是**检测**这件事（2 % 容差），
**而不是把它硬编码进去**，并把这些构建体的选择性指数标记为**不可信**。

> **The only valid protein-level selectivity figure we have is `GSDMD-NT-SsrA`'s
> 3.33×** (CT26 4.77 ± 0.80 / L929 1.43 ± 0.49, n = 3, p < 0.001), paired within
> a single block. That matters for design, not just bookkeeping: **the safety
> argument has to come from the circuit's tissue selectivity, not from any
> preference GSDMD-NT has for cancer cells.**

◆ **我们手上唯一有效的蛋白层面选择性数字，是 `GSDMD-NT-SsrA` 的 3.33×**
（CT26 4.77 ± 0.80 / L929 1.43 ± 0.49，n = 3，p < 0.001），**在单个区块内部配对**
得出。这件事**对设计有意义，不只是记账**：**安全性论证必须来自回路的组织选择性，
而不是来自 GSDMD-NT 本身对癌细胞的任何偏好。**

**2 · We cancelled a planned molecular-dynamics chapter.** We had intended to use
MD to argue why the effector does not kill the chassis. We dropped it for two
reasons: the MD material we had inherited turned out not to be this project's
work at all (a keyword scan found no GSDMD, TAT, EcN, PelB, SsrA, tumour or
lactate anywhere in it — it is a generic lipid-raft methods exercise), and, more
importantly, **the question MD was meant to answer had already been answered by
direct measurement** in Cycle 1. Using a simulation to re-argue a settled point
is answering a solved question with weaker evidence.

◆ **2 · 我们取消了原定的分子动力学章节。** 我们本来打算用 MD 来论证效应蛋白为什么
不杀死底盘。放弃它有两个理由：我们继承下来的那份 MD 材料**根本不是本项目的工作**
（关键词扫描在里面找不到 GSDMD、TAT、EcN、PelB、SsrA、肿瘤或乳酸中的任何一个
——那是一份通用的脂筏方法练习），以及——**更重要的**——**MD 本来要回答的那个问题，
在循环 1 里已经被直接测量回答了**。用模拟去重新论证一个已经了结的点，
**等于用更弱的证据回答一个已经解决的问题**。

**3 · We adopted published measurements over two inherited parameters.** Two
sensor parameters we had been carrying turned out to have published measurements
that disagreed with them. We took the measurements and recomputed every
downstream number.

◆ **3 · 有两个继承下来的参数，我们改用了已发表的测量值。** 我们一直在用的两个
传感器参数，后来发现**有已发表的测量值与它们不符**。我们**采用了测量值，并把所有
下游数字重算了一遍**。

---

## How these cycles connect｜这些循环之间的关系

🖼 **Figure 5.** Cycle map: each Learn, and the Design decision it changed.
Blue arrows add something to the design, orange arrows take something out, and
the dashed arrow is the cycle still open. Two of the six point at a removal.

◆ **图 5.** 循环图：每一个 Learn，以及它改变了的那个 Design 决定。**蓝色箭头**表示
往设计里**加**了东西，**橙色箭头**表示从设计里**拿掉**了东西，**虚线箭头**是那一轮
还开着的循环。**六条里有两条指向"拿掉"。**

Two of our six cycles ended by **removing** something — a peptide and a planned
optimisation — and the section above removed a third thing, a whole chapter we
had intended to write. One cycle ended before any DNA was ordered. We think that
is what the engineering cycle is for: the cheapest iteration is the one that
happens in the Design stage, and the most useful Learn is often the one that
tells you not to build what you were about to build.

◆ 我们六轮循环里有**两轮是以"拿掉"某个东西收尾的**——一个肽，和一项既定的优化
——而**上面那一节又拿掉了第三样东西**：一整章我们本来打算写的内容。**还有一轮在任何
DNA 被订购之前就结束了。** 我们认为**这正是工程循环的用处**：**最便宜的那次迭代发生
在设计阶段**，而**最有用的那个 Learn，往往是告诉你"别造你正要造的东西"的那一个**。

Every number on this page is traceable to the frozen data workbook or to code in
our repository, and our test suite pins each reported figure to the function that
produces it — so this page cannot carry a stale number, and a reader who wants to
check one can run it.

◆ 本页上的**每一个数字**都可以追溯到那份**冻结的数据工作簿**或我们仓库里的代码，
而且我们的测试套件**把每一个报出来的数字钉回生成它的那个函数**——所以**这一页不可能
带着一个过期的数字**，而想核对其中任何一个的读者**可以自己跑一遍**。
