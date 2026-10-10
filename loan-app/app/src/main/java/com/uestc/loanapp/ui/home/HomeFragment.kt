package com.uestc.loanapp.ui.home

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
import com.google.android.material.button.MaterialButton
import com.uestc.loanapp.R
import com.uestc.loanapp.model.Product
import com.uestc.loanapp.net.ApiCallback
import com.uestc.loanapp.net.ApiService
import com.uestc.loanapp.ui.loan.LoanApplyActivity
import com.uestc.loanapp.util.SpUtil
import java.util.Locale

/**
 * 首页：显示问候语 + 可以申请的贷款产品列表。
 *
 * 数据从 ApiService.getProducts() 拿。拿到之前先显示转圈，
 * 拿到之后交给 Adapter 显示 —— 这一步很关键：Fragment 本身不直接往列表里塞数据，
 * 而是把整个 List 交给 Adapter，Adapter 负责把每条数据变成一行界面。
 */
class HomeFragment : Fragment() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var progressBar: ProgressBar
    private lateinit var adapter: ProductAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        // 第三个参数 false：先不把布局挂到 container 上，由 Fragment 自己管理
        return inflater.inflate(R.layout.fragment_home, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        recyclerView = view.findViewById(R.id.rv_products)
        progressBar = view.findViewById(R.id.progress_bar)

        // 问候语：名字是登录时存进 SharedPreferences 的
        val greeting: TextView = view.findViewById(R.id.tv_greeting)
        val name = SpUtil.getName(requireContext())
        greeting.text = getString(
            R.string.home_greeting,
            if (name.isEmpty()) getString(R.string.home_greeting_guest) else name
        )

        adapter = ProductAdapter()
        // LinearLayoutManager 表示垂直方向、一行一个的列表
        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        recyclerView.adapter = adapter

        loadProducts()
    }

    private fun loadProducts() {
        progressBar.visibility = View.VISIBLE
        ApiService.getInstance(requireContext()).getProducts(object : ApiCallback<List<Product>> {

            override fun onSuccess(data: List<Product>?) {
                // 回调回来时页面可能已经被销毁了（比如用户已经退出），所以要判断一下
                if (!isAdded) {
                    return
                }
                progressBar.visibility = View.GONE
                adapter.setData(data)
                if (data.isNullOrEmpty()) {
                    Toast.makeText(requireContext(), R.string.home_empty, Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(message: String?) {
                if (!isAdded) {
                    return
                }
                progressBar.visibility = View.GONE
                Toast.makeText(
                    requireContext(),
                    getString(R.string.home_load_failed, message),
                    Toast.LENGTH_SHORT
                ).show()
            }
        })
    }

    /** 把金额做成 12,000 这样的千分位写法，看起来更像金融类应用 */
    private fun formatAmount(amount: Double): String = String.format(Locale.CHINA, "%,.0f", amount)

    /**
     * 产品列表的适配器。
     *
     * 为什么需要 Adapter？RecyclerView 只负责滚动和“回收看不见的行”（复用机制），
     * 它并不知道 List 里的数据要怎么变成界面。Adapter 就是两者之间的翻译官：
     * onCreateViewHolder 负责“造行”（把 item_product.xml 变成 View），
     * onBindViewHolder 负责“填数据”。
     *
     * 这里的 inner class 表示它是 HomeFragment 的内部类，可以直接调用外面的
     * getString、requireContext 等方法。
     */
    private inner class ProductAdapter : RecyclerView.Adapter<ProductAdapter.ProductHolder>() {

        private val data = ArrayList<Product>()

        fun setData(products: List<Product>?) {
            data.clear()
            if (products != null) {
                data.addAll(products)
            }
            // 数据整体换了一遍，直接通知刷新。数据量很小，不需要用 DiffUtil 做精细比较
            notifyDataSetChanged()
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ProductHolder {
            val itemView = LayoutInflater.from(parent.context)
                .inflate(R.layout.item_product, parent, false)
            return ProductHolder(itemView)
        }

        override fun onBindViewHolder(holder: ProductHolder, position: Int) {
            val product = data[position]

            holder.nameText.text = product.name
            holder.amountText.text = getString(
                R.string.product_amount_value,
                formatAmount(product.minAmount), formatAmount(product.maxAmount)
            )
            holder.rateText.text = product.rateText
            holder.termText.text = getString(R.string.term_range_format, product.minTerm, product.maxTerm)
            holder.descriptionText.text = product.description

            // 点“立即申请”跳到申请页。
            // Intent 可以理解成一张“便签”：告诉系统我要去哪个界面；
            // putExtra 是往便签上写数据，目标页面用同一个 key 就能读出来。
            holder.applyButton.setOnClickListener {
                val intent = Intent(requireContext(), LoanApplyActivity::class.java)
                // 产品编号：提交申请时后端要的是 id，不是产品名
                intent.putExtra(LoanApplyActivity.EXTRA_PRODUCT_ID, product.id)
                // 产品名：只是拿来在申请页上显示
                intent.putExtra(LoanApplyActivity.EXTRA_PRODUCT_NAME, product.name)
                startActivity(intent)
            }
        }

        override fun getItemCount(): Int = data.size

        /** ViewHolder 的作用：把 findViewById 的结果缓存起来，滚动时不用反复查找控件 */
        inner class ProductHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {

            val nameText: TextView = itemView.findViewById(R.id.tv_product_name)
            val descriptionText: TextView = itemView.findViewById(R.id.tv_product_description)
            val amountText: TextView = itemView.findViewById(R.id.tv_product_amount)
            val rateText: TextView = itemView.findViewById(R.id.tv_product_rate)
            val termText: TextView = itemView.findViewById(R.id.tv_product_term)
            val applyButton: MaterialButton = itemView.findViewById(R.id.btn_apply)
        }
    }
}