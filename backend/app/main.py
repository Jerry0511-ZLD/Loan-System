"""应用入口：注册路由、CORS、统一响应外壳的异常处理。

启动：在 backend 目录下执行 `python run.py`（或 uvicorn app.main:app --port 8080）
接口文档：http://127.0.0.1:8080/docs
"""

import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.applications import router as applications_router
from app.api.auth import router as auth_router
from app.api.loans import router as loans_router
from app.api.products import router as products_router
from app.config import settings
from app.database import init_db
from app.seed import seed_all


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()   # MVP：启动即建表
    await seed_all()  # 演示数据（幂等，已存在就跳过）
    yield


# debug 固定 False：这样 500 也走统一外壳。debug=True 时 Starlette 会直接回 HTML 堆栈页，
# 前端解析不了。要看堆栈看下面 500 处理器打印的控制台输出；想打印 SQL 改 .env 里的 DEBUG=true。
app = FastAPI(title=settings.app_name, debug=False, lifespan=lifespan)

# CORS：允许前端跨域调（默认放开所有来源，上线前把 .env 的 CORS_ORIGINS 收敛成具体域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,  # 用的是 Bearer token，不需要带 cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

# 所有业务接口统一挂在 /api 前缀下（前端 baseURL 就是 http://localhost:8080/api）
app.include_router(auth_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(loans_router, prefix="/api")
app.include_router(applications_router, prefix="/api")


@app.get("/health", summary="健康检查（不套响应外壳）")
async def health():
    return {"status": "ok"}


# ---- 统一错误外壳：/api 下任何报错，前端拿到的都是 {code, message, data:null} ----

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """业务错误：code 直接用 HTTP 状态码（400/401/403/404...）。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": str(exc.detail), "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数校验失败：定位到具体字段，方便前端排查。"""
    errors = exc.errors()
    message = "参数校验失败"
    if errors:
        first = errors[0]
        loc = first.get("loc", [])
        field = ".".join(str(x) for x in loc if x not in ("body", "query", "path"))
        message = f"参数校验失败：{field} {first.get('msg', '')}"
    return JSONResponse(
        status_code=422, content={"code": 422, "message": message, "data": None}
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """兜底：未预期的异常不把堆栈甩给前端，只在控制台打印。"""
    traceback.print_exc()
    return JSONResponse(
        status_code=500, content={"code": 500, "message": "服务器内部错误", "data": None}
    )
