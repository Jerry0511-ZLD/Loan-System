package com.uestc.loanapp.ui

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ProgressBar
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import com.uestc.loanapp.R
import com.uestc.loanapp.model.LoginResult
import com.uestc.loanapp.net.ApiCallback
import com.uestc.loanapp.net.ApiService
import com.uestc.loanapp.util.SpUtil

/**
 * 登录界面（App 的启动页）。
 *
 * 它做了三件事：
 * 1. 提交前先自己检查一遍：手机号必须是 11 位、密码不能为空。
 *    这种“明显不合法”的输入没必要浪费一次网络请求。
 * 2. 调用 ApiService.login() 去请求登录。
 * 3. 登录成功后把服务器返回的 token 存进 SharedPreferences，然后跳到主界面并关掉自己。
 *
 * 要特别注意：登录结果不是马上返回的（网络是异步的），
 * 所以点击登录后先显示“登录中…”并禁用按钮，等在 onSuccess / onFailure 回调里再恢复。
 * 这个套路在后面的每个页面里都会重复出现。
 *
 * Kotlin 小提示：这里用 lateinit var 声明控件，表示“我保证在用到它之前一定会赋值”，
 * 这样就不用像 Java 那样写一堆 = null 了。findViewById 会自己做类型推断，不用强转。
 */
class LoginActivity : AppCompatActivity() {

    private lateinit var phoneLayout: TextInputLayout
    private lateinit var passwordLayout: TextInputLayout
    private lateinit var phoneInput: TextInputEditText
    private lateinit var passwordInput: TextInputEditText
    private lateinit var loginButton: Button
    private lateinit var progressBar: ProgressBar

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)

        phoneLayout = findViewById(R.id.layout_phone)
        passwordLayout = findViewById(R.id.layout_password)
        phoneInput = findViewById(R.id.et_phone)
        passwordInput = findViewById(R.id.et_password)
        loginButton = findViewById(R.id.btn_login)
        progressBar = findViewById(R.id.progress_bar)

        loginButton.setOnClickListener { doLogin() }
    }

    private fun doLogin() {
        // 先把上一次的错误提示清掉，否则用户改好了还会看到红字
        phoneLayout.error = null
        passwordLayout.error = null

        val phone = textOf(phoneInput)
        val password = textOf(passwordInput)

        if (phone.length != PHONE_LENGTH) {
            phoneLayout.error = getString(R.string.error_phone_length)
            return
        }
        if (password.isEmpty()) {
            passwordLayout.error = getString(R.string.error_password_empty)
            return
        }

        setLoading(true)
        ApiService.getInstance(this).login(phone, password, object : ApiCallback<LoginResult> {

            override fun onSuccess(data: LoginResult?) {
                setLoading(false)
                // 后端把 token 和 user 分两层放，所以这两个都要判空
                if (data == null || data.token == null) {
                    Toast.makeText(
                        this@LoginActivity,
                        getString(R.string.login_failed, getString(R.string.error_empty_data)),
                        Toast.LENGTH_SHORT
                    ).show()
                    return
                }
                // 保存登录信息：token 从 data 取，手机号/姓名在后端返回的 user 里
                SpUtil.saveLogin(this@LoginActivity, data.token, data.user?.phone, data.user?.name)
                Toast.makeText(this@LoginActivity, R.string.login_success, Toast.LENGTH_SHORT).show()

                startActivity(Intent(this@LoginActivity, MainActivity::class.java))
                // finish() 把自己关掉：登录页只是入口，不留在返回栈里，
                // 否则用户在主界面按返回键又回到了登录页，体验很奇怪
                finish()
            }

            override fun onFailure(message: String?) {
                setLoading(false)
                Toast.makeText(
                    this@LoginActivity,
                    getString(R.string.login_failed, message),
                    Toast.LENGTH_SHORT
                ).show()
            }
        })
    }

    /** 统一处理“加载中”时的界面状态：按钮禁用 + 文案变化 + 转圈 */
    private fun setLoading(loading: Boolean) {
        loginButton.isEnabled = !loading
        loginButton.setText(if (loading) R.string.login_loading else R.string.action_login)
        progressBar.visibility = if (loading) View.VISIBLE else View.GONE
    }

    private fun textOf(input: TextInputEditText): String = input.text?.toString()?.trim().orEmpty()

    companion object {
        private const val PHONE_LENGTH = 11
    }
}