from fastapi import APIRouter
from sqlalchemy import text

from src.core.database import AsyncSessionFactory

router = APIRouter()


@router.get("/health")
async def health():
    async with AsyncSessionFactory() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok"}
