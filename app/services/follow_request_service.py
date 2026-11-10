
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.follow import Follow
from app.models.follow_request import FollowRequest
from app.models.user import User


def send_follow_request(
    db: Session,
    requester: User,
    target_id: int,
):
    if requester.id == target_id:
        raise ValueError("You cannot send a follow request to yourself.")

    target = db.scalar(
        select(User).where(User.id == target_id)
    )

    if target is None:
        raise ValueError("User not found.")

    if not target.is_active:
        raise ValueError("This account is unavailable.")

    if not target.is_private:
        raise ValueError("This account is public. Follow directly.")

    existing_follow = db.scalar(
        select(Follow).where(
            Follow.follower_id == requester.id,
            Follow.following_id == target_id,
        )
    )

    if existing_follow:
        raise ValueError("You are already following this user.")

    existing_request = db.scalar(
        select(FollowRequest).where(
            FollowRequest.requester_id == requester.id,
            FollowRequest.target_id == target_id,
        )
    )

    if existing_request:
        raise ValueError("A follow request is already pending.")

    follow_request = FollowRequest(
        requester_id=requester.id,
        target_id=target_id,
    )

    try:
        db.add(follow_request)
        db.commit()
        db.refresh(follow_request)
        return follow_request

    except IntegrityError:
        db.rollback()
        raise ValueError("A follow request is already pending.")

    except Exception:
        db.rollback()
        raise


def get_pending_requests(
    db: Session,
    target_id: int,
    skip: int = 0,
    limit: int = 20,
):
    return db.scalars(
        select(FollowRequest)
        .where(FollowRequest.target_id == target_id)
        .order_by(
            FollowRequest.created_at.desc(),
            FollowRequest.id.desc(),
        )
        .offset(skip)
        .limit(limit)
    ).all()


def accept_follow_request(
    db: Session,
    request_id: int,
    current_user: User,
):
    follow_request = db.scalar(
        select(FollowRequest).where(
            FollowRequest.id == request_id,
            FollowRequest.target_id == current_user.id,
        )
    )

    if follow_request is None:
        raise ValueError("Follow request not found.")

    new_follow = Follow(
        follower_id=follow_request.requester_id,
        following_id=follow_request.target_id,
    )

    try:
        db.add(new_follow)
        db.delete(follow_request)
        db.commit()
        db.refresh(new_follow)
        return new_follow

    except IntegrityError:
        db.rollback()
        raise ValueError("A follow relationship already exists.")

    except Exception:
        db.rollback()
        raise


def reject_follow_request(
    db: Session,
    request_id: int,
    current_user: User,
) -> bool:
    follow_request = db.scalar(
        select(FollowRequest).where(
            FollowRequest.id == request_id,
            FollowRequest.target_id == current_user.id,
        )
    )

    if follow_request is None:
        return False

    try:
        db.delete(follow_request)
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise


def cancel_follow_request(
    db: Session,
    request_id: int,
    current_user: User,
) -> bool:
    follow_request = db.scalar(
        select(FollowRequest).where(
            FollowRequest.id == request_id,
            FollowRequest.requester_id == current_user.id,
        )
    )

    if follow_request is None:
        return False

    try:
        db.delete(follow_request)
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise
