"""DataPilot MCP Server 启动入口。"""

import asyncio

from app.database.connection import close_db
from app.mcp_server import create_mcp_server


async def main() -> None:
    """启动 MCP Server，并在退出时释放数据库资源。"""

    server = create_mcp_server()

    try:
        await server.run_stdio_async()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
