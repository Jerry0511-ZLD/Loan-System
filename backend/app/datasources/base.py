from abc import ABC, abstractmethod


class DataSource(ABC):
    """数据源适配层统一抽象。

    每个外部数据源(征信/运营商/公积金/设备指纹...)实现此接口。
    MVP 阶段用 Mock 实现返回伪数据;接入真实源时只改对应 adapter,
    上层聚合与规则引擎不受影响。
    """

    name: str

    @abstractmethod
    async def fetch(self, id_card: str, phone: str) -> dict:
        """返回该数据源的原始字段。字段结构由各 adapter 自定义。"""
        ...
