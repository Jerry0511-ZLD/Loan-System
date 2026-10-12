package com.uestc.loanapp.ui

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.uestc.loanapp.R
import com.uestc.loanapp.ui.home.HomeFragment
import com.uestc.loanapp.ui.loan.LoanListFragment
import com.uestc.loanapp.ui.profile.ProfileFragment

/**
 * 主界面：登录之后的“壳”，负责在底部三个 tab 之间切换。
 *
 * 它是怎么工作的？底部导航栏每个 item 都有一个 id（nav_home / nav_loan / nav_profile）。
 * 用户点击时，我们根据这个 id 创建对应的 Fragment，
 * 再用 FragmentManager 把 Fragment 塞进布局里的 FragmentContainerView 里。
 *
 * 这里的 replace 每次都会重新创建 Fragment，好处是逻辑简单、数据总是最新的
 * （回到“我的贷款”就会重新拉一次列表）。坏处是切换时会丢失页面内的滚动位置，
 * 对本项目来说完全可以接受。
 */
class MainActivity : AppCompatActivity() {

    private lateinit var toolbar: MaterialToolbar
    private lateinit var bottomNav: BottomNavigationView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        toolbar = findViewById(R.id.toolbar)
        bottomNav = findViewById(R.id.bottom_nav)

        // Kotlin 可以把 Java 的匿名内部类直接写成 lambda
        bottomNav.setOnItemSelectedListener { item ->
            showTab(item.itemId)
            true
        }

        if (savedInstanceState == null) {
            // 第一次进来默认停在首页。selectedItemId 会触发上面的监听器，把首页显示出来
            bottomNav.selectedItemId = R.id.nav_home
        } else {
            // 屏幕旋转等导致 Activity 重建时，Fragment 会被系统自动恢复，
            // 我们只要把标题改回当前 tab 对应的文字即可
            updateTitle(bottomNav.selectedItemId)
        }
    }

    /** 根据 tab 的 id 换成对应的 Fragment，并同步标题 */
    private fun showTab(itemId: Int) {
        val fragment: Fragment = when (itemId) {
            R.id.nav_loan -> LoanListFragment()
            R.id.nav_profile -> ProfileFragment()
            else -> HomeFragment()
        }

        supportFragmentManager.beginTransaction()
            .replace(R.id.fragment_container, fragment)
            .commit()

        updateTitle(itemId)
    }

    /** 标题栏文字跟着当前 tab 走，用户一眼就知道自己在哪一页 */
    private fun updateTitle(itemId: Int) {
        when (itemId) {
            R.id.nav_loan -> toolbar.setTitle(R.string.title_my_loans)
            R.id.nav_profile -> toolbar.setTitle(R.string.title_profile)
            else -> toolbar.setTitle(R.string.title_home)
        }
    }
}