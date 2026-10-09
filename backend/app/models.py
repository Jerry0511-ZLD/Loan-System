import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class DecisionStatus(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL = "manual"  # 转人工


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    applicant_name: Mapped[str] = mapped_column(String(64))
    id_card: Mapped[str] = mapped_column(String(32))          # 身份证(脱敏前由调用方处理)
    phone: Mapped[str] = mapped_column(String(20))
    monthly_income: Mapped[float] = mapped_column(Float)
    requested_amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/done
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    application_id: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[DecisionStatus] = mapped_column(Enum(DecisionStatus))
    approved_amount: Mapped[float] = mapped_column(Float, default=0.0)
    rate: Mapped[float] = mapped_column(Float, default=0.0)         # 年化利率
    reasons: Mapped[list] = mapped_column(JSON, default=list)      # 触发的规则原因
    feature_profile: Mapped[dict] = mapped_column(JSON, default=dict)  # 聚合后的特征(留痕)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
