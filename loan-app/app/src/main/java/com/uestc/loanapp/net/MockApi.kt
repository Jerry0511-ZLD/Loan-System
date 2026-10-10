package com.uestc.loanapp.net

import android.os.Handler
import android.os.Looper
import com.uestc.loanapp.model.LoanApplication
import com.uestc.loanapp.model.LoginResult
import com.uestc.loanapp.model.Product
import com.uestc.loanapp.model.User
import com.uestc.loanapp.util.StatusUtil
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * 本地假数据（Mock）。
 *
 * 用 object 声明，整个 App 只有这一个 MockApi 实例，
 * 所以它里面那几个 List 天然就是“全局的内存数据库”。
 *
 * 当 [com.uestc.loanapp.AppConfig.USE_MOCK] 为 true 时，
 * ApiService 会把所有请求转到这里，于是没有后端也能把整个流程点一遍，
 * 用来演示、写文档、给老师看效果都很方便。
 *
 * 每个回调都故意延迟 400 毫秒再返回，是为了让“加载中”的转圈动画能被看见。
 * 如果立刻返回，你根本来不及看到加载状态，也就发现不了界面上的问题。
 * 延迟用的是主线程的 Handler，所以回调自然就在主线程上，和真实网络的行为一致。
 */
object MockApi {

    /** 演示账号：手机号（和后端 seed.py 里的 demo 账号保持一致） */
    const val DEMO_PHONE: String = "13800000001"

    /** 演示账号：密码 */
    const val DEMO_PASSWORD: String = "123456"

    /** 模拟网络耗时（毫秒） */
    private const val DELAY_MS = 400L

    private val MAIN_HANDLER = Handler(Looper.getMainLooper())

    /** 内存里的“数据库”，App 运行期间一直存在，退出重进就恢复初始数据 */
    private val PRODUCTS = ArrayList<Product>()
    private val LOANS = ArrayList<LoanApplication>()

    private var nextLoanId = 100

    init {
        initProducts()
        initLoans()
    }

    // ==================== 对外的接口，和 ApiService 一一对应 ====================

    fun login(phone: String, password: String, callback: ApiCallback<LoginResult>) {
        postDelayed {
            if (DEMO_PHONE == phone && DEMO_PASSWORD == password) {
                // 结构和真实后端一致：token 在 data 这层，用户信息在同级的 user 里
                callback.onSuccess(
                    LoginResult(
                        token = "mock-token-13800000001",
                        tokenType = "Bearer",
                        expiresIn = 7 * 24 * 3600L,
                        user = User(
                            id = "U1001",
                            username = "demo",
                            name = "陈晓",
                            role = "user",
                            phone = DEMO_PHONE
                        )
                    )
                )
            } else {
                callback.onFailure("手机号或密码错误，请使用演示账号登录")
            }
        }
    }

    fun getProducts(callback: ApiCallback<List<Product>>) {
        postDelayed {
            // 复制一份再返回，防止外面不小心改动了我们的“数据库”
            callback.onSuccess(ArrayList(PRODUCTS))
        }
    }

    fun getMyLoans(callback: ApiCallback<List<LoanApplication>>) {
        postDelayed {
            callback.onSuccess(ArrayList(LOANS))
        }
    }

    fun getLoanDetail(id: String, callback: ApiCallback<LoanApplication>) {
        postDelayed {
            val found = LOANS.firstOrNull { it.id == id }
            if (found != null) {
                callback.onSuccess(found)
            } else {
                callback.onFailure("没有找到该笔申请")
            }
        }
    }

    /**
     * 提交申请：补上编号、状态和申请时间，然后插到列表最前面，
     * 这样回到“我的贷款”就能第一眼看到刚提交的那笔。
     */
    fun submitApplication(application: LoanApplication, callback: ApiCallback<LoanApplication>) {
        postDelayed {
            nextLoanId += 1
            application.id = "L2025" + String.format(Locale.CHINA, "%04d", nextLoanId)
            // 新提交的申请一定是“待审批”，风控结果要等风控服务给出（第二阶段）
            application.status = StatusUtil.PENDING
            application.applyTime = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.CHINA).format(Date())
            application.riskLevel = null
            application.riskScore = null
            LOANS.add(0, application)
            callback.onSuccess(application)
        }
    }

    // ==================== 初始化假数据 ====================

    private fun initProducts() {
        PRODUCTS.add(
            newProduct(
                "P01", "消费贷·随借随还", 1000.0, 50000.0, 0.036, "3.6% 起", 3, 12,
                "按日计息，随借随还，最快 5 分钟到账"
            )
        )
        PRODUCTS.add(
            newProduct(
                "P02", "装修贷", 10000.0, 200000.0, 0.042, "4.2% 起", 12, 24,
                "专款专用，装修场景大额分期，支持先息后本"
            )
        )
        PRODUCTS.add(
            newProduct(
                "P03", "教育贷", 5000.0, 80000.0, 0.039, "3.9% 起", 6, 24,
                "学费分期，凭录取通知书可申请，还款压力小"
            )
        )
        PRODUCTS.add(
            newProduct(
                "P04", "经营贷", 20000.0, 300000.0, 0.048, "4.8% 起", 12, 24,
                "面向小微企业主，需提供营业执照与经营流水"
            )
        )
    }

    private fun initLoans() {
        LOANS.add(
            newLoan(
                "L2025090001", "消费贷·随借随还", 20000.0, 12, "日常消费周转",
                "APPROVED", "2025-09-01 10:23", "低风险", 92.5
            )
        )
        LOANS.add(
            newLoan(
                "L2025090002", "装修贷", 80000.0, 24, "房屋装修",
                "PENDING", "2025-09-15 14:05", null, null
            )
        )
        LOANS.add(
            newLoan(
                "L2025090003", "教育贷", 30000.0, 12, "在职研究生学费",
                "REJECTED", "2025-08-20 09:12", "高风险", 41.0
            )
        )
        LOANS.add(
            newLoan(
                "L2025090004", "经营贷", 150000.0, 24, "店铺进货周转",
                "APPROVED", "2025-07-11 16:40", "中风险", 78.0
            )
        )
        LOANS.add(
            newLoan(
                "L2025090005", "消费贷·随借随还", 5000.0, 3, "更换手机数码产品",
                "PENDING", "2025-09-19 20:31", null, null
            )
        )
    }

    private fun newProduct(
        id: String, name: String, minAmount: Double, maxAmount: Double,
        rate: Double, rateText: String, minTerm: Int, maxTerm: Int, description: String
    ): Product {
        return Product(
            id = id,
            name = name,
            minAmount = minAmount,
            maxAmount = maxAmount,
            rate = rate,
            rateText = rateText,
            minTerm = minTerm,
            maxTerm = maxTerm,
            description = description
        )
    }

    private fun newLoan(
        id: String, product: String, amount: Double, term: Int, purpose: String,
        status: String, applyTime: String, riskLevel: String?, riskScore: Double?
    ): LoanApplication {
        return LoanApplication(
            id = id,
            product = product,
            amount = amount,
            term = term,
            purpose = purpose,
            status = status,
            applyTime = applyTime,
            riskLevel = riskLevel,
            riskScore = riskScore
        )
    }

    /** 延迟一小会儿再执行，模拟真实网络的等待时间 */
    private fun postDelayed(task: () -> Unit) {
        MAIN_HANDLER.postDelayed(Runnable { task() }, DELAY_MS)
    }
}