# Contribution — Modeling（建模组稿）

> **编者注（不要粘到 wiki 上）**
>
> 按 XJTLU-Science-China 2025 那页的规格写的：建模贡献 **3 条**，每条一个"能拿走的
> 东西"（一套流程 / 三个方程 / 一条诊断规则）。
>
> **双语排法：每条先英文、后中文，内容对应。**英文块是上 wiki 的那一份，可直接复制；
> **中文块只供组内和导师审稿，不要粘到 wiki 上。** ⚠️ 一处是只有你们能填的空（仓库地址）。
>
> 写法上：先给通用方法，我们自己的数只作每条末尾一句脚注，这样别队读到的是可以搬走的
> 东西，不是我们的结论。三条分别对应别队最容易踩的三个坑：只算靶点不算给药路径、
> 剂量和安全分两章算、把 Lux 系统默认当双稳开关。
>
> Word 版：`CONTRIBUTION.docx`，由 `build_contribution_docx.py` 从本文件生成
> （跳过本编者注，公式为 Word 原生对象）。六条版 / 八节版备份在 scratchpad。
>
> ⚠️ `WIKI_DRAFT.md` 第 48 行 "a test suite of 329 assertions" 是旧数（实跑 336
> tests），`Modeling.docx` 正文也带着它，改了要重建。

---

## Modeling Contribution

Our own model is specific to one circuit — a hypoxia-AND-lactate gate driving a
pyroptosis effector in orally dosed *E. coli* Nissle 1917 — so we have tried to write
down the three things we would hand to **any** team whose therapeutic depends on an
environment-sensing genetic circuit, with our own numbers kept to a footnote.

⚠️ *All three are implemented in our repository:* `<GitLab URL>`.

**中文** — 我们的模型是为一个特定回路算的（低氧 AND 乳酸门驱动焦亡效应蛋白，口服给药的
*E. coli* Nissle 1917），直接交给别队用不上。所以下面写的是我们会交给**任何**“疗效依赖环境感应回路”的队伍的三件事，我们自己的数字一律压到每条末尾的一句脚注里。

---

### 1. A site-enumeration protocol for safety claims about sensing circuits

The common failure is to model the circuit **in the target** and show it switches on.
That is the efficacy question. A safety claim needs the complement — *where else are
all the inputs true?* — and that is a bookkeeping problem, not a simulation. Our
protocol:

1. **List sites, including the route of administration.** Every anatomical compartment
   the chassis passes through or persists in, not only the healthy analogue of the
   target tissue. Oral, inhaled and topical delivery all add compartments whose
   chemistry is nothing like the tissue you designed against.
2. **Give each input a range, not a value**, with a source and an evidence grade per
   site. A site entering the table as a point value will leave it as a false claim.
3. **Write the gate output per site as a product and keep the factors separate:**
   $R_{\text{site}} = \big(\prod_k A_k^{\text{designed}}\big)\times\rho^{\text{native}}$,
   where $A_k$ are your designed arms and $\rho^{\text{native}}$ is the host's own
   regulation of the promoters you borrowed.
4. **Read the two factors apart.** If $\rho^{\text{native}}$ carries the margin, your
   designed circuit is not what makes the therapy safe — and any "improvement" that
   removes that regulation deletes the safety argument. Re-run the table against every
   proposed sensor modification and report what it *deletes*, not only what it adds.

> *In our project this moved the bottleneck site from a tissue to the gut lumen, which
> our previous site list had omitted entirely, and it showed that a de-repressed
> sensor variant — an obvious-looking improvement — would have collapsed luminal
> discrimination by about two orders of magnitude.*

**中文 · 感应回路安全性论证的位点枚举协议**

常见的做法是**在靶点里**模拟回路、证明它会开——那是有效性问题。安全性问题是它的补集：
**除了靶点，还有哪里所有输入同时为真？**这是一道记账题，不是仿真题。我们的四步：

1. **先列位点，而且必须包含给药路径。**底盘经过或驻留的每一个解剖腔室，不只是靶组织的
   健康对照。口服、吸入、局部给药都会引入化学环境与你设计时假想的组织毫不相干的腔室。
2. **每个输入给区间，不给点值**，并逐位点注明来源与证据等级。以点值进表的位点，出表时
   就是一条假陈述。
3. **把逐位点的门输出写成乘积，并把两类因子分开记：**
   $R_{\text{site}} = \big(\prod_k A_k^{\text{designed}}\big)\times\rho^{\text{native}}$，
   其中 $A_k$ 是你设计的各条臂，$\rho^{\text{native}}$ 是你借用的那些启动子在宿主体内
   自带的调控。
4. **分开读这两个因子。**如果余量是 $\rho^{\text{native}}$ 撑起来的，那么让这套疗法安全的
   并不是你设计的回路；而任何去掉这层调控的“改进”，会把安全性论证一并删掉。每提出一个
   传感器改动，就把位点表重跑一遍，并报告它**删掉了什么**，而不只是增加了什么。

> *在我们项目里，这一步把瓶颈位点从组织换成了肠腔——而肠腔在我们上一版位点表里根本
> 没有；同时它表明，一个“去阻遏”的传感器变体（看起来是显而易见的改进）会把腔室判别力
> 砸掉约两个数量级。*

---

### 2. Treat required dose and available safety margin as one budget

Efficacy and safety are usually separate chapters that never meet, so a project can
pass both and still be infeasible. They are the same budget and can be closed in
three lines. Given a dose–response fitted as a power law $f = A\,d^{\,b}$ and a
required effect $f_{\text{req}}$:

$$d^{*}=\left(\frac{f_{\text{req}}}{A}\right)^{1/b}$$

$$\varepsilon_j=\left(\frac{f_{\text{req},j}}{f_{\text{ref}}}\right)^{1/b},
\qquad \varepsilon=\prod_j \varepsilon_j$$

$$M_{\text{left}}=\frac{M_{0}}{\varepsilon}$$

$d^{*}$ is the dose a required effect demands. Each independent reason your real
target is harder than the one you measured — a smaller lesion, weaker local circuit
output, a stricter kill fraction — contributes its own escalation factor
$\varepsilon_j$, and **they multiply**. $M_0$ is the on-/off-target margin at the
reference dose and $M_{\text{left}}$ is what survives paying for $\varepsilon$,
off-target exposure being proportional to dose. **Feasible iff
$M_{\text{left}} \ge M_{\text{req}}$.**

Note that a *ratio* margin is unchanged by dose — raising the dose lifts both sides.
What the escalation actually spends is the distance to an **absolute** tolerance, which
is why the two chapters can each look fine on their own.

The value is in what a failure means: when $M_{\text{left}} < M_{\text{req}}$, you have
found a **design requirement**, not a parameter to optimise. No dose answers it, and
the project needs a different mechanism — which is a conclusion neither chapter
reaches alone.

> *In our project the hardest target class failed this inequality, which is why our
> design relies on an immune-mediated cascade rather than on dose escalation.*

**中文 · 把所需剂量和可用安全余量当同一本预算**

有效性和安全性通常是互不见面的两章，于是一个项目可以两章都过、整体仍然不可行。它们花的
是同一本预算，三行就能合上。设剂量—响应拟合为幂律 $f = A\,d^{\,b}$，所需效应为
$f_{\text{req}}$：

$$d^{*}=\left(\frac{f_{\text{req}}}{A}\right)^{1/b}$$

$$\varepsilon_j=\left(\frac{f_{\text{req},j}}{f_{\text{ref}}}\right)^{1/b},
\qquad \varepsilon=\prod_j \varepsilon_j$$

$$M_{\text{left}}=\frac{M_{0}}{\varepsilon}$$

$d^{*}$ 是达到所需效应所要的剂量。“真实靶点比你实测的那个更难”的每一个独立原因——病灶
更小、局部回路输出更弱、要求的杀伤分数更高——各贡献一个升级因子 $\varepsilon_j$，而
**它们相乘**。$M_0$ 是参考剂量下的靶/非靶余量，$M_{\text{left}}$ 是付掉 $\varepsilon$
之后剩下的余量（前提是非靶暴露与剂量成正比）。**可行条件是
$M_{\text{left}} \ge M_{\text{req}}$。**

注意**比值**型余量不随剂量变化——提高剂量会同时抬高两边。升级真正花掉的是到**绝对**
容限的距离，这正是两章各看各的时候都显得没问题的原因。

价值在于失败意味着什么：当 $M_{\text{left}} < M_{\text{req}}$ 时，你拿到的是一条**设计
要求**，不是一个待优化的参数。没有任何剂量能回答它，项目需要换机制——而这是两章各自都
到不了的结论。

> *在我们项目里，最难的那一类靶点没能通过这个不等式，这正是我们的设计转而依赖免疫介导
> 级联、而不是继续抬剂量的原因。*

---

### 3. A one-line wiring check for whether your quorum module is a switch

Quorum sensing is modelled almost everywhere as a bistable switch with a density
threshold and hysteresis. **That depends entirely on which promoter drives the
synthase, and many iGEM circuits are wired the other way without noticing.**

Check whether your synthase (`LuxI` or equivalent) sits under the quorum-responsive
promoter or under an independent one. If it is independent, signal production does not
depend on signal concentration, so:

- there is **no autoinduction loop**, and the governing
  diffusion–degradation equation is **linear**;
- **superposition is exact**, so any arrangement of colonies has a closed-form signal
  field and needs no numerical solver — a far more trustworthy result than a grid;
- the module is a **colonised-volume integrator, not a switch**: graded response, no
  hysteresis, no sharp threshold. It cannot be tripped accidentally, but it also cannot
  be relied upon for sharpness.

The practical consequence is that most of the quorum-sensing modelling literature
does not describe your circuit, and that clustering questions — whether many small
colonies can pool one signal and self-activate — become a closed-form calculation
rather than a simulation.

> *In our project this turned a feared risk window into an analytic result: clusters at
> realistic spacing never leave the OFF state, and reaching ON requires a contiguous
> millimetre-scale mass our single-lesion model already covered.*

**中文 · 一行接线检查：判断你的群体感应模块到底是不是开关**

群体感应几乎在所有地方都被建模成“带密度阈值和滞后的双稳开关”。**这件事完全取决于
合成酶挂在哪个启动子下，而不少 iGEM 回路在无意中接成了另一种。**

去看你的合成酶（`LuxI` 或等价元件）是挂在群体感应响应启动子下，还是挂在一个独立启动子
下。如果是独立的，信号产生就不依赖信号浓度，于是：

- **没有自诱导环**，支配方程（扩散—降解）是**线性**的；
- **叠加精确成立**，任意菌落排布都有闭式信号场，不需要数值解算器——而且比网格解可信
  得多；
- 模块是**被定植体积的积分器，而不是开关**：渐变响应，无滞后，无陡阈值。它不会被误
  触发，但也不能指望它提供陡峭的判别。

实际后果有两条：大半群体感应建模文献描述的不是你的回路；而聚集类问题——很多小菌落
会不会共享一个信号池自行激活——会变成一次闭式计算，而不是一次仿真。

> *在我们项目里，这把一个被担心的风险窗口变成了一个解析结果：现实间距下的簇从不离开
> OFF 态，要到 ON 需要一个连续的毫米级团块——而那已经被单病灶模型覆盖了。*
