
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database.session import get_db
from app.schemas.user import UserLogin, TokenResponse
from app.services.auth_service import (
    authenticate_user,
    issue_token_pair,
    rotate_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
)

from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
)
from app.services.user_service import register_user
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        return register_user(db, user_data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

@router.post("/login", response_model=TokenResponse)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db=db,
        email=str(login_data.email),
        password=login_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cresdentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return issue_token_pair(
        db=db,
        user=user,
    )

@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_tokens(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    try:
        return rotate_refresh_token(
            db=db,
            raw_token=token_data.refresh_token,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout")
def logout(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    revoke_refresh_token(
        db=db,
        raw_token=token_data.refresh_token,
    )

    return {"message": "Logged out successfully."}


@router.post("/logout-all")
def logout_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    revoke_all_user_tokens(
        db=db,
        user_id=current_user.id,
    )

    return {"message": "Logged out from all sessions successfully."}
