"""风险评级：把特征画像折算成 0~100 的风险分 + LOW/MEDIUM/HIGH 三档。

说明（重要）：
- 这套权重是本项目自己定的演示口径，不是论文也不是行业标准，想调直接改下面几个数。
- 分数越高越危险。
- 最后会按规则引擎的结论做一次对齐，保证两处口径不打架：
    规则判 REJECTED  -> 分数至少 70（HIGH）
    规则判 MANUAL    -> 分数落在 40~69（MEDIUM）
    规则判 APPROVED  -> 分数最多 39（LOW）
"""

from app.models import DecisionStatus
from app.services.feature import FeatureProfile


def base_score(profile: FeatureProfile) -> int:
    """按特征算原始风险分（0~100）。"""
    score = 0.0

    # 履约表现（最多 80 分）
    score += min(profile.overdue_count_6m, 4) * 10  # 近6月每逾期一次 +10
    if profile.is_blacklisted:
        score += 40

    # 负债压力（最多 30 分）
    if profile.dti > 1.0:
        score += 30
    elif profile.dti > 0.7:
        score += 22
    elif profile.dti > 0.4:
        score += 12
    elif profile.dti > 0.2:
        score += 5

    # 多头授信（最多 15 分）
    score += min(profile.credit_card_count, 6) * 2.5

    # 稳定性（最多 15 分）
    if profile.active_months < 3:
        score += 8
    elif profile.active_months < 12:
        score += 4
    if not profile.fund_active:
        score += 7
    elif profile.fund_months < 6:
        score += 3

    return int(round(min(score, 100)))


def risk_result(profile: FeatureProfile, decision_status: DecisionStatus) -> tuple[int, str]:
    """返回 (风险分, 风险档位)。"""
    score = base_score(profile)

    if decision_status == DecisionStatus.REJECTED:
        score = max(score, 70)
    elif decision_status == DecisionStatus.MANUAL:
        score = min(max(score, 40), 69)
    else:
        score = min(score, 39)

    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"
    return score, level
