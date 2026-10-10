package com.uestc.loanapp.model

/**
 * 分页返回结构，对应 `GET /api/loans` 里 `data` 这一层的对象。
 *
 * JSON 长这样：
 * {
 *   "list": [ {...}, {...} ],
 *   "items": [ {...}, {...} ],   // 和 list 是同一份数组，写哪个都行
 *   "total": 12, "page": 1, "pageSize": 10, "totalPages": 2
 * }
 *
 * 注意：列表接口返回的**不是**纯数组，而是一个包着数组的对象，
 * 所以要取里面的 list，而不是直接当 List 解析。
 */
data class PageData<T>(
    var list: List<T>? = null,
    var items: List<T>? = null,
    var total: Int = 0,
    var page: Int = 1,
    var pageSize: Int = 10,
    var totalPages: Int = 0
)