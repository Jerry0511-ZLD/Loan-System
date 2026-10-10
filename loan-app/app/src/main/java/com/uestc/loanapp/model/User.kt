package com.uestc.loanapp.model

/**
 * 用户（借款人）信息。
 *
 * 字段和后端 `GET /api/me`、以及登录接口返回里的 `user` 对象一一对应，
 * 所以名字必须和 JSON 里的键完全一致（Gson 是按字段名对应的）。
 *
 * 注意：token 不在这个对象里。后端登录接口把它放在 data 这一层，
 * 和 user 平级，所以那边用 [LoginResult] 来接。
 */
data class User(
    var id: String? = null,

    /** 登录名，例如 demo / admin */
    var username: String? = null,

    /** 姓名，例如 陈晓 */
    var name: String? = null,

    /** 角色：user 普通用户 / admin 管理员 */
    var role: String? = null,

    var phone: String? = null,

    /** 身份证号（后端已脱敏，例如 5101********0021） */
    var idCard: String? = null,

    /** 月收入（元） */
    var monthlyIncome: Double = 0.0,

    /** 注册时间 */
    var createdAt: String? = null
)