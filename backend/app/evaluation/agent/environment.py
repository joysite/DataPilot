"""Agent 评测环境组装与生命周期管理。"""

from pathlib import Path
from typing import Any

from sqlalchemy.engine import make_url

from app.agent.agent import DataPilotAgent
from app.agent.tool_executor import create_tool_registry
from app.core.config import settings
from app.evaluation.agent.database import (
    close_evaluation_database,
    create_evaluation_database,
    initialize_evaluation_database,
)
from app.evaluation.agent.loader import seed_evaluation_database


class AgentEvaluationEnvironment:
    """管理与正式业务环境隔离的 Agent 评测资源。"""

    def __init__(
        self,
        *,
        database_url: str,
        checkpointer_path: str | Path,
    ) -> None:
        """初始化评测环境配置，不创建数据库连接或启动 Agent。"""

        if not isinstance(database_url, str) or not database_url.strip():
            raise ValueError("评测数据库 URL 不能为空")

        if not isinstance(checkpointer_path, (str, Path)):
            raise ValueError("Checkpointer 路径必须是字符串或 Path")

        if not str(checkpointer_path).strip():
            raise ValueError("Checkpointer 路径不能为空")

        self.database_url = database_url
        self.checkpointer_path = Path(checkpointer_path).expanduser().resolve()

        evaluation_url = make_url(database_url)
        if evaluation_url.drivername != "sqlite+aiosqlite":
            raise ValueError("评测数据库必须使用 sqlite+aiosqlite")

        if not evaluation_url.database or evaluation_url.database == ":memory:":
            raise ValueError("评测数据库必须使用独立 SQLite 文件")

        evaluation_path = Path(evaluation_url.database).expanduser().resolve()

        if self.checkpointer_path.name == ":memory:":
            raise ValueError("Checkpointer 必须使用独立 SQLite 文件")

        if evaluation_path == self.checkpointer_path:
            raise ValueError("评测数据库与 Checkpointer 必须使用不同文件")

        production_url = make_url(settings.database_url)
        if production_url.drivername not in {"sqlite", "sqlite+aiosqlite"}:
            raise ValueError("当前正式数据库不是受支持的 SQLite 数据库")

        production_path = Path(production_url.database).expanduser().resolve()

        if evaluation_path == production_path:
            raise ValueError("评测数据库不能与正式业务数据库使用同一个文件")

        if self.checkpointer_path == production_path:
            raise ValueError("评测 Checkpointer 不能与正式数据库使用同一个文件")

        production_checkpointer_path = (
            Path(settings.checkpointer_path).expanduser().resolve()
        )

        if self.checkpointer_path == production_checkpointer_path:
            raise ValueError("评测 Checkpointer 不能与正式 Checkpointer 使用同一个文件")

        self.engine = None
        self.session_factory = None
        self.tool_registry: dict[str, Any] | None = None
        self.agent: DataPilotAgent | None = None

    async def initialize(self) -> None:
        """按顺序初始化评测数据库和隔离 Agent。"""

        if self.agent is not None:
            return

        try:
            self.engine, self.session_factory = create_evaluation_database(
                self.database_url
            )

            await initialize_evaluation_database(self.engine)
            await seed_evaluation_database(self.session_factory)

            self.tool_registry = create_tool_registry(self.session_factory)

            self.agent = DataPilotAgent(
                checkpointer_path=self.checkpointer_path,
                tool_registry=self.tool_registry,
                enable_memory=False,
            )

            await self.agent.initialize()

        except Exception:
            await self.close()
            raise

    async def close(self) -> None:
        """关闭 Agent 和评测数据库，释放全部资源。"""

        try:
            if self.agent is not None:
                await self.agent.close()
        finally:
            self.agent = None
            self.tool_registry = None
            self.session_factory = None

            if self.engine is not None:
                try:
                    await close_evaluation_database(self.engine)
                finally:
                    self.engine = None
