"""初始化演示数据：5 个登录账号 + 6 个贷款产品。

- 启动时自动执行，幂等（已存在就跳过，不会重复插入）。
- 4 个普通用户的身份证号是特意挑的：Mock 数据源用身份证号做随机种子，
  这 4 个号能稳定复现「通过 / 通过但降额 / 转人工 / 拒贷」四种风控结果，方便演示。
  （月收入都按 15000 算，申请金额建议 50000、期限 12 期）
"""

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Product, User, RiskRuleConfig


DEMO_USERS = [
    {
        "username": "admin", "password": "admin123", "name": "风控管理员", "role": "admin",
        "phone": "13900000001", "id_card": "510101199001010001", "monthly_income": 30000,
        "note": "管理端账号：能看申请列表",
    },
    {
        "username": "demo", "password": "123456", "name": "陈晓", "role": "user",
        "phone": "13800000001", "id_card": "510101199001010021", "monthly_income": 15000,
        "note": "申请结果：通过",
    },
    {
        "username": "demo2", "password": "123456", "name": "李伟", "role": "user",
        "phone": "13800000002", "id_card": "510101199001010016", "monthly_income": 15000,
        "note": "申请结果：通过但降额 20%（公积金未正常缴纳）",
    },
    {
        "username": "demo3", "password": "123456", "name": "王芳", "role": "user",
        "phone": "13800000003", "id_card": "510101199001010029", "monthly_income": 15000,
        "note": "申请结果：转人工（多头授信）",
    },
    {
        "username": "demo4", "password": "123456", "name": "赵强", "role": "user",
        "phone": "13800000004", "id_card": "510101199001010001", "monthly_income": 15000,
        "note": "申请结果：拒贷（近 6 月多次逾期 + 负债收入比过高）",
    },
]

DEMO_PRODUCTS = [
    {
        "id": "p001", "name": "极速信用贷", "description": "纯线上申请，最快 5 分钟到账，适合短期周转",
        "min_amount": 500, "max_amount": 20000, "min_term": 3, "max_term": 12,
        "base_rate": 0.072, "tags": ["小额", "极速", "新人专享"], "featured": True, "sort_order": 1,
    },
    {
        "id": "p002", "name": "工薪优享贷", "description": "面向上班族，凭工牌即可申请，利率低至 4.8%",
        "min_amount": 10000, "max_amount": 200000, "min_term": 6, "max_term": 36,
        "base_rate": 0.048, "tags": ["低息", "工薪族", "额度高"], "featured": True, "sort_order": 2,
    },
    {
        "id": "p003", "name": "公积金贷", "description": "连续缴存公积金 6 个月以上可申请，利率最低",
        "min_amount": 20000, "max_amount": 300000, "min_term": 12, "max_term": 36,
        "base_rate": 0.039, "tags": ["公积金", "超低息"], "featured": True, "sort_order": 3,
    },
    {
        "id": "p004", "name": "大额消费贷", "description": "单笔最高 50 万，支持装修、购车、教育等大额消费场景",
        "min_amount": 50000, "max_amount": 500000, "min_term": 12, "max_term": 60,
        "base_rate": 0.065, "tags": ["大额", "长期"], "featured": False, "sort_order": 4,
    },
    {
        "id": "p005", "name": "装修分期", "description": "装修专属额度，凭装修合同可提额，支持先息后本",
        "min_amount": 10000, "max_amount": 150000, "min_term": 6, "max_term": 48,
        "base_rate": 0.056, "tags": ["装修", "分期"], "featured": False, "sort_order": 5,
    },
    {
        "id": "p006", "name": "车主贷", "description": "有车即可申请，不押车，额度最高 20 万",
        "min_amount": 30000, "max_amount": 200000, "min_term": 12, "max_term": 36,
        "base_rate": 0.085, "tags": ["有车", "不押车"], "featured": False, "sort_order": 6,
    },
]


DEFAULT_RULE_CONFIGS = [
    {"rule_name": "blacklist"},
    {"rule_name": "overdue_6m", "threshold": 2},
    {"rule_name": "dti", "threshold": 0.7},
    {"rule_name": "multi_platform", "threshold": 5},
    {"rule_name": "short_tenure", "threshold": 3},
    {"rule_name": "fund_inactive", "reduce_ratio": 0.2},
]


async def seed_all() -> None:
    async with SessionLocal() as db:
        # 1. 账号
        rows = (await db.execute(select(User.username))).scalars().all()
        existing_usernames = set(rows)
        for item in DEMO_USERS:
            if item["username"] in existing_usernames:
                continue
            db.add(
                User(
                    username=item["username"],
                    password_hash=hash_password(item["password"]),
                    name=item["name"],
                    role=item["role"],
                    phone=item["phone"],
                    id_card=item["id_card"],
                    monthly_income=item["monthly_income"],
                )
            )

        # 2. 产品
        for item in DEMO_PRODUCTS:
            if await db.get(Product, item["id"]) is None:
                db.add(Product(**item))

        # 3. 规则阈值配置（幂等：已有同名规则就跳过，不覆盖管理员改过的值）
        existing_rules = set(
            (await db.execute(select(RiskRuleConfig.rule_name))).scalars().all()
        )
        for item in DEFAULT_RULE_CONFIGS:
            if item["rule_name"] in existing_rules:
                continue
            db.add(RiskRuleConfig(**item))


        await db.commit()
