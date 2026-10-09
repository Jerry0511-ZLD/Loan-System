"""决策编排:并发拉多源数据 → 特征聚合 → 规则求值 → 输出授信。"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.datasources.carrier import CarrierSource
from app.datasources.credit import CreditBureauSource
from app.datasources.housing import HousingFundSource
from app.models import Application, Decision, DecisionStatus
from app.services.feature import aggregate
from app.services.rule_engine import evaluate

BASE_RATE = 0.12          # 年化基础利率
RISK_PREMIUM_RATE = 0.15  # 有降额规则时的风险利率
INCOME_MULTIPLE = 6       # 授信倍数:月收入的 N 倍封顶


async def run_decision(application: Application, db: AsyncSession) -> Decision:
    # 1. 并发拉取多源数据(MVP 全 Mock,真实接入换 adapter 内部即可)
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
    base_amount = min(application.requested_amount, application.monthly_income * INCOME_MULTIPLE)

    if result.status == DecisionStatus.APPROVED:
        approved_amount = round(base_amount * (1 - result.reduce_ratio), 2)
        rate = RISK_PREMIUM_RATE if result.reduce_ratio > 0 else BASE_RATE
    elif result.status == DecisionStatus.MANUAL:
        approved_amount = 0.0      # 待人工复核后定
        rate = 0.0
    else:  # REJECTED
        approved_amount = 0.0
        rate = 0.0

    # 5. 落库
    decision = Decision(
        application_id=application.id,
        status=result.status,
        approved_amount=approved_amount,
        rate=rate,
        reasons=result.reasons,
        feature_profile=profile.model_dump(),
    )
    db.add(decision)
    application.status = "done"
    await db.commit()
    await db.refresh(decision)
    return decision
