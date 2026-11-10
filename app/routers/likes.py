from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services import like_service


router = APIRouter(
    prefix="/posts",
    tags=["Likes"],
)


@router.post(
    "/{post_id}/like",
    status_code=status.HTTP_201_CREATED,
)
def like_existing_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        like = like_service.like_post(
            db=db,
            post_id=post_id,
            current_user=current_user,
        )
    except ValueError as exc:
        if str(exc) == "Post not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return {
        "message": "Post liked successfully.",
        "like_id": like.id,
    }


@router.delete(
    "/{post_id}/like",
    status_code=status.HTTP_200_OK,
)
def unlike_existing_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    unliked = like_service.unlike_post(
        db=db,
        post_id=post_id,
        current_user=current_user,
    )

    if not unliked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found.",
        )

    return {
        "message": "Post unliked successfully."
    }


@router.get(
    "/{post_id}/likes/count",
)
def read_post_like_count(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = like_service.get_post_like_count(
        db=db,
        post_id=post_id,
    )

    return {
        "post_id": post_id,
        "like_count": count,
    }


@router.get(
    "/{post_id}/likes/me",
)
def check_my_like_status(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    liked = like_service.has_user_liked_post(
        db=db,
        post_id=post_id,
        current_user=current_user,
    )

    return {
        "post_id": post_id,
        "liked": liked,
    }