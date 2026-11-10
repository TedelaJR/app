
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.follow import (
    FollowResponse,
    FollowStatusResponse,
    FollowCountResponse,
)
from app.services.follow_service import (
    follow_user,
    unfollow_user,
    get_followers,
    get_following,
    is_following,
    get_follow_counts,
)

router = APIRouter(prefix="/users", tags=["Follows"])


@router.post(
    "/{user_id}/follow",
    response_model=FollowResponse,
    status_code=status.HTTP_201_CREATED,
)
def follow(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return follow_user(db, current_user, user_id)
    except ValueError as exc:
        message = str(exc)

        if message == "User not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )


@router.delete(
    "/{user_id}/follow",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unfollow(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not unfollow_user(db, current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow relationship not found.",
        )

    return None


@router.get(
    "/{user_id}/followers",
    response_model=list[FollowResponse],
)
def followers(
    user_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return get_followers(db, user_id, skip, limit)


@router.get(
    "/{user_id}/following",
    response_model=list[FollowResponse],
)
def following(
    user_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return get_following(db, user_id, skip, limit)


@router.get(
    "/{user_id}/follow-status",
    response_model=FollowStatusResponse,
)
def follow_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return {
        "user_id": user_id,
        "is_following": is_following(
            db,
            current_user.id,
            user_id,
        ),
    }


@router.get(
    "/{user_id}/follow-counts",
    response_model=FollowCountResponse,
)
def follow_counts(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return get_follow_counts(db, user_id)
