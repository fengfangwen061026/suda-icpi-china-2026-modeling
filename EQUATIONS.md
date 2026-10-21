# 方程总表

全项目方程的唯一编号来源。模块文档引用时写"式(4.6-4)"，**不重复推导**。
编号规则 `(章.节-序)`。每条给出：方程、符号定义、证据等级、代码位置。

格式约定见 [`DOC_STANDARD.md`](DOC_STANDARD.md)。参数数值见
[`config/parameters.csv`](config/parameters.csv)（36 行，`src/parameters.py` 逐行
与代码常量对账，漂移即测试失败）。

---

## 第 2 章 Calibration — 把本队数据变成参数

### 2.2 AND 门的乘性检验（probit 反演）

细胞内对数表达量设为正态 $\mathcal N(\mu,\sigma^2)$，流式阈值固定在 $\theta$，
则阳性率

$$p = \Phi\!\left(\frac{\mu-\theta}{\sigma}\right) \tag{2.2-1}$$

反解单个角点的均值：

$$\mu = \theta + \sigma\,\Phi^{-1}(p) \tag{2.2-2}$$

两角点间的倍数：

$$\text{fold} = \exp\!\big(\sigma\,\Delta z\big),\qquad \Delta z = \Phi^{-1}(p_1)-\Phi^{-1}(p_2) \tag{2.2-3}$$

乘性判据——probit 单位下可加，即二阶交互项为零：

$$\Delta z_{AB} - \Delta z_{A} - \Delta z_{B} \;=\; 0 \tag{2.2-4}$$

| 符号 | 含义 |
|---|---|
| $p$ | 流式阳性率（实测） |
| $\Phi$, $\Phi^{-1}$ | 标准正态 CDF 与其反函数（probit） |
| $\mu$ | 该条件下细胞群对数表达均值 |
| $\theta$ | 流式门阈值，各条件相同，可消去 |
| $\sigma$ | 细胞间表达离散度，**本数据集不可辨识** |

> **关键**：式(2.2-3) 的**倍数**与 $\sigma$ 成正比，故 17.4×、642× 这类数字只能
> 作为 $\sigma$-条件结论报告；式(2.2-4) 的**乘性判据**与 $\sigma$ 完全无关，
> 这才是可以向外报的结论。代码：`src/gate.py`。

### 2.3 生长层

Gompertz：

$$N(t) = K\exp\!\big(-b\,e^{-c t}\big) \tag{2.3-1}$$

饱和指数（备择模型，用于检验"失拟是否来自形状"）：

$$N(t) = K-(K-N_0)e^{-k t} \tag{2.3-2}$$

拟合优劣以 RMSE 计：

$$\mathrm{RMSE}=\sqrt{\tfrac1n\sum_i\big(N(t_i)-y_i\big)^2} \tag{2.3-3}$$

$K$ 为承载量（OD），$b,c$ 为形状参数，$N_0$ 初始 OD，$k$ 速率（1/h）。

> **两式的结构差别就是诊断工具**：式(2.3-1) 的最大增速在**内部拐点**，式(2.3-2) 的在
> $t=0$。若数据的最大增速在 $t=0$，前者**结构上**拟不出来。

**失拟定位量**——去掉 $t=0$ 一个点后的改善倍数：

$$\mathcal J=\frac{\mathrm{RMSE}_{\text{含}\,t=0}}{\mathrm{RMSE}_{\,t\ge1\text{h}}} \tag{2.3-4}$$

**两相速率**：

$$v_{0\to1}=\frac{y_1-y_0}{t_1-t_0},\quad
v_{1\to24}=\frac{y_{24}-y_1}{t_{24}-t_1},\quad
\text{ratio}=\frac{v_{0\to1}}{v_{1\to24}} \tag{2.3-5}$$

**暴发保留率**——同培养基、同氧条件下诱导孔相对**自身未诱导对照**的首小时暴发：

$$\mathcal B=\frac{v_{0\to1}(\text{诱导})}{v_{0\to1}(\text{未诱导})} \tag{2.3-6}$$

**承载量与区间**（$n=3$，故 $t_{0.975,\,\mathrm{df}=2}=4.3027$）：

$$K=\bar y_{24},\qquad
\text{半宽}=t_{0.975,2}\frac{s}{\sqrt n},\qquad
\text{相对精度}=\frac{\text{半宽}}{K} \tag{2.3-7}$$

代码：`src/growth.py`。代入见 `MODULE_2_3.md` §4。

> 下游**不使用拟合曲线**：模块 3.1 的位点密度与模块 3.4 的底盘代价都取
> **实测 24 h 承载量**，所以 0→1 h 的失拟没有传播路径。

---

## 第 3 章 Safety — AND 门守得住吗

### 3.1 三条臂与位点倍数

乳酸臂（lldPRD/LldR，**随乳酸单调递增**）：

$$f_L(L) = b_L + (1-b_L)\,\frac{L^{\,n_L}}{EC_{50}^{\,n_L}+L^{\,n_L}} \tag{3.1-1}$$

低氧臂（pPepT/FNR，**随氧单调递减**）：

$$f_{O}(C) = b_{O} + (1-b_{O})\,\frac{K_{O_2}^{\,n_O}}{K_{O_2}^{\,n_O}+C^{\,n_O}} \tag{3.1-2}$$

群体感应臂。本回路中 `LuxI` 位于 `pPepT` 之下（**不**在 `pLux` 之下），故 AHL
产量不依赖 AHL 浓度，信号正比于"低氧活性 × 菌密度"：

$$Q \;\propto\; f_O(C)\cdot N,\qquad
\text{quorum arm} = \left(\frac{Q_{\text{tumour}}}{Q_{\text{site}}}\right)^{\,n_Q} \tag{3.1-3}$$

位点总倍数（相对瘤核）：

$$\mathcal R(\text{site}) =
\underbrace{\frac{f_L(L_t)}{f_L(L_s)}}_{\text{乳酸臂}}\cdot
\underbrace{\frac{f_O(C_t)}{f_O(C_s)}}_{\text{低氧臂}}\cdot
\underbrace{\left(\frac{f_O(C_t)N_t}{f_O(C_s)N_s}\right)^{n_Q}}_{\text{群体感应臂}}\cdot
\underbrace{\rho_{\text{anox}}\rho_{\text{glu}}}_{\text{天然抑制}} \tag{3.1-4}$$

| 符号 | 含义 | 等级 |
|---|---|---|
| $L$ | 乳酸浓度 (mM) | 位点表 |
| $C$ | 氧分压 (% O₂ 气相) | 位点表 |
| $EC_{50}=1.6$ mM, $n_L=1$, $b_L=1/7$ | 野生型 lldPRD 实测表征（ALPaGA, 2021） | literature_prior |
| $K_{O_2}=1$ %, $n_O=2$, $b_O=0.05$ | 低氧臂先验 | scenario |
| $n_Q$ | 群体感应 Hill 系数，**全轴第一未知量**，1–3 扫描 | scenario |
| $N$ | 菌密度，取该位点自身 O₂/乳酸条件下的**实测** 24 h 承载量 | calibration |
| $\rho_{\text{anox}},\rho_{\text{glu}}$ | 天然启动子的无氧 / 葡萄糖抑制残余活性 | — |

**临界肠腔密度。** 令 $\mathcal R=1$ 并对密度比 $d=N_s/N_t$ 求解：

$$d_{\text{crit}}=\text{hyp}\cdot\big(\text{lac}\cdot\text{hyp}\cdot R\big)^{1/n_Q},
\qquad R=\rho_{\text{anox}}^{-1}\rho_{\text{glu}}^{-1} \tag{3.1-5}$$

低于 $d_{\text{crit}}$ 时群感臂把肠腔关住，高于则关不住。
**抑制买到的余量按 $R^{1/n_Q}$ 增长——群感臂越陡，强抑制越不值钱。**

代码：`src/sensors.py`, `src/tissue.py`。代入见 `MODULE_3_1.md` §4。

> **"22–910×" 不是测量区间**，而是 $n_Q\in[1.0,\,2.978]$ 两套标定的跨度；见式(3.1-3)
> 中 $n_Q$ 处于指数位。

### 3.2 病灶尺寸开关

缺氧核半径与缺氧体积分数（纯几何，不含任何传感器参数）：

$$r_{\text{core}}(R) = \max\!\big(R-d_{O_2},\,0\big),\qquad
\phi_{\text{hyp}}(R) = \left(\frac{r_{\text{core}}(R)}{R}\right)^{3} \tag{3.2-1}$$

体积平均低氧活性：

$$\bar f_O(R) = \phi_{\text{hyp}}(R)\,f_O(C_{\text{core}}) + \big(1-\phi_{\text{hyp}}(R)\big) f_O(C_{\text{rim}}) \tag{3.2-2}$$

整病灶门输出 = 单位体积产量 × 体积积分核（核即式(4.4-3)）：

$$G(R) = \Big[\bar f_O(R)\cdot \Psi_{\text{centre}}(R)\Big]^{\,n_Q} \tag{3.2-3}$$

**机制拆分**（在取 $n_Q$ 次方**之前**，故两项可乘可分）：

$$\underbrace{\frac{\bar f_O(R_2)}{\bar f_O(R_1)}}_{\text{低氧体积项}}\times
\underbrace{\frac{\Psi_{\text{centre}}(R_2)}{\Psi_{\text{centre}}(R_1)}}_{\text{AHL 积分项}}
=\frac{Q(R_2)}{Q(R_1)} \tag{3.2-4}$$

**参数无关的几何底线**，式(3.2-1) 的直接推论：

$$R<d_{O_2}\ \Longrightarrow\ \phi_{\text{hyp}}(R)\equiv0\ \Longrightarrow\
\bar f_O(R)\equiv f_O(C_{\text{rim}})=\text{const} \tag{3.2-5}$$

$d_{O_2}=178$ µm（由 9.23 自述"400 µm 瘤内 1 % O₂ 等值面在 222 µm"反推），
$C_{\text{rim}}=5$ %，$C_{\text{core}}=0.5$ %。代码：`src/lesion_size.py`。

> **不需要任何标定的安全陈述**（式(3.2-1) 的直接推论）：
> $R < d_{O_2} = 178$ µm 的病灶 $\phi_{\text{hyp}} \equiv 0$，**完全没有缺氧体积**，
> 低氧臂在任何参数下都离不开基础水平 $b_O$。

### 3.3 结肠腔：结构性反向选择

**无参数判据。** 两条设计臂都对自身刺激单调。若非靶位点的刺激不低于靶位点，则

$$s_{\text{offsite}} \ge s_{\text{target}}
\;\Longrightarrow\;
\frac{f(s_{\text{target}})}{f(s_{\text{offsite}})} \le 1
\quad\text{对一切 } (EC_{50},\,n,\,b) \tag{3.3-1}$$

低氧刺激用单调变换 $s_{O}=-C$ 表达（氧越低刺激越大）。

**乳酸臂判别能力的解析上限。** 把 $EC_{50}$ 推到远高于两地浓度，两点都落在
幂律段 $f\sim L^{\,n_L}$，比值从下方趋近 $(L_t/L_{\text{off}})^{n_L}$ 而**永不超过**；
非零基础水平再把它压到 $1/b_L$：

$$\sup_{EC_{50}} \frac{f_L(L_t)}{f_L(L_{\text{off}})}
= \min\!\left\{\left(\frac{L_t}{L_{\text{off}}}\right)^{n_L},\ \frac{1}{b_L}\right\} \tag{3.3-2}$$

反解"要达到给定倍数所需的 Hill 系数"（$b_L=0$ 时）：

$$n_L \;\ge\; \frac{\ln \mathcal R_{\text{req}}}{\ln\!\big(L_t/L_{\text{off}}\big)} \tag{3.3-3}$$

**唯一不反向选择的机制：AHL 冲刷。** 肠腔稳态 AHL 相对滞留腔室：

$$\eta_{\text{ret}} = \frac{k_{\text{decay}}}{k_{\text{decay}}+k_{\text{wash}}},\qquad
k_{\text{decay}}=\frac{\ln 2}{t_{1/2}^{\text{AHL}}},\quad
k_{\text{wash}}=\frac{1}{\tau_{\text{transit}}} \tag{3.3-4}$$

| 符号 | 含义 | 等级 |
|---|---|---|
| $s$ | 刺激量（乳酸浓度，或 $-C$） | — |
| $L_t=8$ mM | 瘤内乳酸 | literature_prior |
| $L_{\text{off}}$ | 肠腔乳酸：健康 0.6 / 粪便上限 5.0 / 菌群失调 100 mM | literature_prior / scenario_only |
| $t_{1/2}^{\text{AHL}}$ | AHL 半衰期，默认 8 h | scenario |
| $\tau_{\text{transit}}$ | 肠腔转运时间，1–24 h 扫描 | scenario |

**天然抑制接上乳酸臂**（$\rho$ 为残余活性分数，只命中厌氧且富糖的肠腔侧）：

$$f_L^{\text{native}}(L)=f_L(L)\,\rho_{\text{anox}}\rho_{\text{glu}},
\qquad
\mathcal R=\frac{f_L(L_t)}{f_L(L_{\text{off}})\,\rho_{\text{anox}}\rho_{\text{glu}}} \tag{3.3-5}$$

反解所需抑制强度：

$$\big(\rho_{\text{anox}}\rho_{\text{glu}}\big)^{-1}\ \ge\
\frac{\mathcal R_{\text{req}}}{\mathcal R_{\text{derepressed}}} \tag{3.3-6}$$

代码：`src/gut_lumen.py`。代入见 `MODULE_3_3.md` §4。

> 式(3.3-1) 是本项目**最强**的一条结论：它不需要那个本周期不会做的乳酸梯度实验。
> 代价是它指向坏消息——肠腔两臂都反向选择，安全性全压在天然 `lldPRD` 的
> 厌氧+葡萄糖抑制上，这是**全项目唯一的单点失效**。

### 3.4 SsrA 降解标签

**留/去标签的闭式判据。** 单位给药下递送到靶点的效应蛋白量 ∝ 生物量 × 单位生物量效力：

$$\frac{\text{delivery(tagged)}}{\text{delivery(untagged)}}
=\frac{1}{r_{\text{biomass}}\;r_{\text{potency}}}
\;>\;1
\quad\Longleftrightarrow\quad
r_{\text{potency}} < \frac{1}{r_{\text{biomass}}} \tag{3.4-1}$$

即：**标签该留，当且仅当它损失的效力小于它换来的生物量。**

降解速率 $\delta$ 作为连续旋钮时，胞内池、效力、生物量三条响应：

$$P(\delta)=\frac{\delta_{\text{nat}}+\delta_{\text{built}}}{\delta_{\text{nat}}+\delta} \tag{3.4-2}$$

$$\text{potency}(\delta)=\frac{P(\delta)}{k_{\text{export}}+P(\delta)} \tag{3.4-3}$$

$$\text{biomass}(\delta)=\exp\!\big(-\lambda P(\delta)\big) \tag{3.4-4}$$

半衰期：

$$t_{1/2}=\frac{\ln 2}{\delta} \tag{3.4-5}$$

**为什么标签是选择性放大器而非单纯衰减器**：ClpXP 降解为 Michaelis–Menten，
有效一阶速率随底物升高而**下降**：

$$v=\frac{v_{\max}P}{K_m+P},
\qquad
k_{\text{eff}}(P)=\frac{v_{\max}}{K_m+P} \tag{3.4-6}$$

故高表达（瘤内）处降解相对变慢、低表达（正常组织）处降解相对更快，输出比值
**超过**启动子本身的转录比值。

| 符号 | 含义 | 值 | 等级 |
|---|---|---|---|
| $r_{\text{biomass}}$ | 诱导后 24 h OD，untagged/tagged | 0.585 | calibration |
| $r_{\text{potency}}$ | 单位 OD 杀伤，untagged/tagged | 1.414 | calibration |
| $\delta_{\text{nat}}$ | 无标签衰减率（$t_{1/2}=8.7$ h） | 0.08 /h | scenario |
| $\delta_{\text{built}}$ | 实际构建体衰减率（$t_{1/2}=1.6$ h） | 0.35 /h | scenario |
| $\lambda,k_{\text{export}}$ | 由两个实测比值反解的形状常数 | derived | derived |

稳态池由 $\gamma P+v_{\max}P/(K_m+P)=\text{production}$ 解出（二次方程取正根）。
**放大倍数**定义为蛋白层面比值超出产率比值的部分：

$$\mathcal A=\frac{P_{\text{ss}}(\text{induced})/P_{\text{ss}}(\text{leak})}
{\text{production}_{\text{induced}}/\text{production}_{\text{leak}}} \tag{3.4-7}$$

**容量窗口**（$\mathcal A>1$ 的结构性要求）：

$$\text{泄漏产率}\ <\ v_{\max}\ <\ \text{诱导产率} \tag{3.4-8}$$

$v_{\max}$ 低于泄漏产率 ⇒ 到处饱和，什么都不保护；高于诱导产率 ⇒ 到处不饱和，
只等比压低、不放大。

代码：`src/ssra.py`。判据代入见 `MODULE_3_4.md` §4.2。

### 3.5 全局灵敏度

对输出 $Y$（安全余量）在**对数尺度**上做 Sobol 分解：

$$\mathrm{Var}[\log Y]=\sum_i V_i+\sum_{i<j}V_{ij}+\cdots,
\qquad S_i=\frac{V_i}{\mathrm{Var}[\log Y]},
\quad S_{Ti}=1-\frac{V_{\sim i}}{\mathrm{Var}[\log Y]} \tag{3.5-1}$$

必须用对数尺度，而且理由是**结构性**的：式(3.1-4) 是连乘，取对数把它变成求和

$$\log\mathcal R=\log\text{lac}+\log\text{hyp}+n_Q\log\frac{\text{hyp}}{d}+\log R \tag{3.5-2}$$

于是**纯乘性模型在对数尺度上应当交互为零、一阶指数之和为 1**。分析因此从描述性变成
**诊断性**：幸存的交互是真实耦合。式(3.5-2) 里只有一个真实耦合——$n_Q$ 乘在
$\log(\text{hyp}/d)$ 上——故可**事先预测** $n_Q$ 有小 $S_1$、大 $S_T$。

可加性检验量与交互占比：

$$\textstyle\sum_i S_i\ (\to1\text{ 为完全可加}),
\qquad
\text{interaction share}_i=1-\frac{S_i}{S_{Ti}} \tag{3.5-3}$$

采样：Saltelli（SALib），$n_{\text{base}}=1024$，关闭二阶，总样本
$1024\times(9+2)=11{,}264$，种子 20261008。代码：`src/sensitivity.py`。
代入与结果见 `MODULE_3_5.md` §4。

---

## 第 4 章 Efficacy — 需要多大剂量

### 4.3 / 4.4 AHL 场的闭式解

稳态 AHL：

$$D\nabla^2 C-\delta C+q(\mathbf x)=0 \tag{4.4-1}$$

屏蔽长度，本章全部无量纲量的来源：

$$\lambda=\sqrt{D/\delta},\qquad \alpha=R/\lambda,\qquad s=r/\lambda \tag{4.4-2}$$

因 `LuxI` 受 `pPepT` 而非 `pLux` 驱动，$q$ **不依赖** $C$：无自诱导环，方程
**线性**，叠加原理精确成立。任意三维球源排布都可由单球闭式场求和得到，
**不需要数值网格**。

归一化（除以 $q/\delta$，即无限大病灶的浓度）后，单个半径 $R$ 球源，
记 $\alpha=R/\lambda$、$s=r/\lambda$：

$$\Psi_{\text{centre}}(R)=1-(1+\alpha)e^{-\alpha} \tag{4.4-3}$$

$$\Psi_{\text{in}}(r;R)=\Psi_{\text{centre}}(\alpha)-(1+\alpha)e^{-\alpha}\left(\frac{\sinh s}{s}-1\right),\quad r\le R \tag{4.4-4}$$

$$\Psi_{\text{out}}(r;R)=\lambda\,g(\alpha)\,\frac{e^{-r/\lambda}}{r},
\qquad g(\alpha)=\alpha e^{\alpha}-(1+\alpha)\sinh\alpha,\quad r\ge R \tag{4.4-5}$$

> **数值注意**：式(4.4-3) 与 $g(\alpha)$ 在小 $\alpha$ 下分别消去到二阶和三阶，
> 必须在 $\alpha<0.01$ 切换到级数
> $\alpha^2/2-\alpha^3/3+\alpha^4/8-\cdots$ 与 $\alpha^3/3+\alpha^5/30+\alpha^7/840$，
> 否则 150 µm 病灶会丢 5 位有效数字、内外边界对不上。

**逃逸分数**（产在病灶内、destroyed 在病灶外的比例，即周围组织暴露）：

$$\mathcal E(R,\lambda)=\frac{3\,g(\alpha)(1+\alpha)e^{-\alpha}}{\alpha^{3}} \tag{4.3-1}$$

**自由场的核:缘梯度**（分子式 4.4-3，分母式 4.4-4 取 $r=R$）：

$$\mathcal G(R,\lambda)=\frac{\Psi_{\text{centre}}(R)}{\Psi_{\text{in}}(R;R)} \tag{4.3-2}$$

**SsrA 空间收益的三项拆分**（占比在对数上取，因两项乘性叠加）：

$$\text{retention}=\frac{1-\mathcal E_{\text{tagged}}}{1-\mathcal E_{\text{untagged}}},
\qquad
\text{confinement}=\frac{\mathcal E_{\text{untagged}}}{\mathcal E_{\text{tagged}}}$$

$$\text{总脱靶降低}=\rho_{\text{pool}}\times\text{confinement},
\qquad
\text{约束占比}=\frac{\ln(\text{confinement})}{\ln(\text{总降低})} \tag{4.3-3}$$

$\rho_{\text{pool}}=5.375$ 来自式(3.4-2)。代入见 `MODULE_4_3_4_5.md` §4.2。

**簇内中心浓度**（由叠加，精确）与**协同因子**：

$$\Psi_{\text{cluster}}(i)=\Psi_{\text{centre}}(R)+\sum_{j\ne i}\Psi_{\text{out}}(d_{ij};R),
\qquad
\text{coop}=\frac{\Psi_{\text{cluster}}(i)}{\Psi_{\text{centre}}(R)} \tag{4.4-6}$$

**等效孤立半径**——反解式(4.4-3)，使阈值被约掉，故不需要 $\beta_Q/K_Q$
（9.23 两套标定在该量上差 27 倍）：

$$R_{\text{eq}}:\quad \Psi_{\text{centre}}(R_{\text{eq}})=\Psi_{\text{cluster}} \tag{4.4-7}$$

**为什么分散不如聚集**，小 $\alpha$ 极限的标度：

$$\underbrace{\Psi_{\text{centre}}\sim\frac{\alpha^2}{2}}_{\text{自身}\ \propto\ R^2}
\qquad\text{vs}\qquad
\underbrace{\Psi_{\text{out}}\sim\frac{R^3}{3\lambda^2 d}}_{\text{邻居}\ \propto\ R^3/d} \tag{4.4-8}$$

自身贡献随 $R^2$、邻居贡献随 $R^3/d$——把体积拆小再分开，自身项掉得比邻居项补回来
的多，**这就是簇协同远弱于体积相加的原因**。
代码：`src/multilesion.py`, `src/spatial.py`。代入见 `MODULE_4_4.md` §4。

| 符号 | 含义 | 值 | 等级 |
|---|---|---|---|
| $\lambda_{\text{AHL}}$ | AHL 屏蔽长度 | 3000 µm | scenario |
| $\lambda_{\text{eff}}$ | GSDMD-N 扩散长度，无/有 SsrA | 670.8 / 300.0 µm | scenario |
| $R$ | 病灶半径 | 150–2000 µm 扫描 | — |

### 4.5 暴露积分

容量受限菌群的累积暴露：

$$\int_0^{T}N(t)\,dt \;=\; K T-\big(K-N_0\big)\frac{1-e^{-rT}}{r} \tag{4.5-1}$$

由单分子逼近 $N(t)=K-(K-N_0)e^{-rt}$（模块 2.3 证明这是这批曲线的正确形状）。
接种量 $N_0$ 只进第二项且被 $1/r$ 压扁——32 倍接种量区间只移动暴露 0.178 %。
半峰时间 $t_{1/2}=\ln\!\big(2(K-N_0)/K\big)/r$。

**持留杠杆**：生长率 $\mu$ 对抗一阶清除 $k_{\text{clr}}$，

$$K_{\text{eff}}=K\max\!\left(1-\frac{k_{\text{clr}}}{\mu},\,0\right),
\qquad \text{暴露}=K_{\text{eff}}\,T \tag{4.5-2}$$

$k_{\text{clr}}>\mu$ 时完全清除。**杠杆是清除率，不是给药方案。**

⚠️ 该模型**不含任何灭绝机制**（9.23 局限 1），故"再给药无用"是**构造的推论**而非
数据推断，见 `MODULE_4_3_4_5.md` §5.5。代码：`src/spatial.py`。

### 4.6 反推有效剂量 ⭐

**第一步：净剂量–杀伤曲线。** 扣除底盘贡献后在 log–log 拟合幂律：

$$f_{\text{net}}(d)=A\,d^{\,b} \tag{4.6-1}$$

$$\ln f_{\text{net}}=\ln A+b\ln d \tag{4.6-2}$$

**第二步：效力判据。** 24 h 暴露窗内杀伤速率追上增殖速率：

$$f_{\text{req}}=100\left(1-e^{-\ln 2\,\cdot\, t_{\exp}/T_{\text{double}}}\right)\ \% \tag{4.6-3}$$

**第三步：反演。**

$$d^{*}=\left(\frac{f_{\text{req}}}{A}\right)^{1/b} \tag{4.6-4}$$

**递送损失补偿**（效率 $\eta$ 需要的剂量加成）：

$$\mathcal M_{\eta}=\eta^{-1/b} \tag{4.6-5}$$

**剂量随病灶半径**（门输出降低需按 $b$ 次方根补偿）：

$$\mathcal M(R)=\left(\frac{G(R)}{G(R_{\text{ref}})}\right)^{-1/b} \tag{4.6-6}$$

**可容忍的脱靶损失**（结肠上皮更新是一个**周期**，故速率为 $1/T_{\text{renew}}$
而非 $\ln 2/T_{\text{renew}}$）：

$$f_{\text{tol}}=100\left(1-e^{-t_{\exp}/T_{\text{renew}}}\right)\ \% \tag{4.6-7}$$

**所需安全余量**，以及**给定余量下的脱靶损失**：

$$m \ \ge\ \left(\frac{f_{\text{target}}}{f_{\text{tol}}}\right)^{1/b},
\qquad
f_{\text{offtarget}}=f_{\text{target}}\,m^{-b} \tag{4.6-8}$$

| 符号 | 含义 | 值 | 等级 |
|---|---|---|---|
| $b$ | 净剂量–杀伤指数 | 2.651（区间 2.651–3.376） | calibration |
| $A$ | 幅度 | 0.02510 %/OD$^b$ | calibration |
| $d$ | 剂量（共培养 OD） | 实测 6 / 8 / 10 | calibration |
| $t_{\exp}$ | 暴露窗 | 24 h | protocol |
| $T_{\text{double}}$ | 体积倍增时间：CT26 24–48 h；人 CRC 100–600 d | — | scenario |
| $T_{\text{renew}}$ | 结肠上皮更新周期 3–5 d | — | scenario |
| $\eta_{\text{nodule}}$ | 400 µm 瘤内带标签效应蛋白滞留分数 | 0.268 | derived |
| $x_{\max}$ | 最大可报外推倍数（护栏） | 3.0× | protocol |
| $b_{\text{cons}}$ | 余量换算用保守指数（完全不计放大） | 1.0 | protocol |

代码：`src/dose.py`。

> **立方律是本模块的全部价值**：$b\approx 3$ 使反演把需求侧的不确定性开三次方根。
> CT26 与人 CRC 的所需杀伤分数差 435×，所需**剂量**只差 6–10×；体内 3.7× 的
> 递送损失只要 1.55× 剂量。答案因此对本项目恰好测不到的那些参数**稳健**。
> 代价是护栏：幂律无阈值，故两个方向的外推都被 $x_{\max}=3.0$ 截断。

---

## 第 6 章 焦亡–免疫–远端杀伤

四状态级联：

$$\begin{aligned}
\dot A &= \Phi-\delta_A A &&\text{抗原 + IL-1β/IL-18 信号}\\
\dot D &= a_D\frac{A}{K_A+A}-\delta_D D &&\text{DC 成熟（饱和）}\\
\dot T &= a_T\,\varepsilon\,D-\delta_T T &&\text{CTL 启动，受 }\varepsilon\text{ 抑制}\\
\dot M &= rM\Big(1-\frac MK\Big)-\frac{kTM}{h+M} &&\text{远端病灶}
\end{aligned} \tag{6-1}$$

上游在稳态坍缩。令 $x=\Phi/(\delta_A K_A)$ 为归一化焦亡通量，定义**免疫压力数**与
**级联增益**：

$$\Psi=\varepsilon\,G\,\frac{x}{1+x},
\qquad
G=\frac{k}{r\,h}\cdot\frac{a_T}{\delta_T}\cdot\frac{a_D}{\delta_D} \tag{6-2}$$

无量纲远端病灶方程（$M$ 以 $K$ 为单位）：

$$\dot M = M\left[(1-M)-\frac{h\,\Psi}{h+M}\right] \tag{6-3}$$

由 $x/(1+x)<1$ 恒成立，得**硬天花板**：

$$\varepsilon G>1 \quad\text{（否则任何焦亡通量都做不到远端控制）} \tag{6-4}$$

天花板之上所需通量：

$$x_{\min}=\frac{1}{\varepsilon G-1} \tag{6-5}$$

双稳结构：非零平衡点是 $M^2-(1-h)M+h(\Psi-1)=0$ 的两根，上根为逃逸态、
下根为 $M=0$ 的吸引域边界；判别式 $\Delta=(1-h)^2-4h(\Psi-1)$。无条件根除阈值：

$$\Psi_{\text{crit}}=1+\frac{(1-h)^2}{4h} \tag{6-6}$$

**两根的显式形式**，$\Delta=(1-h)^2-4h(\Psi-1)$：

$$M_{\pm}=\frac{(1-h)\pm\sqrt{\Delta}}{2} \tag{6-7}$$

上根 $M_+$ 是稳定的**逃逸态**负荷；下根 $M_-$ 是 $M=0$ 的**吸引域边界**，即
**最大可治负荷**。$\Delta<0$ 时无正平衡点 ⇒ 无条件根除。

**局部 vs 远端拆分**（六条第 6 条的算式）：

$$\text{total}=\underbrace{f_{\text{local}}(1-\phi_{\text{dist}})}_{\text{局部，可测}}
+\underbrace{\mathcal R(\Psi)\,\phi_{\text{dist}}}_{\text{远端，scenario\_only}},
\qquad
\mathcal R(\Psi)=1-\frac{M_+(\Psi)}{M_+(0)} \tag{6-8}$$

$\phi_{\text{dist}}$ 为负荷中播散部分的占比。⚠️ 远端项**不得作为预测引用**。

| 符号 | 含义 | 值 | 等级 |
|---|---|---|---|
| $\varepsilon\in(0,1]$ | 免疫抑制因子；本项目靶向 **pMMR/MSS 冷肿瘤**，故 $\varepsilon$ 小 | 扫描 | scenario_only |
| $G$ | 级联增益 | 扫描 1–100 | scenario_only |
| $h$ | 半数免疫杀伤对应的负荷（占容量分数） | 0.2 | scenario_only |
| $x$ | 归一化焦亡通量 | 扫描 | scenario_only |

代码：`src/immune.py`。

> 本章**全部** `scenario_only`：$G$ 与 $\varepsilon$ 都无本队数据。故只报**可行性
> 边界**（式(6-4)、(6-6)），不报预测疗效。

---

## 验证层 — 留出法

预测/实测比值判据与标准误判据，**两者均在跑之前声明**：

$$\left|\frac{\hat y}{y}-1\right|\le \text{tol}_{\text{ratio}}=0.25,
\qquad
\frac{|\hat y-y|}{\mathrm{SE}(y)}\le \text{tol}_{\text{SE}}=2 \tag{V-1}$$

汇总表的"最差比值"定义为 $\max_i|\hat y_i/y_i-1|+1$。

**门的留一角规则**——把式(2.2-4) 的乘性判据改写成预测。四角在 probit 单位下可加，
故任意三角决定第四角：

$$\hat z_{\mathcal H}=z_i+z_j-z_k,
\qquad
\hat p_{\mathcal H}=\Phi\big(\hat z_{\mathcal H}\big) \tag{V-2}$$

四条规则：$\hat z_A=z_C+z_B-z_D$ · $\hat z_B=z_D+z_A-z_C$ ·
$\hat z_C=z_D+z_A-z_B$ · $\hat z_D=z_C+z_B-z_A$。
标准误由四角合成 $\mathrm{SE}=\sqrt{\mathrm{SE}_i^2+\mathrm{SE}_j^2+\mathrm{SE}_k^2+\mathrm{SE}_{\mathcal H}^2}$。

**系统偏差在比值上抵消。** 承载量外推有系统偏差 $\beta$（式 2.3-1 的 Gompertz 抓不住
creep 相，把平台读高 5.0 %），但式(3.4-1) 的判据用的是两株之比：

$$\hat r_{\text{biomass}}
=\frac{\beta_{\text{untagged}}K_{\text{untagged}}}{\beta_{\text{tagged}}K_{\text{tagged}}}
\ \longrightarrow\ r_{\text{biomass}}
\quad\text{当}\ \beta_{\text{untagged}}\approx\beta_{\text{tagged}} \tag{V-3}$$

承载量留出用 $t\le t_{\text{cut}}=12$ h 外推 24 h（**必须排除 24 h 靶点**），
拟合从 $t=1$ h 起（模块 2.3 的结论）。
代码：`src/validation.py`。代入见 `MODULE_VALIDATION.md` §4。
