"""密码哈希 + 登录 token（只用标准库，不引第三方包）。

- 密码：pbkdf2_hmac(sha256) 加盐哈希，数据库里不存明文。
- token：形如 "载荷.签名" 的字符串（思路和 JWT 一样，但不是标准 JWT）。
  载荷 = base64url({"uid": 用户id, "role": 角色, "exp": 过期时间戳})
  签名 = HMAC-SHA256(secret_key, 载荷) 的十六进制
  前端拿到后放进请求头：Authorization: Bearer <token>
"""

import base64
import hashlib
import hmac
import json
import secrets
import time

from app.config import settings

PBKDF2_ROUNDS = 200_000


# ---- 密码 ----

def hash_password(password: str) -> str:
    """把明文密码变成 "pbkdf2_sha256$轮数$盐$哈希" 存库。"""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ROUNDS
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """校验明文密码和库里的哈希是否匹配。"""
    parts = (stored or "").split("$")
    if len(parts) != 4:
        return False
    _, rounds, salt, digest = parts
    try:
        calc = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(rounds)
        ).hex()
    except ValueError:
        return False
    return hmac.compare_digest(calc, digest)


# ---- token ----

def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _sign(body: str) -> str:
    return hmac.new(
        settings.secret_key.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def create_token(user_id: str, role: str, ttl_seconds: int | None = None) -> str:
    """签发 token。"""
    ttl = settings.token_ttl_seconds if ttl_seconds is None else ttl_seconds
    payload = {"uid": user_id, "role": role, "exp": int(time.time()) + ttl}
    body = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{body}.{_sign(body)}"


def parse_token(token: str) -> dict | None:
    """校验签名和过期时间。通过返回 payload，否则返回 None。"""
    parts = (token or "").split(".")
    if len(parts) != 2:
        return None
    body, signature = parts
    if not hmac.compare_digest(signature, _sign(body)):
        return None
    try:
        payload = json.loads(_b64decode(body))
    except Exception:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload
