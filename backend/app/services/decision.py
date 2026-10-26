"""决策编排：并发拉多源数据 → 特征聚合 → 规则求值 → 输出授信 → 回写申请单状态。"""

import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from app.datasources.carrier import CarrierSource
from app.datasources.credit import CreditBureauSource
from app.datasources.housing import HousingFundSource
from app.models import Application, ApplicationStatus, Decision, DecisionStatus, Product, RiskRuleConfig
from app.services.feature import aggregate
from app.services.risk_engines import get_engine
from app.services.repayment import generate_repayment_plan

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

    # 2.5 读取规则阈值配置：改库即改风控的关键一步。
    #     引擎必须保持纯函数（base.py 的约定），所以配置由这里读好、当参数传进去。
    rows = (await db.execute(select(RiskRuleConfig))).scalars().all()
    rule_configs = {}
    for row in rows:
        rule_configs[row.rule_name] = {
            "enabled": row.enabled,
            "threshold": row.threshold,
            "reduce_ratio": row.reduce_ratio,
        }


    # 3. 交给风控引擎决策。
    #    这里不直接调用规则引擎，而是通过 get_engine() 取引擎实例：
    #    阶段 I 拿到的是 RuleEngineV0（规则占位），阶段 II 换成评分卡时只要改配置项
    #    risk_engine，本文件与所有路由都不用动。
    engine = get_engine()
    verdict = engine.decide(profile, rule_configs)

    # 4. 计算授信额度与利率
    base_amount = min(
        application.requested_amount, application.monthly_income * INCOME_MULTIPLE
    )
    base_rate = product.base_rate if product is not None else BASE_RATE

    if verdict.status == DecisionStatus.APPROVED:
        approved_amount = round(base_amount * (1 - verdict.reduce_ratio), 2)
        if verdict.reduce_ratio > 0:
            rate = base_rate + RISK_PREMIUM_RATE
        else:
            rate = base_rate
    else:
        # 转人工：等人工复核后再定；拒绝：都是 0
        approved_amount = 0.0
        rate = 0.0

    # 5. 回写申请单状态。
    #    review_required 单独存一列，而不是每次去 decisions 表里查「是否有 manual 结论」，
    #    是为了让管理端的「待办列表」能直接在 SQL 层过滤 + 分页，
    #    不用把全部数据捞到内存里再筛（数据量一大就会出问题）。
    application.status = APPLICATION_STATUS_OF[verdict.status]
    application.review_required = verdict.status == DecisionStatus.MANUAL
    application.risk_level = verdict.risk_level
    application.risk_score = verdict.risk_score
    application.decided_at = datetime.now()

    # 6. 落决策记录。
    #    除了结论本身，这里额外留三份痕迹，供管理端「风控明细」页与事后审计使用：
    #    - feature_profile：聚合后的特征画像（决策时这个人是什么样）
    #    - raw_data：三个数据源各自返回的原始数据（这个画像是由什么聚合出来的）
    #    - engine + model_version：结论是哪套机制、哪个版本算出来的（便于新旧机制效果对比）
    decision = Decision(
        application_id=application.id,
        status=verdict.status,
        approved_amount=approved_amount,
        rate=rate,
        reasons=verdict.reasons,
        engine=verdict.engine,
        model_version=verdict.model_version,
        feature_profile=profile.model_dump(),
        raw_data=raw,
        source="auto",
    )
    db.add(decision)

    # 7. 审批通过 → 生成还款计划（只 add 不 commit，随下方 flush 一起入库）
    if verdict.status == DecisionStatus.APPROVED:
        generate_repayment_plan(application, approved_amount, rate, db)


    # 只 flush 不 commit：事务边界统一交给路由层（见 api/loans.py、api/applications.py）。
    # 好处是「写申请单 + 写决策记录」要么一起成功、要么一起回滚；
    # 也不会出现 service 层偷偷提交、调用方以为后续还能改动数据的情况。
    await db.flush()
    return decision
