import request from './request'
import { USE_MOCK } from './config'
import {
  mockGetLoanList,
  mockGetLoanDetail,
  mockReviewLoan,
  mockGetDashboardStats
} from './mock'

/**
 * 贷款申请相关接口（管理端）。
 *
 * 对接的后端接口（前缀 /api，需管理员 token）：
 *   POST /api/login                              登录（见 user.js）
 *   GET  /api/applications                       申请单列表（分页 + 状态 + 关键字）
 *   GET  /api/applications/{id}                  申请单详情
 *   GET  /api/applications/{id}/decision         风控决策明细
 *
 * 后端统一返回：{ code: 200, message, data }，由 request.js 的拦截器拆包，
 * 所以这里拿到的就是 data 本身。
 */

/**
 * 把后端的"贷款对象"拍平成页面用的字段。
 *
 * 为什么要这一步：后端字段名（applicantName / productName / createdAt）
 * 和页面里用的名字（applicant / product / applyTime）不一样，
 * 统一在这里转换，页面代码就不用改来改去。
 */
function normalizeLoan(dto) {
  if (!dto) return dto
  return {
    id: dto.id,
    applicant: dto.applicantName,
    idCard: dto.idCard,
    phone: dto.phone,
    monthlyIncome: dto.monthlyIncome,
    productId: dto.productId,
    product: dto.productName,
    amount: dto.amount,
    term: dto.term,
    purpose: dto.purpose,
    status: dto.status,
    decisionStatus: dto.decisionStatus,
    reviewRequired: dto.reviewRequired,
    riskLevel: dto.riskLevel,
    riskScore: dto.riskScore,
    approvedAmount: dto.approvedAmount,
    rate: dto.rate,
    rateText: dto.rateText,
    reasons: dto.reasons || [],
    applyTime: dto.createdAt,
    decidedAt: dto.decidedAt
  }
}

/** 查询申请列表（管理端看全部） */
export async function getLoanList(params = {}) {
  if (USE_MOCK) return mockGetLoanList(params)

  const { keyword = '', status = '', page = 1, pageSize = 10 } = params
  const data = await request.get('/applications', {
    params: {
      page,
      pageSize,
      status: status || undefined,
      keyword: keyword || undefined
    }
  })
  const rows = data.list || data.items || []
  return { list: rows.map(normalizeLoan), total: data.total ?? rows.length }
}

/** 查询申请详情（顺带取一次风控决策明细） */
export async function getLoanDetail(id) {
  if (USE_MOCK) return mockGetLoanDetail(id)

  const loan = normalizeLoan(await request.get(`/applications/${id}`))
  // 决策明细单独取；该申请可能还没有决策结果，取不到不影响主信息展示
  try {
    loan.decision = await request.get(`/applications/${id}/decision`)
  } catch (e) {
    loan.decision = null
  }
  return loan
}

/**
 * 提交审批结果。
 */
export function reviewLoan(id, data) {
  if (USE_MOCK) return mockReviewLoan(id, data)
  return Promise.reject(
    new Error('审批提交失败，请稍后重试')
  )
}

/**
 * 工作台统计：由申请列表在前端汇总计算。
 */
export async function getDashboardStats() {
  if (USE_MOCK) return mockGetDashboardStats()

  const data = await request.get('/applications', { params: { page: 1, pageSize: 100 } })
  const rows = (data.list || data.items || []).map(normalizeLoan)

  const pending = rows.filter((item) => item.status === 'PENDING')
  const approved = rows.filter((item) => item.status === 'APPROVED')
  const reviewed = rows.filter((item) => item.status !== 'PENDING')
  const today = new Date().toISOString().slice(0, 10)

  return {
    todayApplications: rows.filter((item) => (item.applyTime || '').startsWith(today)).length,
    pendingCount: pending.length,
    approvedAmount: approved.reduce((sum, item) => sum + (item.approvedAmount || 0), 0),
    passRate: reviewed.length ? Math.round((approved.length / reviewed.length) * 100) : 0,
    latest: rows.slice(0, 5)
  }
}