package com.uestc.loanapp.ui.loan

import android.content.res.ColorStateList
import android.os.Bundle
import android.view.View
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.google.android.material.appbar.MaterialToolbar
import com.uestc.loanapp.R
import com.uestc.loanapp.model.LoanApplication
import com.uestc.loanapp.net.ApiCallback
import com.uestc.loanapp.net.ApiService
import com.uestc.loanapp.util.StatusUtil
import java.util.Locale

/**
 * 申请详情页：把一笔申请的完整信息展示出来。
 *
 * 它是从列表页点进来的，只会收到一个“申请编号”（Intent extra），
 * 然后自己再拿这个编号去调用 getLoanDetail 查询完整数据。
 * 为什么不直接把整个对象传过来？因为对象里的信息可能已经过期了，
 * 重新查一次才能保证看到的是最新的状态。
 *
 * 页面分四块：基本信息、申请进度、还款计划（第二阶段占位）、风控评分（接口占位）。
 */
class LoanDetailActivity : AppCompatActivity() {

    private lateinit var loanId: String

    private lateinit var scrollContent: ScrollView
    private lateinit var progressBar: ProgressBar

    private lateinit var idText: TextView
    private lateinit var statusText: TextView
    private lateinit var amountText: TextView
    private lateinit var termText: TextView
    private lateinit var purposeText: TextView
    private lateinit var timeText: TextView
    private lateinit var riskResultText: TextView

    private lateinit var dotSubmit: View
    private lateinit var dotRisk: View
    private lateinit var dotManual: View
    private lateinit var dotDisburse: View
    private lateinit var titleSubmit: TextView
    private lateinit var titleRisk: TextView
    private lateinit var titleManual: TextView
    private lateinit var titleDisburse: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_loan_detail)

        // 取出上一个页面传来的申请编号
        val extraId = intent.getStringExtra(EXTRA_LOAN_ID)
        if (extraId.isNullOrEmpty()) {
            Toast.makeText(
                this,
                getString(R.string.detail_load_failed, getString(R.string.error_missing_id)),
                Toast.LENGTH_SHORT
            ).show()
            finish()
            return
        }
        loanId = extraId

        val toolbar: MaterialToolbar = findViewById(R.id.toolbar)
        toolbar.setNavigationOnClickListener { finish() }

        scrollContent = findViewById(R.id.scroll_content)
        progressBar = findViewById(R.id.progress_bar)
        idText = findViewById(R.id.tv_detail_id)
        statusText = findViewById(R.id.tv_detail_status)
        amountText = findViewById(R.id.tv_detail_amount)
        termText = findViewById(R.id.tv_detail_term)
        purposeText = findViewById(R.id.tv_detail_purpose)
        timeText = findViewById(R.id.tv_detail_time)
        riskResultText = findViewById(R.id.tv_risk_result)

        dotSubmit = findViewById(R.id.dot_step_submit)
        dotRisk = findViewById(R.id.dot_step_risk)
        dotManual = findViewById(R.id.dot_step_manual)
        dotDisburse = findViewById(R.id.dot_step_disburse)
        titleSubmit = findViewById(R.id.title_step_submit)
        titleRisk = findViewById(R.id.title_step_risk)
        titleManual = findViewById(R.id.title_step_manual)
        titleDisburse = findViewById(R.id.title_step_disburse)

        loadDetail()
    }

    private fun loadDetail() {
        progressBar.visibility = View.VISIBLE
        scrollContent.visibility = View.GONE

        ApiService.getInstance(this).getLoanDetail(loanId, object : ApiCallback<LoanApplication> {

            override fun onSuccess(data: LoanApplication?) {
                progressBar.visibility = View.GONE
                if (data == null) {
                    Toast.makeText(
                        this@LoanDetailActivity,
                        getString(R.string.detail_load_failed, getString(R.string.error_empty_data)),
                        Toast.LENGTH_SHORT
                    ).show()
                    finish()
                    return
                }
                scrollContent.visibility = View.VISIBLE
                render(data)
            }

            override fun onFailure(message: String?) {
                progressBar.visibility = View.GONE
                Toast.makeText(
                    this@LoanDetailActivity,
                    getString(R.string.detail_load_failed, message),
                    Toast.LENGTH_SHORT
                ).show()
                finish()
            }
        })
    }

    /** 把数据填到界面上 */
    private fun render(loan: LoanApplication) {
        idText.text = loan.id
        StatusUtil.applyStatusPill(statusText, loan.status)
        amountText.text = getString(R.string.amount_unit, formatAmount(loan.amount))
        termText.text = getString(R.string.term_unit, loan.term)
        purposeText.text = loan.purpose
        timeText.text = loan.applyTime

        // 风控结果：本阶段的风控模型还没实现，所以大部分数据都是 null，
        // 这里把“没有结果”也如实展示出来，而不是假装有个分数。
        // 第二阶段要做的就是把 com.uestc.loanapp.risk.RiskService 的实现类写好，
        // 在这里调用 riskService.getRiskResult(loan.id, ...) 拿到等级和分数即可，
        // 下面的展示代码不用改。
        //
        // Kotlin 小提示：先把 loan.riskScore 存到局部变量，Kotlin 才能帮你做“智能转换”
        // （确认不为 null 之后再当非空用），直接写 loan.riskScore 是不行的。
        val score = loan.riskScore
        if (score == null) {
            riskResultText.setText(R.string.detail_risk_none)
        } else {
            riskResultText.text = getString(
                R.string.detail_risk_result,
                riskLabel(loan.riskLevel),
                String.format(Locale.CHINA, "%.1f", score)
            )
        }

        renderSteps(loan.status)
    }

    /**
     * 根据状态点亮进度条上的步骤。
     *
     * 四个步骤依次是：提交申请 → 风控审核 → 人工审批 → 放款。
     * - 待审批 PENDING：前两步已完成（资料已提交、系统风控已跑过），卡在人工审批；
     * - 已通过 APPROVED：四步全部点亮；
     * - 已拒绝 REJECTED：走到人工审批为止（这一步“走完了”，只是结论是拒绝）。
     */
    private fun renderSteps(status: String?) {
        val finishedStep = when (status) {
            StatusUtil.APPROVED -> 3
            StatusUtil.REJECTED -> 2
            else -> 1
        }

        setStepState(dotSubmit, titleSubmit, finishedStep >= 0)
        setStepState(dotRisk, titleRisk, finishedStep >= 1)
        setStepState(dotManual, titleManual, finishedStep >= 2)
        setStepState(dotDisburse, titleDisburse, finishedStep >= 3)
    }

    /** 一个步骤的两种样子：完成的（蓝色）和未完成的（灰色） */
    private fun setStepState(dot: View, title: TextView, finished: Boolean) {
        val color = ContextCompat.getColor(this, if (finished) R.color.primary else R.color.step_inactive)
        // 小圆点用的是同一个 drawable，所以这里靠 tint 来上色，不会影响别的步骤
        dot.backgroundTintList = ColorStateList.valueOf(color)
        title.setTextColor(color)
    }

    private fun formatAmount(amount: Double): String = String.format(Locale.CHINA, "%,.0f", amount)

    /**
     * 风险等级的中文文案。
     *
     * 后端返回的是英文代码（LOW / MEDIUM / HIGH），界面要显示中文，
     * 所以在这里翻译一下 —— "翻译表"只写这一处，以后加档位也只改这里。
     */
    private fun riskLabel(level: String?): String = when (level?.uppercase()) {
        "LOW" -> getString(R.string.risk_level_low)
        "MEDIUM" -> getString(R.string.risk_level_medium)
        "HIGH" -> getString(R.string.risk_level_high)
        else -> getString(R.string.risk_level_unknown)
    }

    companion object {

        /** Intent extra 的键名，和列表页里 putExtra 用的一致 */
        const val EXTRA_LOAN_ID: String = "extra_loan_id"
    }
}