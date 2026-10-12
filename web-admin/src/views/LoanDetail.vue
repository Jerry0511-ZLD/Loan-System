<!--
  申请详情页：审批员在这里看完整资料 -> 看多数据源信息 -> 填写审批结果。
  这是整个后台最核心的页面。
-->
<template>
  <div v-loading="loading">
    <!-- 顶部操作条 -->
    <el-card shadow="never" class="page-card">
      <div class="top-bar">
        <div>
          <el-button link @click="router.back()">
            <el-icon><ArrowLeft /></el-icon>返回
          </el-button>
          <span class="order-no">申请编号：{{ detail.id }}</span>
          <el-tag v-if="detail.status" :type="LOAN_STATUS[detail.status]?.type" style="margin-left: 10px">
            {{ LOAN_STATUS[detail.status]?.label }}
          </el-tag>
        </div>
        <el-button
          v-if="detail.status === 'PENDING'"
          type="primary"
          @click="dialogVisible = true"
        >
          审批
        </el-button>
      </div>
    </el-card>

    <el-row :gutter="16" style="margin-top: 16px">
      <!-- 左栏：申请人资料 + 多数据源 -->
      <el-col :span="16">
        <el-card shadow="never" class="page-card">
          <template #header><b>申请人资料</b></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="姓名">{{ detail.applicant }}</el-descriptions-item>
            <el-descriptions-item label="身份证号">{{ detail.idCard }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ detail.phone }}</el-descriptions-item>
            <el-descriptions-item label="年龄">{{ detail.age ?? '-' }} 岁</el-descriptions-item>
            <el-descriptions-item label="所在城市">{{ detail.city || '-' }}</el-descriptions-item>
            <el-descriptions-item label="单位名称">{{ detail.company || '-' }}</el-descriptions-item>
            <el-descriptions-item label="申请产品">{{ detail.product }}</el-descriptions-item>
            <el-descriptions-item label="申请金额">
              {{ formatAmount(detail.amount) }} 元
            </el-descriptions-item>
            <el-descriptions-item label="贷款期限">{{ detail.term }} 期</el-descriptions-item>
            <el-descriptions-item label="资金用途">{{ detail.purpose }}</el-descriptions-item>
            <el-descriptions-item label="申请渠道">{{ detail.channel || '-' }}</el-descriptions-item>
            <el-descriptions-item label="申请时间">{{ detail.applyTime }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!--
          多数据源融合信息：本系统的核心能力。
          数据源不是写死的 4 个，后端以后加数据源，前端这页不用改。
        -->
        <el-card shadow="never" class="page-card" style="margin-top: 16px">
          <template #header><b>多数据源融合信息</b></template>

          <el-row :gutter="16">
            <el-col v-for="source in (detail.dataSources || [])" :key="source.key" :span="12">
              <div class="source-box">
                <div class="source-title">
                  <span>{{ source.name }}</span>
                  <el-tag :type="source.status === 'OK' ? 'success' : 'warning'" size="small" effect="light">
                    {{ source.status === 'OK' ? '正常' : '异常' }}
                  </el-tag>
                </div>
                <div v-for="item in source.items" :key="item.label" class="source-item">
                  <span class="label">{{ item.label }}</span>
                  <span class="value">{{ item.value }}</span>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- 右栏：风险结论 + 流转记录 -->
      <el-col :span="8">
        <el-card shadow="never" class="page-card">
          <template #header><b>风险结论</b></template>

          <div class="risk-score">
            <div class="score">{{ detail.riskScore ?? '-' }}</div>
            <div class="score-label">综合评分</div>
          </div>

          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="风险等级">
              <el-tag :type="RISK_LEVEL[detail.riskLevel]?.type" effect="light">
                {{ RISK_LEVEL[detail.riskLevel]?.label || '-' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="建议额度">
              {{ formatAmount(detail.approvedAmount || detail.amount) }} 元
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never" class="page-card" style="margin-top: 16px">
          <template #header><b>流转记录</b></template>
          <el-timeline>
            <el-timeline-item
              v-for="(item, index) in (detail.history || [])"
              :key="index"
              :timestamp="item.time"
              placement="top"
            >
              <div class="history-action">{{ item.action }}</div>
              <div class="history-remark">{{ item.operator }}：{{ item.remark }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <!-- 审批弹窗 -->
    <el-dialog v-model="dialogVisible" title="审批处理" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="审批结果" prop="result">
          <el-radio-group v-model="form.result">
            <el-radio value="APPROVE">通过</el-radio>
            <el-radio value="REJECT">拒绝</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.result === 'APPROVE'" label="批准金额" prop="amount">
          <el-input-number v-model="form.amount" :min="0" :max="detail.amount" :step="1000" />
          <span class="unit">元（不超过申请金额 {{ formatAmount(detail.amount) }}）</span>
        </el-form-item>

        <el-form-item v-if="form.result === 'APPROVE'" label="年化利率" prop="rate">
          <el-input-number v-model="form.rate" :min="0" :max="36" :step="0.1" :precision="2" />
          <span class="unit">%（监管上限 36%）</span>
        </el-form-item>

        <el-form-item label="审批意见" prop="remark">
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="3"
            maxlength="200"
            show-word-limit
            placeholder="请填写审批意见，将记入流转记录"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getLoanDetail, reviewLoan } from '@/api/loan'
import { LOAN_STATUS, RISK_LEVEL, formatAmount } from '@/utils/dict'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const detail = ref({})

const form = reactive({
  result: 'APPROVE',
  amount: 0,
  rate: 7.2,
  remark: ''
})

const rules = {
  result: [{ required: true, message: '请选择审批结果', trigger: 'change' }],
  amount: [{ required: true, message: '请输入批准金额', trigger: 'blur' }],
  remark: [{ required: true, message: '请填写审批意见', trigger: 'blur' }]
}

async function loadDetail() {
  loading.value = true
  try {
    detail.value = await getLoanDetail(route.params.id)
    // 默认批准金额 = 申请金额
    form.amount = detail.value.amount
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    detail.value = await reviewLoan(route.params.id, form)
    dialogVisible.value = false
    ElMessage.success('审批已提交')
  } finally {
    submitting.value = false
  }
}

onMounted(loadDetail)
</script>

<style scoped>
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.order-no {
  margin-left: 12px;
  font-weight: 600;
}

.source-box {
  padding: 10px 12px;
  margin-bottom: 12px;
  background-color: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}

.source-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-weight: 600;
}

.source-item {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  font-size: 13px;
}

.source-item .label {
  color: #909399;
}

.source-item .value {
  color: #303133;
}

.risk-score {
  padding: 12px 0;
  text-align: center;
}

.risk-score .score {
  font-size: 34px;
  font-weight: 700;
  color: #409eff;
}

.risk-score .score-label {
  color: #909399;
  font-size: 13px;
}

.history-action {
  font-size: 14px;
  font-weight: 600;
}

.history-remark {
  margin-top: 2px;
  color: #909399;
  font-size: 12px;
}

.unit {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}
</style>