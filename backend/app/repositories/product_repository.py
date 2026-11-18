"""商品数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.ingestion import ProductImport


class ProductRepository:
    """商品数据访问操作。"""

    @staticmethod
    async def get_existing_ids(
        session: AsyncSession,
        product_ids: list[str],
    ) -> set[str]:
        """查询已经存在的商品 ID。"""
        if not product_ids:
            return set()

        result = await session.scalars(
            select(Product.product_id).where(Product.product_id.in_(product_ids))
        )
        return set(result.all())

    @staticmethod
    async def bulk_insert(
        session: AsyncSession,
        products: list[ProductImport],
    ) -> int:
        """批量插入商品记录，不负责提交事务。"""
        if not products:
            return 0

        existing_ids = await ProductRepository.get_existing_ids(
            session,
            [product.product_id for product in products],
        )

        new_products = [
            Product(
                product_id=product.product_id,
                product_name=product.product_name,
                category=product.category,
                price=product.price,
            )
            for product in products
            if product.product_id not in existing_ids
        ]

        if not new_products:
            return 0

        session.add_all(new_products)
        await session.flush()

        return len(new_products)
