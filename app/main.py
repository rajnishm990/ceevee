import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI , Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware 

from sqlalchemy import text 
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.base import BaseModel
from app.db.session import engine 
from app.db.migrate import upgrade_to_head
from app.db.session import get_db 




@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.AUTO_MIGRATE:
        await asyncio.to_thread(upgrade_to_head)
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ALLOWED_HOSTS!=["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[*settings.ALLOWED_HOSTS, "localhost", "127.0.0.1"])


app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}

@app.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ready"} 