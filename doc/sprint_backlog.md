# Sprint Backlog（v3 对齐修正版）

> 需求基线：`需求文档 v3`  
> 目标原则：**产品视角、录入融合、走势可信、收益参考、不误导**

> Sprint 建议节奏：1 周 / Sprint  
> 方法论：**每个 Sprint 结束，都敢作为真实个人用户使用**

---

## 全局冻结原则（适用于所有 Sprint）

1. **Snapshot 是最高权威**
   - Snapshot 不被 Transaction / 估值 / 推导结果纠正
   - 不一致仅提示 Warning，不阻断、不回写

2. **估值是观察事实**
   - 允许缺失、不连续
   - 系统不得“补成事实”

3. **推导只用于展示与分析**
   - 插值、收益近似、区间计算只存在于 Derived Series
   - 永不回写事实表

4. **收益默认是参考值**
   - 精确口径不成立时，只能给“参考收益”
   - 不做伪精确

5. **产品是唯一用户操作对象**
   - 本阶段不维护 Lot / InternalHolding；未来可基于 Transaction 回放重建。

---

## 🟦 Sprint 0：项目骨架 & 可运行系统

### 🎯 Sprint Goal

> 打开页面即可使用，无真实数据也不报错

### Backlog

- 项目初始化（前端 + 后端）
- 基础 Layout / Sidebar
- 健康检查接口

---

## 🟦 Sprint 1：账户 & 产品主数据

### 🎯 Sprint Goal

> 能把现实世界中的账户和产品准确建模

### Backlog

- Institution CRUD
- Account CRUD（is_liquid）
- Product CRUD（规则、风险等级、赎回 T+N）

**验收**

- 产品与账户可独立维护
- 不涉及交易与估值

---

## 🟦 Sprint 2：资产快照 & Dashboard

### 🎯 Sprint Goal

> Snapshot 成为所有资产展示的权威来源

### Backlog

- Snapshot 批量录入
- Dashboard v1（总资产 / 流动资产 / 负债）
- Snapshot vs 推导差异 Warning

---

## 🟦 Sprint 3：产品详情页（录入融合 + 走势核心 Sprint）

### 🎯 Sprint Goal（冻结）

> 在**一个产品详情页**完成：  
> 录入（买入 / 卖出 / 估值） + 展示（走势 / 参考收益），  
> 且 **走势真实、重点突出、不被插值或现金流误导**。

---

### S3-1 产品详情页：统一录入能力【必做】

**能力范围**

- 产品估值点录入（ProductValuation）
- 买入 / 赎回 / 到账（Transaction）

**规则**

- 所有操作都绑定 product_id
- 交易必须选择 account_id

**验收**

- 在一个页面完成估值与交易录入
- 无独立“交易页 / 估值页”

---

### S3-2 产品市值序列生成（Derived）【必做】

**输入**

- ProductValuation（manual）
- 插值规则

**输出**

- Product Market Value Series：
  - date
  - value
  - source = manual | interpolated

**规则（冻结）**

- 插值仅发生在两个 manual 点之间
- 无 manual 点的区间 → 断线，不补

---

### S3-3 走势可视化（重点强化）【最高优先级】

> 本 Story 是 Sprint 3 的核心价值

#### 4.1 点与事件的视觉区分（必须）

- **观察点（manual）**
  - 实心点 / 强对比色
  - Tooltip 显示“观察估值”

- **插值点（interpolated）**
  - 空心点 / 虚线
  - Tooltip 显示“插值估算，仅用于参考”

- **买入 / 卖出事件**
  - 垂直事件线（不同颜色区分 buy / redeem）
  - Hover 显示金额与日期

---

#### 4.2 Y 轴范围的处理规则（必须明确）

**问题背景**

- 大额买入 / 赎回会导致市值台阶变化
- 自动缩放可能掩盖真实走势

**规则（冻结）**

1. Y 轴默认基于：
   - 产品市值序列（manual + interpolated）
   - - 买入 / 卖出当日的市值跳变
2. 当买入 / 卖出导致极端值时：
   - 不压缩历史波动到不可见
   - 允许增加 padding 或断轴提示
3. Tooltip 必须明确：
   - 市值变化是否来自“市场变化”或“资金流动”

**验收**

- 用户能直观看到：
  - 哪些波动来自估值变化
  - 哪些来自资金进出

---

### S3-5 收益与风险指标（参考档）【必做】

**收益指标**

- 默认展示：参考收益率（含现金流，近似）
- 明确标注：
  > “参考值，包含资金流动影响，不用于精确比较”

**严格收益**

- 仅在以下条件成立时展示：
  - 区间内无现金流
  - manual 估值点 ≥ 2 周

**风险指标**

- 最大回撤、回撤修复、波动
- 可使用插值点
- 必须提示“受现金流影响”

---

### Sprint 3 明确不做（冻结）

- Lot / 批次 UI
- 批次估值录入
- 精确 TWR / XIRR
- 自动收益拆分

---

## 🟦 Sprint 4：赎回在途 & 现金可用性

### 🎯 Sprint Goal

> 赎回 ≠ 到账，现金可用性准确

### Backlog

- redeem_request / redeem_settle 区分
- 在途资金不计入可用现金
- 产品详情页提示到账时间

---

## 🟦 Sprint 5：资金预测

### 🎯 Sprint Goal

> 回答“未来什么时候有钱可用”

---

## 🟦 Sprint 6：对账

### 🎯 Sprint Goal

> 看见不一致

---

## 完成定义（DoD）

当系统做到：

- 走势中**观察点、插值点、资金事件一眼可分**
- 收益率不会被当作精确结论
- 我能基于它做个人投资判断

则认为 Backlog 设计成功。
