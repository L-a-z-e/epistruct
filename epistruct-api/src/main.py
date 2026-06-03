from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import engine
from src.core.exceptions import register_exception_handlers
from src.core.router import router as core_router
from src.modules.ai_pipeline.router import router as pipeline_router
from src.modules.auth.router import router as auth_router
from src.modules.knowledge.router import router as knowledge_router
from src.modules.space.router import router as space_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect():  # 시작 시 DB 연결 가능 여부 확인
        pass
    yield
    await engine.dispose()  # 종료 시 연결 풀 반납


def create_app() -> FastAPI:
    app = FastAPI(
        title="Epistruct API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env == "development" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(core_router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(knowledge_router, prefix="/api/v1")
    app.include_router(space_router, prefix="/api/v1")
    app.include_router(pipeline_router, prefix="/api/v1")

    return app


app = create_app()
