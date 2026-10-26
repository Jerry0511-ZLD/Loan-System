"""贷款产品接口（首页用，无需登录）。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.response import ok
from app.database import get_db
from app.serializers import product_to_dict
from app.api.deps import require_admin
from app.models import Product, User, Application
from app.schemas import ProductCreateRequest, ProductUpdateRequest

router = APIRouter(tags=["产品"])


@router.get("/products", summary="贷款产品列表（首页卡片）")
async def list_products(
        keyword: str | None = None,
        minAmount: float | None = None,
        maxAmount: float | None = None,
        minTerm: int | None = None,
        maxTerm: int | None = None,
        minRate: float | None = None,
        maxRate: float | None = None,
        tags: str | None = None,
        db: AsyncSession = Depends(get_db)):
    stmt = select(Product).where(Product.status == "on").order_by(Product.sort_order.asc())
    conditions = []
    if keyword:
        conditions.append(Product.name.ilike(f"%{keyword}%"))
    if minAmount is not None:
        conditions.append(Product.min_amount >= minAmount)
    if maxAmount is not None:
        conditions.append(Product.max_amount <= maxAmount)
    if minTerm is not None:
        conditions.append(Product.min_term >= minTerm)
    if maxTerm is not None:
        conditions.append(Product.max_term <= maxTerm)
    if minRate is not None:
        conditions.append(Product.base_rate >= minRate)
    if maxRate is not None:
        conditions.append(Product.base_rate <= maxRate)
    if tags:
        conditions.append(Product.tags.ilike(f"%{tags}%"))

    stmt = stmt.where(*conditions)
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


@router.post("/admin/poroducts", summary="上架新产品")
async def create_product(
        payload: ProductCreateRequest,
        user: User = Depends(require_admin),
        db: AsyncSession = Depends(get_db)
):
    if payload.max_amount < payload.min_amount:
        raise HTTPException(status_code=400, detail="最高金额不能低于起贷金额")
    if payload.max_term < payload.min_term:
        raise HTTPException(status_code=400, detail="最长期限不能短于最短期限")

    product = Product(
        name=payload.name,
        description=payload.description,
        min_amount=payload.min_amount,
        max_amount=payload.max_amount,
        min_term=payload.min_term,
        max_term=payload.max_term,
        base_rate=payload.base_rate,
        tags=payload.tags,
        featured=payload.featured,
        sort_order=payload.sort_order,
    )

    db.add(product)
    await db.commit()
    return ok(product_to_dict(product), message="产品已上架")


@router.put("/admin/products/{product_id}", summary="更新产品（传哪项改哪项）")
async def update_product(
        product_id: str,
        payload: ProductUpdateRequest,
        user: User = Depends(require_admin),
        db: AsyncSession = Depends(get_db)
):
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="产品不存在")

    updated_product = payload.model_dump(exclude_unset=True)

    new_min = updated_product.get("min_amount", product.min_amount)
    new_max = updated_product.get("max_amount", product.max_amount)
    if new_max < new_min:
        raise HTTPException(status_code=400, detail="最高金额不能低于起贷金额")
    new_min_term = updated_product.get("min_term", product.min_term)
    new_max_term = updated_product.get("max_term", product.max_term)
    if new_max_term < new_min_term:
        raise HTTPException(status_code=400, detail="最长期限不能短于最短期限")

    for key, value in updated_product.items():
        setattr(product, key, value)

    await db.commit()
    return ok(product_to_dict(product), message="产品已更新")


@router.delete("/admin/products/{product_id}")
async def delete_product(
        product_id: str,
        user: User = Depends(require_admin),
        db: AsyncSession = Depends(get_db)
):
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="产品不存在")

    stmt = select(func.count()).where(Application.id == product.id)
    num = (await db.execute(stmt)).scalar_one()
    if num > 0:
        raise HTTPException(status_code=409, detail=f"该产品已有 {num} 笔申请记录，只能下架（status=off），不能删除",)\

    await db.delete(product)
    await db.commit()
    return ok(None, message="产品已删除")