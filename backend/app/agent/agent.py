"""DataPilot Agent 主流程。"""

from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from sqlalchemy.engine import make_url

from app.agent.tracing import AgentTracer, stream_graph_with_tracing
from app.agent.workflow import build_agent_graph
from app.core.config import settings


class AgentInvocationError(Exception):
    """Agent Graph 调用异常，保留错误信息和执行状态。"""

    def __init__(
        self,
        error: str,
        message: str,
        state: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error = error
        self.message = message
        self.state = state if isinstance(state, dict) else {}


class DataPilotAgent:
    """DataPilot 业务分析 Agent。"""

    def __init__(
        self,
        *,
        checkpointer_path: str | Path | None = None,
        tool_registry: dict[str, Any] | None = None,
        enable_memory: bool = True,
    ) -> None:
        """初始化 Agent 属性，支持评测环境依赖注入。"""

        if not isinstance(enable_memory, bool):
            raise ValueError("enable_memory 必须是布尔值")

        if tool_registry is not None and not isinstance(tool_registry, dict):
            raise ValueError("tool_registry 必须是字典")

        if checkpointer_path is not None:
            if not isinstance(checkpointer_path, (str, Path)):
                raise ValueError("checkpointer_path 必须是字符串或 Path")

            if not str(checkpointer_path).strip():
                raise ValueError("checkpointer_path 不能为空")

            if str(checkpointer_path).strip() == ":memory:":
                raise ValueError("Checkpointer 必须使用独立 SQLite 文件")

        self.checkpointer_path = checkpointer_path
        self.tool_registry = tool_registry
        self.enable_memory = enable_memory

        self.graph = None
        self.checkpointer = None
        self._saver_context = None

    async def initialize(self) -> None:
        """初始化 SQLite Checkpointer 并编译工作流。"""

        if self.graph is not None:
            return

        production_url = make_url(settings.database_url)

        if production_url.drivername not in {
            "sqlite",
            "sqlite+aiosqlite",
        }:
            raise ValueError("Agent Checkpointer 仅支持 SQLite 数据库")

        if not production_url.database:
            raise ValueError("SQLite 数据库文件路径不能为空")

        production_path = Path(production_url.database).expanduser().resolve()

        if self.checkpointer_path is None:
            database_path = Path(settings.checkpointer_path).expanduser().resolve()
        else:
            database_path = Path(self.checkpointer_path).expanduser().resolve()

        if database_path == production_path:
            raise ValueError("Checkpointer 不能与正式数据库使用同一个文件")

        if database_path.name == ":memory:":
            raise ValueError("Checkpointer 必须使用 SQLite 文件")

        database_path.parent.mkdir(parents=True, exist_ok=True)

        self._saver_context = AsyncSqliteSaver.from_conn_string(str(database_path))

        try:
            self.checkpointer = await self._saver_context.__aenter__()
            await self.checkpointer.setup()

            self.graph = build_agent_graph(
                checkpointer=self.checkpointer,
                enable_memory=self.enable_memory,
            )
        except Exception:
            try:
                await self._saver_context.__aexit__(None, None, None)
            finally:
                self._saver_context = None
                self.checkpointer = None
                self.graph = None
            raise

    async def close(self) -> None:
        """关闭 Checkpointer 并释放数据库连接。"""

        if self._saver_context is None:
            return

        try:
            await self._saver_context.__aexit__(None, None, None)
        finally:
            self._saver_context = None
            self.checkpointer = None
            self.graph = None

    async def delete_conversation(
        self,
        thread_id: str,
        user_id: str,
    ) -> None:
        """删除指定用户拥有的会话及其全部 Checkpoint。"""

        if not isinstance(thread_id, str) or not thread_id.strip():
            raise AgentInvocationError(
                "invalid_thread_id",
                "会话 ID 不能为空。",
            )

        if not isinstance(user_id, str) or not user_id.strip():
            raise AgentInvocationError(
                "invalid_user_id",
                "用户 ID 不能为空。",
            )

        if self.graph is None or self.checkpointer is None:
            raise AgentInvocationError(
                "agent_not_initialized",
                "Agent 尚未初始化，无法删除会话。",
            )

        normalized_thread_id = thread_id.strip()
        normalized_user_id = user_id.strip()

        config = {
            "configurable": {
                "thread_id": normalized_thread_id,
                "user_id": normalized_user_id,
            }
        }

        snapshot = await self.graph.aget_state(config)
        values = snapshot.values or {}

        if not values:
            raise AgentInvocationError(
                "conversation_not_found",
                "会话不存在或已经删除。",
            )

        thread_owner_id = values.get("thread_owner_id")

        if thread_owner_id != normalized_user_id:
            raise AgentInvocationError(
                "identity_conflict",
                "会话身份冲突：当前用户无权删除该会话。",
            )

        await self.checkpointer.adelete_thread(normalized_thread_id)

    async def _invoke_graph(
        self,
        user_query: str,
        thread_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """执行一次带链路追踪的 Agent 调用。"""

        trace_thread_id = (
            thread_id if isinstance(thread_id, str) and thread_id.strip() else None
        )
        tracer = AgentTracer(thread_id=trace_thread_id)

        async with tracer.span("agent.invoke"):
            return await self._invoke_graph_untraced(
                user_query=user_query,
                thread_id=thread_id,
                user_id=user_id,
                tracer=tracer,
            )

    async def _invoke_graph_untraced(
        self,
        user_query: str,
        thread_id: str,
        user_id: str,
        tracer: AgentTracer,
    ) -> dict[str, Any]:
        """执行 Graph 并返回完整工作流状态。"""

        if not isinstance(thread_id, str) or not thread_id.strip():
            raise AgentInvocationError(
                "invalid_thread_id",
                "会话 ID 不能为空。",
            )

        if not isinstance(user_query, str) or not user_query.strip():
            raise AgentInvocationError(
                "invalid_input",
                "用户问题不能为空",
            )

        if not isinstance(user_id, str) or not user_id.strip():
            raise AgentInvocationError(
                "invalid_user_id",
                "用户 ID 不能为空。",
            )

        if self.graph is None:
            raise AgentInvocationError(
                "agent_not_initialized",
                "Agent 尚未初始化，请先调用 initialize()。",
            )

        normalized_thread_id = thread_id.strip()
        normalized_user_id = user_id.strip()
        normalized_query = user_query.strip()

        configurable = {
            "thread_id": normalized_thread_id,
            "user_id": normalized_user_id,
        }

        if self.tool_registry is not None:
            configurable["tool_registry"] = self.tool_registry

        config = {"configurable": configurable}

        try:
            snapshot = await self.graph.aget_state(config)
            thread_owner_id = (snapshot.values or {}).get("thread_owner_id")

            if thread_owner_id and thread_owner_id != normalized_user_id:
                raise AgentInvocationError(
                    "identity_conflict",
                    "会话身份冲突：当前用户无权访问该会话。",
                )

            initial_state = {
                "user_query": normalized_query,
                "messages": [
                    HumanMessage(content=normalized_query),
                ],
            }

            result = await stream_graph_with_tracing(
                graph=self.graph,
                input_state=initial_state,
                config=config,
                tracer=tracer,
            )

            if not isinstance(result, dict):
                raise TypeError("Agent Graph 必须返回字典状态")

            return result

        except AgentInvocationError:
            raise
        except Exception as exc:
            execution_state = {}

            try:
                snapshot = await self.graph.aget_state(config)

                if isinstance(snapshot.values, dict):
                    execution_state = snapshot.values.copy()

            except Exception:
                pass

            raise AgentInvocationError(
                "workflow_execution_error",
                "Agent 工作流执行失败，请稍后重试。",
                state=execution_state,
            ) from exc

    async def run_for_evaluation(
        self,
        user_query: str,
        thread_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """执行评测工作流并返回完整 Graph 状态。"""

        try:
            return await self._invoke_graph(
                user_query=user_query,
                thread_id=thread_id,
                user_id=user_id,
            )
        except AgentInvocationError as exc:
            state = exc.state.copy()
            state["error_type"] = exc.error
            state["error"] = exc.message

            return state

    async def run(
        self,
        user_query: str,
        thread_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """执行业务工作流并返回统一业务结果。"""

        try:
            result = await self._invoke_graph(
                user_query=user_query,
                thread_id=thread_id,
                user_id=user_id,
            )
        except AgentInvocationError as exc:
            return {
                "success": False,
                "error": exc.error,
                "message": exc.message,
            }

        error_type = result.get("error_type")

        if error_type:
            failure = {
                "success": False,
                "error": error_type,
                "message": result.get("error")
                or result.get("final_answer")
                or "请求处理过程中发生错误，请稍后重试。",
            }

            if error_type == "answer_generation_error":
                failure.update(
                    {
                        "tool_name": result.get("tool_name"),
                        "arguments": result.get("tool_arguments"),
                        "result": result.get("tool_result"),
                    }
                )

            return failure

        return {
            "success": True,
            "tool_name": result["tool_name"],
            "arguments": result["tool_arguments"],
            "result": result["tool_result"],
            "answer": result["final_answer"],
        }
