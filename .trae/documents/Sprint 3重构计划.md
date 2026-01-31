## Sprint 3 重大变更修改计划

### 核心变更
1. **Lot/批次完全内部化** - 用户无感知，删除所有 Lot UI
2. **产品详情页成为唯一入口** - 统一录入买/卖/估值
3. **走势可视化升级** - 区分 manual/interpolated/资金事件
4. **收益指标明确为"参考值"** - 避免误导

### 阶段一：删除多余功能
- 删除前端：LotValuations页面、lot_valuations.ts、lots.ts
- 删除后端：lots.py、lot_service.py、LotValuation相关接口
- 删除菜单：批次估值（Lot）

### 阶段二：新增 Transaction
- 新增 Transaction 模型（buy/redeem_request/redeem_settle/fee）
- 新增 transactions.py API
- 新增 transaction_service.py

### 阶段三：重构产品详情页
- 完全重写 Detail.tsx
- 新增内联估值录入
- 新增交易操作表单
- 走势显示 manual（实心）+ interpolated（空心）+ 事件线
- 指标默认显示"参考值"

### 阶段四：后端估值序列重构
- 修改 get_valuation_series：只在manual点之间插值，之外断线
- 新增 /chart-v2 接口，返回 points + events

### 阶段五：指标计算重构
- 参考收益率：使用插值市值+现金流近似
- 严格收益率：无现金流且manual≥2周时才显示

### 文件变更汇总
| 操作 | 文件 |
|------|------|
| 删除 | frontend/src/pages/LotValuations/ |
| 删除 | frontend/src/services/lot_valuations.ts |
| 删除 | frontend/src/services/lots.ts |
| 删除 | backend/api/v1/lots.py |
| 删除 | backend/services/lot_service.py |
| 新增 | backend/models/transaction.py |
| 新增 | backend/api/v1/transactions.py |
| 新增 | backend/services/transaction_service.py |
| 新增 | frontend/src/services/transactions.ts |
| 重写 | frontend/src/pages/Products/Detail.tsx |
| 修改 | backend/api/v1/valuations.py |
| 修改 | backend/services/valuation_service.py |
| 修改 | frontend/.umirc.ts |

请确认后开始执行。