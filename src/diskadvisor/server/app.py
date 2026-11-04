"""FastAPI 应用。"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from diskadvisor import __version__
from diskadvisor.server.routes import (
    advise,
    execute,
    journal,
    kb,
    recommend,
    scan,
)
import sys

if getattr(sys, "frozen", False):
    STATIC_DIR = Path(sys._MEIPASS) / "diskadvisor" / "server" / "static"  # type: ignore[attr-defined]
else:
    STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    """创建 FastAPI 应用。"""
    app = FastAPI(
        title="DiskAdvisor",
        version=__version__,
        description="Windows 磁盘空间规划顾问",
    )

    # API 路由
    app.include_router(scan.router, prefix="/api", tags=["scan"])
    app.include_router(recommend.router, prefix="/api", tags=["recommend"])
    app.include_router(advise.router, prefix="/api", tags=["advise"])
    app.include_router(execute.router, prefix="/api", tags=["execute"])
    app.include_router(journal.router, prefix="/api", tags=["journal"])
    app.include_router(kb.router, prefix="/api", tags=["kb"])

    # 静态资源
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        """返回首页。"""
        index_path = STATIC_DIR / "index.html"
        if not index_path.exists():
            raise FileNotFoundError("index.html 不存在")
        return FileResponse(str(index_path))

    @app.get("/api/version")
    async def version() -> dict[str, str]:
        """返回版本号。"""
        return {"version": __version__}

    return app