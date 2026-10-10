# Loan-System

一个多数据源融合的互联网个人贷款风控系统（进阶式挑战性综合项目）。

## 项目结构

```
Loan-System/
└── backend/                     # FastAPI 后端
    ├── app/
    │   ├── api/                 # 路由：认证 / 产品 / 贷款 / 申请管理（管理端）
    │   ├── core/                # 统一响应外壳、密码与 token
    │   ├── datasources/         # 多数据源适配层（征信 / 运营商 / 公积金，MVP 为 Mock）
    │   ├── services/            # 特征聚合 → 规则引擎 → 授信计算 → 风险评级
    │   ├── config.py            # 配置（可用 .env 覆盖）
    │   ├── models.py            # 数据表：用户 / 产品 / 申请单 / 决策
    │   ├── schemas.py           # 入参模型（字段名兼容多种写法）
    │   ├── serializers.py       # 出参组装（统一 camelCase、时间格式、脱敏）
    │   ├── seed.py              # 演示账号 + 产品种子数据
    │   └── main.py              # 入口：CORS、统一异常外壳、路由注册
    ├── API.md                   # ★ 前后端接口契约（前端照着写就行）
    ├── run.py                   # 本地启动（8080 端口）
    ├── requirements.txt
    └── .env.example             # 可覆盖的配置项（成功码、密钥、CORS 来源）
```

## 启动

```bash
cd backend
pip install -r requirements.txt
python run.py                    # http://127.0.0.1:8080
```

首次启动自动建表并灌演示数据。在线接口文档：<http://127.0.0.1:8080/docs>

## 演示账号

| 账号 | 密码 | 说明 |
| --- | --- | --- |
| `admin` | `admin123` | 管理端（可看全部申请单） |
| `demo` / `demo2` / `demo3` / `demo4` | `123456` | 普通用户，申请结果分别是：通过 / 降额通过 / 转人工 / 拒贷 |

## 对接说明

前端从 `backend/API.md` 开始看：接口前缀 `/api`、端口 `8080`、统一响应 `{code, message, data}`、鉴权用 `Authorization: Bearer <token>`。
