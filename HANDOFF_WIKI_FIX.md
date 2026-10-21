# 交接：wiki 建模页 5 处数字修正

**2026-10-20。** 对 https://2026.igem.wiki/suda-icpi-china/ 的 7 个建模页做了全量复算。

**结论先说：模型计算没有错。** 所有由代码产出的表格都复现得上，多数到 4–5 位有效数字
（b=2.65078、A=0.0250985、r²=0.9956、d_crit=23.08、R_eq=333.3/400.6/651.7/1009.8 µm、
六个 per-construct 指数连 r² 一字不差、承载量 2.6133/2.3600/1.5667/1.5067、
测量总数 391=192+48+48+62+41）。

**下面 5 处全部在散文句子里**，不在任何表格里，也不进入任何下游计算。原因是
`tests/test_wiki.py` 的 guard 只校验表格、公式、图、引用，不校验句子里手写的数字。

改完后请顺手检查：不要改动任何表格里的数值，它们都是对的。

---

## 1. 「AHL 占 6.5× 权重」→ **7.0×**

**页面**：`/model/safety/`（Lesion-size calculation）和 `/model/spatial/`（Micro-lesion
field superposition）各出现一次。

**现文**（safety 页）：
> **The AHL term carries 6.5× the weight of the hypoxia term** — the size switch is fundamentally a *volume integrator*

**现文**（spatial 页）：
> This agrees with §2.2, where AHL integration carried 6.5× the weight of the hypoxia term.

**改为**：两处 `6.5×` → `7.0×`

**依据**：同页表格给的是低氧体积 **5.293×** × AHL 积分 **36.907×** = **195.4×**。
36.907 / 5.293 = **6.97**，不是 6.5。表里的三个数都对，错的只有这句口算。

**同时要改**（否则下次重建会回退）：
- `MODULE_3_2.md:126`、`:181`、`:234` —「6.5 倍」→「7.0 倍」
- `MODULE_4_4.md:53` —「6.5 倍权重」→「7.0 倍权重」
- `WIKI_DRAFT.md:741`、`:1450`

---

## 2. 「overestimate of 9.47×」→ **8.88×**

**页面**：`/model/safety/`，Lesion-size calculation 末尾的 ⚠️ 框。

**现文**：
> Our free-field kernel has no boundary sink, giving a signal fold of 195.4× against last cycle's 22× — an overestimate of **9.47×**

**改为**：`9.47×` → `8.88×`

**依据**：195.4 / 22 = **8.88**。而且 `MODULE_3_2.md:201` 里算的就是 8.88：

```
$$\frac{195.37}{22.0}=\mathbf{8.88\times}\ \text{高估}$$
```

模块原文正确，是 `WIKI_DRAFT.md:753` 转抄时写错的。**只需改 wiki 侧。**

---

## 3. 「1 % oxygen with lactate」→ **without lactate**（最该改的一处）

**页面**：`/model/`（Gate Calibration），Experimental data and readout handling 一节。

**现文**：
> One group — **1 % oxygen with lactate** at 24 h — reads 40433, 32134 and 0; we print all three, because a mean with an SD would imply a noise model that is not there.

**改为**：`1 % oxygen with lactate` → `1 % oxygen without lactate`
（或写成 `the 1 % O₂ single-input corner`）

**依据**：这三个值出自 Excel 区块 3 的 F–H 列，表头 `1% - `，即 **1% 氧、无乳酸**
（corner B）。1%+20 mM（corner D）那组 24 h 读的是 339382 / 344385 / 328229，
均值 **337,332**——正是同一页「intensity 1.33× (253,571 → 337,332)」里的那个数。

页面自身即可证伪：corner D 的阳性率是 98.3 / 98.9 / 96.4 %，不可能对应一个含截断孔
的强度组；而 40433 / 32134 / 0 配的阳性率正是 **31.9 / 31.3 / 31.9**，即页面 corner B 那行。

源文件标得是对的，**只需改 wiki 侧**：
- `DATA_CONVENTIONS.md:28` → `| 1% − | 24h | 40433, 32134, 0 | 31.9, 31.3, 31.9 |` ✅
- `MEETING_BRIEF.md:592` → 「1% 氧，**无乳酸**」✅
- `WIKI_DRAFT.md:2272` ❌ 写成了 `with lactate`

---

## 4. 「0.84–0.95×」→ **0.84–0.89×**

**页面**：`/model/spatial/`，Micro-lesion field superposition 末尾。

**现文**：
> **Dispersing a given burden always produces less centre signal than compacting it (0.84–0.95×)**

**改为**：`(0.84–0.95×)` → `(0.84–0.89×)`

**依据**：数值本身没错，但 wiki 上这张表只留了 4 行（4→0.842、8→0.837、27→0.890、
125→0.869），**显示范围的上界是 0.890**。0.945 来自源表 `MODULE_4_4.md:178` 的
n=13 那一行，建 wiki 表时被删掉了，于是正文引了一个页面上查不到的上界。

> 备选方案：把 n=13 行补回 wiki 表，保留 0.95。但 n=13 是 FCC 首壳、与其余行的立方
> 点阵不同构，补回去反而不整齐——**建议改数不补行**。

只需改 `WIKI_DRAFT.md:1583`，`MODULE_4_4.md` 的原文（含完整表）不用动。

---

## 5. 「7.6-fold apart for every construct」→ 改成区间

**页面**：`/model/efficacy/`，Paired data and batch handling。

**现文**：
> Blocks 5 and 6 sit about **7.6-fold apart for every construct** measured independently in both

**改为**：
> Blocks 5 and 6 sit **3.3–14.8-fold apart (geometric mean 7.6×)** for the constructs measured independently in both

**依据**：两块都独立测过的四个构建体，区块 5（10 OD）/ 区块 6（ct26）：

| 构建体 | 区块 5 | 区块 6 | 比值 |
|---|---|---|---|
| EcN | 3.600 | 0.300 | 12.0× |
| gfp | 4.233 | 0.733 | 5.8× |
| gfp-TAT | 8.367 | 0.567 | 14.8× |
| GSDMD-SsrA | 15.800 | 4.767 | 3.3× |

几何均值 7.63×（= 1/0.131，与 `DATA_CONVENTIONS.md:78` 一致），但**单个构建体跨
3.3×–14.8×**，「每个构建体都约 7.6 倍」不成立。源文件本身就是按区间写的
（`DATA_CONVENTIONS.md:79` 写「压低系数 0.131–0.302」），是 `WIKI_DRAFT.md:2283`
把区间硬化成了点值。

---

## 不要改的东西

- 任何表格里的数值。全部复算通过。
- Validation 页「t ≤ 12 h 外推 24 h 平台高估 5.0%」及预报比 0.58712 / 0.88809。
  我用单分子律复现不出同样的数，但这取决于原作用的是 Gompertz 还是逐复孔拟合，
  **方法未知不等于算错**，不在本次修正范围内。
- 「the low measurement is 55 % of the other two」（14.3 / 26.35 = 54.3%）。
  若按 14.3 / 26.0 则正好 55%，属可接受的取整，不必动。

## 影响评估

5 处都不承重，**没有一处改变任何结论**：6.5 还是 7.0，结论都是「尺寸开关主要是体积
积分器」；9.47 还是 8.88，结论都是「自由场高估了，绝对值用 22×」；#3 是条件标签；
#4、#5 是措辞精度。进入下游计算的量全部在表里，而表都是代码出的、都有 guard、都对。

## 根因（给维护者）

`tests/test_wiki.py` 的 52 个测试守表格不守句子，而 `numpy / scipy / pandas / pytest /
matplotlib / SALib` 在原机器上一个都没装，这套 guard 从未执行过。链条
代码 → 表 → `MODULE_*.md` → `WIKI_DRAFT.md` → HTML 每跳手抄一遍，**只有句子这一层
是裸的**。#2 #3 #5 只存在于 `WIKI_DRAFT.md`、模块原文都对，即三处都是英文转抄阶段
新引入的。长期办法是给散文里的「A×B=C」「X 占 Y 倍」这类句子也加断言，从表值重算，
而不是手写数字。
