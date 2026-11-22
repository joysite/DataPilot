# DataPilot

DataPilot 是一个基于本地大语言模型的电商业务数据分析与异常检测 Agent。

项目使用 **LangGraph** 构建 Agent 工作流，通过 **Ollama** 调用本地大语言模型，并结合 Python、Pandas 和 SQLite 完成真实的数据查询、统计分析与异常检测。

项目遵循 LLM 负责理解与决策、Python 和 SQL 负责精确计算的设计原则，确保分析过程可控、结果可验证。

## 项目目标

构建一个能够理解自然语言业务问题、规划分析任务、调用受控业务工具，并生成结构化分析结果的本地数据分析 Agent。

核心设计原则：

- LLM 负责理解任务、规划分析步骤和选择业务工具。
- Python 和 SQL 负责真实的数据查询与统计计算。
- Agent 只能通过授权的业务工具访问数据。
- 不允许 LLM 任意执行 SQL、Python 或 Shell 代码。
- 优先保证分析结果的准确性、可验证性和可测试性。
- 使用本地模型完成推理，减少对外部大模型服务的依赖。

## 技术栈

| 类别 | 技术 |
|---|---|
| 编程语言 | Python 3.12 |
| Agent 工作流 | LangGraph |
| LLM 框架 | LangChain |
| 大语言模型服务 | Ollama |
| 当前聊天模型 | qwen2.5-coder:7b |

| 数据处理 | Pandas |
| 数据校验 | Pydantic |
| 数据库 | SQLite |
| ORM | SQLAlchemy |
| 异步数据库访问 | SQLAlchemy Async |
| 后端 API | FastAPI |
| 前端框架 | Vue 3 |
| 前端构建 | Vite |
| 前端语言 | TypeScript |
| 前端状态管理 | Pinia |
| 前端 UI | Element Plus |
| 测试 | pytest |
| 代码质量 | Ruff |

## 核心功能

### 1. 数据接入

- 使用模拟数据生成脚本构建电商业务数据集。
- 支持用户、商品和订单数据。
- 使用固定随机种子生成可复现的数据。
- 支持将 CSV 数据导入 SQLite。
- 使用 SQLAlchemy ORM 管理数据模型。
- 实现数据导入记录和导入错误记录。
- 检查数据完整性和外键约束。

当前数据集包含：

| 数据表 | 数据量 |
|---|---:|
| users | 3,000 |
| products | 500 |
| orders | 10,000 |

### 2. 业务分析工具

通过受控业务工具完成数据查询和分析，目前已实现六个核心工具：

| 工具 | 功能 |
|---|---|
| `query_database` | 查询订单、商品和用户明细 |
| `inspect_data` | 检查数据表结构、NULL 值、外键完整性和导入历史 |
| `get_order_summary` | 统计 GMV、有效订单量、客单价等订单指标 |
| `analyze_trend` | 分析月度 GMV 趋势 |
| `detect_anomalies` | 检测电商业务数据异常 |
| `compare_categories` | 比较不同商品品类的业务指标 |

业务指标通过 Python 和 SQL 完成计算，不依赖 LLM 自行推算。

主要指标口径：

- GMV：支付、发货和已完成订单的金额总和。
- 有效订单量：支付、发货和已完成订单的数量。
- 客单价：GMV / 有效订单量。
- 取消率：取消订单量 / 全部订单量。

### 3. 业务异常检测

实现了五类业务异常检测：

- `category_gmv_drop`：品类 GMV 下降。
- `order_count_spike`：订单量异常激增。
- `region_gmv_concentration`：地区 GMV 集中度异常。
- `overall_gmv_drop`：整体 GMV 下降。
- `abnormal_order_amount`：订单金额异常。

通过模拟数据注入异常场景，验证异常检测逻辑，并使用独立的 Ground Truth 数据进行评估。

当前异常检测评估结果：

- 五类异常场景均完成事件级匹配验证。
- 订单金额异常完成订单级评估。
- 已实现 Precision、Recall、F1 等基础指标计算。
- 未匹配检测结果保留供人工审核，不直接认定为误报。

### 4. LangGraph Agent

使用 LangGraph 构建基础 Agent 工作流。

当前实现的节点：

- `context_resolver`：结合历史对话整理当前问题。
- `task_understanding`：理解用户任务。
- `task_planner`：生成多步骤执行计划。
- `tool_selector`：选择业务工具并生成调用参数。
- `tool_executor`：执行受控业务工具。
- `result_validator`：验证工具执行结果。
- `report_generator`：汇总执行结果并生成最终回答。
- `error_handler`：统一处理工作流错误。

当前支持：

- 基于自然语言识别业务分析任务。
- 根据任务生成单步或多步执行计划。
- 按执行计划顺序调用多个授权业务工具。
- 使用 Pydantic Schema 校验工具参数。
- 通过工具白名单限制可执行操作。
- 使用条件边控制工作流执行路径。
- 工具执行失败时进行有限重试。
- 验证工具执行结果并统一处理错误。
- 汇总多步骤执行结果并生成最终回答。
- 使用 SQLite Checkpointer 持久化会话状态。
- 通过 Thread ID 隔离不同对话。
- 结合历史对话理解省略表达。
- 对支持的相对日期表达进行确定性解析。


## 项目结构

```text
DataPilot/
├── backend/
│   ├── app/
│   │   ├── agent/             # LangGraph Agent 工作流、节点与工具执行
│   │   ├── api/               # FastAPI 应用与 REST API 路由
│   │   ├── core/              # 配置与基础模块
│   │   ├── database/          # 数据库连接、会话与初始化
│   │   ├── evaluation/        # Agent 评测与异常检测评估
│   │   │   └── agent/         # Agent 评测数据集、执行器与指标
│   │   ├── ingestion/         # CSV 数据读取与结构验证
│   │   ├── mcp_server/        # MCP Server
│   │   ├── models/            # SQLAlchemy 数据模型
│   │   ├── repositories/      # 数据访问层
│   │   ├── schemas/           # Pydantic 数据结构
│   │   ├── services/          # 业务逻辑层
│   │   └── tools/             # Agent 业务工具
│   ├── tests/                 # 后端自动化测试
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/               # 后端 API 请求
│   │   ├── assets/            # 静态资源
│   │   ├── components/        # 通用组件
│   │   ├── layouts/           # 页面布局
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # Pinia 状态管理
│   │   └── views/             # 业务页面
│   ├── nginx.conf             # Nginx 生产环境配置
│   ├── Dockerfile
│   └── package.json
├── scripts/
│   ├── generate_mock_data.py  # 模拟数据生成
│   └── inject_anomalies.py    # 异常数据注入
├── data/
│   ├── raw/                   # 原始数据
│   └── processed/             # 处理后的数据
├── evaluation/
│   ├── ground_truth/          # 本地评估标签
│   └── reports/               # 本地评估报告
├── .env.example               # 环境变量示例
├── .gitignore
├── .dockerignore
├── compose.yaml               # Docker Compose 配置
├── pyproject.toml
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
└── README.md
```

说明：

- `data/raw/`、`data/processed/` 中的本地业务数据不纳入 Git 版本管理。
- `evaluation/ground_truth/` 和 `evaluation/reports/` 中的本地评估数据与报告不纳入 Git 版本管理。
- `.env` 用于本地环境配置，不应提交；`.env.example` 提供配置参考。
- Docker 配置目前已完成静态检查，尚未进行镜像构建、容器启动或真实部署。


## 开发环境

- Ubuntu 24.04
- Python 3.12
- Conda
- Ollama

当前使用的本地模型：

- `qwen2.5-coder:7b`

## 安装

创建并激活 Conda 环境后，在项目根目录执行：

```bash
python -m pip install -e ".[dev]"
```

确保 Ollama 服务正常运行，并提前准备好项目所需的本地模型。

检查 Ollama 服务：

```bash
ollama list
```

## 开发与检查

代码质量检查：

```bash
ruff check backend
ruff format --check backend
```

运行 pytest：

```bash
pytest -q
```

当前已建立正式自动化后端测试套件，共 90 项测试，覆盖 Agent 核心解析、CSV 数据读取与校验、SQLite 数据约束和导入事务。运行 `pytest -c pyproject.toml -q` 即可执行全部测试。

## 开发进度

项目按照阶段计划逐步开发。

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 0 | 项目调研与初始化 | 已完成 |
| Phase 1 | 数据接入模块 | 已完成 |
| Phase 2 | 业务分析工具 | 已完成 |
| Phase 3 | LangGraph 基础 Agent | 已完成 |
| Phase 4 | 动态工作流与错误恢复 | 已完成 |
| Phase 5 | Agent Memory | 已完成 |
| Phase 6 | Agent 评测与链路追踪 | 已完成  |
| Phase 7 | MCP Server | 已完成 |
| Phase 8 | FastAPI 与 Vue 前后端 | 已完成（核心业务验收通过） |
| Phase 9 | Docker 部署 | 配置准备与静态验收已完成（未执行构建、启动或部署） |
| Phase 10 | 项目优化与开源 | 进行中 |

### 已完成阶段

- [x] Python 开发环境与项目依赖配置
- [x] Ollama 本地模型调用验证
- [x] 模拟电商数据生成
- [x] 业务异常数据注入
- [x] SQLite 数据库与 ORM 模型
- [x] CSV 数据导入及完整性检查
- [x] 六个核心业务分析工具
- [x] 五类业务异常检测
- [x] 异常检测 Ground Truth 评估
- [x] LangGraph 基础工作流
- [x] Agent 工具选择、执行与结果验证
- [x] 多步骤执行计划与动态工具编排
- [x] 工具执行失败重试与错误恢复
- [x] 基础错误处理与条件路由
- [x] 真实 Ollama 模型调用验收
- [x] SQLite Checkpointer 持久化
- [x] Thread ID 会话隔离
- [x] 短期对话记忆与历史消息维护
- [x] 多轮对话上下文整理
- [x] 相对日期确定性解析
- [x] FastAPI 后端 API 与 Vue 前端
- [x] 首页经营概况展示
- [x] CSV 数据导入与导入历史
- [x] 数据质量与关联完整性检查
- [x] 业务分析、月度 GMV 趋势与日期筛选
- [x] 五类业务异常检测及详情展示
- [x] Agent 页面基础交互与会话管理
- [x] Phase 8 前后端核心业务浏览器验收

### 当前进度与后续计划

Phase 9 已完成 Dockerfile、Docker Compose、环境变量和数据卷配置准备，并通过静态配置检查。尚未执行镜像构建、容器启动或实际部署。

Phase 10 正在进行项目优化与开源整理，当前已完成正式后端自动化测试体系和基础开源文档。

当前已完成的交付内容：
- [x] 90 项正式后端自动化测试
- [x] 后端 Ruff 检查与格式检查
- [x] MIT License
- [x] CHANGELOG.md
- [x] CONTRIBUTING.md
- [x] SECURITY.md

当前仍需注意：
- Phase 8 已完成前后端核心业务验收。
- Agent 真实对话尚未进行端到端验收。
- Docker 仅完成配置准备与静态检查，未进行真实构建、启动或部署。

## 项目定位

DataPilot 是一个以本地 LLM 为任务理解与工具调度核心、以 Python 和 SQL 为业务计算基础的电商数据分析 Agent。

项目重点探索：

- LangGraph 工作流设计。
- 本地 LLM 工具调用。
- Agent 与确定性业务工具的协作。
- 结构化业务数据分析。
- 异常检测与结果评估。
- Agent 执行过程的可控性与可验证性。
