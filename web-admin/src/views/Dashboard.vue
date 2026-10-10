<!-- 工作台：给审批员一眼看清"现在有多少活、今天情况怎么样" -->
<template>
  <div v-loading="loading">
    <!-- 四张统计卡片 -->
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="今日新增申请" :value="stats.todayApplications" />
          <el-icon class="stat-icon color-blue"><Document /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="待审批" :value="stats.pendingCount" />
          <el-icon class="stat-icon color-orange"><Clock /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="已批准金额（元）" :value="stats.approvedAmount" />
          <el-icon class="stat-icon color-green"><Money /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="通过率" :value="stats.passRate" suffix="%" />
          <el-icon class="stat-icon color-purple"><TrendCharts /></el-icon>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最新申请 -->
    <el-card shadow="never" class="page-card" style="margin-top: 16px">
      <template #header>
        <div class="card-header">
          <span>最新申请</span>
          <el-button type="primary" link @click="router.push('/loans')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>

      <el-table :data="stats.latest" style="width: 100%">
        <el-table-column prop="id" label="申请编号" width="180" />
        <el-table-column prop="applicant" label="申请人" width="100" />
        <el-table-column prop="product" label="产品" min-width="150" />
        <el-table-column label="申请金额（元）" width="140" align="right">
          <template #default="{ row }">{{ formatAmount(row.amount) }}</template>
        </el-table-column>
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
        <el-table-column prop="applyTime" label="申请时间" width="180" />
        <el-table-column label="操作" width="90" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="router.push(`/loans/${row.id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getDashboardStats } from '@/api/loan'
import { LOAN_STATUS, RISK_LEVEL, formatAmount } from '@/utils/dict'

const router = useRouter()
const loading = ref(false)

// 先给一个空壳，避免页面刚打开时报 undefined
const stats = ref({
  todayApplications: 0,
  pendingCount: 0,
  approvedAmount: 0,
  passRate: 0,
  latest: []
})

// onMounted：组件第一次显示到页面上之后执行，通常用来请求数据
onMounted(async () => {
  loading.value = true
  try {
    stats.value = await getDashboardStats()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stat-card {
  position: relative;
  border-radius: 8px;
}

.stat-icon {
  position: absolute;
  top: 18px;
  right: 18px;
  font-size: 26px;
  opacity: 0.75;
}

.color-blue {
  color: #409eff;
}
.color-orange {
  color: #e6a23c;
}
.color-green {
  color: #67c23a;
}
.color-purple {
  color: #909399;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
</style>