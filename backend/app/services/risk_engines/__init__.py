"""风控引擎工厂 / 注册表。

上层不直接 import 具体引擎类，而是调用 get_engine()：
    engine = get_engine()                     # 按配置项选
    verdict = engine.decide(profile)

新增一个引擎（例如阶段 II 的评分卡）时，只需要两步：
    1. 写一个继承 RiskEngine 的类，放在本目录下；
    2. 在下面的 _REGISTRY 里登记一行。
decision.py 与所有业务代码都不需要改。
"""

from app.config import settings
from app.services.risk_engines.base import RiskEngine, RiskVerdict
from app.services.risk_engines.rule_v0 import RuleEngineV0

# 引擎注册表：配置值 -> 引擎类
_REGISTRY = {
    "rule_v0": RuleEngineV0,
}

# 配置项写错或引擎尚未实现时的兜底引擎
DEFAULT_ENGINE = "rule_v0"


def get_engine(name: str | None = None) -> RiskEngine:
    """按名称取引擎实例；不传则读配置项 risk_engine。

    配置了尚未实现的引擎（例如阶段 II 的 scorecard 还没写完）时，
    不直接抛异常中断业务流程，而是回退到默认引擎并打印提示——
    这样开发过程中改配置不会把整条链路弄挂，决策记录里的 engine 字段
    也会如实写成实际使用的引擎，不会误导复盘。
    """
    engine_name = name or settings.risk_engine
    engine_cls = _REGISTRY.get(engine_name)
    if engine_cls is None:
        print(
            f"[risk_engine] 未找到引擎 {engine_name!r}，"
            f"已回退到 {DEFAULT_ENGINE!r}。可用引擎：{sorted(_REGISTRY)}"
        )
        engine_cls = _REGISTRY[DEFAULT_ENGINE]
    return engine_cls()


__all__ = ["RiskEngine", "RiskVerdict", "get_engine"]
