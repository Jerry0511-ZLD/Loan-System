package com.uestc.loanapp.risk

/**
 * 风控服务接口 —— **第一阶段只做“定义”，没有任何实现类**。
 *
 * 为什么现在就把它写出来？因为前端界面已经需要展示“风险等级 / 风险评分”这两个字段了。
 * 先约定好接口长什么样，第二阶段的同学直接写一个实现类（对接真实模型和多数据源）就能接上，
 * 界面代码几乎不用改。
 *
 * 第二阶段的使用方式会类似这样（现在还不存在实现类，所以先不写这行代码）：
 *
 *     val riskService: RiskService = MockRiskServiceImpl()   // 第二阶段提供
 *     riskService.getRiskResult(applicationId, callback)     // 拿到评分后再刷新界面
 *
 * 第一阶段的运行时行为：不做任何计算，风控字段保持为空，详情页显示“暂无评分”。
 */
interface RiskService {

    /**
     * 根据申请编号查询这笔申请的风控结果。
     *
     * @param applicationId 申请编号（LoanApplication#getId）
     * @param callback      结果回调
     */
    fun getRiskResult(applicationId: String, callback: Callback)

    /**
     * 风控结果的回调。这里单独定义在接口内部，
     * 是为了避免和网络层的 ApiCallback 混在一起 —— 风控服务可能来自远程接口，也可能是本地模型。
     */
    interface Callback {

        /**
         * @param riskLevel 风险等级，例如 低风险 / 中风险 / 高风险
         * @param riskScore 风险评分，0~100
         */
        fun onSuccess(riskLevel: String?, riskScore: Double?)

        fun onFailure(message: String?)
    }
}