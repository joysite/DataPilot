"""受限业务明细查询工具。"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from langchain_core.tools import StructuredTool

from app.database.connection import AsyncSessionLocal
from app.schemas.query import QueryDatabaseRequest
from app.services.query_service import QueryDatabaseService


def create_query_tools(session_factory=AsyncSessionLocal):
    """创建绑定指定数据库 Session 工厂的明细查询工具。"""

    async def _query_database(
        entity: Literal["orders", "products", "users"],
        limit: int = 20,
        order_status: Literal[
            "pending",
            "paid",
            "shipped",
            "completed",
            "cancelled",
        ]
        | None = None,
        user_id: str | None = None,
        product_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """执行受限业务明细查询。"""

        request = QueryDatabaseRequest(
            entity=entity,
            limit=limit,
            order_status=order_status,
            user_id=user_id,
            product_id=product_id,
        )

        async with session_factory() as session:
            results = await QueryDatabaseService().query(
                session=session,
                request=request,
            )

        serialized_results = []

        for row in results:
            serialized_row = {}

            for key, value in row.items():
                if isinstance(value, Decimal):
                    serialized_row[key] = str(value)
                elif isinstance(value, datetime):
                    serialized_row[key] = value.isoformat()
                else:
                    serialized_row[key] = value

            serialized_results.append(serialized_row)

        return serialized_results

    query_database = StructuredTool.from_function(
        coroutine=_query_database,
        name="query_database",
        description=(
            "查询业务数据库中的订单、商品或用户明细。"
            "仅支持预定义实体和筛选参数，不执行任意 SQL。"
        ),
        args_schema=QueryDatabaseRequest,
    )

    return {
        "query_database": query_database,
    }


_DEFAULT_TOOLS = create_query_tools()

query_database = _DEFAULT_TOOLS["query_database"]
