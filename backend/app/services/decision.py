"""决策编排：并发拉多源数据 → 特征聚合 → 规则求值 → 输出授信 → 回写申请单状态。"""

import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.datasources.carrier import CarrierSource
from app.datasources.credit import CreditBureauSource
from app.datasources.housing import HousingFundSource
from app.models import Application, ApplicationStatus, Decision, DecisionStatus, Product
from app.services.feature import aggregate
from app.services.risk import risk_result
from app.services.rule_engine import evaluate

BASE_RATE = 0.12          # 兜底年化基础利率（没选产品时用）
RISK_PREMIUM_RATE = 0.08  # 命中降额规则时，利率的加点（风险溢价）
INCOME_MULTIPLE = 6       # 授信倍数：月收入的 N 倍封顶

# 规则引擎结论 -> 对前端暴露的申请单状态
# 转人工对前端表现为 PENDING（待审批），详情里另有 reviewRequired=true 标识
APPLICATION_STATUS_OF = {
    DecisionStatus.APPROVED: ApplicationStatus.APPROVED.value,
    DecisionStatus.REJECTED: ApplicationStatus.REJECTED.value,
    DecisionStatus.MANUAL: ApplicationStatus.PENDING.value,
}


async def run_decision(
    application: Application,
    db: AsyncSession,
    product: Product | None = None,
) -> Decision:
    # 1. 并发拉取多源数据（MVP 全 Mock，真实接入只换 adapter 内部实现）
    credit = CreditBureauSource()
    carrier = CarrierSource()
    housing = HousingFundSource()

    c_raw, ca_raw, h_raw = await asyncio.gather(
        credit.fetch(application.id_card, application.phone),
        carrier.fetch(application.id_card, application.phone),
        housing.fetch(application.id_card, application.phone),
    )
    raw = {credit.name: c_raw, carrier.name: ca_raw, housing.name: h_raw}

    # 2. 特征聚合
    profile = aggregate(raw, application.monthly_income)

    # 3. 规则求值
    result = evaluate(profile)

    # 4. 计算授信额度与利率
    base_amount = min(
        application.requested_amount, application.monthly_income * INCOME_MULTIPLE
    )
    base_rate = product.base_rate if product is not None else BASE_RATE

    if result.status == DecisionStatus.APPROVED:
        approved_amount = round(base_amount * (1 - result.reduce_ratio), 2)
        if result.reduce_ratio > 0:
            rate = base_rate + RISK_PREMIUM_RATE
        else:
            rate = base_rate
    else:
        # 转人工：等人工复核后再定；拒绝：都是 0
        approved_amount = 0.0
        rate = 0.0

    # 5. 风险分档（分数越高越危险，见 services/risk.py）
    risk_score, risk_level = risk_result(profile, result.status)

    # 6. 回写申请单状态 + 落库
    application.status = APPLICATION_STATUS_OF[result.status]
    application.risk_level = risk_level
    application.risk_score = risk_score
    application.decided_at = datetime.now()

    decision = Decision(
        application_id=application.id,
        status=result.status,
        approved_amount=approved_amount,
        rate=rate,
        reasons=result.reasons,
        feature_profile=profile.model_dump(),
    )
    db.add(decision)
    await db.commit()
    await db.refresh(decision)
    return decision
