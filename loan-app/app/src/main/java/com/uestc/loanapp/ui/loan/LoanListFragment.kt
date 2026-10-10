package com.uestc.loanapp.ui.loan

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.uestc.loanapp.R
import com.uestc.loanapp.model.LoanApplication
import com.uestc.loanapp.net.ApiCallback
import com.uestc.loanapp.net.ApiService
import com.uestc.loanapp.util.StatusUtil
import java.util.Locale

/**
 * “我的贷款”页：显示当前用户提交过的所有申请。
 *
 * 用 SwipeRefreshLayout 包住 RecyclerView，用户下拉就能刷新；
 * 列表为空时显示空状态提示，首次加载时显示转圈 —— 这三种状态都要考虑到，
 * 因为用户看到的“什么都没有”很可能只是还没加载完。
 *
 * 刷新写在 onResume 里：这样从申请页返回时列表会自动更新，
 * 刚提交的那笔申请马上就能看到，不需要用户手动下拉。
 */
class LoanListFragment : Fragment() {

    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var recyclerView: RecyclerView
    private lateinit var progressBar: ProgressBar
    private lateinit var emptyView: View
    private lateinit var countText: TextView
    private lateinit var adapter: LoanAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_loan_list, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        swipeRefresh = view.findViewById(R.id.swipe_refresh)
        recyclerView = view.findViewById(R.id.rv_loans)
        progressBar = view.findViewById(R.id.progress_bar)
        emptyView = view.findViewById(R.id.empty_view)
        countText = view.findViewById(R.id.tv_count)

        adapter = LoanAdapter()
        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        recyclerView.adapter = adapter

        swipeRefresh.setOnRefreshListener { loadLoans() }
    }

    override fun onResume() {
        super.onResume()
        loadLoans()
    }

    private fun loadLoans() {
        // 下拉刷新时 SwipeRefreshLayout 自己会转圈，不用再显示中间的 ProgressBar
        if (!swipeRefresh.isRefreshing) {
            progressBar.visibility = View.VISIBLE
        }

        ApiService.getInstance(requireContext()).getMyLoans(object : ApiCallback<List<LoanApplication>> {

            override fun onSuccess(data: List<LoanApplication>?) {
                if (!isAdded) {
                    return
                }
                hideLoading()

                val list = data.orEmpty()
                emptyView.visibility = if (list.isEmpty()) View.VISIBLE else View.GONE
                countText.text = getString(R.string.loan_list_count, list.size)
                adapter.setData(list)
            }

            override fun onFailure(message: String?) {
                if (!isAdded) {
                    return
                }
                hideLoading()
                Toast.makeText(
                    requireContext(),
                    getString(R.string.loan_list_load_failed, message),
                    Toast.LENGTH_SHORT
                ).show()
            }
        })
    }

    private fun hideLoading() {
        progressBar.visibility = View.GONE
        swipeRefresh.isRefreshing = false
    }

    /** 列表适配器：每一行显示产品名、金额、期限、申请时间和状态胶囊 */
    private inner class LoanAdapter : RecyclerView.Adapter<LoanAdapter.LoanHolder>() {

        private val data = ArrayList<LoanApplication>()

        fun setData(loans: List<LoanApplication>?) {
            data.clear()
            if (loans != null) {
                data.addAll(loans)
            }
            notifyDataSetChanged()
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): LoanHolder {
            val itemView = LayoutInflater.from(parent.context)
                .inflate(R.layout.item_loan, parent, false)
            return LoanHolder(itemView)
        }

        override fun onBindViewHolder(holder: LoanHolder, position: Int) {
            val loan = data[position]

            holder.productText.text = loan.product
            holder.amountText.text = getString(
                R.string.loan_list_amount_format,
                String.format(Locale.CHINA, "%,.0f", loan.amount)
            )
            holder.termText.text = getString(R.string.loan_list_term_format, loan.term)
            holder.timeText.text = getString(R.string.loan_list_time_format, loan.applyTime)

            // 状态胶囊：把英文状态翻译成中文 + 对应颜色，逻辑都在 StatusUtil 里
            StatusUtil.applyStatusPill(holder.statusText, loan.status)

            // 点击整行进入详情页，只把申请编号带过去，详情页再根据编号去查完整数据
            holder.itemView.setOnClickListener {
                val intent = Intent(requireContext(), LoanDetailActivity::class.java)
                intent.putExtra(LoanDetailActivity.EXTRA_LOAN_ID, loan.id)
                startActivity(intent)
            }
        }

        override fun getItemCount(): Int = data.size

        inner class LoanHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {

            val productText: TextView = itemView.findViewById(R.id.tv_loan_product)
            val statusText: TextView = itemView.findViewById(R.id.tv_loan_status)
            val amountText: TextView = itemView.findViewById(R.id.tv_loan_amount)
            val termText: TextView = itemView.findViewById(R.id.tv_loan_term)
            val timeText: TextView = itemView.findViewById(R.id.tv_loan_time)
        }
    }
}