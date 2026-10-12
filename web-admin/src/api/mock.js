/**
 * 本地模拟数据（Mock）。
 *
 * 用途：在后端接口就绪前，前端也能把页面与交互完整跑起来；
 * 后端就绪后，把 config.js 里的 USE_MOCK 改成 false 即可切换到真实接口。
 *
 * 这里的字段名 = 前后端约定的接口字段名，保持一致。
 */

// 模拟网络延迟，让 loading 效果能看出来
const delay = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms))

/**
 * 贷款申请数据。
 * riskScore / riskLevel 为风控结果字段，此处为示例数据。
 */
const loans = [
  {
    id: 'LN202609180001',
    applicant: '张伟',
    idCard: '5101**********1234',
    phone: '138****8888',
    age: 29,
    city: '成都',
    company: '成都云图科技有限公司',
    product: '消费贷·随借随还',
    amount: 50000,
    term: 12,
    purpose: '房屋装修',
    channel: 'Android APP',
    applyTime: '2026-09-18 10:23:45',
    status: 'PENDING',
    riskLevel: 'MEDIUM',
    riskScore: 52
  },
  {
    id: 'LN202609180002',
    applicant: '李娜',
    idCard: '5101**********2388',
    phone: '139****6666',
    age: 26,
    city: '成都',
    company: '四川启明教育咨询有限公司',
    product: '消费贷·随借随还',
    amount: 20000,
    term: 6,
    purpose: '日常消费',
    channel: 'Android APP',
    applyTime: '2026-09-18 09:12:03',
    status: 'PENDING',
    riskLevel: 'LOW',
    riskScore: 15
  },
  {
    id: 'LN202609170003',
    applicant: '王强',
    idCard: '5101**********5512',
    phone: '135****1234',
    age: 41,
    city: '绵阳',
    company: '绵阳恒达汽配经营部',
    product: '经营贷',
    amount: 150000,
    term: 24,
    purpose: '经营周转',
    channel: 'Android APP',
    applyTime: '2026-09-17 16:40:11',
    status: 'REJECTED',
    riskLevel: 'HIGH',
    riskScore: 78
  },
  {
    id: 'LN202609170004',
    applicant: '刘洋',
    idCard: '5101**********7743',
    phone: '186****5566',
    age: 33,
    city: '成都',
    company: '成都锦程物流有限公司',
    product: '装修贷',
    amount: 80000,
    term: 36,
    purpose: '房屋装修',
    channel: 'Android APP',
    applyTime: '2026-09-17 11:05:27',
    status: 'PENDING',
    riskLevel: 'MEDIUM',
    riskScore: 58
  },
  {
    id: 'LN202609160005',
    applicant: '陈静',
    idCard: '5101**********9021',
    phone: '158****9900',
    age: 31,
    city: '德阳',
    company: '德阳市第二人民医院',
    product: '消费贷·随借随还',
    amount: 30000,
    term: 12,
    purpose: '医疗支出',
    channel: 'Android APP',
    applyTime: '2026-09-16 14:52:09',
    status: 'APPROVED',
    riskLevel: 'LOW',
    riskScore: 18
  },
  {
    id: 'LN202609160006',
    applicant: '赵磊',
    idCard: '5101**********3310',
    phone: '137****4433',
    age: 38,
    city: '成都',
    company: '成都磊鑫建材有限公司',
    product: '经营贷',
    amount: 100000,
    term: 18,
    purpose: '经营周转',
    channel: 'Android APP',
    applyTime: '2026-09-16 10:18:36',
    status: 'APPROVED',
    riskLevel: 'LOW',
    riskScore: 25
  },
  {
    id: 'LN202609150007',
    applicant: '孙倩',
    idCard: '5101**********6624',
    phone: '150****7788',
    age: 24,
    city: '成都',
    company: '成都自由职业',
    product: '教育贷',
    amount: 40000,
    term: 24,
    purpose: '职业培训',
    channel: 'Android APP',
    applyTime: '2026-09-15 19:33:41',
    status: 'REJECTED',
    riskLevel: 'HIGH',
    riskScore: 71
  },
  {
    id: 'LN202609150008',
    applicant: '周敏',
    idCard: '5101**********1102',
    phone: '188****2211',
    age: 27,
    city: '眉山',
    company: '眉山市第一中学',
    product: '消费贷·随借随还',
    amount: 15000,
    term: 6,
    purpose: '日常消费',
    channel: 'Android APP',
    applyTime: '2026-09-15 08:47:52',
    status: 'PENDING',
    riskLevel: 'LOW',
    riskScore: 12
  }
]

/** 由字符串算出一个固定数字，用来造“看起来不一样但每次刷新都一样”的假数据 */
function seedFrom(text) {
  let s = 0
  for (const ch of text) s += ch.charCodeAt(0)
  return s
}

function now() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

/**
 * 多数据源融合信息。这些数据来自征信机构、运营商、电商平台、社保等外部数据源，
 * 此处为示例数据，接口结构保持一致。
 */
function buildDataSources(loan) {
  const s = seedFrom(loan.id)
  const isHighRisk = loan.riskLevel === 'HIGH' || loan.riskLevel === 'MEDIUM'

  return [
    {
      key: 'credit',
      name: '央行征信',
      status: isHighRisk ? 'WARN' : 'OK',
      items: [
        { label: '近6个月逾期次数', value: `${isHighRisk ? 2 : 0} 次` },
        { label: '近3个月查询次数', value: `${3 + (s % 5)} 次` },
        { label: '信贷账户数', value: `${2 + (s % 4)} 个` },
        { label: '信用历史长度', value: `${3 + (s % 8)} 年` }
      ]
    },
    {
      key: 'telecom',
      name: '运营商数据',
      status: 'OK',
      items: [
        { label: '在网时长', value: `${24 + (s % 60)} 个月` },
        { label: '手机号实名认证', value: '已认证' },
        { label: '近3个月停机次数', value: `${s % 3} 次` },
        { label: '常用联系人数量', value: `${15 + (s % 20)} 人` }
      ]
    },
    {
      key: 'ecommerce',
      name: '电商消费',
      status: isHighRisk ? 'WARN' : 'OK',
      items: [
        { label: '月均消费金额', value: `${2000 + (s % 4000)} 元` },
        { label: '收货地址稳定性', value: `${12 + (s % 24)} 个月未变更` },
        { label: '消费能力等级', value: isHighRisk ? '一般' : '良好' }
      ]
    },
    {
      key: 'social',
      name: '社保 / 公积金',
      status: 'OK',
      items: [
        { label: '连续缴纳月数', value: `${6 + (s % 36)} 个月` },
        { label: '公积金月缴存额', value: `${400 + (s % 1600)} 元` },
        { label: '单位性质', value: loan.company.includes('公司') ? '民营企业' : '其他' }
      ]
    }
  ]
}

/** 审批流转记录 */
function buildHistory(loan) {
  const history = [
    { time: loan.applyTime, operator: '借款人', action: '提交贷款申请', remark: `申请渠道：${loan.channel}` },
    { time: loan.applyTime, operator: '系统', action: '身份四要素核验', remark: '核验通过' }
  ]

  if (loan.status !== 'PENDING') {
    history.push({ time: loan.applyTime, operator: '系统', action: '反欺诈规则校验', remark: '命中规则 0 条' })
    history.push({
      time: loan.reviewTime || loan.applyTime,
      operator: loan.reviewer || '审批员 admin',
      action: loan.status === 'APPROVED' ? '人工审批通过' : '人工审批拒绝',
      remark: loan.remark || (loan.status === 'APPROVED' ? '同意授信' : '综合评分未达标')
    })
  }

  return history
}

/* ------------------------------------------------------------------ */
/* 下面每个函数，都对应后端的一个真实接口                                */
/* ------------------------------------------------------------------ */

/** 对应 POST /api/auth/login */
export async function mockLogin({ username, password }) {
  await delay(400)
  if (username === 'admin' && password === 'admin123') {
    return {
      token: `mock-token-${Date.now()}`,
      tokenType: 'Bearer',
      user: { name: '风控管理员', username: 'admin', role: 'admin' }
    }
  }
  throw new Error('用户名或密码错误')
}

/**
 * 对应 GET /api/loan/applications
 * @param {{keyword?:string,status?:string,page?:number,pageSize?:number,dateRange?:string[]}} params
 */
export async function mockGetLoanList(params = {}) {
  await delay()
  const { keyword = '', status = '', page = 1, pageSize = 10, dateRange } = params

  let result = [...loans]

  if (keyword) {
    const kw = keyword.trim()
    result = result.filter((item) => item.applicant.includes(kw) || item.id.includes(kw))
  }
  if (status) {
    result = result.filter((item) => item.status === status)
  }
  if (dateRange && dateRange.length === 2) {
    const [begin, end] = dateRange
    result = result.filter((item) => item.applyTime >= begin && item.applyTime <= `${end} 23:59:59`)
  }

  const total = result.length
  const start = (page - 1) * pageSize
  return { list: result.slice(start, start + pageSize), total }
}

/** 对应 GET /api/loan/applications/{id} */
export async function mockGetLoanDetail(id) {
  await delay()
  const loan = loans.find((item) => item.id === id)
  if (!loan) throw new Error('该贷款申请不存在')
  return {
    ...loan,
    dataSources: buildDataSources(loan),
    history: buildHistory(loan)
  }
}

/** 对应 POST /api/loan/applications/{id}/review */
export async function mockReviewLoan(id, payload) {
  await delay(500)
  const loan = loans.find((item) => item.id === id)
  if (!loan) throw new Error('该贷款申请不存在')

  loan.status = payload.result === 'APPROVE' ? 'APPROVED' : 'REJECTED'
  loan.approvedAmount = payload.result === 'APPROVE' ? payload.amount : 0
  loan.approvedRate = payload.rate
  loan.remark = payload.remark
  loan.reviewer = '审批员 admin'
  loan.reviewTime = now()

  return { ...loan, dataSources: buildDataSources(loan), history: buildHistory(loan) }
}

/** 对应 GET /api/loan/dashboard/stats */
export async function mockGetDashboardStats() {
  await delay()
  const pending = loans.filter((item) => item.status === 'PENDING')
  const approved = loans.filter((item) => item.status === 'APPROVED')
  const reviewed = loans.filter((item) => item.status !== 'PENDING')

  return {
    todayApplications: loans.filter((item) => item.applyTime.startsWith('2026-09-18')).length,
    pendingCount: pending.length,
    approvedAmount: approved.reduce((sum, item) => sum + (item.approvedAmount || item.amount), 0),
    passRate: reviewed.length ? Math.round((approved.length / reviewed.length) * 100) : 0,
    // 工作台下方“最新申请”列表
    latest: [...loans]
      .sort((a, b) => (a.applyTime < b.applyTime ? 1 : -1))
      .slice(0, 5)
      .map(({ id, applicant, product, amount, applyTime, status, riskLevel }) => ({
        id,
        applicant,
        product,
        amount,
        applyTime,
        status,
        riskLevel
      }))
  }
}