package com.uestc.loanapp.model

import com.google.gson.annotations.SerializedName

/**
 * 一笔贷款申请单。这是整个借款人端最核心的数据。
 *
 * 字段和后端 `GET /api/loans`、`GET /api/loans/{id}` 返回的对象一一对应。
 *
 * 状态 status 只有三个值，必须和 Web 管理端的约定完全一致：
 * - PENDING  待审批（包含风控判定的"转人工"）
 * - APPROVED 已通过
 * - REJECTED 已拒绝
 *
 * ⚠️ 两个字段名和后端不一致，所以用 @SerializedName 做映射
 *（Gson 默认按字段名严格对应，名字对不上就会解析成 null）：
 * - 本地叫 product，后端叫 productName
 * - 本地叫 applyTime，后端叫 createdAt
 * 需要一个字段"本地名字更顺手、但 JSON 里是另一个名字"时，就用它。
 */
data class LoanApplication(
    var id: String? = null,

    /** 产品编号，例如 p001。提交申请时后端要的是它 */
    var productId: String? = null,

    /** 产品名称，例如 极速信用贷（JSON 里是 productName） */
    @SerializedName("productName")
    var product: String? = null,

    /** 申请金额（元） */
    var amount: Double = 0.0,

    /** 借款期限（月） */
    var term: Int = 0,

    /** 资金用途 */
    var purpose: String? = null,

    /** 状态：PENDING / APPROVED / REJECTED */
    var status: String? = null,

    /** 申请时间（JSON 里是 createdAt），例如 2026-10-10 12:34:56 */
    @SerializedName("createdAt")
    var applyTime: String? = null,

    /** 风险等级：LOW / MEDIUM / HIGH */
    var riskLevel: String? = null,

    /** 风险评分，0~100，越高越危险 */
    var riskScore: Double? = null
)