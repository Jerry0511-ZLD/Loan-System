package com.uestc.loanapp.net

/**
 * 网络请求的回调接口（一个只有两个方法的“约定”）。
 *
 * 为什么要用回调？因为网络请求是“异步”的：调用 login() 之后不会立刻拿到结果，
 * 要等几秒服务器才回话。所以我们先告诉它“成功时调用 onSuccess，失败时调用 onFailure”，
 * 结果回来时它再反过来通知我们。
 *
 * Kotlin 里接口的写法就是 fun 关键字，实现这个接口的匿名对象可以简写成 lambda 或 object 表达式。
 *
 * **重要约定：**这两个方法一定是在主线程（UI 线程）被调用的。
 * Android 规定只有主线程才能修改界面，而我们又不能让联网这种事占用主线程（会卡死界面），
 * 所以 ApiService 在内部把结果用 Handler 切回主线程后再回调，
 * 这样你在 onSuccess 里就可以放心地直接 setText、notifyDataSetChanged。
 *
 * 数据写成可空类型 T?，因为服务器有可能返回 {"data": null}。
 */
interface ApiCallback<T> {

    /** 请求成功，data 是服务器返回的业务数据。 */
    fun onSuccess(data: T?)

    /** 请求失败（网络断了、服务器报错、账号密码不对等），message 是可以直接给用户看的提示。 */
    fun onFailure(message: String?)
}