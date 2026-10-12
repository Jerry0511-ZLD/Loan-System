package com.uestc.loanapp.ui.loan

import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.CheckBox
import android.widget.ProgressBar
import android.widget.RadioGroup
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import com.uestc.loanapp.R
import com.uestc.loanapp.model.LoanApplication
import com.uestc.loanapp.net.ApiCallback
import com.uestc.loanapp.net.ApiService

/**
 * 申请借款表单页。
 *
 * 页面上的数据分两类：
 * - 产品名：从首页传过来的（Intent extra），只显示不给改；
 * - 金额、期限、用途、还款方式、协议勾选：由用户填，提交前必须逐项校验。
 *
 * 校验写在客户端只是为了少发无用请求、让提示更及时，
 * 真正的合法性判断还是以后端为准。
 *
 * 提交成功后弹一个对话框告诉用户“等待审批”，然后 finish() 回到上一页。
 * 此刻按钮处于禁用状态，是为了防止用户连点两次提交出两笔申请。
 */
class LoanApplyActivity : AppCompatActivity() {

    private lateinit var productName: String
    private lateinit var productId: String

    private lateinit var amountLayout: TextInputLayout
    private lateinit var purposeLayout: TextInputLayout
    private lateinit var amountInput: TextInputEditText
    private lateinit var purposeInput: TextInputEditText
    private lateinit var termGroup: RadioGroup
    private lateinit var repayGroup: RadioGroup
    private lateinit var agreeCheckBox: CheckBox
    private lateinit var submitButton: Button
    private lateinit var progressBar: ProgressBar

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_loan_apply)

        // 取出上一页传来的产品名。取不到就给个默认值，避免界面出现空白
        val extraName = intent.getStringExtra(EXTRA_PRODUCT_NAME)
        productName = if (extraName.isNullOrEmpty()) getString(R.string.app_name) else extraName

        // 产品编号：提交申请时要用（后端要的是产品 id，不是产品名）
        productId = intent.getStringExtra(EXTRA_PRODUCT_ID).orEmpty()

        val toolbar: MaterialToolbar = findViewById(R.id.toolbar)
        toolbar.setNavigationOnClickListener { finish() }

        val productValue: TextView = findViewById(R.id.tv_product_value)
        productValue.text = productName

        amountLayout = findViewById(R.id.layout_amount)
        purposeLayout = findViewById(R.id.layout_purpose)
        amountInput = findViewById(R.id.et_amount)
        purposeInput = findViewById(R.id.et_purpose)
        termGroup = findViewById(R.id.rg_term)
        repayGroup = findViewById(R.id.rg_repay)
        agreeCheckBox = findViewById(R.id.cb_agree)
        submitButton = findViewById(R.id.btn_submit)
        progressBar = findViewById(R.id.progress_bar)

        submitButton.setOnClickListener { submit() }
    }

    private fun submit() {
        amountLayout.error = null
        purposeLayout.error = null

        // 1. 金额：必填、必须是数字、必须大于 0
        //    toDoubleOrNull 转不动就会返回 null，正好把“格式不对”和“输入为空”一起处理掉
        val amountText = textOf(amountInput)
        if (amountText.isEmpty()) {
            amountLayout.error = getString(R.string.error_amount_empty)
            return
        }
        val amount = amountText.toDoubleOrNull()
        if (amount == null || amount <= 0) {
            amountLayout.error = getString(R.string.error_amount_invalid)
            return
        }

        // 2. 资金用途：必填
        val purpose = textOf(purposeInput)
        if (purpose.isEmpty()) {
            purposeLayout.error = getString(R.string.error_purpose_empty)
            return
        }

        // 3. 必须勾选借款协议
        if (!agreeCheckBox.isChecked) {
            Toast.makeText(this, R.string.error_agreement, Toast.LENGTH_SHORT).show()
            return
        }

        // 4. 把表单组装成一个 LoanApplication 对象发给后端
        //    ⚠️ 后端要的是产品编号 productId，不是产品名；产品名只用来在界面上显示
        val application = LoanApplication(
            productId = productId,
            product = productName,
            amount = amount,
            term = selectedTerm(),
            purpose = purpose
        )
        // 说明：还款方式（等额本息/先息后本）此处作为表单信息，
        // 将在生成还款计划时随申请单一起使用。
        // status（状态）由后端决定，客户端不设置，提交成功后后端会返回 PENDING。

        setLoading(true)
        ApiService.getInstance(this).submitApplication(application, object : ApiCallback<LoanApplication> {

            override fun onSuccess(data: LoanApplication?) {
                setLoading(false)
                showSuccessDialog()
            }

            override fun onFailure(message: String?) {
                setLoading(false)
                Toast.makeText(
                    this@LoanApplyActivity,
                    getString(R.string.apply_failed, message),
                    Toast.LENGTH_SHORT
                ).show()
            }
        })
    }

    /** 读取 RadioGroup 选中项对应的期限。默认选中 12 期。 */
    private fun selectedTerm(): Int = when (termGroup.checkedRadioButtonId) {
        R.id.rb_term_3 -> 3
        R.id.rb_term_6 -> 6
        R.id.rb_term_24 -> 24
        else -> 12
    }

    private fun showSuccessDialog() {
        AlertDialog.Builder(this)
            .setTitle(R.string.apply_success_title)
            .setMessage(R.string.apply_success_message)
            // 不允许点空白处关掉，必须点“确定”，保证用户确实看到了结果
            .setCancelable(false)
            .setPositiveButton(R.string.action_ok) { _, _ -> finish() }
            .show()
    }

    /** 提交过程中禁用按钮并显示转圈，防止重复提交 */
    private fun setLoading(loading: Boolean) {
        submitButton.isEnabled = !loading
        submitButton.setText(if (loading) R.string.apply_submitting else R.string.action_submit)
        progressBar.visibility = if (loading) View.VISIBLE else View.GONE
    }

    private fun textOf(input: TextInputEditText): String = input.text?.toString()?.trim().orEmpty()

    companion object {

        /**
         * Intent extra 的键名。定义成常量可以避免这边写 "product_name"、那边写成 "productName"。
         * Kotlin 里 const val 就相当于 Java 的 public static final。
         */
        const val EXTRA_PRODUCT_NAME: String = "extra_product_name"

        /** 产品编号，提交申请时发给后端 */
        const val EXTRA_PRODUCT_ID: String = "extra_product_id"
    }
}