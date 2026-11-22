"""Agent 对话 API。"""

from fastapi import APIRouter, HTTPException, Query

from app.agent.agent import AgentInvocationError
from app.api.dependencies import AgentDependency
from app.api.schemas import AgentChatRequest, AgentChatResponse

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    summary="提交 Agent 业务分析问题",
)
async def chat(
    request: AgentChatRequest,
    agent: AgentDependency,
) -> AgentChatResponse:
    """调用 DataPilot Agent 处理业务分析问题。"""

    result = await agent.run(
        user_query=request.user_query,
        thread_id=request.thread_id,
        user_id=request.user_id,
    )

    return AgentChatResponse.model_validate(result)


@router.delete(
    "/conversations/{thread_id}",
    summary="删除 Agent 会话及其历史状态",
)
async def delete_conversation(
    thread_id: str,
    agent: AgentDependency,
    user_id: str = Query(min_length=1, max_length=128),
) -> dict[str, bool]:
    """删除指定用户拥有的会话。"""

    try:
        await agent.delete_conversation(
            thread_id=thread_id,
            user_id=user_id,
        )
    except AgentInvocationError as exc:
        status_code = {
            "agent_not_initialized": 503,
            "conversation_not_found": 404,
            "identity_conflict": 403,
            "invalid_thread_id": 422,
            "invalid_user_id": 422,
        }.get(exc.error, 500)

        raise HTTPException(
            status_code=status_code,
            detail=exc.message,
        ) from exc

    return {"success": True}
