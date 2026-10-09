from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Application, Decision
from app.schemas import ApplicationCreate, ApplicationOut, DecisionOut
from app.services.decision import run_decision

router = APIRouter()


@router.post("/applications", response_model=DecisionOut, summary="提交进件并即时决策")
async def create_application(payload: ApplicationCreate, db: AsyncSession = Depends(get_db)):
    application = Application(**payload.model_dump())
    db.add(application)
    await db.flush()  # 生成 application.id
    decision = await run_decision(application, db)
    return decision


@router.get("/applications/{app_id}", response_model=ApplicationOut, summary="查询申请单")
async def get_application(app_id: str, db: AsyncSession = Depends(get_db)):
    application = await db.get(Application, app_id)
    if not application:
        raise HTTPException(status_code=404, detail="申请不存在")
    return application


@router.get("/applications/{app_id}/decision", response_model=DecisionOut, summary="查询决策结果")
async def get_decision(app_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Decision).where(Decision.application_id == app_id)
    result = await db.execute(stmt)
    decision = result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="决策不存在")
    return decision
