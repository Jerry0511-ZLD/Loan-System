"""管理端接口：申请单列表 / 详情 / 决策明细，以及直录进件的联调口子。

全部需要管理员 token（用 admin 账号登录拿到的那个）。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.response import ok, page_data
from app.database import get_db
from app.models import Application, Product
from app.schemas import ApplicationCreateRequest
from app.serializers import decision_to_dict, loan_to_dict
from app.services.decision import run_decision
from app.services.lookup import load_decisions, load_products

router = APIRouter(tags=["申请管理（管理端）"])


@router.get("/applications", summary="申请单列表（管理端）")
async def list_applications(
    page: int = 1,
    page_size: int = 10,
    pageSize: int | None = None,   # 兼容前端驼峰写法
    status: str | None = None,     # PENDING / APPROVED / REJECTED
    keyword: str | None = None,    # 按姓名或手机号模糊搜索
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    size = pageSize or page_size
    if page < 1:
        page = 1
    if size < 1 or size > 100:
        size = 10

    conditions = []
    if status:
        conditions.append(Application.status == status.upper())
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(Application.applicant_name.like(like), Application.phone.like(like))
        )

    base_stmt = select(Application)
    if conditions:
        base_stmt = base_stmt.where(*conditions)

    total = (
        await db.execute(select(func.count()).select_from(base_stmt.subquery()))
    ).scalar_one()
    stmt = (
        base_stmt.order_by(Application.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = (await db.execute(stmt)).scalars().all()

    decisions = await load_decisions(db, [row.id for row in rows])
    products = await load_products(db, [row.product_id for row in rows])

    items = []
    for row in rows:
        items.append(
            loan_to_dict(row, decisions.get(row.id), products.get(row.product_id))
        )
    return ok(page_data(items, total, page, size))


@router.post("/applications", summary="直录一笔进件（管理端/联调用，不依赖登录用户资料）")
async def create_application(
    payload: ApplicationCreateRequest,
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    product = None
    if payload.product_id:
        product = await db.get(Product, payload.product_id)
        if product is None:
            raise HTTPException(status_code=404, detail=f"产品不存在：{payload.product_id}")

    application = Application(
        user_id="",
        product_id=payload.product_id or "",
        applicant_name=payload.applicant_name,
        id_card=payload.id_card,
        phone=payload.phone,
        monthly_income=payload.monthly_income,
        requested_amount=payload.requested_amount,
        term=payload.term,
        purpose=payload.purpose or "",
    )
    db.add(application)
    await db.flush()
    decision = await run_decision(application, db, product)
    return ok(loan_to_dict(application, decision, product), message="进件已受理，风控结果已出")


@router.get("/applications/{app_id}", summary="申请单详情（管理端）")
async def get_application(
    app_id: str,
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    application = await db.get(Application, app_id)
    if application is None:
        raise HTTPException(status_code=404, detail="申请不存在")
    decisions = await load_decisions(db, [application.id])
    products = await load_products(db, [application.product_id])
    return ok(
        loan_to_dict(application, decisions.get(application.id), products.get(application.product_id))
    )


@router.get("/applications/{app_id}/decision", summary="申请单的风控决策明细（管理端）")
async def get_decision(
    app_id: str,
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    application = await db.get(Application, app_id)
    if application is None:
        raise HTTPException(status_code=404, detail="申请不存在")
    decisions = await load_decisions(db, [application.id])
    decision = decisions.get(application.id)
    if decision is None:
        raise HTTPException(status_code=404, detail="该申请还没有决策结果")
    return ok(decision_to_dict(decision))
