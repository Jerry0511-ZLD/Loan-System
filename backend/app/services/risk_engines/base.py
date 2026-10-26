"""风控引擎的统一接口（抽象层）。

为什么要有这一层
----------------
阶段 I 的决策逻辑是「一堆 if-else 规则」，直接写在 services/rule_engine.py 里。
但按课程规划，阶段 II 要换成基于评分卡的机制（分箱 → WOE → 逻辑回归 → 评分标尺），
阶段 III 还要支持多模型与 A/B 对比。如果决策链路直接把 evaluate(profile) 写死，
每换一次机制就要动 decision.py，历史决策也没法标记「这条是哪套机制算出来的」。

这里把「怎么算」和「怎么用」拆开：
- 上层（decision.py）只依赖 RiskEngine.decide() 这个契约；
- 具体实现（rule_v0 / scorecard / ml）各自独立成文件，通过配置 config.risk_engine 切换。

换引擎时只需要：新增一个实现类 + 在 risk_engines/__init__.py 注册 + 改配置项，
decision.py 一行都不用动。这也是需求规格说明书 6.5 节「风控引擎可替换」的落地方式。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models import DecisionStatus
from app.services.feature import FeatureProfile


@dataclass
class RiskVerdict:
    """风控引擎的统一输出结构。

    所有引擎（规则、评分卡、机器学习）都必须返回这个结构，
    上层不关心引擎内部是查表、算分还是过模型，只认这几个字段。

    字段说明：
    - status：决策结论，approved / manual / rejected 三选一
    - reduce_ratio：降额比例，0 表示不降额，0.2 表示批核额度打八折
    - reasons：命中原因列表，管理端展示和事后审计都靠它
    - risk_score：0~100 的风险分，越高越危险
    - risk_level：风险档位，LOW / MEDIUM / HIGH
    - engine：引擎标识，会写进 decisions.engine，用于区分「这条决策是谁算的」
    - model_version：引擎/模型版本，阶段 II 换评分卡后，用它对历史决策做效果对比
    """

    status: DecisionStatus
    reduce_ratio: float
    reasons: list
    risk_score: int
    risk_level: str
    engine: str
    model_version: str


class RiskEngine(ABC):
    """风控引擎抽象基类。

    子类必须定义 name / version 两个类属性，并实现 decide()。
    name 用来在配置里选择引擎，version 用来标记决策记录的模型版本。
    """

    name: str = "base"
    version: str = "0"

    @abstractmethod
    def decide(self, profile: FeatureProfile, rule_configs: dict | None = None) -> RiskVerdict:
        """输入特征画像，输出决策结论。

        实现方注意：本方法应保持「纯函数」语义——只根据传入的特征计算，
        不读写数据库、不调用外部接口。这样同一份特征永远得到同一个结论，
        便于单元测试和问题复现。
        """
        raise NotImplementedError
