package com.uestc.loanapp.model

/**
 * 登录接口的返回结构，对应 `POST /api/login` 里 `data` 这一层的对象。
 *
 * JSON 长这样：
 * {
 *   "token": "xxxxx.yyyy",
 *   "tokenType": "Bearer",
 *   "expiresIn": 604800,
 *   "user": { "id": "...", "name": "陈晓", "phone": "...", ... }
 * }
 *
 * 关键点：token 和 user 是**平级**的，不在 user 里面。
 * 所以不能直接拿 data 当 [User] 解析，否则 user 里的字段全会是 null。
 */
data class LoginResult(
    var token: String? = null,
    var tokenType: String? = null,

    /** token 有效期（秒） */
    var expiresIn: Long = 0,

    var user: User? = null
)