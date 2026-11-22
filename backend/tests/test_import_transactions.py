import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.models  # noqa: F401
from app.database.base import Base
from app.models.import_record import ImportRecord
from app.models.user import User
from app.repositories.import_repository import ImportRepository
from app.repositories.user_repository import UserRepository
from app.services import import_service


@pytest.mark.asyncio
async def test_import_rolls_back_business_data_but_preserves_failure_record(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "transaction_test.sqlite"
    csv_path = tmp_path / "transaction_users.csv"
    csv_path.write_text(
        "user_id,register_time,region\n"
        "tx-user-1,2025-01-01T10:00:00+08:00,east\n"
        "tx-user-2,2025-01-02T10:00:00+08:00,west\n",
        encoding="utf-8",
    )

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        echo=False,
    )

    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # 只替换导入服务使用的 Session 工厂，所有操作均进入临时数据库。
        monkeypatch.setattr(
            import_service,
            "AsyncSessionLocal",
            session_factory,
        )

        # 保留真实 Repository 插入行为：先执行 INSERT 和 flush，
        # 再抛出异常，模拟业务写入过程中发生故障。
        original_bulk_insert = UserRepository.bulk_insert

        async def fail_after_flush(session, users):
            inserted = await original_bulk_insert(session, users)
            assert inserted == 2
            raise RuntimeError("transaction rollback test")

        monkeypatch.setattr(
            UserRepository,
            "bulk_insert",
            staticmethod(fail_after_flush),
        )

        result = await import_service.import_dataset(
            csv_path,
            "users",
        )

        assert result["status"] == "failed"
        assert result["total_rows"] == 2
        assert result["imported_rows"] == 0
        assert result["skipped_rows"] == 0
        assert result["failed_rows"] == 2

        assert len(result["errors"]) == 1
        assert result["errors"][0]["error_type"] == ("import_processing_error")
        assert result["errors"][0]["error_message"] == ("transaction rollback test")

        async with session_factory() as session:
            # 事务 B 回滚：已经 flush 的两条用户记录均不存在。
            user_count = await session.scalar(select(func.count()).select_from(User))
            assert user_count == 0

            # 事务 A 创建的导入记录仍然存在。
            record = await session.get(
                ImportRecord,
                result["import_record_id"],
            )
            assert record is not None
            assert record.status == "failed"
            assert record.total_rows == 2
            assert record.imported_rows == 0
            assert record.failed_rows == 2

            # 事务 C 保存的错误明细仍然存在。
            errors = await ImportRepository.get_errors_by_record_id(
                session,
                record.id,
            )
            assert len(errors) == 1
            assert errors[0].error_type == "import_processing_error"
            assert errors[0].error_message == ("transaction rollback test")

        print("事务 B：业务数据已回滚")
        print("事务 A：processing 导入记录已保留")
        print("事务 C：failed 状态和错误明细已保存")

    finally:
        await engine.dispose()
