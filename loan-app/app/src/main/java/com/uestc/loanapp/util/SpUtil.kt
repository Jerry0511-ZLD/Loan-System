package com.uestc.loanapp.util

import android.content.Context
import android.content.SharedPreferences

/**
 * SharedPreferences 的小封装，专门用来保存登录信息。
 *
 * SharedPreferences 可以理解成一个“键值对文件”：
 * 保存进去的数据在 App 关掉、手机重启后依然存在，非常适合存 token、手机号这种很小的信息。
 * （它不适合存大量数据，那种情况要用数据库。）
 *
 * Kotlin 里用 object 就能得到工具类，不用再写 private 构造函数。
 */
object SpUtil {

    private const val SP_NAME = "loan_app_prefs"

    private const val KEY_TOKEN = "key_token"
    private const val KEY_PHONE = "key_phone"
    private const val KEY_NAME = "key_name"

    /** 拿到 SharedPreferences 对象。注意用 applicationContext，避免持有 Activity 造成内存泄漏。 */
    private fun sp(context: Context): SharedPreferences {
        return context.applicationContext.getSharedPreferences(SP_NAME, Context.MODE_PRIVATE)
    }

    /** 登录成功后调用，把 token、手机号、姓名一起存起来。 */
    fun saveLogin(context: Context, token: String?, phone: String?, name: String?) {
        sp(context).edit()
            .putString(KEY_TOKEN, token)
            .putString(KEY_PHONE, phone)
            .putString(KEY_NAME, name)
            .apply()
    }

    fun getToken(context: Context): String = sp(context).getString(KEY_TOKEN, "").orEmpty()

    fun getPhone(context: Context): String = sp(context).getString(KEY_PHONE, "").orEmpty()

    fun getName(context: Context): String = sp(context).getString(KEY_NAME, "").orEmpty()

    /** 有 token 就认为登录过。 */
    fun isLoggedIn(context: Context): Boolean = getToken(context).isNotEmpty()

    /** 退出登录：把保存的信息全部清掉。 */
    fun clear(context: Context) {
        sp(context).edit().clear().apply()
    }
}