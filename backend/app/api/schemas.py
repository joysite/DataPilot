"""Agent API 请求与响应 Schema。"""

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmptyString = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]


class AgentChatRequest(BaseModel):
    """Agent 对话请求。"""

    model_config = ConfigDict(extra="forbid")

    user_query: Annotated[NonEmptyString, StringConstraints(max_length=4000)]
    thread_id: Annotated[NonEmptyString, StringConstraints(max_length=128)]
    user_id: Annotated[NonEmptyString, StringConstraints(max_length=128)]


class AgentChatResponse(BaseModel):
    """Agent 对话响应。"""

    model_config = ConfigDict(extra="forbid")

    success: bool
    tool_name: str | None = None
    arguments: dict[str, Any] | None = None
    result: Any = None
    answer: str | None = None
    error: str | None = None
    message: str | None = None
