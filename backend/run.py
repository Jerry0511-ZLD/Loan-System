"""本地启动入口。

在 backend 目录下执行：
    python run.py

等价于：
    uvicorn app.main:app --reload --port 8080

端口用 8080 是和前端约定好的（前端 baseURL = http://localhost:8080/api）。
想让同一个局域网的手机/其他电脑访问，把下面的 host 改成 "0.0.0.0"。
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
