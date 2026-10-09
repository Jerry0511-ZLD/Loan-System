from pydantic import BaseModel, Field

from app.models import DecisionStatus


# ---- 进件 ----
class ApplicationCreate(BaseModel):
    applicant_name: str
    id_card: str
    phone: str
    monthly_income: float = Field(gt=0)
    requested_amount: float = Field(gt=0)


class ApplicationOut(BaseModel):
    id: str
    applicant_name: str
    phone: str
    monthly_income: float
    requested_amount: float
    status: str


# ---- 决策 ----
class DecisionOut(BaseModel):
    id: str
    application_id: str
    status: DecisionStatus
    approved_amount: float
    rate: float
    reasons: list
    feature_profile: dict
