import hashlib

from app.datasources.base import DataSource


def _seed(id_card: str) -> int:
    return int(hashlib.md5(id_card.encode()).hexdigest(), 16)


class CreditBureauSource(DataSource):
    """人行征信 Mock。真实接入时换 httpx 调用。"""

    name = "credit_bureau"

    async def fetch(self, id_card: str, phone: str) -> dict:
        s = _seed(id_card)
        return {
            "overdue_count_6m": s % 4,            # 近6月逾期次数
            "overdue_count_24m": s % 8,          # 近24月逾期次数
            "current_debt": (s % 50) * 1000,     # 当前未结清负债(元)
            "loan_balance": (s % 30) * 10000,    # 贷款余额(元)
            "credit_card_count": s % 6,          # 信用卡数
            "is_blacklisted": (s % 13 == 0),     # 是否命中黑名单
        }
