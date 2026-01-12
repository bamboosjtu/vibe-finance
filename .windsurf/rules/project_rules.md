---
trigger: always_on
---

# 项目配置

## 项目概述
这是一个投资记录与分析工具，帮助用户统一记录账户、理财与净值，自动汇总资产负债和可用现金，预测到期资金，计算年化/回撤/XIRR并对比产品，提醒闲置资金，辅助稳健再投资。

## 技术栈
- 前端：React 18 + UmiMax（基于 Umi 4）  
- UI 框架：Ant Design Pro  
- 后端：Python + Flask  
- 数据库：SQLite  
- ORM：SQLModel（基于 SQLAlchemy + Pydantic）  
- 环境管理：uv（用于 Python 依赖与虚拟环境）  
- 构建工具：Umi（集成 Webpack/Vite）  

## 目录结构
- frontend/  
  - src/pages：页面路由组件（遵循 Umi 约定式路由）  
  - src/components：通用或业务组件  
  - src/services：API 请求封装  
  - src/models：UmiMax 状态管理模型  
  - src/utils：工具函数  
  - src/types：TypeScript 类型定义  
  - mock/：本地模拟数据  
  - config/：Umi 配置  

- backend/  
  - app.py                # Flask 应用工厂入口  
  - config.py             # 配置类（如 DATABASE_URL、DEBUG 等）  
  - extensions.py         # Flask 扩展初始化（如需要）  
  - api/  
    - __init__.py          
    - v1/                  # API 版本 1 路由  
  - services/             # 业务逻辑层（模块化，不预设具体文件）  
  - models/               # 数据模型定义  
  - utils/                # 通用工具函数  
  - requirements.txt      # Python 依赖清单（由 uv 生成）  
  - .env.example          # 环境变量示例文件  

- db/  
  - construction.db       # SQLite 数据库文件（开发用，不提交）  
  - schema.sql            # 数据库表结构初始化脚本  

- doc/  
  - analysis_spec.md      # 承载力分析逻辑说明  
  - deployment_guide.md   # 部署文档  

- openapi.yml             # 前后端接口规范（OpenAPI 3.0）  
- README.md               # 项目总览与快速启动指引  
- .gitignore              # 忽略构建产物、数据库文件、环境文件等  

## 编码规范
- 前端使用函数式组件，禁用 class 组件  
- 所有 API 调用通过 frontend/src/services 管理，并与 openapi.yml 一致  
- 组件文件使用 PascalCase 命名，工具函数使用 camelCase  
- TypeScript 禁用 `any`，启用严格模式  
- Flask 采用应用工厂 + Blueprint 模式，路由与业务逻辑分离  
- 业务逻辑必须实现在 services/，api/ 仅处理请求/响应  
- 所有数据库操作必须通过 SQLModel 模型和会话（Session）完成  
- SQLModel 模型需同时用于数据库表定义和 Pydantic 验证（利用其双重继承特性）  
- 响应格式统一：{ "code": int, "data": ..., "message": str }  
- 所有配置通过 config.py 或环境变量注入  

## 禁止事项
- 前端禁止使用内联样式（必须用 Ant Design 或 CSS Modules）  
- 禁止在 api/ 中编写业务逻辑  
- 禁止提交 db/construction.db 或 .env 到版本控制  
- 禁止硬编码业务参数（如权重、阈值）  
- 禁止在后端使用全局 Flask app 实例  
- 禁止前后端接口偏离 openapi.yml 定义  

