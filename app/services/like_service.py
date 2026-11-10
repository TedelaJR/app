from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.like import Like
from app.models.post import Post
from app.models.user import User


def like_post(
    db: Session,
    post_id: int,
    current_user: User,
) -> Like:
    """Like a post if it exists and hasn't already been liked."""

    post = db.get(Post, post_id)

    if post is None:
        raise ValueError("Post not found.")

    existing_like = db.scalar(
        select(Like).where(
            Like.post_id == post_id,
            Like.user_id == current_user.id,
        )
    )

    if existing_like:
        raise ValueError("You have already liked this post.")

    new_like = Like(
        user_id=current_user.id,
        post_id=post_id,
    )

    try:
        db.add(new_like)
        db.commit()
        db.refresh(new_like)
        return new_like
    except IntegrityError:
        db.rollback()
        raise ValueError("You have already liked this post.") from None
    except Exception:
        db.rollback()
        raise


def unlike_post(
    db: Session,
    post_id: int,
    current_user: User,
) -> bool:
    """Remove a like belonging to the authenticated user."""

    existing_like = db.scalar(
        select(Like).where(
            Like.post_id == post_id,
            Like.user_id == current_user.id,
        )
    )

    if existing_like is None:
        return False

    try:
        db.delete(existing_like)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def get_post_like_count(
    db: Session,
    post_id: int,
) -> int:
    """Return the total number of likes on a post."""

    return db.scalar(
        select(func.count(Like.id)).where(
            Like.post_id == post_id
        )
    ) or 0


def has_user_liked_post(
    db: Session,
    post_id: int,
    current_user: User,
) -> bool:
    """Check whether the authenticated user liked a post."""

    return db.scalar(
        select(Like.id).where(
            Like.post_id == post_id,
            Like.user_id == current_user.id,
        )
    ) is not None