package com.uestc.loanapp.ui.profile

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import com.uestc.loanapp.R
import com.uestc.loanapp.ui.LoginActivity
import com.uestc.loanapp.util.SpUtil

/**
 * “我的”页：显示当前登录用户的信息，并提供退出登录。
 *
 * 姓名和手机号不是从网上取的，而是登录时存在 SharedPreferences 里的，
 * 这里直接读出来显示即可（这也是 SharedPreferences 的典型用法）。
 *
 * “我的额度”和“还款计划”都还只是入口：额度要等风控服务给出评估结果，
 * 还款计划属于第二阶段的开发内容，所以点击后只给一个提示，
 * 这样既让页面看起来完整，也不会给用户“这里坏了”的错觉。
 */
class ProfileFragment : Fragment() {

    private lateinit var nameText: TextView
    private lateinit var phoneText: TextView

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_profile, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        nameText = view.findViewById(R.id.tv_name)
        phoneText = view.findViewById(R.id.tv_phone)

        val name = SpUtil.getName(requireContext())
        nameText.text = if (name.isEmpty()) getString(R.string.profile_default_name) else name
        phoneText.text = SpUtil.getPhone(requireContext())

        view.findViewById<View>(R.id.row_credit).setOnClickListener {
            toast(R.string.profile_credit_toast)
        }
        view.findViewById<View>(R.id.row_repay).setOnClickListener {
            toast(R.string.profile_repay_toast)
        }
        view.findViewById<View>(R.id.row_help).setOnClickListener {
            toast(R.string.profile_help_toast)
        }

        val logoutButton: Button = view.findViewById(R.id.btn_logout)
        logoutButton.setOnClickListener { confirmLogout() }
    }

    /** 退出前先问一句，避免误触；确认后清空登录信息并回到登录页 */
    private fun confirmLogout() {
        AlertDialog.Builder(requireContext())
            .setTitle(R.string.logout_confirm_title)
            .setMessage(R.string.logout_confirm_message)
            .setNegativeButton(R.string.action_cancel, null)
            .setPositiveButton(R.string.action_ok) { _, _ -> logout() }
            .show()
    }

    private fun logout() {
        SpUtil.clear(requireContext())

        // 这里用 NEW_TASK + CLEAR_TASK 两个标志，
        // 意思是“把之前打开的界面全部清掉，只留一个全新的登录页”，
        // 否则用户在主界面按返回键还能回到已经退出登录的页面
        val intent = Intent(requireContext(), LoginActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        requireActivity().finish()
    }

    private fun toast(stringResId: Int) {
        Toast.makeText(requireContext(), stringResId, Toast.LENGTH_SHORT).show()
    }
}