from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.database import SessionFactory
from app.redis_client import create_redis

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(response: Response) -> dict[str, object]:
    checks: dict[str, bool] = {"postgres": False, "redis": False}
    try:
        async with SessionFactory() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = True
    except Exception:
        pass
    redis = create_redis()
    try:
        checks["redis"] = bool(await redis.ping())
    except Exception:
        pass
    finally:
        await redis.aclose()
    if not all(checks.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if all(checks.values()) else "degraded", "checks": checks}
