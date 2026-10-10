<!-- 贷款申请列表：筛选 + 表格 + 分页。这是后台用得最多的页面。 -->
<template>
  <el-card shadow="never" class="page-card">
    <!-- 筛选条件 -->
    <div class="filter-bar">
      <el-input
        v-model="query.keyword"
        placeholder="申请人姓名 / 申请编号"
        clearable
        style="width: 240px"
        @keyup.enter="handleSearch"
      />

      <el-select v-model="query.status" placeholder="全部状态" clearable style="width: 150px">
        <el-option
          v-for="item in LOAN_STATUS_OPTIONS"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>

      <!-- value-format 让日期直接是 'YYYY-MM-DD' 字符串，省去自己格式化 -->
      <el-date-picker
        v-model="query.dateRange"
        type="daterange"
        value-format="YYYY-MM-DD"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="width: 260px"
      />

      <el-button type="primary" @click="handleSearch">
        <el-icon><Search /></el-icon>查询
      </el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- 数据表格 -->
    <el-table v-loading="loading" :data="list" style="width: 100%; margin-top: 16px">
      <el-table-column prop="id" label="申请编号" width="180" />
      <el-table-column prop="applicant" label="申请人" width="90" />
      <el-table-column prop="product" label="产品" min-width="150" />
      <el-table-column label="申请金额（元）" width="140" align="right">
        <template #default="{ row }">{{ formatAmount(row.amount) }}</template>
      </el-table-column>
      <el-table-column label="期限" width="90" align="center">
        <template #default="{ row }">{{ row.term }} 期</template>
      </el-table-column>
      <el-table-column prop="applyTime" label="申请时间" width="170" />
      <el-table-column label="风险等级" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="RISK_LEVEL[row.riskLevel]?.type" effect="light">
            {{ RISK_LEVEL[row.riskLevel]?.label || '-' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="LOAN_STATUS[row.status]?.type">
            {{ LOAN_STATUS[row.status]?.label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="130" align="center" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="goDetail(row.id)">查看</el-button>
          <el-button
            v-if="row.status === 'PENDING'"
            type="primary"
            link
            @click="goDetail(row.id)"
          >
            审批
          </el-button>
        </template>
      </el-table-column>

      <!-- 没数据时显示的东西 -->
      <template #empty>
        <el-empty description="暂无符合条件的申请" />
      </template>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="query.page"
      v-model:page-size="query.pageSize"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next, jumper"
      style="margin-top: 16px; justify-content: flex-end"
      @current-change="loadData"
      @size-change="handleSearch"
    />
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getLoanList } from '@/api/loan'
import { LOAN_STATUS, LOAN_STATUS_OPTIONS, RISK_LEVEL, formatAmount } from '@/utils/dict'

const router = useRouter()
const loading = ref(false)
const list = ref([])
const total = ref(0)

// 查询条件集中放在一个对象里，请求时一起带给后端
const query = reactive({
  keyword: '',
  status: '',
  dateRange: [],
  page: 1,
  pageSize: 10
})

async function loadData() {
  loading.value = true
  try {
    const data = await getLoanList(query)
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

// 点“查询”时回到第一页重新查
function handleSearch() {
  query.page = 1
  loadData()
}

function handleReset() {
  query.keyword = ''
  query.status = ''
  query.dateRange = []
  handleSearch()
}

function goDetail(id) {
  router.push(`/loans/${id}`)
}

onMounted(loadData)
</script>