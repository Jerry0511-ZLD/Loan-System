from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置。每一项都可以在 backend/.env 里覆盖（见 .env.example）。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Loan Risk MVP"
    debug: bool = True  # True 时打印 SQL，方便排查
    database_url: str = "sqlite+aiosqlite:///./risk.db"
    datasource_mode: str = "mock"  # mock | live
    # 风控引擎：对应 services/risk_engines 里注册的名字。
    # 阶段 I 只有 rule_v0（规则占位）；阶段 II 实现 scorecard 后，改这一行就能切换机制，
    # 决策链路代码不用动，历史决策也能靠 decisions.engine 字段区分是哪套机制算的。
    risk_engine: str = "rule_v0"

    # ---- 统一响应外壳 {code, message, data} ----
    # 业务成功时 code 返回几。前端拦截器按这个值判断成功，两边对齐即可。
    # 默认 200：前端写 if (res.code !== 200) 就直接能用；改成 0 也不用动业务代码。
    api_success_code: int = 200
    api_success_message: str = "success"

    # ---- 登录鉴权 ----
    secret_key: str = "loan-mvp-dev-secret-key-please-change"  # token 签名密钥，上线必须换
    token_ttl_seconds: int = 7 * 24 * 3600  # token 有效期：7 天

    # ---- CORS ----
    # 默认放开所有来源（前端端口还没定）；上线前收敛成 ["http://你的域名"]
    cors_origins: list[str] = ["*"]


settings = Settings()
