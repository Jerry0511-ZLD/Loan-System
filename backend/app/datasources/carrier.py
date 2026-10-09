import hashlib

from app.datasources.base import DataSource


def _seed(id_card: str) -> int:
    return int(hashlib.md5(id_card.encode()).hexdigest(), 16)


class CarrierSource(DataSource):
    """运营商数据 Mock。"""

    name = "carrier"

    async def fetch(self, id_card: str, phone: str) -> dict:
        s = _seed(id_card)
        return {
            "active_months": (s % 36) + 1,      # 在网时长(月)
            "real_named": True,                 # 是否实名
            "last_active_days": s % 7,          # 最近活跃距今天数
        }
