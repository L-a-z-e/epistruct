from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.exceptions import register_exception_handlers
from src.modules.auth.presentation.router import router as auth_router
from src.modules.knowledge.presentation.router import router as knowledge_router
from src.modules.space.presentation.router import router as space_router
from src.modules.ai_pipeline.presentation.router import router as pipeline_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


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

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(knowledge_router, prefix="/api/v1")
    app.include_router(space_router, prefix="/api/v1")
    app.include_router(pipeline_router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
