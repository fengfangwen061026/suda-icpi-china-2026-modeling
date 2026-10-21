# Presentation Video — Modeling 口播稿

> 参考风格：XJTLU-Science-China 2025（#5636，Gold / Top 10）Team Presentation。
> 第一人称、口语、按"遇到什么 → 怎么办 → 结果 → 所以我们改了什么"推进，不解释自己在答什么题。
>
> 本段时长 **约 4:00**（可裁到 2:40，见 §3）。数字全部出自 `model_v2/` 模块文档，
> `300 passed, 1 skipped`（2026-10-13 复跑）。

---

## 1. 这一段讲的是一个什么故事

**一句话**：我们造了一个只该在肿瘤里打开的门，但培养板只能告诉我们门在瓶子里能开能关——
它答不了"在病人肠道里还守不守得住"和"到底要给多少菌"。建模就是为这两个问题而建的，
**而它给的每一个答案，都变成了实验台上的一个决定。**

故事走向（**不按模块编号讲**）：

```
实验数据 ──▶ 模型发现我们读错了数   ──▶ 回到实验：不用新做，导一次原始数据就行
         ──▶ 模型发现没人看过的风险 ──▶ 回到设计：否决换启动子，定下该做的那块板
         ──▶ 模型在不开工的情况下定了两个构建决策（留单 SsrA、去掉 TAT）
         ──▶ 模型反推出剂量：人结直肠癌，现有剂量已经够
         ──▶ 两个模型撞上同一面墙 ──▶ 免疫级联从"点缀"变成"必需"，这是下一轮的设计起点
         ──▶ 藏数据考模型：预测 98.13 %，实测 98.08 %
```

---

## 2. 主稿（约 4:00）

格式：**[时间] 画面 → EN 口播 → 中文对照**。`(pause)` 是给剪辑留的呼吸点。
英文约 610 词，按 145 wpm 计 4:12；按 155 wpm 计 3:56。

---

### ① 我们为什么需要模型 ｜ 0:00–0:28

**画面**：三层门线路动画（缺氧 → LuxI → AHL ／ 乳酸 → LuxR ／ pLux → GSDMD-N–SsrA），
最后定格成一个 AND 门符号。

> **EN** — Our circuit is an AND gate. The bacteria should only fire when they see
> hypoxia, **and** lactate, **and** enough of their own neighbours — in other words,
> only inside a tumour. But here is the problem we ran into. A culture plate can tell
> you the gate opens and closes in a flask. It cannot tell you whether that gate still
> holds in a patient's gut, and it cannot tell you how many bacteria a patient would
> actually need. (pause) Those two questions are what our modelling was built for.
> And every answer it gave came back to the bench as a decision.

> **中** — 我们的线路是一个 AND 门：细菌只有同时看到缺氧、乳酸，以及足够多的同伴时才
> 启动——也就是说，只在肿瘤里启动。但我们遇到的问题是：培养板能告诉你门在瓶子里开得了
> 关得上，却答不了两件事——这个门在病人的肠道里还守不守得住，以及一个病人到底需要多少
> 细菌。这两个问题，就是我们建模的全部目的。而它给出的每一个答案，都变成了实验台上的
> 一个决定。

---

### ② 第一圈：数据教给模型，模型回头纠正了我们 ｜ 0:28–1:06

**画面**：原始荧光四角柱状图（两根顶到天花板）→ 切到 probit 变换后的四角图，两图并排。

> **EN** — We started from our own data, and the first thing the model did was catch us
> making a mistake. When we read the gate straight off the raw fluorescence, the numbers
> did not add up — two of the four conditions were off by more than tenfold. The model
> showed us why: those measurements were **saturating**. The signal had flattened out, so the
> gate looked far weaker than it was. Once we put the readings on a probit scale, the
> four corners became consistent again, and the AND logic came out clean at
> twenty-four hours — but **not** at nine. (pause) So the model stopped us from claiming
> something too loudly: our gate is multiplicative at the endpoint, not all the way
> through. And the fix went straight back to the lab — the single-cell distributions we
> need were already sitting in our raw flow cytometry files. No new experiment. Just a
> re-export.

> **中** — 我们是从自己的数据出发的，而模型做的第一件事，是抓住了我们的一个错误。直接
> 用原始荧光去读这个门时，数字对不上——四个条件里有两个偏差超过十倍。模型告诉我们原因：
> 那两个孔**饱和**了，信号被压平，于是门看起来比实际弱得多。把读数放到 probit 尺度上之后，
> 四个角重新自洽，AND 逻辑在 24 小时干干净净地成立——但 9 小时**不成立**。所以模型拦住了
> 我们一句说得太满的话：我们的门是终点处乘性的，不是全程乘性的。而解决办法直接回到了
> 实验室——我们需要的单细胞分布，本来就躺在原始流式文件里。不用新做实验，重新导一次就行。

---

### ③ 第二圈：模型找到了一个没人看过的风险 ｜ 1:06–1:52

**画面**：人体口服路径动画（口 → 胃 → 结肠腔 → 肿瘤），在结肠腔处停住并标出
"0 % O₂ ／ lactate"；然后切 `fig3_3_arm_direction.png`。

> **EN** — Then the model found something none of us had been looking at. We deliver
> **orally**. So before our bacteria ever reach a tumour, they spend hours in the colon
> — and the colon is **strictly anaerobic**, and it carries lactate. Which means both of
> the sensors we designed actually prefer the gut **over** the tumour. (pause) And this
> is not a fitting result. It holds for any sensor parameters you choose. What saves us
> is something we had not designed on purpose: our lactate sensor is the **native**
> *lldPRD* promoter, so it still carries its own anaerobic and glucose repression. The
> gut is anaerobic and sugar-rich, so the promoter stays shut. The tumour core is
> hypoxic but not anoxic, and its glucose is consumed by the Warburg effect — so there,
> it opens. With that repression, the gate separates tumour from gut by twenty- to
> sixtyfold. Without it, the sign **flips** — the gut opens wider than the tumour does.

> **中** — 接着，模型找到了一件我们谁都没看过的事。我们是**口服**给药。所以细菌在到达
> 肿瘤之前，要先在结肠里待上几个小时——而结肠**绝对厌氧**，并且含有乳酸。这意味着我们
> 设计的两个传感器，其实更"偏爱"肠道而不是肿瘤。而且这不是拟合出来的结果，它对任何
> 传感器参数都成立。真正救了我们的，是一件我们并非有意设计的事：我们的乳酸传感器是
> **天然的** `lldPRD` 启动子，它自带厌氧抑制和葡萄糖抑制。肠道厌氧且富糖，所以启动子
> 保持关闭；瘤核低氧但不厌氧，葡萄糖又被 Warburg 效应耗光，所以在那里它才打开。有这层
> 抑制，门把肿瘤和肠腔分开 23 到 60 倍；没有它，判别力掉到 1 以下——**肠腔比肿瘤开得更大**。

---

### ④ 于是我们改了设计，也定下了该做的那块板 ｜ 1:52–2:28

**画面**：三张决策卡依次推入——❌ 换启动子（打叉）／ ✅ 单拷贝 SsrA ／ ❌ TAT（打叉），
最后定格一块 96 孔板，标 "0 % vs 1 % O₂"。

> **EN** — That one result changed our design in two ways. We had planned to swap in a
> **de-repressed**, hypoxia-optimised lactate sensor, to get stronger expression inside
> the tumour. We cancelled it — it would have thrown away the only thing keeping the gut
> quiet. And it told us exactly which experiment matters most: **one plate**, the lactate
> promoter on its own, at zero versus one percent oxygen. Out of everything still unknown
> in this project, that is the only measurement that could flip a conclusion rather than
> just widen an error bar — so it went to the top of our list. (pause) The model also
> settled two build decisions **without a build**. We keep a single SsrA tag instead of
> engineering a second one, because the tag we already have is stronger than it needs to
> be. And we removed the TAT peptide — it multiplied off-target killing **sevenfold**,
> and on-target potency by only thirty percent.

> **中** — 这一个结果改了我们两处设计。我们原本打算换一个**去抑制**的、经低氧优化的乳酸
> 传感器，好让肿瘤内表达更强。我们取消了——那会把唯一能让肠道安静下来的机制一起扔掉。
> 它同时告诉我们哪一个实验最该做：**一块板**，单独测乳酸启动子，0 % 对 1 % 氧。在这个
> 项目所有尚未确定的东西里，只有这一个测量能让结论**变号**，而不只是把误差棒撑宽——
> 所以它排到了第一位。模型还**在不开工的情况下**定了两个构建决策：我们保留单拷贝 SsrA
> 而不去造第二个，因为现有标签已经强于所需；我们去掉了 TAT——它把脱靶杀伤乘以 **7 倍**，
> 靶上效力只乘 1.3 倍。

---

### ⑤ 第二个问题：到底要给多大剂量 ｜ 2:28–3:00

**画面**：`fig4_6_dose_requirement.png`，剂量—杀伤点列上去，再叠一条"所需清除率"的横线。

> **EN** — The second question was dose. Our killing data follow a near-cubic law —
> kill scales as dose **cubed**. Put that against how fast a tumour grows back, and you
> get the dose you actually need. Human colorectal cancer doubles over **months**, so it
> only needs well under one percent of the lesion cleared per day. At our **lowest**
> tested dose, we already measured three percent. (pause) So all three of the doses we
> tested clear the bar for the human indication — and that is a direct comparison, not an
> extrapolation. CT26 in mice grows back a hundred times faster and needs roughly
> one-and-a-half times more. Which is worth saying plainly: **"not enough in mice" does
> not mean not enough in patients.**

> **中** — 第二个问题是剂量。我们的杀伤数据服从一条接近立方的规律——杀伤正比于剂量的
> **三次方**。把它和肿瘤长回来的速度放在一起，就得到真正需要的剂量。人的结直肠癌倍增
> 时间以**月**计，所以每天只需要清掉病灶的百分之一都不到；而在我们**最低**的一个测试
> 剂量下，实测已经是百分之三。所以我们测过的三个剂量，全部满足人体适应症的要求——
> 而且这是直接比较，不是外推。小鼠的 CT26 长回来快一百倍，需要大约 1.5 倍的量。这一点
> 值得说清楚：**"在小鼠身上不够"不等于"在病人身上不够"。**

---

### ⑥ 两个模型撞上同一面墙 ｜ 3:00–3:30

**画面**：`fig4_4_cluster.png` 与 `fig6_immune_feasibility.png` 分屏，中间画一堵墙，
两条箭头从两边撞上去。

> **EN** — But then two models, built on completely different data, hit the **same wall**.
> Quorum sensing cannot switch on inside a micrometastasis — we showed that even a
> cluster of a hundred and twenty-five of them still sits below the threshold. And from
> the other direction, pushing the dose high enough to reach those lesions drops our
> safety margin below the tenfold we require — twenty-two-fold down to four. (pause) Two independent roads, one conclusion: **distant
> lesions can only be cleared by the immune cascade.** That is why pyroptosis-driven
> immunity is not a bonus feature in this project — it is a requirement. And it is what
> our next cycle is designed around.

> **中** — 但接着，两个建立在完全不同数据上的模型，撞上了**同一面墙**。群体感应在微转移
> 灶里开不起来——我们算出来，哪怕 125 个这样的病灶聚成一簇，仍然低于开启阈值。而从另一
> 个方向看，把剂量提高到够得着这些病灶，会把安全余量从 22 倍压到 4 倍，低于我们自己定的 10 倍要求。两条独立的路，
> 同一个结论：**远处的病灶只能靠免疫级联清除。** 这就是为什么焦亡驱动的免疫在我们这个
> 项目里不是一个加分项，而是一个必要条件——它也正是我们下一轮设计的起点。

---

### ⑦ 我们怎么知道模型不是画了条好看的曲线 ｜ 3:30–4:00

**画面**：留出法动画——四角图其中一角被遮住 → 模型吐出 98.13 % → 揭开，实测 98.08 %。

> **EN** — And we tested the model the only honest way we could: by **hiding data from
> it**. Twenty-eight times, we took part of our dataset away, refit, and asked the model
> to tell us what it had never seen. The best one: if the gate really is multiplicative,
> then any three corners determine the fourth. So we hid the fully-induced corner and
> predicted **ninety-eight point one three percent**. The measurement was **ninety-eight
> point zero eight**. (pause) We also deliberately included a test we **expected to
> fail** — the same check at nine hours, where we already knew the gate is not yet
> multiplicative. It failed, four times out of four, exactly as predicted. Because a
> check that passes everything is not a check. (pause) This is internal cross-validation
> on our own dataset, not an external one — and we say so inside the model itself.
> **That is the loop we tried to close: our data trained the model, and the model sent
> us back to the bench with a shorter list.**

> **中** — 我们也用唯一诚实的方式考了模型：**把数据藏起来**。28 次，我们把一部分数据从
> 拟合里拿走，重新拟合，然后让模型说出它从没见过的那部分。最漂亮的一次：如果这个门真的
> 是乘性的，那么任意三个角就决定了第四个。于是我们把全开的那个角藏起来，模型预测
> **98.13 %**，实测是 **98.08 %**。我们还故意放进了一条**预期会失败**的检验——同一个
> 检查放在 9 小时，那时我们已经知道门还不是乘性的。它 4 次全部失败，和预测的一样。
> 因为一个什么都能通过的检查，不算检查。这是在我们自己数据集上的内部交叉验证，不是外部
> 验证——这句话我们写进了模型本身。**这就是我们想闭上的那个环：数据训练了模型，模型又
> 把我们送回实验台，带着一张更短的清单。**

---

## 3. 短版（2:40）

删 ② 和 ⑤ 的后半，保留 ① ③ ④ ⑥ ⑦。②（读数饱和）是最容易让外行听丢的一段，优先砍。

| 版本 | 段落 | 时长 |
|---|---|---|
| 主稿 | ①②③④⑤⑥⑦ | ~4:00 |
| 短版 | ①③④⑤(半)⑥⑦ | ~2:40 |
| 极限版 | ①③④⑦ | ~1:50 |

> ⚠️ **不要靠加速语速塞时长**——iGEM 明确写了这算作弊。要短就砍段。

---

## 4. 画面清单

| 段 | 画面 | 素材 |
|---|---|---|
| ① | 三层门动画 → AND 门符号 | 需新作（PPT 已有线路图，重排）|
| ② | 原始四角 vs probit 四角，并排 | 数见 `MODULE_2_2.md`，需作图 |
| ③ | 口服路径动画，停在结肠腔 → 两臂方向 | 需新作 + `outputs/figures/fig3_3_arm_direction.png` |
| ④ | 三张决策卡 → 96 孔板定格 | 需新作（纯文字卡）|
| ⑤ | 剂量反推 | `outputs/figures/fig4_6_dose_requirement.png` |
| ⑥ | 簇 / 免疫分屏 + 一堵墙 | `fig4_4_cluster.png`、`fig6_immune_feasibility.png` |
| ⑦ | 遮角 → 预测 → 揭开 | 需新作（`MODULE_VALIDATION.md` 的表改成动画）|

字号按 1080p 全屏可读排；**画面里不得出现国旗**；字幕单独出 `.vtt`，不要烧进画面；
旁白只能由在册学生录。

---

## 附录 A　口播里每个数字的出处

| 口播说法 | 精确值 | 来源 |
|---|---|---|
| "偏差超过十倍" | 12.214× | `MODULE_2_2.md` §5 |
| "24 h 干净、9 h 不成立" | 交互项 −0.011 ± 0.157 ／ +1.135 ± 0.350 | `MODULE_2_2.md` §5 |
| "判别力约一百倍 / 没有它就反过来" | 乳酸臂 86.9–227.6× ／ 0.87–2.28×；**全门 23–60× ／ 0.23–0.60×** | `MODULE_3_3.md` §4.5、`src/tissue.py`（测试钉住 23.08×） |
| "标签已强于所需" | 比最优强 2.35×，代价 7.34 %；余量 1.21–1.93× | `MODULE_3_4.md` §7 |
| "TAT ×7 对 ×1.3" | 脱靶 7.0×，收益 1.33× | `DATA_CONVENTIONS.md` 已定案 4 |
| "接近立方" | b = 2.65–3.38，r² > 0.995 | `MODULE_4_6.md` §5 |
| "人 CRC 不到 1 % ／ 实测 3 %" | 需 0.12–0.69 %；6 OD 实测 2.97 % | `MODULE_4_6.md` §5 |
| "小鼠需约 1.5 倍" | 1.30–1.76× | `MODULE_4_6.md` §5 |
| "125 个仍低于阈值" | 等效 652 µm < 1000 µm；需 512 个 | `MODULE_4_4.md` §5 |
| "余量压到 10× 以下" | 150 µm 病灶需 4.95× 剂量，21.85× 余量剩 4.41×（换先验前为 14.46× / 1.36×） | `MODULE_4_6.md` §5.4 |
| "28 次 / 98.13 vs 98.08 / 9 h 四次全败" | 同上 | `MODULE_VALIDATION.md` |

**被问到文献一致性时**（口播没念）：健康直肠腔 L-乳酸 0.5 mM
[[Crit Care 2006](https://pmc.ncbi.nlm.nih.gov/articles/PMC1794470)]、健康粪便 < 5 mM
[[Duncan AEM 2004](https://journals.asm.org/doi/10.1128/aem.70.10.5810-5817.2004)]、
失调可达 100 mM [[Mayeur PLoS ONE 2013](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0054335)、
[Hove 1994](https://pubmed.ncbi.nlm.nih.gov/8209186/)]；`BBa_M36021` = 天然 *lldPRD* 启动子。

## 附录 B　不能说的话

1. **不报任何口服 CFU 数**——缺两座桥（OD → 每癌细胞 CFU 的平板计数、口服后瘤内 CFU/g）。
   这条写成了可执行记录 `effective_dose_conclusion(reports_oral_cfu=False)`。
2. **不说"远端杀伤占 35.2 %"**——那是演示算例。第 6 章全章 `scenario_only`，对外只报
   可行性边界。
3. **不说"外部验证"**，只说 hold-out / internal cross-validation。
4. **不把 17.4× / 642× 当测量值报**（σ-conditional）。
5. 提导师意见时说"总评两项 + 六条"，不说"第几问"（见 `SUPERVISOR_FEEDBACK.md`）。

## 附录 C　纯英文连读版（录音时照这个念）

Our circuit is an AND gate. The bacteria should only fire when they see hypoxia, and
lactate, and enough of their own neighbours — in other words, only inside a tumour. But
here is the problem we ran into. A culture plate can tell you the gate opens and closes
in a flask. It cannot tell you whether that gate still holds in a patient's gut, and it
cannot tell you how many bacteria a patient would actually need. Those two questions are
what our modelling was built for. And every answer it gave came back to the bench as a
decision.

We started from our own data, and the first thing the model did was catch us making a
mistake. When we read the gate straight off the raw fluorescence, the numbers did not add
up — two of the four conditions were off by more than tenfold. The model showed us why:
those measurements were saturating. The signal had flattened out, so the gate looked far weaker
than it was. Once we put the readings on a probit scale, the four corners became
consistent again, and the AND logic came out clean at twenty-four hours — but not at
nine. So the model stopped us from claiming something too loudly: our gate is
multiplicative at the endpoint, not all the way through. And the fix went straight back
to the lab — the single-cell distributions we need were already sitting in our raw flow
cytometry files. No new experiment. Just a re-export.

Then the model found something none of us had been looking at. We deliver orally. So
before our bacteria ever reach a tumour, they spend hours in the colon — and the colon is
strictly anaerobic, and it carries lactate. Which means both of the sensors we designed
actually prefer the gut over the tumour. And this is not a fitting result. It holds for
any sensor parameters you choose. What saves us is something we had not designed on
purpose: our lactate sensor is the native lldPRD promoter, so it still carries its own
anaerobic and glucose repression. The gut is anaerobic and sugar-rich, so the promoter
stays shut. The tumour core is hypoxic but not anoxic, and its glucose is consumed by the
Warburg effect — so there, it opens. With that repression, the gate separates tumour from
gut by twenty- to sixtyfold. Without it, the sign flips — the gut opens wider than the
tumour does.

That one result changed our design in two ways. We had planned to swap in a de-repressed,
hypoxia-optimised lactate sensor, to get stronger expression inside the tumour. We
cancelled it — it would have thrown away the only thing keeping the gut quiet. And it
told us exactly which experiment matters most: one plate, the lactate promoter on its
own, at zero versus one percent oxygen. Out of everything still unknown in this project,
that is the only measurement that could flip a conclusion rather than just widen an error
bar — so it went to the top of our list. The model also settled two build decisions
without a build. We keep a single SsrA tag instead of engineering a second one, because
the tag we already have is stronger than it needs to be. And we removed the TAT peptide —
it multiplied off-target killing sevenfold, and on-target potency by only thirty percent.

The second question was dose. Our killing data follow a near-cubic law — kill scales as
dose cubed. Put that against how fast a tumour grows back, and you get the dose you
actually need. Human colorectal cancer doubles over months, so it only needs well under
one percent of the lesion cleared per day. At our lowest tested dose, we already measured
three percent. So all three of the doses we tested clear the bar for the human indication
— and that is a direct comparison, not an extrapolation. CT26 in mice grows back a
hundred times faster and needs roughly one-and-a-half times more. Which is worth saying
plainly: "not enough in mice" does not mean not enough in patients.

But then two models, built on completely different data, hit the same wall. Quorum
sensing cannot switch on inside a micrometastasis — we showed that even a cluster of a
hundred and twenty-five of them still sits below the threshold. And from the other
direction, pushing the dose high enough to reach those lesions drops our safety margin below the
tenfold we require — twenty-two-fold down to four. Two independent roads, one conclusion: distant lesions can only be cleared
by the immune cascade. That is why pyroptosis-driven immunity is not a bonus feature in
this project — it is a requirement. And it is what our next cycle is designed around.

And we tested the model the only honest way we could: by hiding data from it. Twenty-eight
times, we took part of our dataset away, refit, and asked the model to tell us what it had
never seen. The best one: if the gate really is multiplicative, then any three corners
determine the fourth. So we hid the fully-induced corner and predicted ninety-eight point
one three percent. The measurement was ninety-eight point zero eight. We also deliberately
included a test we expected to fail — the same check at nine hours, where we already knew
the gate is not yet multiplicative. It failed, four times out of four, exactly as
predicted. Because a check that passes everything is not a check. This is internal
cross-validation on our own dataset, not an external one — and we say so inside the model
itself. That is the loop we tried to close: our data trained the model, and the model sent
us back to the bench with a shorter list.
