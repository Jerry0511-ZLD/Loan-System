package com.uestc.loanapp.util

import android.content.Context
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.widget.TextView
import androidx.core.content.ContextCompat
import com.uestc.loanapp.R

/**
 * 申请状态的小工具。
 *
 * 后端返回的状态是英文常量（PENDING / APPROVED / REJECTED），
 * 界面上要显示的是中文和对应的颜色。这个“翻译表”只写一遍放在这里，
 * 列表页和详情页都调用它，以后加状态也只改这一处。
 *
 * 用 object 声明，方法直接 StatusUtil.getLabel(...) 调用；
 * 里面用 when 代替 Java 的 if-else，写起来更像一张对照表。
 */
object StatusUtil {

    /** 待审批 */
    const val PENDING = "PENDING"

    /** 已通过 */
    const val APPROVED = "APPROVED"

    /** 已拒绝 */
    const val REJECTED = "REJECTED"

    /** 状态 -> 中文文案 */
    fun getLabel(context: Context, status: String?): String = when (status) {
        APPROVED -> context.getString(R.string.status_approved)
        REJECTED -> context.getString(R.string.status_rejected)
        PENDING -> context.getString(R.string.status_pending)
        else -> context.getString(R.string.status_unknown)
    }

    /** 状态 -> 颜色（文字色、圆点色都用它） */
    fun getColor(context: Context, status: String?): Int = when (status) {
        APPROVED -> ContextCompat.getColor(context, R.color.status_approved)
        REJECTED -> ContextCompat.getColor(context, R.color.status_rejected)
        else -> ContextCompat.getColor(context, R.color.status_pending)
    }

    /** 状态 -> 浅色背景（把上面那个颜色调淡，用作胶囊底色） */
    fun getLightColor(context: Context, status: String?): Int {
        val color = getColor(context, status)
        return Color.argb(38, Color.red(color), Color.green(color), Color.blue(color))
    }

    /**
     * 一次性把状态胶囊设置好：浅色底 + 深色字 + 中文文案。
     *
     * 这里用 mutate() 复制了一份背景 drawable，因为 drawable 默认是共享的，
     * 直接改颜色会让列表里所有胶囊都变成同一种颜色。
     */
    fun applyStatusPill(view: TextView, status: String?) {
        val background = ContextCompat.getDrawable(view.context, R.drawable.bg_status_pill)
            ?.mutate() as GradientDrawable
        background.setColor(getLightColor(view.context, status))
        view.background = background
        view.setTextColor(getColor(view.context, status))
        view.text = getLabel(view.context, status)
    }
}