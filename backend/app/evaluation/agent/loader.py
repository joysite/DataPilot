"""Agent 评测环境的合成业务数据加载器。"""

from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ingestion.reader import DatasetType, read_csv
from app.services.import_service import process_dataset_rows

DATASET_ORDER: tuple[DatasetType, ...] = (
    "users",
    "products",
    "orders",
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SYNTHETIC_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def _load_synthetic_rows() -> dict[DatasetType, list[dict[str, str]]]:
    """只读取项目固定目录中的合成 CSV 文件。"""
    data_dir = SYNTHETIC_DATA_DIR.resolve()

    if data_dir != SYNTHETIC_DATA_DIR:
        raise ValueError("合成数据目录不能通过符号链接重定向")

    datasets = {}

    for dataset_type in DATASET_ORDER:
        file_path = data_dir / f"{dataset_type}.csv"

        if file_path.resolve().parent != data_dir:
            raise ValueError(f"合成数据文件路径异常：{file_path}")

        datasets[dataset_type] = read_csv(file_path, dataset_type)

        if not datasets[dataset_type]:
            raise ValueError(f"合成数据集不能为空：{dataset_type}")

    return datasets


async def seed_evaluation_database(
    session_factory: async_sessionmaker[AsyncSession],
) -> dict[str, Any]:
    """将合成业务数据导入隔离的评测数据库。"""
    if not isinstance(session_factory, async_sessionmaker):
        raise TypeError("session_factory 必须是 async_sessionmaker")

    datasets = _load_synthetic_rows()
    import_summary = {}

    async with session_factory() as session:
        async with session.begin():
            for dataset_type in DATASET_ORDER:
                rows = datasets[dataset_type]

                result = await process_dataset_rows(
                    session,
                    rows,
                    dataset_type,
                )

                imported_rows = result["imported_rows"]
                skipped_rows = result["skipped_rows"]
                failed_rows = result["failed_rows"]

                if (
                    imported_rows != len(rows)
                    or skipped_rows != 0
                    or failed_rows != 0
                    or result["errors"]
                ):
                    raise RuntimeError(
                        f"评测数据导入不完整：{dataset_type}，"
                        f"总行数={len(rows)}，"
                        f"导入={imported_rows}，"
                        f"跳过={skipped_rows}，"
                        f"失败={failed_rows}，"
                        f"错误数={len(result['errors'])}"
                    )

                import_summary[dataset_type] = {
                    "total_rows": len(rows),
                    "imported_rows": imported_rows,
                }

    return import_summary
