## Sprint 6: 对账中心（Reconciliation Center）实现计划

### 目标
实现"看见不一致"的能力，让系统把"现实记录不完整/口径不一致"显性化、可解释化。

---

### 一、后端实现

#### 1. 新建 `backend/services/reconciliation_service.py`
实现对账核心逻辑：

**S6-2 账户对账（Snapshot vs 推导余额）**
- 计算每个账户的派生余额（基于 Transaction 现金流累计）
- 与 Snapshot 余额比较，超过阈值生成 Warning
- 支持按日期范围查询

**S6-3 赎回在途一致性检查**
- 检查 redeem_request 与 redeem_settle 的匹配情况
- 检测负数在途（到账>申请）
- 检测长期未结（超过 T+N+buffer）

**S6-4 估值断档提示**
- 检测超过 14 天未录估值的产品
- 若期间有交易，提升提示级别

#### 2. 扩展 `backend/api/v1/reconciliation.py`
新增/完善 API 端点：
- `GET /api/reconciliation/warnings` - 获取所有警告（支持过滤）
- `GET /api/reconciliation/account_diffs` - 账户对账差异
- `GET /api/reconciliation/redeem_check` - 赎回一致性检查
- `GET /api/reconciliation/valuation_gaps` - 估值断档产品

#### 3. 可选：新建 `backend/models/warning.py`
如需持久化警告状态（acknowledged/muted）

---

### 二、前端实现

#### 1. 扩展 `frontend/src/services/reconciliation.ts`
完善类型定义和 API 调用：
- `ReconciliationWarning` 类型（支持多种警告类型）
- `getReconciliationWarnings()` - 获取警告列表
- `getAccountDiffs()` - 账户对账
- `getRedeemCheck()` - 赎回检查
- `getValuationGaps()` - 估值断档

#### 2. 新建 `frontend/src/pages/Reconciliation/index.tsx`
对账中心页面（S6-1）：
- 聚合所有 Warning 的列表视图
- 支持按级别/类型/对象/日期过滤
- 显示差异数值和建议动作
- 一键跳转到：账户快照页/产品详情页

#### 3. 增强 `frontend/src/pages/Dashboard/index.tsx`（S6-1）
- 添加"对账提醒（N）"轻量入口
- 展示 Top 3 Warning

#### 4. 增强 `frontend/src/pages/Products/Detail.tsx`（S6-3, S6-4）
- 显示赎回在途异常提示
- 显示估值断档提示

---

### 三、OpenAPI 合同更新
更新 `openapi.yaml`：
- `/api/reconciliation/warnings` 响应 schema
- 新增 `/api/reconciliation/account_diffs`
- 新增 `/api/reconciliation/redeem_check`
- 新增 `/api/reconciliation/valuation_gaps`

---

### 四、实现顺序

1. **后端服务层** - `reconciliation_service.py` 核心逻辑
2. **后端 API** - 扩展 `reconciliation.py` 端点
3. **前端服务** - 完善 `reconciliation.ts` 类型和 API
4. **前端页面** - 新建 `Reconciliation` 对账中心页
5. **Dashboard 集成** - 添加对账提醒入口
6. **产品详情增强** - 赎回/估值异常提示
7. **OpenAPI 更新** - 同步合同

---

### 五、验收用例覆盖

1. **漏录一笔转账** → 账户对账 diff > 阈值
2. **redeem_settle 金额录错** → 在途金额 < 0 警告
3. **两周未录估值** → 估值断档提示
4. **Snapshot 与推导长期不一致** → Warning 可被 acknowledged（如实现 S6-5）

---

### 六、约束边界（不做）

- ❌ 不做任何数据导入（Excel/CSV/银行流水）
- ❌ 不自动更正 Snapshot/Transaction/Valuation
- ❌ 不做精确收益拆分或审计级对账
- ❌ 不做 Lot/InternalHolding 生成分配
- ✅ 只做提示与定位，帮助快速补录/纠错