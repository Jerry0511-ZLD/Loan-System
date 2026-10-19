"""列表页用的批量查表：把一批申请单对应的决策 / 产品一次性查出来。

避免每行都去查库（N+1 查询）。
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Decision, Product


async def load_decisions(db: AsyncSession, application_ids: list[str]) -> dict[str, Decision]:
    """返回 {application_id: 最新一条 Decision}。

    注意「最新一条」这个语义：一笔申请可能有多条决策记录——
    提交时的自动决策（source=auto）一条，人工复核通过/拒绝时再追加一条（source=manual），
    原始记录保留不覆盖，用于审计。

    这里按 created_at 升序读取，后读到的覆盖先读到的，最终留下的是最新一条。
    必须显式写 order_by：不写的话数据库返回顺序不做保证（SQLite 通常按 rowid，
    但换库或加了索引后就不一定），可能取到旧的自动决策，
    造成「申请单已是 APPROVED、详情却显示 manual」这种前后矛盾。
    """
    result_map: dict[str, Decision] = {}
    if not application_ids:
        return result_map
    stmt = (
        select(Decision)
        .where(Decision.application_id.in_(application_ids))
        .order_by(Decision.created_at.asc())
    )
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
