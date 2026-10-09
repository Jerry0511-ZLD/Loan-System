from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.applications import router as applications_router
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()  # MVP: 启动即建表
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.include_router(applications_router, prefix="/api/v1")


@app.get("/health", summary="健康检查")
async def health():
    return {"status": "ok"}
