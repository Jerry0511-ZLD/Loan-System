"""列表页用的批量查表：把一批申请单对应的决策 / 产品一次性查出来。

避免每行都去查库（N+1 查询）。
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Decision, Product


async def load_decisions(db: AsyncSession, application_ids: list[str]) -> dict[str, Decision]:
    """返回 {application_id: Decision}。"""
    result_map: dict[str, Decision] = {}
    if not application_ids:
        return result_map
    stmt = select(Decision).where(Decision.application_id.in_(application_ids))
    rows = (await db.execute(stmt)).scalars().all()
    for row in rows:
        result_map[row.application_id] = row
    return result_map


async def load_products(db: AsyncSession, product_ids: list[str]) -> dict[str, Product]:
    """返回 {product_id: Product}。"""
    result_map: dict[str, Product] = {}
    ids = [pid for pid in product_ids if pid]
    if not ids:
        return result_map
    stmt = select(Product).where(Product.id.in_(ids))
    rows = (await db.execute(stmt)).scalars().all()
    for row in rows:
        result_map[row.id] = row
    return result_map
