package com.uestc.loanapp.risk

/**
 * 风控服务接口：约定“查询某笔申请的风控结果”这件事。
 *
 * 界面需要展示“风险等级 / 风险评分”两个字段，因此先把接口约定好；
 * 具体实现（对接真实模型与多数据源）由实现类提供，界面代码无需改动。
 *
 * 使用方式：
 *
 *     val riskService: RiskService = ...                     // 获得一个实现
 *     riskService.getRiskResult(applicationId, callback)     // 拿到评分后再刷新界面
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