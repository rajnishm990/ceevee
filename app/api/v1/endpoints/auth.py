from fastapi import APIRouter, Depends, Request , status

from app.api.deps import get_user_repo , get_current_user, get_account_service
from app.core.rate_limit import limiter
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import RefreshRequest, TokenPair, UserCreate, UserLogin, UserResponse , DeleteAccountRequest
from app.services.auth_service import AuthService
from app.services.account_service import AccountService


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

@router.get("/me", response_model=UserResponse)
async def me(current_user:User = Depends(get_current_user)):
    return current_user 

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_me(request:Request , payload: DeleteAccountRequest , current_user: User = Depends(get_current_user), service: AccountService = Depends(get_account_service)):
    await service.delete_account(current_user , payload.password)