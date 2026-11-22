"""DataPilot FastAPI 应用入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.agent.agent import DataPilotAgent
from app.api.routes.agent import router as agent_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.anomalies import router as anomalies_router
from app.api.routes.data_inspection import router as data_inspection_router
from app.api.routes.imports import router as imports_router
from app.database.connection import close_db
from app.database.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理 FastAPI 应用及 Agent 的生命周期。"""

    agent = DataPilotAgent()

    try:
        await init_db()
        await agent.initialize()
        app.state.agent = agent
        yield
    finally:
        try:
            await agent.close()
        finally:
            await close_db()


app = FastAPI(
    title="DataPilot API",
    description="Local LLM-powered e-commerce data analysis and anomaly detection.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(
    agent_router,
    prefix="/api/v1",
)

app.include_router(
    analytics_router,
    prefix="/api/v1",
)

app.include_router(
    anomalies_router,
    prefix="/api/v1",
)

app.include_router(
    imports_router,
    prefix="/api/v1",
)

app.include_router(
    data_inspection_router,
    prefix="/api/v1",
)


@app.get("/health", tags=["Health"])
async def health(request: Request) -> dict:
    """检查 API 和 Agent 初始化状态。"""

    agent = getattr(request.app.state, "agent", None)

    return {
        "status": "healthy",
        "agent_initialized": (agent is not None and agent.graph is not None),
    }
