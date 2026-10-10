package com.uestc.loanapp.model

/**
 * 后端统一返回格式：{"code":0, "message":"ok", "data":{...}}。
 *
 * 泛型 <T> 就是 data 的具体类型：登录接口是 ApiResponse<LoginResult>，
 * 产品列表接口是 ApiResponse<List<Product>>，贷款列表接口是 ApiResponse<PageData<LoanApplication>>。
 * 有了泛型，一个类就能装下所有接口的返回值，不用每个接口都写一个返回类。
 *
 * 这里用 data class 是因为它天生就是“装数据的类”：自动生成 equals/hashCode/toString，
 * 还自带一个全默认参数的构造函数（Gson 解析时正好需要它）。
 *
 * 字段都写成可空类型并且给了默认值，因为 JSON 里可能根本没有这个键，
 * 这样解析出来是 null 而不是直接崩溃。
 * Gson 解析 JSON 时靠“字段名对应”，所以这里的字段名必须和后端返回的 JSON 键名完全一致。
 */
data class ApiResponse<T>(
    var code: Int = 0,
    var message: String? = null,
    var data: T? = null
) {

    /** 约定 code 为 0（有些后端用 200）表示这次请求处理成功。 */
    val isSuccess: Boolean
        get() = code == 0 || code == 200
}