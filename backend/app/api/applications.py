"""管理端接口：申请单列表 / 详情 / 决策明细 / 人工复核 / 多数据源明细。

全部需要管理员 token（用 admin 账号登录拿到的那个）。

阶段 I 的能力边界：
- 已实现：列表检索、详情、决策明细、直录进件、**人工复核**、**多数据源明细**；
- 未实现（阶段 II）：产品维护、批量审批、放款与账务管理。
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.response import ok, page_data
from app.database import get_db
from app.models import Application, ApplicationStatus, Decision, DecisionStatus, Product, User
from app.schemas import ApplicationCreateRequest, ReviewRequest
from app.serializers import decision_to_dict, fmt_time, loan_to_dict
from app.services.decision import BASE_RATE, INCOME_MULTIPLE, run_decision
from app.services.lookup import load_decisions, load_products
from app.services.repayment import generate_repayment_plan


router = APIRouter(tags=["申请管理（管理端）"])


def _parse_date(value: str, end_of_day: bool = False) -> datetime:
    """把前端传的日期字符串解析成 datetime。

    为什么要单独写这个：
    - 前端日期选择器传的是 "2026-10-01" 这种纯日期，不带时分秒；
    - 而 created_at 是带时分秒的，如果直接比较，"10-01 到 10-01" 会查不到当天的数据
      （因为 10-01 00:00:00 <= 10-01 10:30:00 之外的时间都被排除了）；
    - 所以结束日期要顺延到当天 23:59:59。
    """
    raw = (value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw, fmt)
            if end_of_day and fmt == "%Y-%m-%d":
                dt = dt + timedelta(days=1) - timedelta(seconds=1)
            return dt
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail=f"日期格式不正确：{value}（应为 YYYY-MM-DD）")


@router.get("/applications", summary="申请单列表（管理端）")
async def list_applications(
    page: int = 1,
    page_size: int = 10,
    pageSize: int | None = None,   # 兼容前端驼峰写法
    status: str | None = None,     # PENDING / APPROVED / REJECTED
    keyword: str | None = None,    # 按姓名或手机号模糊搜索
    # 只看「等待人工复核」的单子。管理端待办列表用这个参数，直接在 SQL 层过滤，
    # 不用把全部数据捞到内存里再筛（数据量一大就会拖慢接口）。
    reviewRequired: bool | None = Query(default=None, description="只看转人工待办"),
    # 日期区间筛选（按申请创建时间）。前端列表页的日期选择器对应这两个参数。
    startDate: str | None = Query(default=None, description="开始日期，如 2026-10-01"),
    endDate: str | None = Query(default=None, description="结束日期，如 2026-10-31"),
    _admin: User = Depends(require_admin),
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
    if reviewRequired is not None:
        conditions.append(Application.review_required == reviewRequired)
    if startDate:
        conditions.append(Application.created_at >= _parse_date(startDate))
    if endDate:
        conditions.append(Application.created_at <= _parse_date(endDate, end_of_day=True))

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
    _admin: User = Depends(require_admin),
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

    # 事务边界在这里收口：申请单与决策记录一起提交，避免只落一半。
    # （run_decision 内部只 flush 不 commit，见 services/decision.py 的说明。）
    await db.commit()
    return ok(loan_to_dict(application, decision, product), message="进件已受理，风控结果已出")


@router.get("/applications/{app_id}", summary="申请单详情（管理端）")
async def get_application(
    app_id: str,
    _admin: User = Depends(require_admin),
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
    _admin: User = Depends(require_admin),
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


@router.get("/applications/{app_id}/datasources", summary="多数据源原始数据明细（管理端）")
async def get_application_datasources(
    app_id: str,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """返回这笔申请在决策时，三个数据源各自返回了什么。

    为什么需要这个接口
    ------------------
    课题名字叫「多数据源融合」，但在此之前，管理端只能看到最终的命中原因，
    看不到「融合之前长什么样」。风控专员复核时无法判断结论是否合理，
    答辩演示时也讲不出「三源数据 → 特征画像 → 决策结论」这条链路。

    为什么读快照而不是实时重算
    --------------------------
    raw_data 是决策发生时落库的快照。实时重算拿到的是「现在」的数据，
    而审计和复盘要回答的是「当时为什么这么判」。这两者不能混为一谈。
    """
    application = await db.get(Application, app_id)
    if application is None:
        raise HTTPException(status_code=404, detail="申请不存在")

    decisions = await load_decisions(db, [application.id])
    decision = decisions.get(application.id)
    if decision is None:
        raise HTTPException(status_code=404, detail="该申请还没有决策结果")

    raw = decision.raw_data or {}
    return ok(
        {
            "applicationId": application.id,
            "sources": [
                {"name": name, "fields": fields or {}}
                for name, fields in raw.items()
            ],
            "featureProfile": decision.feature_profile or {},
            "engine": decision.engine,
            "modelVersion": decision.model_version,
            "decidedAt": fmt_time(decision.created_at),
        }
    )


@router.post("/applications/{app_id}/review", summary="人工复核（处理转人工的申请单）")
async def review_application(
    app_id: str,
    payload: ReviewRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """风控专员对「转人工」的申请单做出人工结论（需求规格说明书 UC-05）。

    三条设计原则：
    1. **只处理待复核的单子**：已经通过或已经拒绝的申请单不再接受复核，
       返回 409 而不是静默覆盖，避免误操作改掉已生效的结论；
    2. **追加记录，不覆盖原记录**：人工结论写成一条新的 decision（source=manual），
       原来那条自动决策原样保留，审计时能看出「系统判了什么、人改成了什么」；
    3. **额度可以手工调整**：专员认为系统给的额度不合适时，可以传 approvedAmount 覆盖。
    """
    application = await db.get(Application, app_id)
    if application is None:
        raise HTTPException(status_code=404, detail="申请不存在")

    if not application.review_required:
        raise HTTPException(
            status_code=409,
            detail=f"该申请当前状态为 {application.status}，不需要人工复核",
        )

    # 取最近一条决策，作为「系统原本判成什么样」的基准（额度、利率、特征快照）
    decisions = await load_decisions(db, [application.id])
    original = decisions.get(application.id)

    now = datetime.now()

    if payload.action == "approve":
        decision_status = DecisionStatus.APPROVED
        new_status = ApplicationStatus.APPROVED.value

        # 额度：专员手工填了就用专员的，没填则退回系统算出来的值
        approved_amount = payload.approved_amount or (original.approved_amount if original else 0.0)
        rate = payload.rate or (original.rate if original else 0.0)

        # 转人工的单子在系统那边额度是 0（见 decision.py：非 APPROVED 一律置 0），
        # 专员也没填的话，按授信规则给一个默认值，避免出现「通过但额度为 0」的矛盾数据。
        if approved_amount <= 0:
            base_amount = min(
                application.requested_amount, application.monthly_income * INCOME_MULTIPLE
            )
            approved_amount = round(base_amount, 2)
            if rate <= 0:
                product = (
                    await db.get(Product, application.product_id)
                    if application.product_id
                    else None
                )
                rate = product.base_rate if product is not None else BASE_RATE
    else:
        decision_status = DecisionStatus.REJECTED
        new_status = ApplicationStatus.REJECTED.value
        approved_amount = 0.0
        rate = 0.0

    # 追加一条人工决策记录；特征画像与原始数据从原自动决策继承，保证审计链路完整
    decision = Decision(
        application_id=application.id,
        status=decision_status,
        approved_amount=approved_amount,
        rate=rate,
        reasons=[f"manual_review: {payload.comment or '人工复核'}"] if payload.comment else ["manual_review: 人工复核"],
        engine="manual",
        model_version="—",
        feature_profile=original.feature_profile if original else {},
        raw_data=original.raw_data if original else {},
        source="manual",
        reviewer_id=admin.id,
        reviewed_at=now,
        comment=payload.comment or "",
    )
    db.add(decision)

    application.status = new_status
    application.review_required = False
    application.decided_at = now
    # 风险档位跟着人工结论走，避免出现「APPROVED 但 riskLevel=HIGH」的自相矛盾
    application.risk_level = "LOW" if decision_status == DecisionStatus.APPROVED else "HIGH"

    # 人工批准 → 生成还款计划（额度/利率用本函数前面最终确定的值）
    if decision_status == DecisionStatus.APPROVED:
        generate_repayment_plan(application, approved_amount, rate, db)

    await db.commit()
    await db.refresh(decision)

    products = await load_products(db, [application.product_id])
    return ok(
        loan_to_dict(application, decision, products.get(application.product_id)),
        message="复核完成",
    )
