"""Agent API 依赖。"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.agent.agent import DataPilotAgent


def get_agent(request: Request) -> DataPilotAgent:
    """获取应用生命周期内初始化的 Agent。"""

    agent = getattr(request.app.state, "agent", None)

    if not isinstance(agent, DataPilotAgent):
        raise HTTPException(
            status_code=503,
            detail="Agent 服务尚未初始化。",
        )

    return agent


AgentDependency = Annotated[DataPilotAgent, Depends(get_agent)]
