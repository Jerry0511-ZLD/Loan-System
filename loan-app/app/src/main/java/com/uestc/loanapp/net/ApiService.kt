package com.uestc.loanapp.net

import android.content.Context
import android.os.Handler
import android.os.Looper
import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.reflect.TypeToken
import com.uestc.loanapp.AppConfig
import com.uestc.loanapp.model.ApiResponse
import com.uestc.loanapp.model.LoanApplication
import com.uestc.loanapp.model.LoginResult
import com.uestc.loanapp.model.PageData
import com.uestc.loanapp.model.Product
import com.uestc.loanapp.util.SpUtil
import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import java.io.IOException
import java.lang.reflect.Type
import java.util.concurrent.TimeUnit

/**
 * 所有网络请求的统一入口（单例，全 App 只有一个对象）。
 *
 * 单例的意思是：OkHttpClient 里维护着连接池和线程池，反复创建很浪费，
 * 所以用 [getInstance] 拿同一个对象来用。
 * Kotlin 里构造函数写成 private 就禁止外部 new，实例放在 companion object 里。
 *
 * 它帮你做了三件麻烦事：
 * 1. 根据 [AppConfig.USE_MOCK] 决定走本地假数据（MockApi）还是真实后端；
 * 2. 真实请求时自动把登录拿到的 token 塞进 Authorization 请求头；
 * 3. 用 Handler 把回调切回主线程，界面代码不用自己操心线程问题。
 *
 * 为什么必须用 Context？因为要读 SharedPreferences 里的 token，
 * 而 SharedPreferences 必须通过 Context 获取。这里只保存 applicationContext，
 * 它和整个 App 同生命周期，不会因为 Activity 被销毁而泄漏内存。
 */
class ApiService private constructor(context: Context) {

    private val appContext: Context = context.applicationContext
    private val gson = Gson()

    // 拿到主线程的 Handler，用来把结果从“网络线程”搬回“界面线程”
    private val mainHandler = Handler(Looper.getMainLooper())

    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .writeTimeout(10, TimeUnit.SECONDS)
        .build()

    // ==================== 对外的五个业务方法 ====================

    /**
     * 登录。
     *
     * 后端返回的 data 是 { token, tokenType, expiresIn, user }，
     * token 和用户信息是平级的，所以这里用 [LoginResult] 来接，不是 [com.uestc.loanapp.model.User]。
     *
     * 登录信息（token、手机号、姓名）的保存交给页面做：因为 Mock 分支是直接回调的，
     * 只有放在页面里统一处理，Mock 和真实后端两种模式才能走同一条保存逻辑。
     */
    fun login(phone: String, password: String, callback: ApiCallback<LoginResult>) {
        if (AppConfig.USE_MOCK) {
            MockApi.login(phone, password, callback)
            return
        }

        val json = JsonObject()
        json.addProperty("phone", phone)
        json.addProperty("password", password)
        val request = newRequest("/login")
            .post(json.toString().toRequestBody(JSON_TYPE))
            .build()

        // TypeToken 的作用：告诉 Gson "这里的 data 是 LoginResult 类型"，不然它解析出来会是 Map
        val responseType = object : TypeToken<ApiResponse<LoginResult>>() {}.type
        execute(request, responseType, callback)
    }

    /** 获取可申请的贷款产品列表（首页用）。 */
    fun getProducts(callback: ApiCallback<List<Product>>) {
        if (AppConfig.USE_MOCK) {
            MockApi.getProducts(callback)
            return
        }
        val request = newRequest("/products").get().build()
        val responseType = object : TypeToken<ApiResponse<List<Product>>>() {}.type
        execute(request, responseType, callback)
    }

    /**
     * 获取“我的贷款”列表（申请记录）。
     *
     * 注意：后端返回的 data 是一个**分页对象** { list, total, page, ... }，
     * 不是纯数组，所以要先用 [PageData] 接住，再把里面的 list 交给页面。
     */
    fun getMyLoans(callback: ApiCallback<List<LoanApplication>>) {
        if (AppConfig.USE_MOCK) {
            MockApi.getMyLoans(callback)
            return
        }
        val request = newRequest("/loans").get().build()
        val responseType = object : TypeToken<ApiResponse<PageData<LoanApplication>>>() {}.type
        execute(request, responseType, object : ApiCallback<PageData<LoanApplication>> {
            override fun onSuccess(data: PageData<LoanApplication>?) {
                callback.onSuccess(data?.list ?: emptyList())
            }

            override fun onFailure(message: String?) {
                callback.onFailure(message)
            }
        })
    }

    /** 按申请编号查询某一笔申请的详情。 */
    fun getLoanDetail(id: String, callback: ApiCallback<LoanApplication>) {
        if (AppConfig.USE_MOCK) {
            MockApi.getLoanDetail(id, callback)
            return
        }
        val request = newRequest("/loans/$id").get().build()
        val responseType = object : TypeToken<ApiResponse<LoanApplication>>() {}.type
        execute(request, responseType, callback)
    }

    /** 提交一笔新的贷款申请。整个申请单会被转成 JSON 放在请求体里发给后端。 */
    fun submitApplication(application: LoanApplication, callback: ApiCallback<LoanApplication>) {
        if (AppConfig.USE_MOCK) {
            MockApi.submitApplication(application, callback)
            return
        }
        val body = gson.toJson(application).toRequestBody(JSON_TYPE)
        val request = newRequest("/loans").post(body).build()
        val responseType = object : TypeToken<ApiResponse<LoanApplication>>() {}.type
        execute(request, responseType, callback)
    }

    // ==================== 内部实现 ====================

    /** 造一个带公共配置的请求构造器：拼上 BASE_URL，并且如果需要就带上 token。 */
    private fun newRequest(path: String): Request.Builder {
        val builder = Request.Builder().url(AppConfig.BASE_URL + path)
        val token = SpUtil.getToken(appContext)
        if (token.isNotEmpty()) {
            // 后端约定：token 放在 Authorization 头里，前面加固定的 "Bearer " 前缀
            builder.header("Authorization", "Bearer $token")
        }
        return builder
    }

    /**
     * 真正发请求的地方。
     *
     * 注意 enqueue：它表示“把请求交给 OkHttp 的后台线程去做，做完再通知我”，
     * 方法会立刻返回，不会卡住界面。绝不能在主线程用 execute() 同步请求，
     * 那样界面会卡住甚至弹出 ANR（应用无响应）对话框。
     *
     * Kotlin 没有受检异常（checked exception），IOException 不用写在方法签名上，
     * 但该 try/catch 的地方还是要写。
     */
    private fun <T> execute(request: Request, responseType: Type, callback: ApiCallback<T>) {
        client.newCall(request).enqueue(object : Callback {

            override fun onFailure(call: Call, e: IOException) {
                // 这里已经在 OkHttp 的后台线程了，所以用 Handler 切回主线程
                notifyFailure(callback, "网络连接失败，请检查网络后重试")
            }

            override fun onResponse(call: Call, response: Response) {
                try {
                    val json = response.body?.string() ?: ""
                    // 后端连出错时也是同一套 {code, message, data:null} 外壳，
                    // 所以先把它解析出来，好把后端的提示（比如"金额超出产品范围"）原样带给用户
                    val result = gson.fromJson<ApiResponse<T>>(json, responseType)
                    if (!response.isSuccessful) {
                        val message = result?.message
                        notifyFailure(
                            callback,
                            if (message.isNullOrEmpty()) "服务器返回错误（${response.code}）" else message
                        )
                        return
                    }
                    if (result == null) {
                        notifyFailure(callback, "服务器返回的数据格式不正确")
                        return
                    }
                    if (result.isSuccess) {
                        notifySuccess(callback, result.data)
                    } else {
                        val message = result.message
                        notifyFailure(callback, if (message.isNullOrEmpty()) "请求失败" else message)
                    }
                } catch (e: Exception) {
                    // 例如返回的不是 JSON、字段类型对不上，都会走到这里
                    notifyFailure(callback, "数据解析失败")
                }
            }
        })
    }

    private fun <T> notifySuccess(callback: ApiCallback<T>, data: T?) {
        mainHandler.post { callback.onSuccess(data) }
    }

    private fun <T> notifyFailure(callback: ApiCallback<T>, message: String?) {
        mainHandler.post { callback.onFailure(message) }
    }

    companion object {

        private val JSON_TYPE: MediaType = "application/json; charset=utf-8".toMediaType()

        @Volatile
        private var instance: ApiService? = null

        /** 获取单例。第一次调用时传入 Context，之后传什么都无所谓。 */
        @JvmStatic
        fun getInstance(context: Context): ApiService {
            return instance ?: synchronized(this) {
                instance ?: ApiService(context).also { instance = it }
            }
        }
    }
}