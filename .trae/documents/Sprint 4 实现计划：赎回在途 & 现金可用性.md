# Sprint 4 实现计划：赎回在途 & 现金可用性

## 一、需求理解

Sprint 4 的核心目标是：**清楚区分"钱什么时候不在产品里了"和"钱什么时候真的能用"**

### 三大现金状态
| 状态 | 含义 | 是否计入可用现金 |
|------|------|-----------------|
| 产品中资金 | 已投入、未赎回 | ❌ |
| 赎回在途 | 已发起赎回、未到账 | ❌ |
| 账户余额 | 已到账 | ✅ |

### 明确边界
- **不做**：Lot/批次模型、精确收益拆分、现金流预测模型
- **必须做**：赎回≠到账语义分离、在途资金不计入可用现金、用户能回答"我现在有多少钱能用"

---

## 二、功能拆解与实现步骤

### 阶段 1：后端服务层 - 在途资金计算（S4-1）

**目标**：实现轻量级在途资金计算，不引入 Lot 模型

**实现内容**：
1. **新建 `backend/services/redeem_service.py`**
   - `calculate_pending_redeems(session, product_id=None)` - 计算在途赎回金额
   - 规则：`Σ redeem_request.amount - Σ redeem_settle.amount`
   - 支持按产品查询和全局查询

2. **新建 `backend/services/cash_service.py`**
   - `calculate_available_cash(session, date)` - 计算可用现金
   - 规则：`Σ 账户余额(is_liquid=true) - 在途赎回金额`
   - `calculate_future_cash_flow(session, start_date, days)` - 计算未来可用现金

3. **修改 `backend/services/dashboard_service.py`**（新建或整合到现有 dashboard.py）
   - 更新汇总接口，包含在途资金数据

### 阶段 2：后端 API 层 - 接口暴露

**修改/新增文件**：
1. **修改 `backend/api/v1/dashboard.py`**
   - `GET /api/dashboard/summary` - 增加 `pending_redeems`、`real_available_cash` 字段
   - `GET /api/dashboard/pending_redeems` - 在途资金明细
   - `GET /api/dashboard/future_cash_flow` - 未来可用现金预测

2. **修改 `backend/api/v1/products.py`**
   - `GET /api/products/{id}/pending_redeem` - 单个产品在途赎回金额
   - 修改产品详情接口，包含在途信息

### 阶段 3：前端服务层 - API 封装

**修改/新增文件**：
1. **修改 `frontend/src/services/dashboard.ts`**
   - 新增接口类型定义
   - 新增 `getPendingRedeems()`、`getFutureCashFlow()` 函数

2. **修改 `frontend/src/services/products.ts`**
   - 新增 `getProductPendingRedeem()` 函数

### 阶段 4：前端页面 - Dashboard 增强

**修改 `frontend/src/pages/Dashboard/index.tsx`**：
1. 新增统计卡片：
   - "赎回在途金额"（红色警示）
   - "实际可用现金"（已扣除在途）
   - "未来7天预计到账"
   - "未来30天预计到账"

2. 新增列表/时间轴展示：
   - 在途赎回明细列表
   - 未来到账预测列表

### 阶段 5：前端页面 - 产品详情页补充

**修改 `frontend/src/pages/Products/Detail.tsx`**：
1. 新增只读信息区：
   - 当前在途赎回金额
   - 最近一次赎回预计到账日
   - 到账规则提示（T+N）

---

## 三、关键数据结构

### 在途资金响应
```typescript
interface PendingRedeem {
  product_id: number;
  product_name: string;
  pending_amount: number;  // 在途金额（负数表示赎回）
  request_date: string;    // 申请日期
  estimated_settle_date: string;  // 预计到账日
}

interface PendingRedeemsSummary {
  total_pending: number;   // 全局在途总额
  items: PendingRedeem[];
}
```

### 未来现金流响应
```typescript
interface FutureCashFlowItem {
  date: string;
  amount: number;
  source: 'redeem' | 'maturity';  // 赎回/到期
  description: string;
}

interface FutureCashFlow {
  items: FutureCashFlowItem[];
  total_7d: number;
  total_30d: number;
}
```

### Dashboard 汇总增强
```typescript
interface DashboardSummary {
  // ... 原有字段
  pending_redeems: number;        // 在途赎回总额
  real_available_cash: number;    // 实际可用现金（已扣在途）
  future_7d: number;              // 未来7天预计到账
  future_30d: number;             // 未来30天预计到账
}
```

---

## 四、验收标准

### S4-1 在途资金建模
- [ ] 任意时刻能算出某产品的在途金额
- [ ] 任意时刻能算出全局在途金额
- [ ] 多笔赎回并行时能正确累计

### S4-2 可用现金计算
- [ ] Dashboard 上"可用现金"与用户直觉一致
- [ ] 发起赎回后可用现金不瞬间跳增
- [ ] 赎回到账后可用现金随之增加

### S4-3 未来可用现金
- [ ] 能基于产品 T+N 规则推算到账日
- [ ] 明确标注"预计/规则推算"
- [ ] 展示时间轴/列表形式

---

## 五、风险与注意事项

1. **不精确匹配**：Sprint 4 不做 redeem_request 和 redeem_settle 的逐笔匹配，只做金额级别追踪
2. **Snapshot 权威**：可用现金计算仍以 Snapshot 为权威，不受推导数据影响
3. **定期产品到期**：对于定期产品，需要基于 term_days 和买入日期推算到期日
4. **时区处理**：日期统一使用 date 类型，不包含时间部分

---

请确认以上计划后，我将按阶段开始实现。