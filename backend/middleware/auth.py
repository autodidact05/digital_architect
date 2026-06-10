"""JWT auth with bcrypt-hashed hardcoded users.

Users come from the `AUTH_USERS` env var (`user:password,user2:password2`).
At process startup their passwords are bcrypt-hashed into memory; the
plaintext is never stored on disk. Tokens are HS256 with an 8h expiry.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.config import settings


def _hash_password(plaintext: str) -> bytes:
    # bcrypt has a 72-byte limit; truncate to be safe for arbitrarily long
    # passwords passed via env vars.
    pw = plaintext.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12))


def _verify_password(plaintext: str, hashed: bytes) -> bool:
    pw = plaintext.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(pw, hashed)
    except ValueError:
        return False

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


class TokenPayload(BaseModel):
    sub: str
    roles: list[str]


class CurrentUser(BaseModel):
    username: str
    roles: list[str]


_HASHED_USERS: dict[str, bytes] = {}


def init_user_store() -> None:
    """Bcrypt-hash all configured users into the in-memory store."""
    _HASHED_USERS.clear()
    for username, password in settings.parsed_auth_users.items():
        _HASHED_USERS[username] = _hash_password(password)


def authenticate(username: str, password: str) -> CurrentUser | None:
    hashed = _HASHED_USERS.get(username)
    if hashed is None or not _verify_password(password, hashed):
        return None
    roles = ["developer"]
    if username in settings.admin_user_set:
        roles.insert(0, "admin")
    return CurrentUser(username=username, roles=roles)


def create_access_token(user: CurrentUser) -> tuple[str, int]:
    expires_in_seconds = settings.jwt_expiry_hours * 3600
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
    payload = {
        "sub": user.username,
        "roles": user.roles,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in_seconds


def decode_token(token: str) -> CurrentUser:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    username = payload.get("sub")
    roles = payload.get("roles") or []
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token",
        )
    return CurrentUser(username=username, roles=roles)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> CurrentUser:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(token)


async def require_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if "admin" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user
