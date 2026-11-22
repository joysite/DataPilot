"""DataPilot MCP Server。"""

import inspect
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from app.agent.tool_executor import (
    create_tool_registry,
    execute_tool,
)
from app.database.connection import AsyncSessionLocal


def _build_mcp_tool(name: str, tool: Any, registry: dict) -> Any:
    """根据现有业务工具的 Pydantic Schema 创建 MCP 包装函数。"""

    parameters = []

    for field_name, field in tool.args_schema.model_fields.items():
        annotation = field.annotation
        metadata = list(field.metadata)

        if field.description or field.title:
            metadata.append(
                Field(
                    description=field.description,
                    title=field.title,
                )
            )

        if metadata:
            annotation = Annotated[annotation, *metadata]

        default = inspect.Parameter.empty if field.is_required() else field.default

        parameters.append(
            inspect.Parameter(
                field_name,
                inspect.Parameter.KEYWORD_ONLY,
                default=default,
                annotation=annotation,
            )
        )

    async def mcp_tool(**kwargs: Any) -> Any:
        return await execute_tool(
            name,
            kwargs,
            registry=registry,
        )

    mcp_tool.__name__ = name
    mcp_tool.__doc__ = tool.description
    mcp_tool.__signature__ = inspect.Signature(
        parameters=parameters,
        return_annotation=Any,
    )

    return mcp_tool


def create_mcp_server(
    session_factory=AsyncSessionLocal,
) -> MCPServer:
    """创建绑定指定数据库 Session 工厂的 MCP Server。"""

    registry = create_tool_registry(session_factory)

    server = MCPServer(
        name="datapilot",
        version="0.1.0",
        description="DataPilot 电商业务分析与异常检测服务。",
        instructions=(
            "提供受限的电商业务分析、数据检查、异常检测和明细查询工具。"
            "所有查询均通过预定义业务工具执行，不支持任意 SQL。"
        ),
    )

    for name, tool in registry.items():
        server.add_tool(
            _build_mcp_tool(name, tool, registry),
            name=name,
            description=tool.description,
        )

        registered_tool = server._tool_manager.get_tool(name)
        if registered_tool is None:
            raise RuntimeError(f"MCP 工具注册失败：{name}")

        registered_tool.fn_metadata.arg_model.model_config["extra"] = "forbid"
        registered_tool.fn_metadata.arg_model.model_rebuild(force=True)

        parameters = tool.args_schema.model_json_schema()
        parameters["additionalProperties"] = False

        server._tool_manager._tools[name] = registered_tool.model_copy(
            update={
                "parameters": parameters,
            }
        )

    return server
