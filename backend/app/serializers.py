"""出参组装：把数据库对象拍平成前端要的 camelCase 字典。

统一在这里出口，好处是字段名/时间格式/脱敏只有一个地方定义。
"""

from datetime import datetime

from app.models import Application, Decision, Product, User

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"  # 时间统一返回这个格式的字符串，前端可直接显示


def fmt_time(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime(TIME_FORMAT)


def mask_id_card(id_card: str) -> str:
    """身份证脱敏：510101********0021 这种。"""
    if not id_card or len(id_card) < 8:
        return id_card or ""
    return id_card[:4] + "*" * (len(id_card) - 8) + id_card[-4:]


def mask_phone(phone: str) -> str:
    """手机号脱敏：138****0001 这种。

    为什么手机号也要脱敏：它和身份证一样属于《个人信息保护法》下的敏感个人信息，
    需求规格说明书 NFR-S4 明确要求「身份证号、手机号在接口返回时均脱敏」。
    脱敏必须放在服务端出口做，不能依赖前端「不显示」——
    前端拿到的响应体才是真正可控的信息边界。
    """
    if not phone or len(phone) < 7:
        return phone or ""
    return phone[:3] + "*" * (len(phone) - 7) + phone[-4:]


def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "role": user.role,  # user | admin，前端据此决定是否显示管理端入口
        "phone": mask_phone(user.phone),      # 脱敏后返回
        "idCard": mask_id_card(user.id_card),  # 脱敏后返回
        "monthlyIncome": user.monthly_income,
        "createdAt": fmt_time(user.created_at),
    }


def product_to_dict(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "minAmount": product.min_amount,
        "maxAmount": product.max_amount,
        "minTerm": product.min_term,
        "maxTerm": product.max_term,
        "rate": product.base_rate,  # 年化利率，小数形式：0.048 表示 4.8%
        "rateText": f"{product.base_rate * 100:g}% 起",  # 直接展示用
        "tags": product.tags or [],
        "featured": product.featured,
    }


def decision_to_dict(decision: Decision) -> dict:
    """决策明细。管理端「风控明细」页直接消费这个结构。

    相比旧版多返回三项，都是为了让决策「可解释、可追溯」：
    - engine / modelVersion：这条结论是哪套识别机制、哪个版本算出来的；
    - source：自动决策（auto）还是人工复核（manual）；
    - reviewerId / reviewedAt / comment：人工复核的留痕。
    """
    return {
        "id": decision.id,
        "status": decision.status.value.upper(),  # APPROVED / REJECTED / MANUAL
        "approvedAmount": decision.approved_amount,
        "rate": decision.rate,
        "rateText": f"{decision.rate * 100:.2f}%",
        "reasons": decision.reasons or [],
        "featureProfile": decision.feature_profile or {},
        "engine": decision.engine,                 # 引擎标识，如 rule_v0
        "modelVersion": decision.model_version,    # 引擎版本
        "source": decision.source,                 # auto | manual
        "reviewerId": decision.reviewer_id,
        "reviewedAt": fmt_time(decision.reviewed_at),
        "comment": decision.comment,
        "createdAt": fmt_time(decision.created_at),
    }


def loan_to_dict(
    application: Application,
    decision: Decision | None = None,
    product: Product | None = None,
) -> dict:
    """一笔申请单 = 前端"我的贷款"列表里的一行，也是管理端列表的一行。"""
    decision_status = decision.status.value.upper() if decision is not None else None
    if decision is not None and decision.rate > 0:
        rate_text = f"{decision.rate * 100:.2f}%"
    else:
        rate_text = ""
    return {
        "id": application.id,
        "userId": application.user_id,
        "applicantName": application.applicant_name,
        "phone": mask_phone(application.phone),   # 管理端同样脱敏，合规要求不分端
        "idCard": mask_id_card(application.id_card),
        "monthlyIncome": application.monthly_income,
        "productId": application.product_id,
        "productName": product.name if product is not None else "",
        "amount": application.requested_amount,  # 申请金额
        "term": application.term,                # 期限(月)
        "purpose": application.purpose,
        "status": application.status,            # PENDING / APPROVED / REJECTED
        "decisionStatus": decision_status,       # 内部结论，转人工是 MANUAL
        "reviewRequired": decision_status == "MANUAL",
        "riskLevel": application.risk_level,     # LOW / MEDIUM / HIGH
        "riskScore": application.risk_score,     # 0~100，越高越危险
        "approvedAmount": decision.approved_amount if decision is not None else 0.0,
        "rate": decision.rate if decision is not None else 0.0,
        "rateText": rate_text,
        "reasons": (decision.reasons or []) if decision is not None else [],
        "createdAt": fmt_time(application.created_at),
        "decidedAt": fmt_time(application.decided_at),
    }
