/**
 * 字典 / 枚举。
 * 前端不要到处硬编码 "PENDING" 这种字符串，统一放这里，
 * 改一处全站生效。
 */

export const LOAN_STATUS = {
  PENDING: { label: '待审批', type: 'warning' },
  APPROVED: { label: '已通过', type: 'success' },
  REJECTED: { label: '已拒绝', type: 'danger' }
}

// 给下拉框用的数组
export const LOAN_STATUS_OPTIONS = Object.entries(LOAN_STATUS).map(([value, item]) => ({
  value,
  label: item.label
}))

export const RISK_LEVEL = {
  LOW: { label: '低风险', type: 'success' },
  MEDIUM: { label: '中风险', type: 'warning' },
  HIGH: { label: '高风险', type: 'danger' }
}

/**
 * 金额千分位显示：50000 -> 50,000
 */
export function formatAmount(value) {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('zh-CN')
}