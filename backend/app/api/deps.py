"""公共依赖：从请求头解析当前登录用户、校验管理员权限。

用法：路由函数参数写 `user: User = Depends(get_current_user)`，
没带 token / token 过期时自动返回 401（统一外壳）。
"""

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import parse_token
from app.database import get_db
from app.models import User


async def get_current_user(
    authorization: str | None = Header(default=None, description="Bearer <token>"),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未登录或缺少 Bearer token")
    token = authorization[7:].strip()
    payload = parse_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")
    user = await db.get(User, payload.get("uid"))
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在，请重新登录")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
