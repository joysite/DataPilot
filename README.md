# DataPilot

DataPilot 是一个基于本地大语言模型的电商业务数据分析与异常检测 Agent。

项目使用 LangGraph 构建 Agent 工作流，通过 Ollama 调用本地大语言模型，并结合 Python、Pandas 和 SQLite 完成真实的数据查询、统计分析与异常检测。

## 项目目标

构建一个能够理解自然语言业务问题、规划分析步骤、调用受控业务工具，并生成结构化分析结果的本地数据分析 Agent。

核心设计原则：

- LLM 负责理解任务、规划步骤和调用工具。
- Python 和 SQL 负责真实的数据查询与统计计算。
- Agent 只能通过授权的业务工具访问数据。
- 不允许 LLM 任意执行 SQL、Python 或 Shell 代码。
- 优先保证分析结果的准确性、可验证性和可测试性。

## 技术栈

| 类别 | 技术 |
|---|---|
| 编程语言 | Python 3.12 |
| Agent 工作流 | LangGraph |
| 大语言模型 | Ollama |
| 当前聊天模型 | qwen2.5-coder:7b |
| Embedding 模型 | nomic-embed-text |
| 数据处理 | Pandas |
| 数据校验 | Pydantic |
| 数据库 | SQLite |
| ORM | SQLAlchemy |
| 后端 API | FastAPI |
| 测试 | pytest |
| 代码质量 | Ruff |

## 项目结构

```text
DataPilot/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── database/
│   │   ├── ingestion/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── tools/
│   │   ├── agent/
│   │   └── api/
│   └── tests/
├── data/
│   ├── raw/
│   └── processed/
├── evaluation/
├── docs/
├── scripts/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```


## 开发环境

- Ubuntu 24.04
- Python 3.12
- Conda
- Ollama

当前使用的本地模型：

- `qwen2.5-coder:7b`
- `nomic-embed-text:latest`

## 安装

创建并激活 Conda 环境后，在项目根目录执行：

```bash
python -m pip install -e ".[dev]"
```

确保 Ollama 服务正常运行，并提前拉取所需模型。

## 开发与检查

```bash
ruff check backend
ruff format --check backend
pytest -q
```


## 开发进度

当前处于 Phase 0：项目基础设施搭建。

- [x] Python 环境准备
- [x] Ollama 本地模型调用验证
- [x] 项目依赖安装与检查
- [x] 项目目录结构创建
- [x] Git 仓库初始化
- [x] 基础 Ruff 与 pytest 配置
- [ ] Phase 0 最终验收

后续将按照项目开发计划逐步实现数据导入、业务分析工具、LangGraph Agent 工作流、评估体系及 API 服务。
