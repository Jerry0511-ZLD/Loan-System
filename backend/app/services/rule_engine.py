"""规则引擎：基于特征画像跑规则集。

规则 = 函数（行为骨架）+ 配置表里的一行数字（参数）。
函数按自己的 rule_name 从 configs 里取阈值；表里没有就用本文件默认值兜底。
求值优先级：reject > manual > approved；reduce 仅在 approved 时生效。
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


# ---- 代码级默认值：配置表查不到某条规则时兜底，行为与"硬编码时代"完全一致 ----
DEFAULTS = {
    "overdue_6m": {"threshold": 2},
    "dti": {"threshold": 0.7},
    "multi_platform": {"threshold": 5},
    "short_tenure": {"threshold": 3},
    "fund_inactive": {"reduce_ratio": 0.2},
}


def _params(configs: dict, name: str) -> dict:
    """取某条规则的参数：DB 配置覆盖代码默认值，最后保证 enabled 有值。"""
    merged = dict(DEFAULTS.get(name, {}))
    merged.update(configs.get(name) or {})
    merged.setdefault("enabled", True)
    return merged


# ---- 规则集（行为留代码，数字进配置）----
def _rule_blacklist(f: FeatureProfile, configs: dict):
    if not _params(configs, "blacklist")["enabled"]:
        return None
    if f.is_blacklisted:
        return RuleHit("blacklist", "reject", "命中征信黑名单")
    return None


def _rule_overdue(f: FeatureProfile, configs: dict):
    cfg = _params(configs, "overdue_6m")
    threshold = cfg.get("threshold")
    if not cfg["enabled"] or threshold is None:
        return None
    if f.overdue_count_6m >= threshold:
        return RuleHit("overdue_6m", "reject", f"近6月逾期{f.overdue_count_6m}次（阈值{threshold:g}）")
    return None


def _rule_dti(f: FeatureProfile, configs: dict):
    cfg = _params(configs, "dti")
    threshold = cfg.get("threshold")
    if not cfg["enabled"] or threshold is None:
        return None
    if f.dti > threshold:
        return RuleHit("dti", "reject", f"负债收入比{f.dti:.2f}超阈值{threshold:g}")
    return None


def _rule_multi_platform(f: FeatureProfile, configs: dict):
    cfg = _params(configs, "multi_platform")
    threshold = cfg.get("threshold")
    if not cfg["enabled"] or threshold is None:
        return None
    if f.credit_card_count >= threshold:
        return RuleHit("multi_platform", "manual", f"多头授信{f.credit_card_count}家（阈值{threshold:g}），转人工")
    return None


def _rule_short_tenure(f: FeatureProfile, configs: dict):
    cfg = _params(configs, "short_tenure")
    threshold = cfg.get("threshold")
    if not cfg["enabled"] or threshold is None:
        return None
    if f.active_months < threshold:
        return RuleHit("short_tenure", "manual", f"在网{f.active_months}月＜{threshold:g}，转人工")
    return None


def _rule_fund_inactive(f: FeatureProfile, configs: dict):
    cfg = _params(configs, "fund_inactive")
    if not cfg["enabled"]:
        return None
    if not f.fund_active:
        ratio = cfg.get("reduce_ratio") or 0.2
        return RuleHit("fund_inactive", "reduce", f"公积金未正常缴纳，降额{ratio:.0%}", reduce_ratio=ratio)
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


def evaluate(f: FeatureProfile, configs: dict | None = None) -> RuleResult:
    configs = configs or {}
    hits = []
    for rule_fn in RULES:
        hit = rule_fn(f, configs)
        if hit is not None:
            hits.append(hit)

    status = DecisionStatus.APPROVED
    for h in hits:
        if h.action == "reject":
            status = DecisionStatus.REJECTED
            break
    if status == DecisionStatus.APPROVED:
        for h in hits:
            if h.action == "manual":
                status = DecisionStatus.MANUAL
                break

    total_reduce = 0.0
    for h in hits:
        if h.action == "reduce":
            total_reduce = total_reduce + h.reduce_ratio
    reduce_ratio = min(total_reduce, 0.9)

    reasons = []
    for h in hits:
        reasons.append(f"{h.rule}: {h.reason}")
    return RuleResult(status=status, reduce_ratio=reduce_ratio, reasons=reasons)
