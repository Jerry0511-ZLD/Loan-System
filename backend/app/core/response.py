"""统一响应外壳：{code, message, data}

约定（前端按这个对接，见 backend/API.md）：
- 成功：路由里 `return ok(data)` 或 `return ok(data, "申请已提交")`
- 失败：路由里 `raise HTTPException(400, "金额不能为负")`，
  由 main.py 里的异常处理器转成同样的外壳 {code: 400, message: "...", data: null}
"""

from typing import Any

from app.config import settings


def ok(data: Any = None, message: str | None = None) -> dict:
    """成功返回。code 取 settings.api_success_code（默认 200）。"""
    return {
        "code": settings.api_success_code,
        "message": settings.api_success_message if message is None else message,
        "data": data,
    }


def fail(code: int, message: str, data: Any = None) -> dict:
    """失败返回。主要给异常处理器复用。"""
    return {"code": code, "message": message, "data": data}


def page_data(rows: list, total: int, page: int, page_size: int) -> dict:
    """分页外壳。list 和 items 是同一份数组，前端写 list 还是 items 都能拿到。"""
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "list": rows,
        "items": rows,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages,
    }
