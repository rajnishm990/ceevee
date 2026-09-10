from app.core.exceptions import ConflictException, InvalidCredentialsException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repo import UserRepository
from app.schemas.user import TokenPair, UserCreate


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, user_in: UserCreate):
        existing = await self.user_repo.get_by_email(user_in.email)
        if existing:
            raise ConflictException("An account with this email already exists.")
        hashed = hash_password(user_in.password)
        return await self.user_repo.create(user_in, hashed)

    async def authenticate(self, email: str, password: str) -> TokenPair:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()
        return TokenPair(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise InvalidCredentialsException("Invalid or expired refresh token.") from exc

        if payload.get("type") != "refresh":
            raise InvalidCredentialsException("That isn't a refresh token.")

        user = await self.user_repo.get_by_id(int(payload["sub"]))
        if not user:
            raise InvalidCredentialsException()

        return TokenPair(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )
