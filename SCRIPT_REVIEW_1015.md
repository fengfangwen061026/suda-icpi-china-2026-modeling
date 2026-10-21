# 建模组对导师重写稿的核对（2026-10-16）

**导师版**：`FLAME_Presentation_Video_最终版_中英文-XT.docx`，修订作者 X Teng，
2026-10-15 22:54 / 23:08 两批修订。英文稿里插入 6 段建模、删除 8 段。
**我们交上去的基线**：`建模讲稿_PresentationVideo.docx`（2026-10-13 22:32）。
**基线之后又改过的**：`WIKI_DRAFT.md` → `Modeling.docx` / `modeling_wiki.html`
（2026-10-14 换传感器先验，见 `PENDING_AFTER_PRIOR_SWAP.md`）。

导师留言：

> 建模我觉得没有抓住重点，我重新提炼了一下，但是让建模组再看一下，不知道我理解的对不对。

全部数字已对 `model_v2/` 逐条核过，`328 passed, 1 skipped`（2026-10-16 复跑）。

---

## 0. 一句话结论

**导师理解得对，而且他提炼的其实就是我们 wiki 自己那段 "What the model decided"——
六条决策，按顺序读下来，一条对一段。** 判断全部成立，数字用的是**换先验之后的新值**
（见 §1），所以基线也是对的。

需要动的是 **5 处错误**（1 处字面意思相反、1 处会被听成自相矛盾、1 处归因挂错了结论、
2 处数字太软），以及 **4 件该强调却整段消失的东西**（§3）。

最值得注意的一点：**导师漏掉的，正好是我们 wiki 的 headline 里也没有的东西**——
第 4 章（留出法验证）和 §3.2（微病灶成簇）在那六条里一个字都没有。
**所以这不是导师漏看，是我们自己的摘要没把它们列进去。**（见 §5）

---

## 1. 先确认一件事：导师读的是哪一版

他读的是**更新后的 wiki**，不是我们交的那份 docx。证据：

| 导师写的 | docx（10-13）附录 A | 更新后的 wiki | 判定 |
|---|---|---|---|
| "about five times more dose" | **14.46×**，口播说"几乎花光" | **4.95×** | 用的是新值 ✅ |
| "leave only a small safety margin" | 剩 **1.36×** | 剩 **4.41×** | 新值 ✅ |
| "nearly a hundredfold" | **46–121×** | **87–228×** | 新值 ✅ |
| "met at the lowest dose tested" | 同 | wiki headline #6 近乎原话 | — |
| "micrometastasis is not a dose problem" | docx 没有这句 | wiki headline #6 **原话** | — |

**结论：导师的数字基线是对的，我们那份 docx 的附录 A 反而是过期的**（换先验前）。
顺带已修正 `PRESENTATION_VIDEO_MODELING.md` 附录 A 那一行（14.46× / 1.36× →
4.95× / 4.41×），并把口播里"几乎花光安全余量"改成"压到 10× 要求以下"——换先验后
不能再说"几乎花光"。

**六条决策的对应关系**（这也说明了他为什么漏掉那几样）：

| wiki headline | 导师第几段 | 情况 |
|---|---|---|
| 1 AND 门是否真是乘积 | ¶2 | ✅ 但丢了留出法（headline 里它只是 #1 的一个从句） |
| 2 还在哪里开（黏膜 21.85×，腔内全部 < 1.0） | ¶3 前半 | ⚠️ 没点名瓶颈位点，也没给 21.85× |
| 3 能不能去掉乳酸启动子的抑制 | ¶3 后半 | ✅ 完全正确 |
| 4 多小的病灶低氧臂点不着（178 µm） | ¶4 | ✅ 正确，但说轻了 |
| 5 SsrA 留还是去 | ¶5 | ❌ 挂错了结论（见 §2.3） |
| 6 需要多大剂量 | ¶6 + ¶7 | ⚠️ 两个数太软，且只剩一条路（见 §3.2） |
| （headline 里没有）第 4 章 留出法验证 | — | ❌ 整段消失 |
| （headline 里没有）§3.2 微病灶成簇 | — | ❌ 整段消失 |

---

## 2. 五处错误

### 2.1 ⛔ "So micrometastasis is not a dose problem." —— 英文字面意思相反

这句是 wiki headline #6 的原话，**所以不是导师读错，是我们自己这句中译英不保真**。
中文"不是剂量问题"的意思是"**不是靠加剂量能解决的问题**"；英文 `not a dose problem`
听起来是"**剂量没问题**"——而结论恰恰是剂量正是在这里撑不住（余量 4.41× < 要求 10×）。
紧接着下一段又说"所以只能靠免疫"，评委会觉得前后不搭。

**改**：`So micrometastasis is not a problem a larger dose can solve.`
**wiki 那句也要一起改**（§ headline #6），否则同样的坑留在页面上。

### 2.2 ⛔ 178 µm 那段和 150 µm 那段会被听成自相矛盾

¶4 说半径低于 178 µm"没有缺氧核，低氧臂**无法激活**"；一分多钟后 ¶6 说"够到
**150 µm** 病灶要约 5 倍剂量"。150 < 178，评委会立刻问：刚说开不了，怎么又算出剂量？

我们模块里是自洽的（`MODULE_4_6.md` §5.3）：低于穿透深度时低氧臂**落到基础表达 $b_O$
而不是零**，所以倍数**大但不发散**，2.82× 就是踩在这点基础泄漏上算出来的。**口播稿里
没有这半句，桥就断了。**

**改**（建议第一个）：
1. ¶4 把 `cannot activate` 改成 `cannot be induced and falls back to its basal
   level`（+6 词），矛盾自动消失；
2. 或把 ¶6 的例子从 150 µm 换成 **180 µm**（上调 4.33×、余量 5.05×，结论不变，
   且 180 > 178 无歧义）。

### 2.3 ⛔ SsrA 那段把决策挂在了错的结论上（这是新发现的一处）

导师写："**88.5 % 来自减少总量而非限制扩散 → 所以支持把 SsrA 保留为稳定性控制而不是
空间屏障。**"

前半句**完全正确**（`MODULE_4_3_4_5.md` §5.2：88.5 % 少做 / 11.5 % 空间约束）。
但**后半句是把两个不同的结论接在了一起**：

- 88.5 % 这个结果回答的是"**脱靶降低是怎么来的**"（机制分解），它**不是**留/去的判据；
- "SsrA 该留"的判据是另一条，闭式且不依赖剂量–响应函数形式：
  $r_{\text{potency}} < 1/r_{\text{biomass}}$（损失的效力 < 换来的生物量），
  三个剂量全部满足，余量 **1.21–1.93×**（`MODULE_3_4.md` §7.1）；
- 而且我们的结论比"稳定性控制"**更强**：ClpXP 饱和让这个标签**放大**启动子的选择性，
  所以它是"**足够的安全阀，不是辅助**"（`MODULE_3_4.md` §7.4，式 3.4-6）。wiki
  headline #5 的原话是 *the degron amplifies selectivity rather than merely damping
  output*。
- 还有一层最该讲的：**这个决策之前是"符号不定"的**。9.23 把 SsrA 的效力代价记成
  1.41–4.70 的区间，两端结论相反。我们用数据一致性规则撤掉了 4.70×（它和被撤的
  11.4× 选择性指数犯的是同一个跨区块错误），**撤完之后 SsrA 才从"符号不定"变成
  "定案保留"**（`MEETING_BRIEF.md` §219、§876）。

**改**：保留 88.5 % 这句（它本身是对的、也好听），但把结论句换成真正的判据；若有时间，
加一句 ClpXP 放大。另外把六条第 2 条点名要的那个数补上：**带标签在正常组织半衰期
≈ 1.61 h，不带标签 8.66 h**——现在导师版里一个数都没有。

### 2.4 ⚠️ 剂量段两个数太软，且漏了 CT26

| 导师写的 | 实际 | 说明 |
|---|---|---|
| "met at the lowest dose tested" | ✅ 对，而且**有 4.3 倍余量，是直接比较不是外推**（6 OD 实测净杀伤 2.967 % vs 人 CRC 最苛刻需求 0.691 %） | 可以说得更硬 |
| （没提 CT26） | ❌ **CT26 需 1.30–1.76× 最高实测剂量** | 不补有风险：我们自己的小鼠细胞数据没达标，评委对着 wiki §3.4 一看就是坑。补上反而加分——"在小鼠不够不等于在人不够"，CT26 倍增比人 CRC 快两个数量级 |
| "leave only a small safety margin" | ❌ 太软。**21.85× 被吃到 4.41×，低于我们自己定的 10× 要求** | "small margin" 听着像"还行"，实际是**没通过**；照实说更可信 |
| "about five times more dose" | ✅ 对（4.95×） | 由 2.82×（尺寸）× 1.757×（CT26 需求）复合而来，口播不必拆 |

### 2.5 ⚠️ 免疫段漏了最硬的那半句

导师写了 "must exceed a certain gain"，但漏掉**不等式那一半**：$\varepsilon G\le 1$ 时
**无论焦亡通量多大都做不到**（`MODULE_6.md` §7.2，式 6-4，是不等式不是估计）。这是
第 6 章唯一一条"参数怎么扫都成立"的结论，也最能说明我们没把免疫当万能解药。8 个词的事。

---

## 3. 被删掉的八段里，有四件该强调的东西整段消失了

导师删的八段，**六段该删**——"this computation addresses a different question from the
reporter assay""examining how conclusions depend on the assumed setting"这类确实空泛，
删得对。但下面四件不该丢，按**性价比**排序（括号里是加回的时长成本）：

### 3.1 留出法验证（+20 秒）—— 最该加回的一件

28 次留出；三个角预测第四个角 **98.13 %**，实测 **98.08 %**；同样的检验在 **9 h 四次
全败、6 h 也四次全败**，正如预期。

这是整段建模里**唯一**回答"你怎么知道模型不是画了条好看的曲线"的内容，iGEM 评委明确
看这一项（Best Model 的判据就写着 model validation）。**而且故意带上失败的那次，比只
报成功的更可信**——"一个什么都能通过的检查不算检查"。导师版删掉之后，建模段落里**没有
任何一句说我们验证过模型**。

### 3.2 两条独立路径撞上同一面墙（+25 秒）—— 失去的是论证结构

导师版的结论是"远端病灶只能靠免疫"，但只给了**一条**理由（剂量余量不够）。我们原稿
是**两条完全不同数据上的路径撞到同一结论**：

- 群体感应**在微病灶里根本开不起来**：哪怕 **125 个** 150 µm 病灶聚成一簇，等效半径
  只有 **651.7 µm**，仍低于 ON 阈；要达到 ON 需要 **512 个相切**，那是一块
  **2.1 mm 的连续团块**——单病灶模型本来就说它会开（`MODULE_4_4.md` §5）；
- 剂量方向：硬提剂量去够它，余量从 21.85× 掉到 4.41×。

**"两条独立的路，一个结论"才是"免疫级联是必需而不是加分项"的论证力所在。** 只剩一条
路时，这句话听起来像是我们没办法了才去讲免疫。

### 3.3 读数饱和 / probit 这一层（+15 秒）

导师版直接说"24 h 数据支持乘性"。但 wiki 上摆着的原始荧光是**双输入只有 226.6×，
乘性门预期 2768×，差 12.2 倍**——评委对着原始数据会认为我们在说谎。必须有半句说明
读数饱和、换到 probit 尺度后四个角才自洽（`MODULE_2_2.md` §7.1）。

附带：这一段还有一个我们最得意的"模型反过来改实验"的例子——**所需的单细胞分布本来
就躺在原始流式文件里，不用新做实验，重新导一次就行**。

### 3.4 瓶颈位点与 21.85×（+8 秒）

导师版从头到尾**没点名安全瓶颈是哪个位点**，却在 ¶6 里花它（"small safety margin"）。
"余量"没有被赋值过，听众不知道在花什么。一句话补上：**瓶颈是结肠黏膜，21.85×**
（wiki headline #2）。

**另外两件可选的**（wiki 上有、两份稿子都没讲，口播不一定放得进去，但**问答一定会用到**）：

- **我们否决了自己的一个计划**：原本要换一个去抑制、经低氧优化的乳酸传感器，为了瘤内
  表达更强；算完之后取消。同时定下了**唯一能让结论变号的那块板**：乳酸启动子单独测，
  0 % 对 1 % O₂。（docx ④ 段有，导师版删了）
- **我们撤回了自己已经发表过的数**：11.4× 和 2.97× 两个选择性指数分子分母跨了实验
  区块，已撤回；唯一合法的是区块内配对的 **3.33×（p < 0.001）**。是我们自己的一致性
  检查查出来的，不是别人提的。（wiki §1.4 / §5.1）
  ⚠️ **PPT 和旧材料里若还印着 11.4×，录视频前必须换掉**，否则 wiki 和片子对不上。

---

## 4. 换先验之后新出现、两份稿子都没有的两件事

这两件是 10-14 之后进 wiki 的，`建模讲稿_PresentationVideo.docx` 里没有（时间上来不及），
导师也没从 wiki 的 headline 里拿到（headline 只在末尾一段提了一句）。
**它们是整页里最强的两个"诚实度"信号，建议至少写进 wiki 的 Contribution/Reflection，
口播放不进去也不吃亏。**

1. **我们换掉了自己的两个继承参数，因为文献里有实测而我们的先验和它不一致**
   （`WIKI_DRAFT.md` §2.5）。Sobol 指出 $K_{O_2}$ 和 $n_Q$ 是决定余量的两个参数；
   两个都有已发表测量，**两个都和继承先验不符**，于是 2026-10-14 换成实测值
   （$K_{O_2}$ 1.0 % → **0.49 %**；$n_Q$ 2.0 → **1.0**）并重算全页。
   这正是 §1 里那些数字变动的来源。**没有一条结论翻转**，只是 150 µm 那一行从
   "余量一点不剩"缓和成"剩 4.41×，仍低于 10×"。
2. **我们撤回了自己发表过的三个比值**（11.4×、2.97×、4.70×），都是跨实验区块配的
   分子分母。撤掉 4.70× 的副产品是：**SsrA 的决策从"符号不定"变成"定案保留"**。

---

## 5. 一条反过来的意见：我们的 wiki headline 该补两项

导师的六段 = 我们 wiki "What the model decided" 的六条。**他漏的两样，headline 里也
没有独立列出**：第 4 章的留出法验证（只作为 #1 的一个从句出现），和 §3.2 的微病灶成簇
（完全没有）。

**任何人读那段摘要都会漏掉同样的两样东西。** 建议在 headline 里加两条（或把 #1 拆成
两条），否则这个问题还会在别人身上重演一次：

> **7 · 模型自己通不通得过考试？** 28 次留出，三角预测第四角 98.13 % / 实测 98.08 %，
> 而 6 h 与 9 h 的同一检验四次全败——协议有鉴别力，不是什么都放过。
> **8 · 微病灶成簇能不能凑够阈值？** 不能。125 个只到等效 651.7 µm；要 512 个相切、
> 2.1 mm 连续团块才到 ON。与 §3.5 的剂量路径独立同向 → §3.6 是必需而非点缀。

---

## 6. 可以直接替换的英文定稿

在导师版基础上改，保留他的段落切分、First / Second / Finally 的推进方式和全部正确判断。
约 **450 词**（导师版约 300 词，**+150 词 ≈ +60 秒**）。

**时长卡死时的砍段顺序**（从后往前砍）：① 先砍 SsrA 半衰期那半句 → ② 再砍第 2 段最后
的留出法 → ③ 最后砍成簇那段。**§2 的五处错误全部必改，与时长无关。**

> Modeling examined how the two inputs combine, where else the circuit might switch on,
> and how much dose a lesion actually needs.
>
> First, it tested whether the AND gate acts as a true product of its inputs. Read
> straight off the raw fluorescence it looks far too weak — but that is because two of
> the four conditions were saturating. Once the readings are placed on a probit scale the
> four corners become consistent again: at twenty-four hours the interaction term is zero
> within error, so the gate is multiplicative; at nine hours it is not. The AND logic
> therefore holds at the endpoint, not mid-course, so early-time ratios should not be
> extrapolated. We also tested this by hiding data from the model: given three corners it
> predicted the fourth at ninety-eight point one three percent GFP-positive, against
> ninety-eight point zero eight measured — and the same check at nine hours failed, four
> times out of four, exactly as we expected it to.
>
> Second, modeling asked where else the circuit might activate. The colon lumen is
> strictly anaerobic and it carries lactate, so the two sensors we designed are
> anti-selective there — they respond more strongly than in the tumor — and that holds
> for any sensor parameters. What keeps the lumen quiet is something we did not design on
> purpose: our lactate sensor is the native lldPRD promoter, so it still carries its own
> glucose and anaerobic repression. With that repression the gate discriminates tumor
> from lumen by roughly ninety- to two-hundred-fold, and our safety bottleneck becomes
> the colonic mucosa at twenty-two-fold; with a de-repressed version luminal
> discrimination falls to about one, destroying the safety argument. We therefore kept
> the native promoter and abandoned the planned replacement — and put the single plate
> that could overturn this, the promoter on its own at zero versus one percent oxygen, at
> the top of our experimental list.
>
> Modeling also identified a geometric safety floor: lesions with a radius below about
> one hundred and seventy-eight micrometres have no hypoxic core, so the hypoxia arm
> cannot be induced and falls back to its basal level. This threshold is pure geometry
> from oxygen penetration depth, with no fitted parameters, and it agrees with
> histological measurements of the same quantity, one hundred and sixty to two hundred
> micrometres — the one parameter in this project where an independent measurement
> confirms a value we derived another way.
>
> *(…第三个问题的湿实验段落不变…)*
>
> Modeling added a separate perspective on activity.
>
> First, it settled whether to keep the SsrA degron. The criterion is closed-form and
> needs no assumed dose-response shape — the potency we lose has to be smaller than the
> biomass we gain — and all three doses clear it. We also asked where the degron's safety
> benefit actually comes from: about eighty-eight percent of it comes from making less
> protein, and only twelve percent from limiting how far it spreads. So the tag earns its
> place as a stability control rather than a spatial barrier, and it puts a number on
> normal tissue: with the tag, the effector's half-life there is about one point six
> hours, against eight point seven without it.
>
> Second, modeling compared dose requirements with safety margins. The human indication
> is met at the lowest dose we tested, with about four-fold to spare — a direct
> comparison, not an extrapolation. CT26 in mice, which doubles two orders of magnitude
> faster, needs one point three to one point eight times our highest. But reaching a one
> hundred and fifty micrometre lesion takes about five times more dose, and that spends
> the mucosa margin from twenty-two-fold down to four — below the tenfold we set
> ourselves.
>
> And a second model, built on completely different data, hits that same wall from the
> other side: quorum sensing cannot switch on inside a micrometastasis at all. Even a
> hundred and twenty-five of them clustered together stay below the threshold; it takes
> five hundred and twelve touching lesions, a contiguous mass two millimetres across, to
> reach it. So micrometastasis is not a problem a larger dose can solve.
>
> Finally, modeling explored whether an immune response could extend the effect to
> distant lesions. It gives a feasibility boundary rather than a prediction: in MSS and
> pMMR tumors the cascade has to clear a minimum gain — below that, no pyroptotic flux
> whatsoever is enough — and above it there is still a maximum treatable burden, so early
> treatment matters more than larger doses. Together, these results connect the third
> question to a clear conclusion: direct bacterial delivery works for larger lesions,
> while distant disease must rely on the immune response, which remains to be tested.

---

## 7. 四件程序性的事

1. **中文稿还没同步。** 导师只改了英文稿；中文稿第 99–106、112–113 段仍是被删掉的那版
   旧文字（"我们从四条件报告系统数据出发……接近饱和的响应，使测量尺度变得重要"）。
   录中文版前必须按 §6 重译，否则两版内容不是一回事。
2. **wiki headline #6 那句 "micrometastasis is not a dose problem" 要一起改**
   （见 §2.1），页面上和片子里是同一个坑。
3. **wiki headline 建议补两条**（见 §5），否则下一个读摘要的人还会漏掉同样两样。
4. **PPT / 旧材料里若还有 11.4× 或 2.97× 的选择性指数，录制前必须换成 3.33×**
   ——这两个数已在 wiki §1.4 公开撤回，片子里再出现就是自相矛盾。
   ⚠️ 若要在片子里讲 TAT 被去掉（脱靶 ×7.0 换效力 ×1.33），注意 L929 的
   `GSDMD-TAT` 只有 n = 2 且两值都是 10.0、标准差为 0：**说"7 倍"可以，不要说
   "显著"**（`DATA_CONVENTIONS.md` 约定 3）。
