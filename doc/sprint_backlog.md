# Sprint Backlog（MVP 阶段）

> Sprint 长度建议：**1 周**
> 原则：**每个 Sprint 结束，你都能像用户一样点一遍系统**

---

## 🟦 Sprint 0：项目骨架 & 最小可运行系统

### 🎯 Sprint Goal

> 打开网页 → 能看到页面 → 前后端能通信
> 为后续并行开发打地基

---

### Backlog

#### T0-1 项目初始化

* [ ] 初始化前端项目（Next.js / React）
* [ ] 初始化后端（API Routes / 独立 API）
* [ ] SQLite 连接 + migrations 机制

**验收标准**

* 能启动前端 `localhost`
* 能访问 `/api/health` 返回 200

---

#### T0-2 基础 Layout

* [ ] 顶部或侧边导航
* [ ] 路由占位页：

  * Dashboard
  * 账户
  * 产品

**验收标准**

* 页面可点击切换
* 不要求有真实数据

---

## 🟦 Sprint 1：账户 & 产品管理（你最强调的并行点）

### 🎯 Sprint Goal

> 能像真实用户一样，把“现实世界里的账户和理财产品”建进系统

---

### Backlog

#### T1-1 Institution 管理

* [ ] POST /api/institutions
* [ ] GET /api/institutions

**验收标准**

* 能新建银行（如：长沙银行）
* 下拉可复用

---

#### T1-2 Account CRUD

* [ ] POST /api/accounts
* [ ] GET /api/accounts
* [ ] PATCH /api/accounts/{id}

**前端**

* [ ] 账户列表
* [ ] 新建 / 编辑账户表单

**验收标准**

* 能区分 cash / debit / credit
* credit 默认 `is_liquid = false`
* 修改 is_liquid 后立刻生效

---

#### T1-3 Product CRUD

* [ ] POST /api/products
* [ ] GET /api/products

**前端**

* [ ] 产品列表
* [ ] 新建产品表单

**验收标准**

* 能录入：期限、R1–R5、T+N
* 产品字段填起来不别扭（主观但重要）

---

## 🟦 Sprint 2：资产快照 & Dashboard v1

### 🎯 Sprint Goal

> 验证「Snapshot 是权威」这条核心设计是否成立

---

### Backlog

#### T2-1 Snapshot 批量录入

* [ ] POST /api/snapshots/batch_upsert
* [ ] GET /api/snapshots?date=

**前端**

* [ ] Snapshot 手工录入页（表格）

**验收标准**

* 同一天可录多个账户
* 覆盖同日数据不报错

---

#### T2-2 Dashboard v1

* [ ] 总资产
* [ ] 流动资产
* [ ] 负债（信用卡）

**验收标准**

* 数值来自 Snapshot
* 修改 Snapshot 后 Dashboard 实时变化

---

## 🟦 Sprint 3：产品估值 & 可比性验证

### 🎯 Sprint Goal

> 回答：**不同期限理财，现在能不能放在一把尺上比？**

---

### Backlog

#### T3-1 Product Valuation 录入

* [ ] POST /api/valuations/batch_upsert
* [ ] GET /api/products/{id}/valuations

**前端**

* [ ] 估值手工录入
* [ ] 简单折线图

**验收标准**

* 支持非每日
* 缺失点不报错

---

#### T3-2 产品指标计算

* [ ] TWR
* [ ] 年化
* [ ] 最大回撤

**前端**

* [ ] 产品详情页指标展示

**验收标准**

* 数据 < 2 周 → 灰显
* 不硬算、不报 NaN

---

## 🟦 Sprint 4：交易流水 & Lot 状态机

### 🎯 Sprint Goal

> 验证「赎回 ≠ 到账」这个你非常在意的真实场景

---

### Backlog

#### T4-1 Lot 创建

* [ ] POST /api/lots
* [ ] GET /api/products/{id}/lots

**前端**

* [ ] Lot 列表

**验收标准**

* 同一产品支持多 Lot

---

#### T4-2 Lot 状态机

* [ ] POST /api/lots/{id}/redeem
* [ ] POST /api/lots/{id}/settle

**前端**

* [ ] 赎回按钮
* [ ] 到账按钮
* [ ] 状态展示（holding / redeeming / settled）

**验收标准**

* 赎回日即从投资中消失
* redeeming 不算可用现金

---

## 🟦 Sprint 5：现金可用性 & 预测

### 🎯 Sprint Goal

> 系统能回答：**我现在、未来什么时候有钱可用？**

---

### Backlog

#### T5-1 Today Available

* [ ] GET /api/cash/today
* [ ] 设置：预留金 / 还款参数

**前端**

* [ ] Dashboard 显示“可用现金”

**验收标准**

* redeeming 资金被排除
* 信用卡正确扣减

---

#### T5-2 Forecast Available

* [ ] GET /api/cash/forecast

**前端**

* [ ] 现金流日历（列表即可）

**验收标准**

* 到账日跳变正确
* 不提前释放资金

---

## 🟦 Sprint 6：Excel 导入 & 对账 Warning

### 🎯 Sprint Goal

> 把你现在的 Excel 无痛迁进来，并且“看见不一致”

---

### Backlog

#### T6-1 Excel 导入

* [ ] 资产表导入
* [ ] 估值表导入

**验收标准**

* 自动建账户 / 产品
* 可回滚（至少逻辑回滚）

---

#### T6-2 Snapshot vs Transaction Warning

* [ ] 对账计算
* [ ] Warning 列表页

**验收标准**

* 不修改数据
* 只提示，不阻断

---

## 🟦 Sprint 7（可选）：XIRR & 收益拆解

### 🎯 Sprint Goal

> 用一个数字回答：**我整体资金效率怎么样？**

---

### Backlog

#### T7-1 XIRR

* [ ] 产品 XIRR
* [ ] 全组合 XIRR

**验收标准**

* 使用现金流 + 期末估值
* 与 Excel 手算结果接近

---

## 🎁 给你一个“单人敏捷”的小建议（很适合你）

每个 Sprint 结束，问自己 **3 个问题**：

1. 今天我敢不敢用这个系统做一次真实决策？
2. 有没有哪个字段/页面让我“录得很不爽”？
3. 有没有哪个数字让我本能觉得“不对劲”？

👉 这 3 个问题比任何 KPI 都重要。

---

如果你愿意，下一步我可以：

* **直接把 Sprint 1 写成「任务 → 接口 → 页面 → 验收」的实现清单**
* 或 **给你一个 Notion / GitHub Projects 的 Backlog 模板**

你选一个，我继续。
