import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    # MVP 用本地时间，前端拿来就能直接展示；正式项目建议统一存 UTC
    return datetime.now()


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class ApplicationStatus(str, enum.Enum):
    """对前端暴露的申请单状态（全大写，和前端约定一致）。"""

    PENDING = "PENDING"    # 待审批（含"转人工复核"）
    APPROVED = "APPROVED"  # 已通过
    REJECTED = "REJECTED"  # 已拒绝


class DecisionStatus(str, enum.Enum):
    """规则引擎的内部结论，比前端多一个"转人工"。"""

    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL = "manual"  # 转人工


class User(Base):
    """登录用户。管理端页面用 role=admin 的账号登录。"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(16), default=UserRole.USER.value)  # user | admin
    phone: Mapped[str] = mapped_column(String(20), default="")
    id_card: Mapped[str] = mapped_column(String(32), default="")     # 资料兜底：申请表单没填就用这里
    monthly_income: Mapped[float] = mapped_column(Float, default=0.0)  # 同上
    created_at: Mapped[datetime] = mapped_column(default=_now)


class Product(Base):
    """贷款产品（首页卡片）。"""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(255), default="")
    min_amount: Mapped[float] = mapped_column(Float, default=0.0)   # 起贷金额(元)
    max_amount: Mapped[float] = mapped_column(Float, default=0.0)   # 最高额度(元)
    min_term: Mapped[int] = mapped_column(Integer, default=3)       # 最短期限(月)
    max_term: Mapped[int] = mapped_column(Integer, default=36)      # 最长期限(月)
    base_rate: Mapped[float] = mapped_column(Float, default=0.12)   # 年化基础利率(小数: 0.048 = 4.8%)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否首页推荐
    status: Mapped[str] = mapped_column(String(8), default="on")    # on 上架 | off 下架
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=_now)


class Application(Base):
    """一笔贷款申请单。既是"我的贷款"，也是管理端的申请记录。"""

    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(32), index=True, default="")   # 提交人
    product_id: Mapped[str] = mapped_column(String(32), default="")            # 贷款产品
    applicant_name: Mapped[str] = mapped_column(String(64))
    id_card: Mapped[str] = mapped_column(String(32))
    phone: Mapped[str] = mapped_column(String(20))
    monthly_income: Mapped[float] = mapped_column(Float)
    requested_amount: Mapped[float] = mapped_column(Float)          # 申请金额(元)，前端字段名 amount
    term: Mapped[int] = mapped_column(Integer, default=12)          # 期限(月)，前端字段名 term
    purpose: Mapped[str] = mapped_column(String(128), default="")   # 借款用途
    # 对前端的状态：PENDING / APPROVED / REJECTED
    status: Mapped[str] = mapped_column(String(16), default=ApplicationStatus.PENDING.value)
    # 是否等待人工复核。转人工时置 True，人工处理完置 False。
    # 单独存一列而不是每次去 decisions 表里查，是为了让管理端"待办列表"能直接在 SQL 层过滤和分页。
    review_required: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(8), default="")   # LOW / MEDIUM / HIGH
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)    # 0~100，越高越危险
    created_at: Mapped[datetime] = mapped_column(default=_now)
    decided_at: Mapped[datetime | None] = mapped_column(default=None)  # 出风控结论的时间


class Decision(Base):
    """规则引擎给出的决策结果（留痕，一笔申请一条）。

    一笔申请可能有多条决策记录：
    - 自动决策：source="auto"，申请提交时由风控引擎产生；
    - 人工复核：source="manual"，风控专员处理"转人工"时追加，原始自动决策保留不覆盖。
    因此读取决策时必须按创建时间取最新一条，见 services/lookup.py。
    """

    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    application_id: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[DecisionStatus] = mapped_column(Enum(DecisionStatus))
    approved_amount: Mapped[float] = mapped_column(Float, default=0.0)  # 批核额度(元)
    rate: Mapped[float] = mapped_column(Float, default=0.0)             # 批核年化利率(小数)
    reasons: Mapped[list] = mapped_column(JSON, default=list)           # 命中的规则原因

    # ---- 决策可追溯性 ----
    engine: Mapped[str] = mapped_column(String(32), default="rule_v0")   # 决策引擎标识
    model_version: Mapped[str] = mapped_column(String(32), default="0.1")  # 引擎/模型版本
    feature_profile: Mapped[dict] = mapped_column(JSON, default=dict)   # 聚合后的特征(留痕)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)          # 三源原始数据快照(留痕)

    # ---- 人工复核 ----
    source: Mapped[str] = mapped_column(String(16), default="auto")     # auto | manual
    reviewer_id: Mapped[str] = mapped_column(String(32), default="")    # 复核人用户ID
    reviewed_at: Mapped[datetime | None] = mapped_column(default=None)  # 复核时间
    comment: Mapped[str] = mapped_column(String(255), default="")       # 复核意见

    created_at: Mapped[datetime] = mapped_column(default=_now)
