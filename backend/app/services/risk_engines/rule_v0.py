"""规则引擎 v0：把现有的 if-else 规则集包装成统一的 RiskEngine 实现。

定位说明
--------
这个实现是**阶段 I 的占位机制**，不是最终的风控方案。它存在的意义有三个：
1. 让「提交申请 → 出决策」这条链路先跑通，验证接口、状态流转与数据落库；
2. 给阶段 II 的评分卡提供一个对照基线（新模型的效果不应低于它）；
3. 作为评分卡上线初期的兜底——模型不可用时可以回退到规则。

它本身不含任何统计学习成分：规则阈值是人工设定的经验值，
不是从数据里拟合出来的，因此不具备真正的风险区分能力。
"""

from app.models import DecisionStatus
from app.services.feature import FeatureProfile
from app.services.risk import risk_result
from app.services.rule_engine import evaluate
from app.services.risk_engines.base import RiskEngine, RiskVerdict


class RuleEngineV0(RiskEngine):
    """阶段 I 的规则引擎实现。

    计算分两步，两步的职责不同，不能合并：
    1. evaluate()：判定结论（通过 / 转人工 / 拒绝）和降额比例，这是「准入决策」；
    2. risk_result()：把特征折算成 0~100 的风险分和风险档位，这是「风险度量」。

    第 2 步内部会按第 1 步的结论做一次对齐（见 services/risk.py），
    保证「规则判通过但分数落在高风险区间」这类自相矛盾的情况不会出现。
    """

    name = "rule_v0"
    version = "1.0"

    def decide(self, profile: FeatureProfile) -> RiskVerdict:
        # 第 1 步：跑规则集，得到结论、降额比例和命中原因
        result = evaluate(profile)

        # 第 2 步：按结论对齐后计算风险分与档位
        score, level = risk_result(profile, result.status)

        return RiskVerdict(
            status=result.status,
            reduce_ratio=result.reduce_ratio,
            reasons=result.reasons,
            risk_score=score,
            risk_level=level,
            engine=self.name,
            model_version=self.version,
        )
