"""Authentication endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.middleware.auth import (
    CurrentUser,
    authenticate,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class UserView(BaseModel):
    username: str
    roles: list[str]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserView


def _build_response(user: CurrentUser) -> LoginResponse:
    token, expires_in = create_access_token(user)
    return LoginResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserView(username=user.username, roles=user.roles),
    )


@router.post("/login", response_model=LoginResponse)
async def login_json(payload: LoginRequest) -> LoginResponse:
    user = authenticate(payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return _build_response(user)


@router.post("/login/form", response_model=LoginResponse)
async def login_form(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> LoginResponse:
    user = authenticate(form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return _build_response(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(_: Annotated[CurrentUser, Depends(get_current_user)]) -> None:
    # Stateless JWT: the client just discards the token.
    return None


@router.get("/me", response_model=UserView)
async def me(user: Annotated[CurrentUser, Depends(get_current_user)]) -> UserView:
    return UserView(username=user.username, roles=user.roles)
