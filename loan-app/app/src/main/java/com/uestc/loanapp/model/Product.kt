package com.uestc.loanapp.model

/**
 * 贷款产品（首页列表里的那几张卡片）。
 *
 * 字段和后端 `GET /api/products` 返回的对象一一对应。
 *
 * 关于利率：后端返回两个字段——
 * - [rate]：年化利率的**数字**形式（0.048 表示 4.8%），以后要算利息用它；
 * - [rateText]：**展示用的文案**（"4.8% 起"），界面上直接显示它。
 * 之前这里只有一个 String 的 rate，和后端对不上，所以拆成两个。
 */
data class Product(
    var id: String? = null,
    var name: String? = null,

    /** 最低可借金额（元） */
    var minAmount: Double = 0.0,

    /** 最高可借金额（元） */
    var maxAmount: Double = 0.0,

    /** 年化利率，小数形式：0.048 = 4.8% */
    var rate: Double = 0.0,

    /** 界面上直接显示的利率文案，例如 "4.8% 起" */
    var rateText: String? = null,

    /** 最短期限（期） */
    var minTerm: Int = 0,

    /** 最长期限（期） */
    var maxTerm: Int = 0,

    /** 一句话产品说明 */
    var description: String? = null,

    /** 标签，例如 ["低息", "工薪族"] */
    var tags: List<String>? = null,

    /** 是否首页推荐 */
    var featured: Boolean = false
)