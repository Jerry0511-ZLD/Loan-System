"""贷款接口：提交申请（前端"申请"按钮）、我的贷款列表（前端"我的贷款"页）。

字段映射（前端 -> 后端）：
    product  -> product_id（贷款产品）
    amount   -> requested_amount（申请金额，元）
    term     -> term（期限，月）
    purpose  -> purpose（用途）
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.response import ok, page_data
from app.database import get_db
from app.models import Application, Product, User
from app.schemas import LoanCreateRequest
from app.serializers import loan_to_dict
from app.services.decision import run_decision
from app.services.lookup import load_decisions, load_products

router = APIRouter(tags=["贷款"])


@router.post("/loans", summary="提交贷款申请（提交即出风控结果）")
async def create_loan(
    payload: LoanCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. 产品必须是上架的
    product = await db.get(Product, payload.product_id)
    if product is None or product.status != "on":
        raise HTTPException(status_code=404, detail=f"产品不存在或已下架：{payload.product_id}")

    # 2. 金额、期限要在产品允许的范围内
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="申请金额必须大于 0")
    if not (product.min_amount <= payload.amount <= product.max_amount):
        raise HTTPException(
            status_code=400,
            detail=f"{product.name} 可申请金额 {product.min_amount:g}~{product.max_amount:g} 元",
        )
    if not (product.min_term <= payload.term <= product.max_term):
        raise HTTPException(
            status_code=400,
            detail=f"{product.name} 可选期限 {product.min_term}~{product.max_term} 期",
        )

    # 3. 申请资料：表单里填了用表单的，没填用登录用户资料兜底
    id_card = payload.id_card or user.id_card
    phone = payload.phone or user.phone
    monthly_income = payload.monthly_income or user.monthly_income
    applicant_name = payload.applicant_name or user.name
    if not id_card or not phone or not monthly_income:
        raise HTTPException(
            status_code=400, detail="缺少身份证号/手机号/月收入，请在申请表单里补全"
        )

    # 4. 落库 + 跑风控
    application = Application(
        user_id=user.id,
        product_id=product.id,
        applicant_name=applicant_name,
        id_card=id_card,
        phone=phone,
        monthly_income=float(monthly_income),
        requested_amount=float(payload.amount),
        term=int(payload.term),
        purpose=payload.purpose or "",
    )
    db.add(application)
    await db.flush()  # 生成 application.id，供决策记录引用

    decision = await run_decision(application, db, product)

    # 事务边界收口：申请单与决策记录一起提交。
    # run_decision 内部只 flush 不 commit（见 services/decision.py），
    # 由路由层统一决定「这一笔业务算不算完成」，避免 service 层悄悄提交。
    await db.commit()
    return ok(loan_to_dict(application, decision, product), message="申请已提交，风控结果已出")


@router.get("/loans", summary="我的贷款列表")
async def list_my_loans(
    page: int = 1,
    page_size: int = 10,
    pageSize: int | None = None,  # 兼容前端驼峰写法
    status: str | None = None,    # PENDING / APPROVED / REJECTED，不传返回全部
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    size = pageSize or page_size
    if page < 1:
        page = 1
    if size < 1 or size > 100:
        size = 10

    conditions = [Application.user_id == user.id]
    if status:
        conditions.append(Application.status == status.upper())

    base_stmt = select(Application).where(*conditions)
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


@router.get("/loans/{loan_id}", summary="贷款详情（含风控明细）")
async def get_loan(
    loan_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    application = await db.get(Application, loan_id)
    if application is None:
        raise HTTPException(status_code=404, detail="申请记录不存在")
    # 只能看自己的；管理员可以看全部
    if application.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权查看这笔申请")

    decisions = await load_decisions(db, [application.id])
    products = await load_products(db, [application.product_id])
    return ok(loan_to_dict(application, decisions.get(application.id), products.get(application.product_id)))
