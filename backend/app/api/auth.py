"""登录相关接口：POST /api/login、GET /api/me。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.core.response import ok
from app.core.security import create_token, verify_password
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest
from app.serializers import user_to_dict

router = APIRouter(tags=["认证"])


@router.post("/login", summary="登录（用户名或手机号 + 密码）")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    account = (payload.username or "").strip()
    password = payload.password or ""
    if not account or not password:
        raise HTTPException(status_code=400, detail="账号和密码不能为空")

    stmt = select(User).where(or_(User.username == account, User.phone == account))
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")

    token = create_token(user.id, user.role)
    return ok(
        {
            "token": token,
            "tokenType": "Bearer",
            "expiresIn": settings.token_ttl_seconds,
            "user": user_to_dict(user),
        },
        message="登录成功",
    )


@router.get("/me", summary="当前登录用户信息")
async def me(user: User = Depends(get_current_user)):
    return ok(user_to_dict(user))
