import hashlib

from app.datasources.base import DataSource


def _seed(id_card: str) -> int:
    return int(hashlib.md5(id_card.encode()).hexdigest(), 16)


class HousingFundSource(DataSource):
    """公积金数据 Mock。"""

    name = "housing_fund"

    async def fetch(self, id_card: str, phone: str) -> dict:
        s = _seed(id_card)
        return {
            "fund_months": (s % 60) + 1,        # 公积金缴纳月数
            "monthly_contribution": (s % 20) * 100,  # 月缴存额(元)
            "active": (s % 10 != 0),            # 是否正常缴纳
        }
