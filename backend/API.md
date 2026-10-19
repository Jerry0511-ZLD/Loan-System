# Loan-System 后端接口文档（前端对接用）

> 这份文档就是前后端的接口契约，前端照着写即可。
> 另外还自动生成了一份可点着测的在线文档：<http://127.0.0.1:8080/docs>

---

## 0. 启动后端

```bash
cd backend
python run.py          # 起在 8080 端口，改代码自动重载
```

首次启动会自动建表（生成 `backend/risk.db`）并灌入演示账号和产品，不用手动初始化。

---

## 1. 全局约定（**先看这里**）

| 项 | 约定 |
| --- | --- |
| 前端 baseURL | `http://localhost:8080/api` |
| 接口前缀 | `/api`（不再是 `/api/v1`） |
| 端口 | `8080` |
| 成功外壳 | `{"code": 200, "message": "success", "data": ...}` |
| 失败外壳 | `{"code": 401, "message": "登录状态已失效，请重新登录", "data": null}` |
| 成功码的值 | **200**（想换成 0 就改 `backend/.env` 里的 `API_SUCCESS_CODE`，业务代码不用动） |
| 鉴权方式 | 请求头 `Authorization: Bearer <token>`，token 有效期 7 天 |
| 字段命名 | 响应体一律 camelCase（`riskLevel`、`createdAt`…）；请求体两种写法都收（`productId` / `product_id` 都行） |
| 分页参数 | `page`（默认 1）、`page_size` 或 `pageSize`（默认 10，最大 100） |
| 时间格式 | 字符串 `"2026-10-10 09:31:48"`（本地时间，可直接显示） |
| 金额单位 | 元，数字类型（不要传 "5万" 这种） |
| 利率单位 | 小数，`0.048` = 年化 4.8%；另有 `rateText: "4.8%"` 可直接展示 |
| 身份证 | 返回时已脱敏：`5101**********0021` |
| 手机号 | 返回时已脱敏：`138****0001`（脱敏在服务端完成，前端拿到就是脱敏后的值） |

**前端 axios 拦截器按这个写就能对上**：

```js
axios.interceptors.response.use(
  (res) => {
    const body = res.data
    if (body.code !== 200) {              // ← 成功码，和后端 .env 的 API_SUCCESS_CODE 保持一致
      if (body.code === 401) { /* 清 token，跳登录页 */ }
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return body.data                       // ← 业务数据在 data 里
  },
  (err) => Promise.reject(err)
)
```

---

## 2. 演示账号

| 账号 | 密码 | 角色 | 登录后会看到 |
| --- | --- | --- | --- |
| `admin` | `admin123` | 管理员 | 能进管理端，看全部申请单列表 |
| `demo` | `123456` | 普通用户 | 申请 → **通过**（额度全额、4.8%） |
| `demo2` | `123456` | 普通用户 | 申请 → **通过但降额 20%**（公积金未正常缴纳） |
| `demo3` | `123456` | 普通用户 | 申请 → **转人工**（列表里显示 `PENDING`） |
| `demo4` | `123456` | 普通用户 | 申请 → **拒贷**（近 6 月多次逾期 + 负债收入比高） |

> 4 个普通用户的身份证号是特意挑的，Mock 数据源用身份证号做种子，所以结果稳定可复现。
> **建议用产品 `p002`、金额 50000、期限 12** 来演示，这个组合在任何账号下都能跑通。

---

## 3. 接口总览

| 方法 | 路径 | 鉴权 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/login` | 不需要 | 登录，拿 token |
| GET | `/api/me` | 需要 | 当前登录用户信息 |
| GET | `/api/products` | 不需要 | 贷款产品列表（首页卡片） |
| GET | `/api/products/{id}` | 不需要 | 产品详情 |
| POST | `/api/loans` | 需要 | **提交贷款申请，提交即出风控结果** |
| GET | `/api/loans` | 需要 | 我的贷款列表（分页） |
| GET | `/api/loans/{id}` | 需要 | 我的贷款详情 |
| GET | `/api/applications` | 管理员 | 申请单列表（管理端，分页 + 筛选） |
| GET | `/api/applications/{id}` | 管理员 | 申请单详情 |
| GET | `/api/applications/{id}/decision` | 管理员 | 风控决策明细（含特征画像、引擎版本） |
| GET | `/api/applications/{id}/datasources` | 管理员 | **多数据源原始数据明细**（三源各自返回了什么） |
| POST | `/api/applications/{id}/review` | 管理员 | **人工复核**（处理「转人工」的申请单） |
| POST | `/api/applications` | 管理员 | 直录一笔进件（联调用） |
| GET | `/health` | 不需要 | 健康检查（这个接口**不套**响应外壳） |

---

## 4. 接口详情

### 4.1 登录 `POST /api/login`

请求（`username` 也可以填手机号）：

```json
{ "username": "demo", "password": "123456" }
```

响应：

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJ1aWQiOiIwMjc3...(一长串)",
    "tokenType": "Bearer",
    "expiresIn": 604800,
    "user": {
      "id": "0277988e9d9d40388c66e44088f7561d",
      "username": "demo",
      "name": "陈晓",
      "role": "user",
      "phone": "13800000001",
      "idCard": "5101**********0021",
      "monthlyIncome": 15000.0,
      "createdAt": "2026-10-10 09:20:00"
    }
  }
}
```

前端拿到 `token` 后存起来（localStorage），`role === "admin"` 才显示管理端入口。密码错误返回 `code: 401`，缺账号密码返回 `code: 400`。

### 4.2 当前用户 `GET /api/me`

响应 `data` 就是上面那个 `user` 对象。用于刷新页面后恢复登录态。

### 4.3 产品列表 `GET /api/products`（首页，无需登录）

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "p002",
      "name": "工薪优享贷",
      "description": "面向上班族，凭工牌即可申请，利率低至 4.8%",
      "minAmount": 10000.0,
      "maxAmount": 200000.0,
      "minTerm": 6,
      "maxTerm": 36,
      "rate": 0.048,
      "rateText": "4.8% 起",
      "tags": ["低息", "工薪族", "额度高"],
      "featured": true
    }
  ]
}
```

共 6 个产品：`p001` 极速信用贷、`p002` 工薪优享贷、`p003` 公积金贷、`p004` 大额消费贷、`p005` 装修分期、`p006` 车主贷。

### 4.4 提交申请 `POST /api/loans`（★ 核心）

请求体（`amount`/`term` 要在所选产品的范围内）：

```json
{
  "product": "p002",
  "amount": 50000,
  "term": 12,
  "purpose": "装修"
}
```

字段说明：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `product` | 是 | 产品 id；写 `productId` 也行，传整个产品对象也行（自动取 id） |
| `amount` | 是 | 申请金额（元） |
| `term` | 否 | 期限（月），默认 12；传 `"12期"` 这种字符串也认 |
| `purpose` | 否 | 借款用途 |
| `applicantName` / `idCard` / `phone` / `monthlyIncome` | 否 | 表单如果收集了就传；不传则用登录用户的资料兜底（演示账号都已带好资料） |

响应（提交即出结果）：

```json
{
  "code": 200,
  "message": "申请已提交，风控结果已出",
  "data": {
    "id": "2094855fbe974c318c7bb7099a8d1b6f",
    "userId": "0277988e9d9d40388c66e44088f7561d",
    "applicantName": "陈晓",
    "phone": "13800000001",
    "idCard": "5101**********0021",
    "monthlyIncome": 15000.0,
    "productId": "p003",
    "productName": "公积金贷",
    "amount": 60000.0,
    "term": 24,
    "purpose": "装修",
    "status": "APPROVED",
    "decisionStatus": "APPROVED",
    "reviewRequired": false,
    "riskLevel": "LOW",
    "riskScore": 5.0,
    "approvedAmount": 60000.0,
    "rate": 0.039,
    "rateText": "3.90%",
    "reasons": [],
    "createdAt": "2026-10-10 09:31:48",
    "decidedAt": "2026-10-10 09:31:48"
  }
}
```

常见报错：金额超产品范围 → `400`「工薪优享贷 可申请金额 10000~200000 元」；产品下架/不存在 → `404`；没带 token → `401`。

### 4.5 我的贷款列表 `GET /api/loans`

Query：`page`、`page_size`（或 `pageSize`）、`status`（可选，`APPROVED` / `PENDING` / `REJECTED`）

响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [ { ...和 4.4 的 data 同结构... } ],
    "items": [ ...同上，给习惯用 items 的写法... ],
    "total": 5,
    "page": 1,
    "pageSize": 10,
    "totalPages": 1
  }
}
```

`list` 和 `items` 是同一份数组，用哪个都行（`total` / `page` / `pageSize` / `totalPages` 都在同一层）。

### 4.6 我的贷款详情 `GET /api/loans/{id}`

返回结构同 4.4 的 `data`。只能看自己的，看别人的返回 `403`（管理员可以看全部）。

### 4.7 管理端申请单列表 `GET /api/applications`

需要 admin 的 token，否则 `403`。

Query：

| 参数 | 说明 |
| --- | --- |
| `page` / `page_size`（或 `pageSize`） | 分页，默认第 1 页、每页 10 条 |
| `status` | `APPROVED` / `PENDING` / `REJECTED` |
| `keyword` | 按姓名或手机号模糊搜索 |
| `reviewRequired` | `true` 只看转人工待办；`false` 只看不需要人工的；不传则全部 |
| `startDate` / `endDate` | 按申请创建时间筛选，格式 `2026-10-01`；`endDate` 含当天 23:59:59 |

响应结构和 4.5 一样（分页 + `list` 数组），每行比用户端多的是申请人信息（`applicantName`、`phone` 脱敏、`idCard` 脱敏、`monthlyIncome`）。

### 4.8 管理端详情 / 决策明细 / 多数据源明细

**`GET /api/applications/{id}`** → 单条申请的完整信息，结构同 4.4 的 `data`。

**`GET /api/applications/{id}/decision`** → 决策明细。相比旧版，`data` 里多了四个字段：

```json
{
  "status": "MANUAL",
  "approvedAmount": 0.0,
  "rate": 0.0,
  "reasons": ["multi_platform: 多头授信5家,转人工"],
  "featureProfile": { "overdue_count_6m": 1, "dti": 0.32, "...": "..." },
  "engine": "rule_v0",          // 这条结论是哪套机制算的（阶段 II 会是 scorecard）
  "modelVersion": "1.0",        // 引擎版本，便于新旧效果对比
  "source": "auto",             // auto = 系统自动决策；manual = 人工复核追加
  "reviewerId": "",             // 人工复核人（source=manual 时才有值）
  "reviewedAt": null,
  "comment": "",
  "createdAt": "2026-10-19 20:11:03"
}
```

**`GET /api/applications/{id}/datasources`** → 三源原始数据快照，用于管理端展示「融合前长什么样」：

```json
{
  "applicationId": "2094855fbe974c318c7bb7099a8d1b6f",
  "sources": [
    { "name": "credit_bureau", "fields": { "overdue_count_6m": 1, "current_debt": 12000, "credit_card_count": 5, "is_blacklisted": false } },
    { "name": "carrier",       "fields": { "active_months": 18, "real_named": true, "last_active_days": 2 } },
    { "name": "housing_fund",  "fields": { "fund_months": 24, "monthly_contribution": 800, "active": true } }
  ],
  "featureProfile": { "...": "聚合后的统一特征" },
  "engine": "rule_v0",
  "modelVersion": "1.0",
  "decidedAt": "2026-10-19 20:11:03"
}
```

> 数据来自 `decisions.raw_data`（决策时落库的快照），不是实时重算 —— 审计要看的是「当时」的数据。

### 4.9 人工复核 `POST /api/applications/{id}/review`

处理那些 `reviewRequired = true` 的申请单（即风控结论为「转人工」的单子）。

请求：

```json
{ "action": "approve", "approvedAmount": 48000, "rate": 0.048, "comment": "公积金正常，同意放款" }
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `action` | 是 | `approve`（通过）/ `reject`（拒绝）；也接受 `pass`、`agree`、`通过`、`拒绝` 等写法，服务端会归一化 |
| `approvedAmount` | 否 | 手工调整批核额度；不传则沿用系统算出的值，系统值为 0 时按授信规则兜底 |
| `rate` | 否 | 手工调整年化利率（小数，`0.048` = 4.8%）；不传则沿用产品或系统值 |
| `comment` | 否 | 复核意见，写进决策记录，供事后追责 |

响应：`data` 是复核后的申请单（结构同 4.4）。

两条规则：

- 只有 `reviewRequired = true` 的单子能复核，否则返回 **`409`**（不静默覆盖已生效的结论）；
- 复核结果会**追加一条新的决策记录**（`source="manual"`），原来那条自动决策保留，审计时能看出「系统判了什么、人改成了什么」。

**`POST /api/applications`** → 管理员直接录一笔进件（联调用，字段：`applicantName`、`idCard`、`phone`、`monthlyIncome`、`requestedAmount`、`term`、`productId`）。

---

## 5. 枚举字典

| 字段 | 取值 | 含义 |
| --- | --- | --- |
| `status` | `PENDING` / `APPROVED` / `REJECTED` | 申请单状态（前端只看这个） |
| `decisionStatus` | `APPROVED` / `REJECTED` / `MANUAL` | 风控内部结论，`MANUAL` = 转人工 |
| `reviewRequired` | `true` / `false` | 是否等待人工复核（= `decisionStatus === "MANUAL"`） |
| `source` | `auto` / `manual` | 决策记录来源：系统自动 / 人工复核追加 |
| `engine` | `rule_v0` / `scorecard` / `manual` | 决策引擎标识，阶段 I 只有 `rule_v0` |
| `riskLevel` | `LOW` / `MEDIUM` / `HIGH` | 风险档位（低/中/高） |
| `riskScore` | 0 ~ 100 的数字 | 风险分，**越高越危险**；≥70 高风险，40~69 中风险，<40 低风险 |
| 用户 `role` | `user` / `admin` | 权限 |

> 注意「转人工」在用户端故意显示成 `PENDING`（待审批），因为前端状态只有三种；需要区分时看 `reviewRequired`。

---

## 6. 错误码

| code | 场景 | 例子 |
| --- | --- | --- |
| 200 | 成功 | — |
| 400 | 业务参数不对 | 金额超出产品范围、账号密码为空 |
| 401 | 未登录 / token 失效 / 账号密码错误 | 没带 `Authorization` 头 |
| 403 | 权限不够 | 普通用户访问管理端 |
| 404 | 资源不存在 | 产品下架、申请单不存在 |
| 409 | 状态冲突 | 对已经处理过的申请单重复复核、对非转人工的单子发起复核 |
| 422 | 请求体字段缺失或类型不对 | 提交申请时漏了 `product` |
| 500 | 服务端异常 | 统一返回「服务器内部错误」，堆栈在后端控制台 |

**无论哪种错误，前端拿到的都是 `{code, message, data: null}` 这三个键**，直接弹 `message` 就行。

---

## 7. 和上一版后端的差异（对照之前那张对比表）

| 维度 | 上一版 | 现在 |
| --- | --- | --- |
| 接口前缀 | `/api/v1` | `/api` |
| 端口 | 8000 | **8080** |
| 响应外壳 | 裸对象 | `{code, message, data}` |
| 登录 | 没有 | `POST /api/login` |
| 产品列表 | 没有 | `GET /api/products` |
| 我的贷款 | 只能按 id 查单个 | `GET /api/loans`（分页） |
| 提交申请 | `POST /applications`，字段 `applicant_name/id_card/phone/monthly_income/requested_amount` | `POST /api/loans`，字段 `product/amount/term/purpose`（两种写法都收） |
| 鉴权 | 没有 | `Authorization: Bearer <token>` |
| 状态值 | `approved/rejected/manual` | `PENDING/APPROVED/REJECTED`（转人工并入 `PENDING`） |
| 风控结果 | 只有 `approved_amount/rate/reasons` | 多了 `riskLevel` / `riskScore`，原来的字段也都还在（`approvedAmount/rate/reasons`） |

---

## 8. 前端页面 → 接口对照

| 页面 | 接口 |
| --- | --- |
| 登录页 | `POST /api/login` |
| 首页（产品卡片） | `GET /api/products` |
| 申请表单 | `POST /api/loans` |
| 我的贷款列表 | `GET /api/loans` |
| 贷款详情 | `GET /api/loans/{id}` |
| 管理端申请列表 | `GET /api/applications` |
| 管理端申请详情 | `GET /api/applications/{id}` |
