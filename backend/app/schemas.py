"""入参模型。

字段名策略：以前端为准（product / amount / term / purpose ...），
同时用 AliasChoices 兼容 camelCase 和后端内部的 snake_case 写法，
前端怎么写都能收到，不会因为一个下划线就 422。
"""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from typing import Literal


class RegisterRequest(BaseModel):
    """注册：账号可以是用户名，也可以是手机号。"""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    username: str | None = Field(
        default=None, validation_alias=AliasChoices("username", "account")
    )
    password: str | None = Field(
        default=None, validation_alias=AliasChoices("password", "passwd", "pwd")
    )
    name: str | None = Field(
        default=None, validation_alias=AliasChoices("name", "n")
    )


class LoginRequest(BaseModel):
    """登录：账号可以是用户名，也可以是手机号。"""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    username: str | None = Field(
        default=None, validation_alias=AliasChoices("username", "account", "phone", "mobile")
    )
    password: str | None = Field(
        default=None, validation_alias=AliasChoices("password", "passwd", "pwd")
    )


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class LoanCreateRequest(BaseModel):
    """提交贷款申请（前端申请表单）。"""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    product_id: str = Field(
        validation_alias=AliasChoices("productId", "product_id", "product")
    )
    amount: float = Field(
        validation_alias=AliasChoices("amount", "requestedAmount", "requested_amount", "loanAmount")
    )
    term: int = Field(
        default=12,
        validation_alias=AliasChoices("term", "termMonths", "term_months", "months", "period"),
    )
    purpose: str | None = Field(
        default=None, validation_alias=AliasChoices("purpose", "loanPurpose", "use")
    )

    # 下面四项：表单里填了就优先用表单的；没填则用登录用户的资料兜底
    applicant_name: str | None = Field(
        default=None, validation_alias=AliasChoices("applicantName", "applicant_name", "name", "realName")
    )
    id_card: str | None = Field(
        default=None, validation_alias=AliasChoices("idCard", "id_card", "idNo", "idNumber")
    )
    phone: str | None = Field(default=None, validation_alias=AliasChoices("phone", "mobile"))
    monthly_income: float | None = Field(
        default=None, validation_alias=AliasChoices("monthlyIncome", "monthly_income", "income")
    )

    @field_validator("product_id", mode="before")
    @classmethod
    def _accept_product_object(cls, value):
        """兼容前端把整个产品对象传过来的写法，自动取出里面的 id。"""
        if isinstance(value, dict):
            return (
                value.get("id")
                or value.get("productId")
                or value.get("product_id")
                or value.get("name")
            )
        return value

    @field_validator("term", mode="before")
    @classmethod
    def _accept_term_string(cls, value):
        """兼容 "12期" / "12" 这类字符串。"""
        if isinstance(value, str):
            digits = "".join(ch for ch in value if ch.isdigit())
            if digits:
                return int(digits)
        return value


class ApplicationCreateRequest(BaseModel):
    """管理端/联调直录一笔进件（不依赖登录用户资料）。"""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    applicant_name: str = Field(
        validation_alias=AliasChoices("applicantName", "applicant_name", "name")
    )
    id_card: str = Field(validation_alias=AliasChoices("idCard", "id_card", "idNo"))
    phone: str = Field(validation_alias=AliasChoices("phone", "mobile"))
    monthly_income: float = Field(
        gt=0, validation_alias=AliasChoices("monthlyIncome", "monthly_income", "income")
    )
    requested_amount: float = Field(
        gt=0, validation_alias=AliasChoices("requestedAmount", "requested_amount", "amount")
    )
    term: int = Field(
        default=12, validation_alias=AliasChoices("term", "termMonths", "term_months")
    )
    purpose: str | None = Field(
        default=None, validation_alias=AliasChoices("purpose", "loanPurpose")
    )
    product_id: str | None = Field(
        default=None, validation_alias=AliasChoices("productId", "product_id", "product")
    )


class ReviewRequest(BaseModel):
    """人工复核请求：管理端处理「转人工」的申请单时使用。

    对应需求规格说明书用例 UC-05（人工复核审批）。
    设计要点：
    - action 必填，只接受 approve / reject 两种语义，但允许前端传中文或 pass 之类的近义词，
      统一在校验器里归一化，避免前端因为一个词不一致就 422；
    - approvedAmount / rate 是「可选覆盖项」：专员认为系统给的额度不合适时可以手工调整；
      不传则沿用系统原决策的数值；
    - comment 是复核意见，会写进决策记录，供事后追责与复盘。
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    action: str = Field(
        validation_alias=AliasChoices("action", "result", "decision", "reviewResult")
    )
    approved_amount: float | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("approvedAmount", "approved_amount", "amount"),
    )
    rate: float | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("rate", "interestRate", "interest_rate"),
    )
    comment: str | None = Field(
        default=None,
        validation_alias=AliasChoices("comment", "remark", "reviewComment", "reason"),
    )

    @field_validator("action", mode="before")
    @classmethod
    def _normalize_action(cls, value):
        """把 approve / pass / 通过 这类不同写法统一成 approve 或 reject。

        多一层归一化而不是直接拒绝，是为了降低前后端联调成本：
        前端同学写 'pass'、'agree'、'通过' 都能被接受，后端内部只处理两个标准值。
        """
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("approve", "approved", "pass", "agree", "通过", "同意", "批准"):
                return "approve"
            if v in ("reject", "rejected", "refuse", "deny", "拒绝", "驳回"):
                return "reject"
        return value

    @field_validator("action")
    @classmethod
    def _check_action(cls, value):
        if value not in ("approve", "reject"):
            raise ValueError("action 只能是 approve（通过）或 reject（拒绝）")
        return value


class ProductCreateRequest(BaseModel):
    """管理端上架新产品。"""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    name: str = Field(min_length=1)
    description: str = ""
    min_amount: float = Field(gt=0, validation_alias=AliasChoices("minAmount", "min_amount"))
    max_amount: float = Field(gt=0, validation_alias=AliasChoices("maxAmount", "max_amount"))
    min_term: int = Field(default=3, ge=1, validation_alias=AliasChoices("minTerm", "min_term"))
    max_term: int = Field(default=36, ge=1, validation_alias=AliasChoices("maxTerm", "max_term"))
    base_rate: float = Field(gt=0, lt=1, validation_alias=AliasChoices("baseRate", "base_rate"))
    tags: list[str] = Field(default=[], validation_alias=AliasChoices("tags"))
    featured: bool = False
    sort_order: int = 0


class ProductUpdateRequest(BaseModel):
    """管理端修改产品：改哪项传哪项，不传的项不动。"""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    name: str | None = None
    description: str | None = None
    min_amount: float | None = Field(default=None, gt=0, validation_alias=AliasChoices("minAmount", "min_amount"))
    max_amount: float | None = Field(default=None, gt=0, validation_alias=AliasChoices("maxAmount", "max_amount"))
    min_term: int | None = Field(default=None, ge=1, validation_alias=AliasChoices("minTerm", "min_term"))
    max_term: int | None = Field(default=None, ge=1, validation_alias=AliasChoices("maxTerm", "max_term"))
    base_rate: float | None = Field(default=None, gt=0, lt=1, validation_alias=AliasChoices("baseRate", "base_rate"))
    tags: list[str] | None = None
    featured: bool | None = None
    sort_order: int | None = None
    status: Literal["on", "off"] | None = None