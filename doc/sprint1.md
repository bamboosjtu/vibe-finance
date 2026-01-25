很好，这一步已经**进入“可以直接开干”的层级**了。
下面是 **Sprint 1 的完整实现清单**，我会严格按你要求的结构来写：

> **任务 → 接口 → 页面 → 验收**
> 并且每一条都做到：**不需要再解释就能开始写代码**。

---

# Sprint 1 实现清单

**主题：账户 & 产品管理（前后端并行）**
**目标**：把现实世界的账户和理财产品，**无损、无歧义地建进系统**

---

## 🎯 Sprint 1 Goal（务必写在看板顶部）

> 我可以像真实用户一样，把我现在用的
> **银行卡 / 现金 / 信用卡 / 理财产品**
> 全部录入系统，并且字段“顺手、不别扭”。

---

# T1-1 Institution（银行/平台）管理

## 任务

建立一个可复用的「机构字典」，供账户和产品选择。

---

### 接口

#### POST /api/institutions

**请求**

```json
{ "name": "长沙银行" }
```

**响应**

```json
{ "id": 1, "name": "长沙银行" }
```

#### GET /api/institutions

**响应**

```json
{
  "items": [
    { "id": 1, "name": "长沙银行" },
    { "id": 2, "name": "支付宝" }
  ]
}
```

**实现要点**

* name 唯一

---

### 页面

**位置**：

* 不单独做页面
* 在「账户/产品新建表单」中以内联方式出现

**交互**

* 下拉选择已有机构
* 支持「新建并立即选中」
* is_liquid：若“未勾选/未触达”视为 false

---

### 验收标准（Acceptance Criteria）

* [x] 能快速新增机构（不跳页）
* [x] 同名机构不能重复创建
* [x] 创建后可立即用于账户/产品

---

# T1-2 Account（账户）管理

## 任务

建立账户模型，准确表达**钱在哪里 & 能不能用**。

---

### 接口

#### POST /api/accounts

**请求**

```json
{
  "name": "长沙银行-借记卡",
  "institution_id": 1,
  "type": "debit",
  "is_liquid": true
}
```

- 前端规则（强约束）：前端提交 POST /api/accounts 时必须传 is_liquid: boolean，未勾选就传 false。
- 后端规则（兜底兼容其它调用方）：后端把 is_liquid 当成 optional：
    - 若请求里 is_liquid 为 null / 缺失：按 type 计算默认值（type == credit => false，否则 true）。
    - 若请求里 is_liquid 为 true/false：直接使用，不改写。

---

#### GET /api/accounts

**响应**

```json
{
  "items": [
    {
      "id": 10,
      "name": "长沙银行-借记卡",
      "type": "debit",
      "is_liquid": true
    },
    {
      "id": 11,
      "name": "花呗",
      "type": "credit",
      "is_liquid": false
    }
  ]
}
```

---

#### PATCH /api/accounts/{id}

**请求**

```json
{ "is_liquid": true }
```

---

### 页面

#### 账户列表页

**展示列**

* 账户名
* 类型（现金 / 银行卡 / 信用卡 / 投资账户）
* 是否计入可用现金（✓ / ×）

**操作**

* 新建账户
* 编辑账户（弹窗即可）

---

#### 新建 / 编辑账户表单

**字段**

* 名称（必填）
* 机构（下拉 + 新建）
* 类型（枚举）
* 是否计入流动资产（checkbox）

**交互约束**

* 选择「信用卡」时，is_liquid 自动取消勾选（可手动改）

---

### 验收标准

* [x] 能完整建模：现金 / 借记卡 / 信用卡 / 投资账户
* [x] 信用卡默认不计入可用现金
* [x] 修改 is_liquid 后，后续计算会用到（Sprint 2 验证）
* [x] 填写过程无“我不知道该填什么”的时刻（主观但重要）

---

# T1-3 Product（理财产品）管理

## 任务

建立理财产品主数据，为后续估值、比较、预测打基础。

---

### 接口

#### POST /api/products

**请求**

```json
{
  "name": "28D",
  "institution_id": 1,
  "product_type": "bank_wmp",
  "risk_level": "R2",
  "term_days": 28,
  "liquidity_rule": "closed",
  "settle_days": 1,
  "note": "到期赎回"
}
```

---

#### GET /api/products

**响应**

```json
{
  "items": [
    {
      "id": 200,
      "name": "28D",
      "risk_level": "R2",
      "term_days": 28,
      "liquidity_rule": "closed",
      "settle_days": 1
    }
  ]
}
```

---

### 页面

#### 产品列表页

**展示列**

* 产品名
* 机构
* 风险等级（R1–R5）
* 期限
* 赎回规则（开放 / 封闭 / 定开）

---

#### 新建 / 编辑产品表单

**字段**

* 产品名（必填）
* 机构
* 风险等级（下拉：R1–R5）
* 期限天数（number，可为空）
* 流动性规则（枚举）
* 赎回到账 T+N
* 备注

**交互设计**

* “日日金”类产品：

  * 期限允许为 0
  * 流动性默认 open
* 不强制你一次填全（MVP 友好）

---

### 验收标准

* [x] 能准确表达 28D / 63D / 91D / 日日金
* [x] 字段与银行 APP 里的信息一一对应
* [x] 不需要理解“系统内部概念”就能填

---

# T1-4 前后端联调 & 数据一致性检查

## 任务

确保前端所见即后端真实数据，无“假页面”。

---

### 联调清单

* [x] 新建账户 → 刷新列表 → 数据一致
* [x] 编辑账户 → 再次进入仍正确
* [x] 新建产品 → 立即出现在列表
* [x] 刷新页面不丢数据

---

下面是在你现有 Sprint 1 实现清单基础上，**补充“Lot（批次）概念到 UI/接口”**的增量版本（不推翻原 Sprint 1，只做最小必要扩展）。我会沿用你文件里的结构与风格。

---


# T1-5 Lot（持仓批次）管理

* **新增批次（Lot）**：表示“我在某次买入形成的一笔持仓批次”
* Sprint 1 只需要做到：**能创建/查看 Lot**
  （赎回/到账状态机在后续Sprint）

## 任务

为同一产品支持多次买入，记录为多个 Lot。Lot 在 Sprint 1 阶段只需支持：

* 创建 Lot（open_date + principal + note）
* 查看产品下 Lot 列表
* （可选）编辑 Lot 的 note / principal（不建议频繁改 principal，但 MVP 可允许）

> 状态机（holding/redeeming/settled）可先固定为 holding，不在 Sprint 1 做赎回/到账。

---

## 接口

### POST /api/lots

**请求**

```json
{
  "product_id": 200,
  "open_date": "2025-01-10",
  "principal": 100000,
  "note": "第1次买入"
}
```

**响应**

```json
{ "id": 9001, "status": "holding" }
```

**服务端规则**

* 默认 `status = holding`
* `open_date` 必填，格式 YYYY-MM-DD
* `principal > 0`

---

### GET /api/products/{id}/lots

**响应**

```json
{
  "product_id": 200,
  "items": [
    {
      "id": 9001,
      "product_id": 200,
      "open_date": "2025-01-10",
      "principal": 100000,
      "status": "holding",
      "note": "第1次买入"
    },
    {
      "id": 9002,
      "product_id": 200,
      "open_date": "2025-02-05",
      "principal": 50000,
      "status": "holding",
      "note": "第2次买入"
    }
  ]
}
```

---

### PATCH /api/lots/{id}

**请求**

```json
{ "note": "补充备注" }
```

**响应**

```json
{
  "code": 200,
  "data": {
    "created_at": "Sat, 24 Jan 2026 15:33:09 GMT",
    "id": 9,
    "note": "\u5df2\u53ef\u8d4e\u56de",
    "open_date": "Tue, 06 Jan 2026 00:00:00 GMT",
    "principal": 30000.0,
    "product_id": 8,
    "status": "holding",
    "updated_at": "Sat, 24 Jan 2026 15:33:09 GMT"
  },
  "message": "ok"
}
```

---

## 页面

> Lot UI 嵌在“产品页”里**，不额外开新模块。

### A. 产品列表页

* 依旧是列表 + 新建/编辑产品

### B. 产品详情页

从产品列表点进来即可

**模块 1：产品基本信息（只读即可）**

* 名称 / 机构 / 风险等级 / 期限 / 流动性 / T+N

**模块 2：批次（Lot）列表**
展示列：

* 批次ID（可隐藏）
* 买入日 open_date
* 本金 principal
* 状态 status（Sprint 1 都是 holding）
* 备注 note

**模块 3：新增批次（Lot）表单（内联）**
字段：

* 买入日（date picker）
* 本金（number）
* 备注（可选）
  按钮：
* “新增批次”

交互建议：

* 新增成功后自动刷新列表
* 同一产品允许多条 Lot，按 open_date 倒序或正序（你习惯即可）

---

## 验收标准（Acceptance Criteria）

* [x] 我能把现在所有账户建进去
* [x] 我能把现在所有理财产品建进去
* [x] 填写过程中没有明显“反人类字段”
* [x] 我对这些数据“以后能一直用”有信心
* [x] 同一产品可以创建多个 Lot（至少 2 条）
* [x] Lot 创建后能在产品详情页看到且刷新不丢
* [x] Lot 默认状态为 holding（Sprint 1 不做状态机）
* [x] 不需要把“第二次买入”当成第二个产品来建模
* [x] 为 Sprint 3 的“分段点识别”预留：Lot.open_date 可被读取（即接口已具备）
* [x] 同一产品支持多次买入，通过 Lot 表达（不拆分为多个 Product）
* [x] 从产品列表进入产品详情页能看到 Lot 列表
* [x] 新增 Lot 后产品详情页立即更新且刷新不丢
---

# 🧠 给你的一个关键提醒（作为 Tech Lead）

> **Sprint 1 不追求“完整”，只追求“真实”。**

如果你在这个 Sprint 里发现：

* 某字段需要改名
* 某字段需要拆分 / 合并
* 某默认值不合理

👉 **现在改，成本最低。**
