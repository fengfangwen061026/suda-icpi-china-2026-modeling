# 演讲视频配图 — 上图点与图注

针对 `FLAME_Presentation_Video_建模组回改_1016.docx`。讲稿里刻意略过的数据和技术细节，
都落在这九张图上：**每个建模小节开口的那一句就是上图点**，图在讲完该小节前不撤。

**九张图已经插进 `FLAME_Presentation_Video_建模组回改_1016.docx` 本身**，中英文两版讲稿
各插一遍，图在它的上图点那一段正下方，图注以「【配图 N】」开头。原稿（无图）留在
`.docx-build/FLAME_Presentation_Video_建模组回改_1016_无配图原稿.docx`。
文档里的修订标记（80 处插入 / 85 处删除）**一处没动**，接受或拒绝修订都不影响这些图。

素材：`outputs/video_cues/`（按上图顺序编号，剪辑直接按文件名走）

重建：

```bash
cd ~/Desktop/IGEM/model_v2 && PYTHONPATH=. .venv/bin/python build_video_cues.py && PYTHONPATH=. .venv/bin/python insert_script_figures.py
```

`insert_script_figures.py` 可反复运行：它先把上一次插进去的图和图注删掉再重插，
所以改了图、或在讲稿里改了字，重跑一遍就行，不会插重。

六张沿用 `Modeling.docx` 里已有的图，三张是这次新作的（下表标 **新**）。

---

## 上图表

| # | 文件 | 上图点（英文稿） | 上图点（中文稿） | 这张图在说什么 |
|---|---|---|---|---|
| 1 | `01_circuit.png` | "The hypoxia-responsive promoter pPepT controls LuxI…" | "低氧响应型启动子 pPepT 控制 LuxI…" | 两条传感臂如何汇成一个 AND 门 |
| 2 | **新** `02_and_gate_holdout.png` | "First, it tested whether the AND gate acts as a true product of its inputs." | "第一，建模检验 AND 门是否真是两个输入的乘积。" | 扣掉全开角，用另外三角把它预测出来：98.13 % 对实测 98.08 %；9 h 同法失败 |
| 3 | `03_arms_anti_selective.png` | "With the gut lumen included, the designed sensors alone are anti-selective there…" | "把肠腔计入之后，我们设计的两条传感臂在那里是反向选择的…" | 两条臂单独看，在肠腔的响应**比肿瘤还强**（<1.0 即反向选择） |
| 4 | `04_tissue_axis_bottleneck.png` | "The lumen stays off because the native lactate promoter is repressed…" | "肠腔之所以保持关闭，是因为天然乳酸启动子受葡萄糖与厌氧抑制…" | 加上天然抑制后瓶颈从肠腔移到结肠黏膜，21.85×；去抑制版本会把判别打回近 1× |
| 5 | **新** `05_lesion_floor_178um.png` | "Modeling also identified a geometric safety floor: lesions with a radius below ~178 μm…" | "建模还给出一条几何安全底线：半径小于约 178 μm 的病灶…" | 氧只穿透固定深度，所以小病灶**根本没有缺氧体积**；与组织学 160–200 μm 吻合 |
| 6 | `06_dose_vs_margin.png` | "First, modeling compared dose requirements with safety margins." | "第一，建模把所需剂量与安全余量放在一起比较。" | 杀伤约按剂量三次方走；够到 150 μm 病灶要 4.95× 剂量，黏膜余量被花到 4.41×，**低于图上那条 10× 要求线** |
| 7 | `07_micrometastasis_cluster.png` | "A second model, built on completely different data, hits that same wall…" | "另一个建立在完全不同数据上的模型，从另一侧撞上同一面墙…" | 125 个微转移灶聚在一起仍低于群体感应开启阈值——加剂量解决不了 |
| 8 | `08_immune_feasibility.png` | "Finally, modeling explored whether an immune response could extend the effect…" | "最后，建模考察了免疫反应能否把作用延伸到远处病灶。" | 可行性边界 εG = 1，以及最大可治负荷——所以早治比加量重要 |
| 9 | **新** `09_contribution.png` | "Across the second and third questions, modeling contributed…" | "围绕第二和第三个问题，建模贡献了…" | 实测数据进 → 五个问题 → 项目真正据此做的决定 |

分时对照：图 1 落在 02:06–03:32；图 2–5 落在 03:32–06:12（问题二建模段）；
图 6–9 落在 06:12–09:19（问题三建模段）。

---

## 剪辑备注

- **图 2 左右两块可以分两次推**：先给 2×2 的四个角（让观众知道"角"是什么），
  念到"predicted a condition we had hidden from it"时再推右边的预测-实测散点。
  若时间紧，只用右半张也成立。
- **图 4 的落点是绿色那组**，不是蓝色。念"肠腔之所以保持关闭"时，镜头给
  `Colonic mucosa` 那一行——21.85× 就是讲稿里的安全瓶颈数字。
- **图 5 左半张（两个圆）是给非专业观众的**，右半张给评委。两块都留着，
  念"半径小于约 178 μm"时观众看左边就够。
- **图 6 的 4.41× 和 10× 要求线已经画在图里了**，不需要叠层：右 panel 橙色虚线就是
  10× 要求，150 μm 那个点被圈出并标注"costs 4.95× dose and leaves 4.41× — under the
  line"。念到"低于我们自己要求的 10×"时镜头推右 panel 左下角即可。
- **图 9 没有数据**，纯粹是收口用的结构图；如果这一段要压时间，它是最先能砍的一张。

## 没有配图的建模句子

- "SsrA 提供了值得进一步研究的蛋白稳定性控制手段"——SsrA 的建模结论在模块 3.4，
  但讲稿这一句是湿实验口径，建议配湿实验的 PI 染色图而不是建模图。
- 灵敏度分析（`fig3_5_sobol_drivers.png`，在 `outputs/figures/`）**这次没有上图点**，
  因为 1016 稿把这一段剪掉了。留作答辩问答时的备用图：它回答的是"21.85× 这个数字
  由什么决定"。
