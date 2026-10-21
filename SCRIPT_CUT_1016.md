# 建模口播的取舍方案（2026-10-16）

> 同意"不呈现所有数据"。但取舍得有判据，否则砍掉的和留下的一样随机。
> 这份文件做三件事：**① 把时间预算算清楚；② 给一条可执行的留/砍规则；③ 按规则出定稿。**
>
> 核对基础见 [`SCRIPT_REVIEW_1015.md`](SCRIPT_REVIEW_1015.md)。
> 数字全部对过 `model_v2/`，`328 passed, 1 skipped`。

---

## 1. 先算预算：建模段其实不缺时间，开头才缺

按导师版 docx 自己的分时表，逐段数英文词数（口播词数 ÷ 时长 = 需要的语速）：

| 段 | 时长 | 词数 | 需要语速 | 判定 |
|---|---|---|---|---|
| 00:00–01:24 背景 + 三个问题 | 84 s | **391** | **279 wpm** | ❌ **念不完** |
| 01:24–02:06 问题一 EcN | 42 s | 61 | 87 wpm | ⬜ 空 11 s |
| 02:06–03:32 问题二 设计 + 实验 | 86 s | 123 | 86 wpm | ⬜ 空 24 s |
| **03:32–06:12 问题二 建模** | **160 s** | **200** | **75 wpm** | ⬜ **空 60 s** |
| 06:12–09:19 问题三（湿 234 + 建模 181） | 187 s | 415 | 133 wpm | ⚠️ 偏紧 |
| 09:19–11:14 教育 | 115 s | 277 | 145 wpm | ⚠️ 偏紧 |
| 11:14–12:37 患者医生公众 | 83 s | 165 | 119 wpm | ✅ |
| 12:37–13:59 贡献 + 结论 | 82 s | 163 | 119 wpm | ✅ |

全片后三段稳定在 **119–120 wpm**，这就是这个片子真实的语速基准。按它算：

> **问题二的建模段有 160 秒，只装了 200 词（75 wpm）——还空着约 120 词、整整 60 秒。**
>
> **而开头 84 秒要念 391 词，需要 279 wpm，是不可能的。**

⚠️ **不能靠加速语速塞时长**，iGEM 明确把这算作弊（我们 docx 附录里记过这条）。

**所以结论和直觉相反：真正必须取舍的不是建模，是开头。** 导师在 paras 25–27 插了约
174 词的新背景（"GSDMD-N is a double-edged sword…"那三段），和 para 28 的内容大量重复
——28 段几乎是 27 段的改写。两段留一段，开头就回到 ~120 wpm。

建模这边的实际约束是：

- **问题二建模段：可以加回约 120 词**（不需要砍任何东西）；
- **问题三建模部分：必须等长替换**（该段整体已 133 wpm，加一句就得砍一句）。

---

## 2. 取舍规则

一个数字留在口播里，只能有三种理由。**三条都不占的，一律砍。**

| | 留下的理由 | 例 |
|---|---|---|
| **A** | **下游另一个结论要用它** | 21.85×（¶剂量 要花它）、178 µm（微转移结论踩在它上面） |
| **B** | **它是一个决定的判据** | 87–228× → ~1×（否决换启动子）、剂量 vs 余量（否决硬提剂量） |
| **C** | **它证明模型被考过** | 留出法 98.13 / 98.08，且 9 h 四次全败 |

**纯描述性的数字一律砍**——哪怕它好听。按这条规则，被砍掉的第一个就是
**88.5 % / 11.5 %**：它回答的是"脱靶降低是怎么来的"，是机制分解，**没有任何下游结论
用到它，它也不是留 SsrA 的判据**（判据见 `SCRIPT_REVIEW_1015.md` §2.3）。

---

## 3. 三张清单

### 3.1 留（口播必须有）

| 内容 | 理由 | 词数 |
|---|---|---|
| 24 h 乘性成立、9 h 不成立、早期比值不可外推 | B（给第 3 章授权分解门） | 含在 ¶2 |
| 读数饱和 → probit 尺度后四角自洽 | A（不说这句，wiki 上 226.6× vs 预期 2768× 会显得我们在说谎） | ~30 |
| 留出法 98.13 / 98.08 + 9 h 四次全败 | C（**唯一**回答"模型不是画了条好看曲线"的内容；Best Model 判据就写着 validation） | ~45 |
| 肠腔反向选择，且**与参数无关** | B（结构性，不依赖未测参数） | 含在 ¶3 |
| 天然 lldPRD 的葡萄糖 + 厌氧抑制：87–228× → ~1× | B（否决换启动子） | 含在 ¶3 |
| **瓶颈 = 结肠黏膜 21.85×** | A（剂量段要花这个余量；不命名它，"margin" 没有指代） | ~10 |
| 那块板（启动子单独测 0 % vs 1 % O₂） | B（模型定实验优先级，iGEM 最认这个） | ~22 |
| 178 µm 几何地板 + 组织学 160–200 µm | A（微转移结论的前提） | ~61 |
| 剂量：最低剂量已达人适应症 + 4 倍余量 + **CT26 需 1.3–1.8×** | B（剂量目标；不提 CT26 是个坑） | 含在 ¶3 |
| 150 µm 要 5 倍，余量 21.85× → 4.41×，**低于 10× 要求** | B（否决硬提剂量） | 含在 ¶3 |
| 成簇也开不起来（125 个仍低于阈值） | B（**第二条独立路径**，"免疫是必需"的论证力全在这） | ~48 |
| 免疫：最小增益 + $\varepsilon G\le1$ 做不到 + 最大可治负荷 | B（可行性边界，不是预测） | ~55 |

### 3.2 砍（口播不讲，wiki 上留着）

| 内容 | 砍的理由 |
|---|---|
| **88.5 % / 11.5 %** SsrA 空间分解 | 纯描述，三条都不占。**这是导师新加的那段，砍它要先跟他说一声**（见 §5） |
| SsrA 半衰期 1.61 h / 8.66 h | 描述性；进答辩清单（它是六条第 2 条点名要的数，一定会被问） |
| TAT 脱靶 ×7.0 / 效力 ×1.33 | 构型选择已由湿实验段承担；且 L929 的 TAT 只有 n=2、SD=0，口播不值得碰 |
| 12.5× AHL 冲刷、各位点 2.28× / 1.54× 明细 | 描述性 |
| 512 个相切 = 2.1 mm 连续团块 | 125 个那一句已经够，这句是补强 |
| 换先验（$K_{O_2}$ 1.0→0.49 %、$n_Q$ 2→1） | 方法论，进 wiki 的 Reflection，不进口播 |
| 撤回 11.4× / 2.97× / 4.70× | 同上。**但 PPT 里若还印着 11.4×，必须换成 3.33×** |
| Sobol 主导参数、$d_{\text{crit}}=23.08$ | 描述性 |

### 3.3 进答辩备用清单（口播不讲，但一定会被问）

1. SsrA 正常组织半衰期 **1.61 h**，不带标签 **8.66 h**；留标签的判据是
   $r_{\text{potency}}<1/r_{\text{biomass}}$，三个剂量全满足，余量 1.21–1.93×
2. 88.5 % 来自"少做"、11.5 % 来自空间约束；ClpXP 饱和让标签**放大**启动子选择性
3. 换先验那件事：Sobol 点出两个决定余量的参数，两个都有已发表实测且与我们的先验不符，
   于是换掉并重算全页——**没有一条结论翻转**
4. 我们自己撤回了三个跨区块比值（11.4× / 2.97× / 4.70×），合法的是 3.33×（p<0.001）；
   撤掉 4.70× 把 SsrA 从"符号不定"变成"定案保留"
5. TAT：脱靶 ×7.0 换效力 ×1.33（注意：**说"7 倍"可以，不要说"显著"**，n=2、SD=0）
6. 512 个相切 150 µm 病灶 = 2.1 mm 连续团块，单病灶模型本来就说它会开
7. 为什么不报口服 CFU：缺两座桥（OD→每癌细胞 CFU 的平板计数、口服后瘤内 CFU/g）
8. 为什么只说 internal cross-validation：只有一份工作簿，没有第二个数据集
9. **那块板只差一半**：肿瘤那一侧已测（1 % O₂ + 乳酸下 97.9 % 阳性，启动子在 1 % 明显
   不受抑制），未测的是肠腔那一侧（0 % O₂）——见 `Modeling.docx` §2.3.4 与 §7.1③

---

## 4. 定稿（按规则砍完的版本）

两段都在预算内，**问题三那段与导师版等长**（181 → 188 词，+3 秒，可忽略）。
`SCRIPT_REVIEW_1015.md` §2 的五处错误已全部修掉。

### 问题二 · 建模段（5 段，339 词 ≈ 170 s；档期 160 s = **127 wpm**）

> 127 wpm 仍慢于问题三段现有的 133 wpm，**不需要赶**。若要压到 120 wpm，砍
> "rather than a formality"（3 词）和 "of the same quantity"（4 词）即可。
> 留出法那两句用的是 `Modeling.docx` §4.1 / §4.2 的原话（见 §7）。

> Modeling examined how the two inputs combine, where else the circuit might switch on,
> and whether the model survives a test.
>
> First, it tested whether the AND gate is a true product of its inputs. Straight off the
> raw fluorescence it looks far too weak, because two of the four conditions were
> saturating; on a probit scale the four corners agree again. At twenty-four hours the
> interaction term is zero within error, so the gate is multiplicative; at nine hours it
> is not, so early-time ratios should not be extrapolated.
>
> We then hid data from the model: given three corners it predicted the fourth at
> ninety-eight point one three percent, against ninety-eight point zero eight measured,
> and all four corners pass. The same check fails on all four at nine hours, and at six —
> which is what makes it a test rather than a formality.
>
> Second, modeling asked where else the circuit might activate. The colon lumen is
> strictly anaerobic and carries lactate, so the two sensors we designed are
> anti-selective there — they respond more strongly than in the tumor — and that holds
> for any sensor parameters. What keeps it quiet was not designed on purpose: our
> lactate sensor is the native lldPRD promoter, which still carries its own glucose and
> anaerobic repression. With it, the gate discriminates tumor from lumen by ninety- to
> two-hundred-fold, and our bottleneck becomes the colonic mucosa at twenty-two-fold;
> without it, that falls to about one. So we kept the native promoter, cancelled the
> de-repressed version we had planned, and put one plate at the top of our list: the
> promoter alone, at zero versus one percent oxygen.
>
> Modeling also found a geometric floor: lesions with a radius below about one hundred
> and seventy-eight micrometres have no hypoxic core, so the hypoxia arm cannot be
> induced and falls back to its basal level. That threshold is pure geometry, with no
> fitted parameters, and it agrees with histological measurements of the same quantity —
> one hundred and sixty to two hundred micrometres.

### 问题三 · 建模段（4 段，188 词 ≈ 94 s；导师版 181 词）

> Modeling added a separate perspective on activity.
>
> Second, it compared dose with safety margin. The human indication is met at our lowest
> tested dose, with four-fold to spare — a direct comparison, not an extrapolation. CT26,
> which doubles two orders of magnitude faster, needs one point three to one point eight
> times our highest. But reaching a one hundred and fifty micrometre lesion takes five
> times more dose, and that spends the mucosa margin from twenty-two-fold down to four,
> below the tenfold we set ourselves.
>
> And a second model, on completely different data, hits that wall from the other side:
> quorum sensing cannot fire inside a micrometastasis at all — even a hundred and
> twenty-five of them clustered stay below the threshold. So micrometastasis is not a
> problem a larger dose can solve.
>
> Finally, modeling asked whether immunity could reach distant lesions. It gives a
> feasibility boundary: in MSS and pMMR tumors the cascade has to clear a minimum gain —
> below that, no pyroptotic flux whatsoever is enough — and above it there is still a
> maximum treatable burden. So early treatment matters more than larger doses.

> 注：第二段开头的 "Second" 需要改成 "First"，或在它前面保留 §5 的 SsrA 句。

---

## 5. 一个需要导师点头的取舍

问题三那段是**等长预算**，所以下面两句**只能留一句**：

| | 词数 | 占哪条规则 | 砍掉的代价 |
|---|---|---|---|
| **A. SsrA 判据**（导师新加那段的位置） | 29 | B | 不大——**SsrA 的选择在上一段湿实验里已经讲过了**（"considering these comparisons alongside safety, we prioritized GSDMD-N-SsrA"），建模这句是补判据 |
| **B. 成簇也开不起来**（第二条独立路径） | 48 | B | **大**——没有它，"远端只能靠免疫"只剩一条理由，听起来像我们没办法了才去讲免疫 |

**建模组的建议：留 B，砍 A。** 理由是 A 的结论片子里已经有了，B 的论证结构片子里没有。
若导师坚持留 A（毕竟 88.5 % 那段是他加的），**就用这一句，并同时砍掉成簇那段**：

> First, it settled whether to keep the SsrA degron: the potency we lose has to stay
> smaller than the biomass we gain, and all three doses clear that line.

（注意这句**不是** 88.5 %。88.5 % 不是留 SsrA 的判据——详见
[`SCRIPT_REVIEW_1015.md`](SCRIPT_REVIEW_1015.md) §2.3。）

---

## 6. 顺手要提的两件（不属于建模，但会连带影响档期）

1. **开头 391 词 / 84 秒念不完。** paras 27 和 28 内容高度重复（27 是导师新插的
   "double-edged sword" 版，28 是原有的 "Developing FLAME requires balancing…" 版），
   **两段留一段就能回到 120 wpm**。这跟建模无关，但它是全片唯一真正超载的地方。
2. **中文稿仍是旧版**（第 99–106、112–113 段），导师只改了英文。录中文前要按 §4 重译。

---

## 7. 对过最新的 `Modeling.docx`（2026-10-15 14:06 导出）

**先说结论：这份导出和 `WIKI_DRAFT.md` 完全同步**，不是过期版本。逐个关键数字对过
（21.85× / 87–228× / 4.95× / 4.41× / 178 / 98.13 / 98.08 / 651.7 / 512 / 2.1 mm /
88.5 / 1.61 / 3.3× / 0.49 / 1.3–1.8），**出现次数两边一模一样**。所以口播只要对着
wiki 写就不会和页面打架。

### 7.1 wiki 上有三处写得比口播稿更强，建议直接取用它的原话

**① §4.1 — 留出法是"样本外预测"，不只是"内部一致性检查"**

> *All four corners pass, worst ratio 1.022. The AND claim is therefore an **out-of-sample
> prediction, not only an internal consistency test**: the held-out corner was not used
> to produce the number that predicts it.*

比我们原来的讲法多两样东西：**四个角全过（最差误差 2.2 %）**，以及"留出的角没有参与
产生预测它的那个数"这一句话的定性升级。§4.2 又补上：**9 h 四个角全败（3.24 个标准误）、
6 h 也全败**，并且——

> *A protocol that passed everywhere would have no power... We assert "endpoint passes
> and mid-course fails" as a single test.*

**"把成功和失败当成同一个断言"**，这句比"我们也放了一个预期失败的检验"有力。§4 的定稿
已按这个改（见 §4 的第 3 段）。
⚠️ 用词红线不变：可以说 **out-of-sample / held-out**，**不能说 external validation**
——只有一份工作簿（`PRESENTATION_VIDEO_MODELING.md` 附录 B 第 3 条）。

**② §3.6 开头就是"两条路撞一面墙"的论证，而且是 wiki 自己写的**

> *Since §3.2 showed colonisation cannot reach disseminated disease and §3.5 showed dose
> escalation cannot either, **this cascade is the only available route to distant
> control. That promotes this section from optional to load-bearing.***

这正是 `SCRIPT_REVIEW_1015.md` §3.2 要求加回成簇那句的理由——**wiki 里有这个论证，
导师版的口播里没有**。所以 §5 那个取舍（留成簇 vs 留 SsrA）应当留成簇。
§3.6 同时自己声明了 *report feasibility boundaries, not predicted efficacy*，与口播
"It gives a feasibility boundary" 一致。

**③ §2.3.4 — 那块板的"一半已经测过了"**

> 已测的一半：*at 1 % O₂ with lactate the circuit reaches its highest corner, 97.9 %
> positive ⇒ the promoter is plainly not repressed at 1 %, which is what the tumour side
> needs*。未测的一半是**肠腔那一侧（0 % O₂）**。

口播里"the promoter alone, at zero versus one percent oxygen"照旧成立，但答辩时要讲成
**"肿瘤那一侧我们已经测了（1 % O₂ 下 97.9 % 阳性），这块板只是去钉住肠腔那一侧"**——
比"有个关键假设没测"听起来扎实得多。这一条加进 §3.3 的答辩清单。

### 7.2 wiki 上两处建议改（与口播无关，但评委会看到）

1. **§3.6 的 Question 段里出现了 "the supervisor's local-versus-distant question"**
   （全页唯一一处 "supervisor"）。评委不知道 supervisor 是谁，这句读起来像内部文档。
   改成 *the local-versus-distant split* 或 *the question of how much of the killing is
   local and how much is immune-mediated* 即可。
2. **§3.2 的结论是按"安全"写的**（*The multi-lesion extension opens no new risk
   window*），而 §3.6 引用它时当作"疗效到不了播散灶"。同一个数两种读法都对，但
   **只读 §3.2 的人拿不到"两条路"那层意思**——这也是 `SCRIPT_REVIEW_1015.md` §5
   建议把它补进 headline 的原因。

---

## 8. 已写进导师文档（2026-10-16）

**输出文件**：`model_v2/FLAME_Presentation_Video_建模组回改_1016.docx`
**导师原文件没有改动**（仍在微信临时目录），这是一份新的副本。

### 做法

全部改动以**修订（tracked changes）**形式写入，作者标为 **建模组**、日期 2026-10-16，
并且**划掉的旧文字和紧跟其后的新文字用两种颜色分开**：

| | 颜色 | 样式 |
|---|---|---|
| 划掉的旧文字（导师原句 / 中文旧稿） | **红色 `C00000`** | 修订删除线 |
| 改动后的新文字 | **蓝色 `0070C0`** | 修订下划线 |

共 36 处红色删除、17 处蓝色新增。这样即使两边都是"建模组"这一个作者，也能一眼分清
哪段是划掉的、哪段是接上来的新文字。

- 在 Word / WPS 里"显示修订"即可逐句对照；
- **接受全部修订** → 得到本文件 §4 的定稿；
- **拒绝建模组的修订** → 逐字回到导师 2026-10-15 的版本（已验证可完整回退）。

⚠️ 颜色是真实的字体颜色（不是修订标记的自动配色，否则同一作者的删除和新增会同色）。
所以**接受全部修订之后，新文字仍然是蓝色**——定稿录制前选中这几段，把字体颜色设为
"自动"即可。

格式沿用导师文档本身：段落样式、字号、`<w:lang>` 设置都复制相邻段落，数字写法跟他一致
（`24 h` / `9 h` / `~178 μm` / `1.3–1.8×` / `160–200 μm`），**没有改成口播用的英文数字拼写**。

### 改了哪些段

| 位置 | 动作 |
|---|---|
| 英文 问题二 建模 4 段 | 改写，并新增 1 段（留出法那段独立成段） |
| 英文 问题三 SsrA 段（88.5 %） | **整段删除**——§5 的取舍定为留成簇 |
| 英文 问题三 剂量段、免疫段 | 改写，并新增 1 段（成簇那段） |
| 中文 问题二 建模 8 段 | 改写为 5 段（多出的 3 段整段删除） |
| 中文 问题三 建模 2 段 | 改写为 4 段（新增 2 段） |
| **其余全部段落** | **一字未动**（已逐段二进制比对：0 处差异） |

同时核过：包内 24 个条目只有 `word/document.xml` 变化，`comments.xml`（导师的批注）、
样式、图片均原样保留；文件已用 LibreOffice 实际打开验证。

中文稿同步重译了——导师只改了英文稿，中文那几段原本还是被删掉的旧版本，不同步的话
录中文版会和英文版讲的不是一回事。

### 最终字数

| | 改后 | 导师版 | 档期语速 |
|---|---|---|---|
| 英文 问题二 建模 | **266 词** | 200 词 | 160 s → **100 wpm** ✅ |
| 英文 问题三 建模 | **207 词** | 181 词 | 该段整体 **141 wpm**（原 133） |

> 2026-10-16 晚按 §9.3 的对齐版重新生成，问题二由 326 词收到 **266 词**。
> 下面的 ⚠️ 仍然有效。

⚠️ **一处与 §4 定稿的差异**：写入时**保留了导师 ¶60 的收尾句**
（*Together, these results connect the third question to a clear conclusion: direct
bacterial delivery works for larger lesions…*），§4 的定稿里没有这句。它是导师自己的
句子、也确实是问题三的收束，所以没有擅自删。**代价是问题三比他的版本多 26 词。**

要严格回到等长，最便宜的一刀就是这句（34 词，删掉后 173 词，比原版还短）——
因为紧随其后的那段（*Across the second and third questions, modeling contributed…*）
已经把同样的话说过一遍了。这一刀留给导师定。

---

## 9. 对照滕院的批注重新检查（2026-10-16，补）

原稿里有 **4 条批注**（`word/comments.xml`，作者 X Teng），之前漏看了。逐条定位后：

| 批注 | 锚在哪 | 原文 |
|---|---|---|
| id 1 | para 24「Against this backdrop…」 | 这里和下面有一个很大的 gap。要先介绍 FLAME 大概是个什么项目，再提出挑战和应对策略 |
| id 44 | para 37–38 湿实验报告段 | 讲主要结论 |
| **id 58 / 59** | **span para 39–48，即旧建模整块** | **原来的 modeling 段落太多技术细节，反而忽略了建模得到的主要结论。我根据徐畅给我的 modeling 文件重新提炼了，这部份你让徐畅也检查一下** |

所以管我们这一块的意见是两条、而且是同一句话：**① 太多技术细节；② 反而忽略了主要结论。**
（另外这也确认了他是**从我们的 modeling 文件提炼的**，并且**本来就要徐畅检查**——即本轮工作。）

### 9.1 逐项对照：我们加回去的，是"结论"还是"技术细节"

| 我们的改动 | 性质 | 对批注 |
|---|---|---|
| 5 处纠错（not a dose problem / 178 vs 150 / SsrA 归因 / 余量没过 10× / εG≤1） | 纠错 | ✅ 与详略无关，必须改 |
| **成簇 125 个**（第二条独立路径） | **主要结论**，而且是他漏掉的那一条 | ✅ 正中"被忽略的主要结论" |
| CT26 需 1.3–1.8× | 主要结论 | ✅ |
| 余量 21.85× → 4.41×，低于 10× | 主要结论（判决） | ✅ |
| εG ≤ 1 时无论通量多大都做不到 | 主要结论 | ✅ |
| "对任何传感器参数都成立" | 结论的强度，不是细节 | ✅ |
| 瓶颈 = 结肠黏膜 21.85× | 结论，且剂量段要用它 | ✅ |
| **probit / 读数饱和（36 词）** | **技术细节（测量尺度）** | ❌ **正是他点名要删的那一类** |
| 留出法的协议叙述 + 四个数字 | 结论是"模型通过了样本外检验"，但我们写成了方法 | ⚠️ 留结论、砍方法 |
| 把他的 "nearly a hundredfold to almost nothing" 换成 87–228× / 约 1× | 他已经用口语把这条结论写好了，我们把它数字化 | ⚠️ 建议回到他的措辞 |
| 那块板（0 % vs 1 % O₂） | 下一步实验，不是结论；他删过一次 | ⚠️ 建议移到答辩清单 |

### 9.2 结论：方向符合，篇幅走反了

**符合的部分是主体**：他说"忽略了主要结论"，我们补回去的成簇、CT26、余量判决、εG 边界，
正是四条主要结论；五处纠错也和详略无关。**这一半是对的，应当保留。**

**不符合的是篇幅**：问题二建模段从他的 **200 词涨到 326 词（+63 %）**，而他的意见恰恰是
"太多技术细节"。上表里 ❌ 和 ⚠️ 的四项加起来约 **60 词**，全部是方法/尺度/下一步，
不是结论。**这四项该收回去。**

### 9.3 对齐版（**已采用，docx 已按此重新生成**）

收完之后：

| | 导师版 | 现在写进 docx 的 | **对齐版** |
|---|---|---|---|
| 问题二 建模 | 200 词 | 326 词（122 wpm） | **266 词（100 wpm）** |
| 问题三 建模 | 181 词 | 207 词 | **210 词**（改动全是结论，基本不动） |

对齐版做了四件事：**删掉 probit/饱和整段**；**留出法压成一句**（只留 98.13 % vs 98.08 %
和 9 h 失败，不讲协议）；**判别力回到他"nearly a hundredfold to almost nothing"的原话**，
只补一个 21.85× 瓶颈；**那块板移到答辩清单**。问题二的四段变成：

> Modeling examined how the two inputs combine, where else the circuit might switch on,
> and whether the model survives a test.
>
> First, it tested whether the AND gate acts as a true product of its inputs. At 24 h the
> four-condition reporter data support multiplicativity; at 9 h they do not. The AND logic
> therefore holds at the endpoint, not mid-course, so early-time ratios should not be
> extrapolated. The model also predicted a condition we had hidden from it — 98.13%
> against 98.08% measured — while the same check at 9 h failed, which is what makes it a
> test.
>
> Second, modeling asked where else the circuit might activate. With the gut lumen
> included, the designed sensors alone are anti-selective there — they respond more
> strongly than in the tumor — and that holds for any sensor parameters. The lumen stays
> off because the native lactate promoter is repressed by glucose and anoxia, which makes
> the colonic mucosa our safety bottleneck, at 21.85×. Replacing it with a de-repressed
> version would collapse tumor-versus-lumen discrimination from nearly a hundredfold to
> almost nothing, destroying the safety argument. We therefore kept the native lldPRD
> promoter and abandoned the planned replacement.
>
> Modeling also identified a geometric safety floor: lesions with a radius below ~178 μm
> have no hypoxic core, so the hypoxia arm cannot be induced and falls back to its basal
> level. This threshold comes from oxygen penetration depth and agrees with histological
> measurements (160–200 μm). Below this size, the circuit cannot be driven by hypoxia, so
> distant disease must be addressed by other means, such as the immune cascade.

**注意第 2、3、4 段现在基本是导师的原句**，我们只动了三处：加"对任何传感器参数都成立"、
加"21.85× 瓶颈"、把 `cannot activate` 改成 `cannot be induced and falls back to its
basal level`（§2.2 那个 178 vs 150 的矛盾），外加一句留出法。**这样他一眼就能看出
我们没有推翻他的提炼，只是补了结论、修了错。**

### 9.4 另两条批注（不属于建模，但顺带说明）

- **id 1（开头 gap）**：他插的 paras 25–27 就是在答自己这条批注，所以 §1 说开头超载时，
  **要砍的是旧的 para 28**（"Developing FLAME requires balancing…"，和他新写的 27 说的是
  同一件事），**不是他新插的 27**。这样既解决 279 wpm，也不违他的批注。
- **id 44（讲主要结论）**：锚在湿实验的报告段，和建模这块是同一条原则——先给结论，
  不要复述测量过程。湿实验那段不是我们动的范围，但值得转告写那段的人。


---

## 10. 对齐版的落地结果（2026-10-16 终稿）

`FLAME_Presentation_Video_建模组回改_1016.docx` 已按 §9.3 重新生成：
**改写 12 段、整段删除 5 段、新增 3 段**，段数 126 → 129。

### 10.1 相对导师原句的逐词 diff —— 沿用他 90% 的原词

| 段 | 导师 | 改后 | 沿用他的原词 | 改动处数 |
|---|---|---|---|---|
| ¶48 开场 | 15 词 | 21 词 | 12/15 | 2（加"模型能否通过检验"的提示） |
| ¶49 AND 门 | 47 词 | 75 词 | **47/47** | 1（只加一句留出法） |
| ¶50 肠腔 | 76 词 | 92 词 | **74/76** | 2（加"对任何参数成立"、加 21.85× 瓶颈） |
| ¶51 178 µm | 62 词 | 70 词 | **61/62** | 1（`cannot activate` → `cannot be induced and falls back to its basal level`） |
| ¶59 剂量 | 47 词 | 60 词 | 24/47 | 5（补 CT26、把"small margin"换成 4.41× 低于 10×、改掉 not a dose problem） |
| ¶60 免疫 | 77 词 | 87 词 | **73/77** | 4（加"不是预测"、加 εG≤1 那半句） |
| **合计** | **324 词** | **405 词** | **291/324 = 90 %** | **15 处** |

> **¶49 / ¶50 / ¶51 / ¶60 是导师的原句加几个从句**，一眼就能看出我们没有推翻他的提炼。
> 改得多的只有 ¶59（剂量段），因为那一段本来就有两处错和两个太软的数。

### 10.2 校验（用 XML 解析做的，不是正则）

- `word/document.xml` **XML 合法**，LibreOffice 打开并重存通过；
- **非建模段落接受修订后文字差异 = 0**；
- **拒绝建模组的修订后，17 个改动段落逐字回到导师版 = 0 处不一致**；
- 颜色：36 处红色删除 / 15 处蓝色新增，`w:color` 在 `rPr` 里的位置全部合规（0 处违规）。

⚠️ 第一轮校验脚本有个 bug 已修正：`<w:del .../>`（pPr 里自闭合的段落标记）被正则当成
成对标签，把中间文字一起吞掉，导致 ¶60 的比对是空比较、假通过。改用 `ElementTree`
按文档顺序走树之后结论不变。顺带确认：`¶60` 在**导师版里段落标记本来就被他删掉了**
（段落会与下一段合并），正文一字未动，我们的版本保持同样行为。
