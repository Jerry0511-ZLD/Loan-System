"""登录相关接口：POST /api/login、GET /api/me。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.core.response import ok
from app.core.security import create_token, verify_password, hash_password
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, ChangePasswordRequest, RegisterRequest
from app.serializers import user_to_dict

router = APIRouter(tags=["认证"])

@router.post("/register", summary="注册（用户名或手机号 + 密码）")
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    username = payload.username
    username = username.strip()
    password = payload.password
    name = payload.name

    if not username or not password or not name:
        raise HTTPException(status_code=400, detail="账号,密码和名字不能为空")

    stmt = select(func.count()).where(User.username == username)
    count = (await db.execute(stmt)).scalar_one()   # 执行 + 取出那个数字
    if count > 0:
        raise HTTPException(status_code=409, detail="当前账号已被注册")

    if len(password) < 6 or len(password) > 20:
        raise HTTPException(status_code=400, detail=f"密码位数应大于6小于20，当前密码位数为{len(password)}")

    user = User(
        username = username,
        password_hash = hash_password(password),
        name = name,
    )
    db.add(user)
    await db.commit()
    token = create_token(user.id, user.role)
    return ok({"token": token, "user": user_to_dict(user)}, message="用户注册成功")


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


@router.post("/me/password", summary="修改密码")
async def me_password(
        payload : ChangePasswordRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    if not payload.new_password:
        raise HTTPException(status_code=400, detail="新密码不能为空")

    same = verify_password(payload.old_password, user.password_hash)

    if not same:
        raise HTTPException(status_code=401, detail="密码错误")

    user.password_hash = hash_password(payload.new_password)
    await db.commit()
    return ok(user_to_dict(user))