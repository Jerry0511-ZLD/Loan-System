"""入参模型。

字段名策略：以前端为准（product / amount / term / purpose ...），
同时用 AliasChoices 兼容 camelCase 和后端内部的 snake_case 写法，
前端怎么写都能收到，不会因为一个下划线就 422。
"""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class LoginRequest(BaseModel):
    """登录：账号可以是用户名，也可以是手机号。"""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    username: str | None = Field(
        default=None, validation_alias=AliasChoices("username", "account", "phone", "mobile")
    )
    password: str | None = Field(
        default=None, validation_alias=AliasChoices("password", "passwd", "pwd")
    )


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
