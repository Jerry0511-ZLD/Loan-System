import calendar

from datetime import datetime
from app.models import Application, RepaymentPlan

def monthly_payment(principal: float, annual_rate: float, months: int) -> float:
    monthly_rate = annual_rate / 12
    M = principal * monthly_rate * (1 + annual_rate) ** months / ((1 + annual_rate) ** months - 1)
    return M


def build_schedule(approved_amount: float, annual_rate: float, months: int) -> list[dict]:
    remaining = approved_amount
    r = annual_rate / 12
    m = monthly_payment(approved_amount, annual_rate, months)
    schedule = []
    for i in range(1, months + 1):
        interest = round(remaining * r, 2)
        if i == months:
            principal = remaining
            payment = remaining + interest
            remaining = 0
        else:
            principal = round(m - interest, 2)
            payment = m
            remaining = round(remaining - principal, 2)
        schedule.append({
            "period_no": i,
            'principal': principal,
            'monthly_payment': payment,
            'interest': interest,
            'remaining_principal': remaining,
        })

    return schedule


def add_months(base: datetime, months: int) -> datetime:
    total = base.month + months - 1
    year = base.year + total // 12
    month = total % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(last_day, base.day)
    return datetime(year, month, day, base.hour, base.minute, base.second)


def generate_repayment_plan(
    application: Application,
    approved_amount: float,
    rate: float,
    db,
) -> None:
    schedule = build_schedule(approved_amount, rate, application.term)
    base = application.decided_at or datetime.now()
    for row in schedule:
        plan = RepaymentPlan(
            apploication_id = application.id,
            period_no = row['period_no'],
            due_date = row['payment'],
            monthly_payment = add_months(base, row['period_no']),
            interest = row['interest'],
            principal=row['principal'],
            remaining_principal = row['remaining_principal'],
            created_at = base
        )
        db.add(plan)