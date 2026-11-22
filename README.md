# DataPilot

**DataPilot** 是一个基于本地大语言模型的电商业务数据分析与异常检测 Agent。项目使用 **LangGraph** 构建 Agent 工作流，通过 **Ollama** 调用本地大语言模型，并结合 Python、Pandas 和 SQLite 完成真实的数据查询、统计分析与异常检测。

项目采用“**LLM 负责理解与决策，Python 和 SQL 负责精确计算**”的设计原则，让自然语言交互与确定性业务逻辑协同工作，使分析过程更加可控、可验证和可测试。

## 项目特点

- **本地 LLM**：通过 Ollama 在本地运行模型，减少对外部大模型服务的依赖。
- **可控 Agent 工作流**：使用 LangGraph 组织任务理解、计划生成、工具选择、执行和结果验证。
- **确定性业务计算**：业务指标由 Python 和 SQL 计算，不依赖 LLM 自行推算。
- **受控工具调用**：Agent 只能调用注册的业务工具，不允许任意执行 SQL、Python 或 Shell 代码。
- **业务异常检测**：实现五类电商业务异常检测，并提供独立评估能力。
- **会话状态管理**：使用 SQLite Checkpointer 持久化 Agent 会话状态。
- **完整 Web 界面**：使用 Vue 3 提供经营概览、数据管理、业务分析、异常检测和 Agent 对话页面。
- **MCP 支持**：提供 MCP Server，将业务能力以工具形式对外提供。

## 功能展示

| 页面 | 路由 | 主要功能 |
|---|---|---|
| 经营概览 | `/` | 查看经营数据概况和关键业务指标 |
| Agent 对话 | `/agent` | 与数据分析 Agent 交互、管理会话 |
| 数据管理 | `/data-management` | 导入 CSV、查看导入记录和数据质量 |
| 业务分析 | `/analytics` | 查看业务趋势、品类分析和日期筛选结果 |
| 异常检测 | `/anomalies` | 查看异常检测结果及异常详情 |

## 技术架构

| 类别 | 技术 |
|---|---|
| 编程语言 | Python 3.12 |
| Agent 工作流 | LangGraph |
| LLM 集成 | LangChain |
| 本地模型服务 | Ollama |
| 当前聊天模型 | `qwen2.5-coder:7b` |
| 数据处理 | Pandas |
| 数据校验 | Pydantic |
| 数据库 | SQLite |
| ORM 与异步访问 | SQLAlchemy Async |
| 后端 API | FastAPI |
| MCP | MCP Python SDK |
| 前端框架 | Vue 3 |
| 前端语言 | TypeScript |
| 前端构建 | Vite |
| 前端路由 | Vue Router |
| 前端状态管理 | Pinia |
| UI 组件库 | Element Plus |
| HTTP 客户端 | Axios |
| 自动化测试 | pytest |
| 代码质量 | Ruff |
| 容器配置 | Docker、Docker Compose、Nginx |

## 核心功能

### 1. 数据接入与管理

- 使用模拟数据生成脚本构建可复现的电商业务数据集。
- 支持用户、商品和订单三类业务数据。
- 支持 CSV 数据导入 SQLite。
- 使用 SQLAlchemy ORM 管理数据模型。
- 记录数据导入历史和导入错误。
- 检查数据完整性、字段结构和外键约束。
- 提供数据质量检查接口和前端页面。

当前模拟数据集规模：

| 数据表 | 数据量 |
|---|---:|
| users | 3,000 |
| products | 500 |
| orders | 10,000 |

模拟数据生成使用固定随机种子，便于重复生成和验证。

### 2. 业务分析工具

通过受控业务工具完成数据查询和分析，目前实现六个核心工具：

| 工具 | 功能 |
|---|---|
| `query_database` | 查询订单、商品和用户明细 |
| `inspect_data` | 检查数据表结构、NULL 值、外键完整性和导入历史 |
| `get_order_summary` | 统计 GMV、有效订单量、客单价等订单指标 |
| `analyze_trend` | 分析月度 GMV 趋势 |
| `detect_anomalies` | 检测电商业务数据异常 |
| `compare_categories` | 比较不同商品品类的业务指标 |

业务指标通过 Python 和 SQL 完成计算。

主要指标口径：

- **GMV**：支付、发货和已完成订单的金额总和。
- **有效订单量**：支付、发货和已完成订单的数量。
- **客单价**：GMV / 有效订单量。
- **取消率**：取消订单量 / 全部订单量。

### 3. 业务异常检测

实现五类业务异常检测：

| 异常类型 | 说明 |
|---|---|
| `category_gmv_drop` | 品类 GMV 下降 |
| `order_count_spike` | 订单量异常激增 |
| `region_gmv_concentration` | 地区 GMV 集中度异常 |
| `overall_gmv_drop` | 整体 GMV 下降 |
| `abnormal_order_amount` | 订单金额异常 |

项目通过模拟数据注入异常场景，验证异常检测逻辑，并使用独立 Ground Truth 数据进行评估。

当前评估能力包括：

- 五类异常场景的事件级匹配验证。
- 订单金额异常的订单级评估。
- Precision、Recall、F1 等基础指标计算。
- 保留未匹配检测结果，供后续人工审核。

本地 Ground Truth 和评估报告属于开发数据，不纳入公开版本控制。

### 4. LangGraph Agent

使用 LangGraph 构建多节点 Agent 工作流：

| 节点 | 职责 |
|---|---|
| `context_resolver` | 结合历史对话整理当前问题 |
| `task_understanding` | 理解用户任务 |
| `task_planner` | 生成多步骤执行计划 |
| `tool_selector` | 选择业务工具并生成调用参数 |
| `tool_executor` | 执行受控业务工具 |
| `result_validator` | 验证工具执行结果 |
| `report_generator` | 汇总结果并生成回答 |
| `error_handler` | 统一处理工作流错误 |

当前实现：

- 基于自然语言识别业务分析任务。
- 根据任务生成单步或多步执行计划。
- 按执行计划顺序调用多个授权业务工具。
- 使用 Pydantic Schema 校验工具参数。
- 通过工具白名单限制可执行操作。
- 使用条件边控制工作流执行路径。
- 工具执行失败时进行有限重试和错误恢复。
- 验证工具执行结果并汇总多步骤结果。
- 使用 SQLite Checkpointer 持久化会话状态。
- 通过 Thread ID 隔离不同对话。
- 结合历史对话理解省略表达。
- 对支持的相对日期表达进行确定性解析。

### 5. Agent Memory 与链路追踪

项目实现了基础会话记忆和执行过程追踪能力：

- 通过 Checkpointer 保存会话状态。
- 在多轮对话中维护历史消息和上下文。
- 支持根据历史对话整理当前问题。
- 提供 Agent 工作流节点与执行过程的追踪能力。
- 支持记录和分析 Agent 执行过程中的关键环节。

会话状态持久化与业务数据库使用独立 SQLite 文件。

### 6. Agent 评测

项目提供 Agent 评测数据集、执行器、评估器和运行环境。

当前评测维度包括：

| 指标 | 评估内容 |
|---|---|
| `task_type_accuracy` | 任务类型识别准确性 |
| `plan_accuracy` | 执行计划准确性 |
| `tool_selection_accuracy` | 工具选择准确性 |
| `argument_accuracy` | 工具参数准确性 |
| `result_completeness` | 结果完整性 |
| `answer_topic_coverage` | 回答主题关键词覆盖情况 |

其中 `answer_topic_coverage` 是基于关键词的覆盖指标，不等同于语义准确率。

### 7. MCP Server

项目提供 MCP Server，将 DataPilot 的业务分析能力以 MCP 工具形式对外提供。

MCP Server 复用 Agent 的业务工具注册表、参数校验和执行逻辑，确保 MCP 客户端与 Agent 使用一致的业务能力。

当前注册六个工具：

| 工具 | 功能 |
|---|---|
| `get_order_summary` | 统计订单和经营指标 |
| `analyze_trend` | 分析业务趋势 |
| `compare_categories` | 比较商品品类指标 |
| `detect_anomalies` | 检测业务数据异常 |
| `inspect_data` | 检查数据结构与质量 |
| `query_database` | 查询业务数据明细 |

所有工具均通过预定义业务接口执行，不支持任意 SQL 执行。

### 8. Web 前端

前端使用 Vue 3、TypeScript、Vite 和 Element Plus 构建，提供以下业务页面：

- 经营概览：查看经营数据和关键指标。
- 数据管理：导入业务 CSV、查看导入历史和数据质量。
- 业务分析：查看趋势和品类分析，支持日期筛选。
- 异常检测：查看五类业务异常和相关详情。
- Agent 对话：管理会话并与数据分析 Agent 交互。

前端通过 REST API 与 FastAPI 后端通信。

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
│   ├── nginx.conf
│   ├── Dockerfile
│   └── package.json
├── scripts/
│   ├── generate_mock_data.py  # 模拟数据生成
│   └── inject_anomalies.py    # 异常数据注入
├── data/
│   ├── raw/                   # 本地原始数据
│   └── processed/             # 本地处理后数据
├── evaluation/
│   ├── ground_truth/          # 本地评估标签
│   └── reports/               # 本地评估报告
├── .env.example               # 环境变量示例
├── .gitignore
├── .dockerignore
├── compose.yaml
├── pyproject.toml
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
└── README.md
```

## 环境要求

本地开发环境：

- Ubuntu 24.04（当前开发环境）
- Python 3.12
- Conda 或其他 Python 虚拟环境工具
- Node.js 24+
- npm 12+
- Ollama
- 本地模型 `qwen2.5-coder:7b`

其他 Linux 环境可以参考相同的安装步骤，具体依赖以项目配置为准。

## 本地开发

### 1. 获取项目

```bash
git clone https://github.com/joysite/DataPilot.git
cd DataPilot
```

### 2. 安装后端依赖

项目要求 Python 版本为 `>=3.12,<3.13`。

创建并激活 Python 环境后，在项目根目录执行：

```bash
python -m pip install -e ".[dev]"
```

### 3. 准备 Ollama 和模型

确保本机已安装 Ollama，并启动 Ollama 服务。

拉取项目当前使用的模型：

```bash
ollama pull qwen2.5-coder:7b
```

检查模型：

```bash
ollama list
```

默认本地 Ollama 地址为：

```text
http://localhost:11434
```

### 4. 启动后端

在项目根目录执行：

```bash
uvicorn app.api.main:app --app-dir backend --host 127.0.0.1 --port 8011
```

后端健康检查：

```text
http://127.0.0.1:8011/health
```

FastAPI API 文档：

```text
http://127.0.0.1:8011/docs
```

后端启动时会初始化数据库并初始化 Agent。首次运行会在项目数据目录创建所需的 SQLite 数据文件。

### 5. 启动前端

另开一个终端：

```bash
cd frontend
npm ci
npm run dev
```

浏览器访问：

```text
http://127.0.0.1:5173
```

Vite 开发服务器会将 `/api` 请求代理到：

```text
http://127.0.0.1:8011
```

代理配置位于 `frontend/vite.config.ts`。

### 6. 前端生产构建

在 `frontend/` 目录执行：

```bash
npm run build
```

构建前会执行 TypeScript 项目检查，成功后由 Vite 生成生产文件，默认输出到 `frontend/dist/`。

本地预览生产构建：

```bash
npm run preview
```

## 配置说明

后端使用 `DATAPILOT_` 作为环境变量前缀，并从项目根目录的 `.env` 文件加载本地配置。

主要配置项：

| 配置项 | 默认值或用途 |
|---|---|
| `DATAPILOT_DATABASE_URL` | 业务数据库连接地址，默认使用项目 `data/datapilot.db` |
| `DATAPILOT_CHECKPOINTER_PATH` | Agent Checkpointer 文件路径，默认使用项目 `data/checkpointer.db` |
| `DATAPILOT_OLLAMA_BASE_URL` | Ollama 服务地址，默认 `http://localhost:11434` |
| `DATAPILOT_OLLAMA_MODEL` | 聊天模型，默认 `qwen2.5-coder:7b` |
| `DATAPILOT_OLLAMA_TEMPERATURE` | 模型温度，默认 `0.0` |

本地开发时，如果使用默认配置，可以不创建 `.env` 文件。需要自定义配置时，可以参考 `.env.example`。

## Docker 配置

项目提供以下容器化配置：

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `compose.yaml`
- `.dockerignore`
- `.env.example`

Docker Compose 默认将前端绑定到宿主机 `127.0.0.1:8088`，并使用命名卷 `datapilot_data` 持久化业务数据库和 Agent Checkpointer。

Docker 环境使用的 Ollama 地址默认为：

```text
http://host.docker.internal:11434
```

**重要说明：Docker 配置目前只完成静态检查，尚未进行镜像构建、容器启动或实际部署验收。** 容器访问宿主机 Ollama 还要求 Ollama 服务监听在容器可访问的宿主机网络接口上；仅配置 `host.docker.internal` 并不能保证宿主机服务已经可以从容器访问。不要为了方便而将 Ollama 服务无保护地暴露到公网。

## 测试与代码质量

### 后端自动化测试

在项目根目录执行：

```bash
pytest -c pyproject.toml -q
```

当前正式后端测试套件包含 **90 项测试**，覆盖：

- Agent 核心解析与相关逻辑。
- CSV 数据读取与结构验证。
- SQLite 数据约束。
- 数据导入事务与回滚行为。

当前回归结果：`90 passed`。

### Ruff 检查

```bash
ruff check backend
ruff format --check backend
```

### 前端构建检查

在 `frontend/` 目录执行：

```bash
npm run build
```

前端构建包含 TypeScript 检查和 Vite 生产构建。

## 项目进度与验收范围

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 0 | 项目调研与初始化 | 已完成 |
| Phase 1 | 数据接入模块 | 已完成 |
| Phase 2 | 业务分析工具 | 已完成 |
| Phase 3 | LangGraph 基础 Agent | 已完成 |
| Phase 4 | 动态工作流与错误恢复 | 已完成 |
| Phase 5 | Agent Memory | 已完成 |
| Phase 6 | Agent 评测与链路追踪 | 已完成 |
| Phase 7 | MCP Server | 已完成 |
| Phase 8 | FastAPI 与 Vue 前后端 | 核心业务验收通过 |
| Phase 9 | Docker 部署 | 配置准备与静态验收完成，未执行真实部署 |
| Phase 10 | 项目优化与开源 | 进行中 |

### 已完成的主要验收

- [x] 模拟电商数据生成与异常数据注入。
- [x] SQLite 数据模型和 CSV 导入。
- [x] 六个核心业务分析工具。
- [x] 五类业务异常检测及评估能力。
- [x] LangGraph Agent 工作流与工具调用。
- [x] 多步骤执行计划、结果验证与错误恢复。
- [x] SQLite Checkpointer 和会话状态持久化。
- [x] FastAPI 后端 API。
- [x] Vue 前端核心业务页面。
- [x] 首页、数据管理、业务分析和异常检测页面的核心浏览器验收。
- [x] Agent 页面基础交互和会话管理验收。
- [x] 90 项正式后端自动化测试。
- [x] Ruff 检查与格式检查。
- [x] Docker 配置静态检查。
- [x] MIT License 和基础开源文档。

### 当前限制

- Agent 页面已完成基础交互验收，但真实 Agent 对话请求尚未完成端到端验收。
- Docker 尚未执行镜像构建、容器启动或真实部署。
- 当前项目面向本地单用户开发场景，尚未实现面向公网多用户环境的完整身份认证与授权体系。
- Agent 评测中的 `answer_topic_coverage` 是关键词覆盖指标，不代表完整的语义质量评估。

## 数据与隐私说明

- `data/raw/` 和 `data/processed/` 中的本地业务数据不纳入 Git 版本管理。
- `evaluation/ground_truth/` 和 `evaluation/reports/` 中的本地评估数据与报告不纳入 Git 版本管理。
- `.env` 用于本地环境配置，不应提交到版本控制。
- `.env.example` 仅提供配置项示例，不包含实际环境密钥。
- 请勿将真实用户数据、业务数据库或敏感凭据提交到公开仓库。

## 开源协议

本项目采用 [MIT License](LICENSE)。

## 贡献

欢迎提交 Issue 和 Pull Request。

提交代码前，请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，并运行相关测试与代码质量检查。

## 安全问题

如果发现安全问题，请参考 [SECURITY.md](SECURITY.md) 中的报告说明。

## 项目定位

DataPilot 希望探索一种更可控的本地数据分析 Agent 架构：

- 由 LLM 理解自然语言任务并组织执行计划。
- 由受控业务工具执行真实数据查询与分析。
- 由确定性代码完成指标计算和异常检测。
- 由工作流状态管理、结果验证和评测机制提高执行过程的可追踪性与可验证性。

项目重点不在于让 LLM 任意生成代码，而在于让 Agent 在明确边界内可靠地使用真实业务数据。
