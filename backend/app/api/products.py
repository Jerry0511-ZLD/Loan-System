"""贷款产品接口（首页用，无需登录）。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import ok
from app.database import get_db
from app.models import Product
from app.serializers import product_to_dict

router = APIRouter(tags=["产品"])


@router.get("/products", summary="贷款产品列表（首页卡片）")
async def list_products(db: AsyncSession = Depends(get_db)):
    stmt = select(Product).where(Product.status == "on").order_by(Product.sort_order.asc())
    rows = (await db.execute(stmt)).scalars().all()
    items = []
    for row in rows:
        items.append(product_to_dict(row))
    return ok(items)


@router.get("/products/{product_id}", summary="贷款产品详情")
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, product_id)
    if product is None or product.status != "on":
        raise HTTPException(status_code=404, detail="产品不存在或已下架")
    return ok(product_to_dict(product))
