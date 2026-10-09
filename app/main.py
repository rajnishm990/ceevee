from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.base import BaseModel
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT == "local":
        # Quick local bootstrap so you're not forced into Alembic for a
        # throwaway dev DB. Production always goes through real migrations
        # (see alembic/env.py) - this block only ever runs for ENVIRONMENT=local.
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
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

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
