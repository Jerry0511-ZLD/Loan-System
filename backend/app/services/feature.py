"""特征聚合:把多数据源原始结果拍平成统一画像,供规则引擎消费。"""

from pydantic import BaseModel


class FeatureProfile(BaseModel):
    # 征信
    overdue_count_6m: int
    current_debt: float
    credit_card_count: int
    is_blacklisted: bool
    # 运营商
    active_months: int
    # 公积金
    fund_months: int
    fund_active: bool
    # 衍生
    dti: float  # 负债收入比 = current_debt / monthly_income


def aggregate(raw: dict[str, dict], monthly_income: float) -> FeatureProfile:
    """raw = {"credit_bureau": {...}, "carrier": {...}, "housing_fund": {...}}"""
    credit = raw.get("credit_bureau", {})
    carrier = raw.get("carrier", {})
    housing = raw.get("housing_fund", {})

    current_debt = credit.get("current_debt", 0.0)
    dti = round(current_debt / monthly_income, 4) if monthly_income > 0 else 99.0

    return FeatureProfile(
        overdue_count_6m=credit.get("overdue_count_6m", 0),
        current_debt=current_debt,
        credit_card_count=credit.get("credit_card_count", 0),
        is_blacklisted=credit.get("is_blacklisted", False),
        active_months=carrier.get("active_months", 0),
        fund_months=housing.get("fund_months", 0),
        fund_active=housing.get("active", False),
        dti=dti,
    )
