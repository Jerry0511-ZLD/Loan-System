"""规则引擎(MVP 版):基于特征画像跑规则集,替代 ML 模型。

规则 = 函数: FeatureProfile -> RuleHit | None
求值优先级:reject > manual > approved;reduce 仅在 approved 时生效。
"""

from dataclasses import dataclass

from app.models import DecisionStatus
from app.services.feature import FeatureProfile


@dataclass
class RuleHit:
    rule: str
    action: str          # reject | manual | reduce
    reason: str
    reduce_ratio: float = 0.0  # 仅 reduce 动作使用


# ---- 规则集(可后续改成 DB 配置) ----
def _rule_blacklist(f: FeatureProfile):
    if f.is_blacklisted:
        return RuleHit("blacklist", "reject", "命中征信黑名单")
    return None


def _rule_overdue(f: FeatureProfile):
    if f.overdue_count_6m >= 2:
        return RuleHit("overdue_6m", "reject", f"近6月逾期{f.overdue_count_6m}次")
    return None


def _rule_dti(f: FeatureProfile):
    if f.dti > 0.7:
        return RuleHit("dti", "reject", f"负债收入比{f.dti:.2f}超阈值0.7")
    return None


def _rule_multi_platform(f: FeatureProfile):
    if f.credit_card_count >= 5:
        return RuleHit("multi_platform", "manual", f"多头授信{f.credit_card_count}家,转人工")
    return None


def _rule_short_tenure(f: FeatureProfile):
    if f.active_months < 3:
        return RuleHit("short_tenure", "manual", f"在网{f.active_months}月<3,转人工")
    return None


def _rule_fund_inactive(f: FeatureProfile):
    if not f.fund_active:
        return RuleHit("fund_inactive", "reduce", "公积金未正常缴纳,降额20%", reduce_ratio=0.2)
    return None


RULES = [
    _rule_blacklist,
    _rule_overdue,
    _rule_dti,
    _rule_multi_platform,
    _rule_short_tenure,
    _rule_fund_inactive,
]


@dataclass
class RuleResult:
    status: DecisionStatus
    reduce_ratio: float   # 总降额比例
    reasons: list         # 触发原因列表


def evaluate(f: FeatureProfile) -> RuleResult:
    hits = [h for r in RULES if (h := r(f)) is not None]

    if any(h.action == "reject" for h in hits):
        status = DecisionStatus.REJECTED
    elif any(h.action == "manual" for h in hits):
        status = DecisionStatus.MANUAL
    else:
        status = DecisionStatus.APPROVED

    reduce_ratio = min(sum(h.reduce_ratio for h in hits if h.action == "reduce"), 0.9)
    reasons = [f"{h.rule}: {h.reason}" for h in hits]
    return RuleResult(status=status, reduce_ratio=reduce_ratio, reasons=reasons)
