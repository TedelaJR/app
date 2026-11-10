
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.follow import Follow
from app.models.user import User


def follow_user(
    db: Session,
    follower: User,
    following_id: int,
) -> Follow:
    # Prevent following yourself.
    if follower.id == following_id:
        raise ValueError("You cannot follow yourself.")

    target_user = db.scalar(
        select(User).where(User.id == following_id)
    )

    if target_user is None:
        raise ValueError("User not found.")
    
    if not target_user.is_active:
        raise ValueError("This account is unavailable.")

    if target_user.is_private:
        raise ValueError(
            "This account is private. Send a follow request instead."
    )

    # Prevent duplicate follows.
    existing_follow = db.scalar(
        select(Follow).where(
            Follow.follower_id == follower.id,
            Follow.following_id == following_id,
        )
    )

    if existing_follow:
        raise ValueError("You are already following this user.")

    new_follow = Follow(
        follower_id=follower.id,
        following_id=following_id,
    )

    try:
        db.add(new_follow)
        db.commit()
        db.refresh(new_follow)
        return new_follow

    except IntegrityError:
        db.rollback()
        raise ValueError("You are already following this user.")

    except Exception:
        db.rollback()
        raise


def unfollow_user(
    db: Session,
    follower: User,
    following_id: int,
) -> bool:
    existing_follow = db.scalar(
        select(Follow).where(
            Follow.follower_id == follower.id,
            Follow.following_id == following_id,
        )
    )

    if existing_follow is None:
        return False

    try:
        db.delete(existing_follow)
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise


def get_followers(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
):
    return db.scalars(
        select(Follow)
        .where(Follow.following_id == user_id)
        .order_by(Follow.created_at.desc(), Follow.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()


def get_following(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
):
    return db.scalars(
        select(Follow)
        .where(Follow.follower_id == user_id)
        .order_by(Follow.created_at.desc(), Follow.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()


def is_following(
    db: Session,
    follower_id: int,
    following_id: int,
) -> bool:
    return db.scalar(
        select(Follow.id).where(
            Follow.follower_id == follower_id,
            Follow.following_id == following_id,
        )
    ) is not None


def get_follow_counts(
    db: Session,
    user_id: int,
) -> dict:
    followers_count = db.scalar(
        select(func.count(Follow.id)).where(
            Follow.following_id == user_id
        )
    ) or 0

    following_count = db.scalar(
        select(func.count(Follow.id)).where(
            Follow.follower_id == user_id
        )
    ) or 0

    return {
        "user_id": user_id,
        "followers_count": followers_count,
        "following_count": following_count,
    }
