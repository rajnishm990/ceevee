from fastapi import APIRouter, Depends, Request

from app.api.deps import get_user_repo
from app.core.rate_limit import limiter
from app.repositories.user_repo import UserRepository
from app.schemas.user import RefreshRequest, TokenPair, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("10/minute")
async def register(request: Request, payload: UserCreate, user_repo: UserRepository = Depends(get_user_repo)):
    return await AuthService(user_repo).register(payload)


@router.post("/login", response_model=TokenPair)
@limiter.limit("10/minute")
async def login(request: Request, payload: UserLogin, user_repo: UserRepository = Depends(get_user_repo)):
    return await AuthService(user_repo).authenticate(payload.email, payload.password)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, user_repo: UserRepository = Depends(get_user_repo)):
    return await AuthService(user_repo).refresh(payload.refresh_token)
