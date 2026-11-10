
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    verify_password,
)
from app.core.config import settings
from app.models.user import User
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, update

from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    get_refresh_token_expiry,
)
from app.core.config import settings
from app.models.refresh_token import RefreshToken


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    if not user.is_active:
        return None

    return user


def create_user_access_token(user: User) -> dict:
    access_token = create_access_token(
        subject=str(user.id)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def _build_token_pair(
    user: User,
    raw_refresh_token: str,
) -> dict:
    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": raw_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def issue_token_pair(
    db: Session,
    user: User,
) -> dict:
    raw_token = generate_refresh_token()

    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        family_id=str(uuid4()),
        expires_at=get_refresh_token_expiry(),
    )

    try:
        db.add(refresh_record)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return _build_token_pair(user, raw_token)


def rotate_refresh_token(
    db: Session,
    raw_token: str,
) -> dict:
    token_hash = hash_refresh_token(raw_token)

    old_record = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
    )

    if old_record is None:
        raise ValueError("Invalid refresh token.")

    now = datetime.now(timezone.utc)

    # Reuse of a rotated token means its session is compromised.
    if old_record.revoked_at is not None:
        db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == old_record.family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        db.commit()
        raise ValueError("Refresh token reuse detected. Please log in again.")

    if old_record.expires_at <= now:
        old_record.revoked_at = now
        db.commit()
        raise ValueError("Refresh token has expired.")

    user = db.get(User, old_record.user_id)

    if user is None or not user.is_active:
        old_record.revoked_at = now
        db.commit()
        raise ValueError("User account is unavailable.")

    new_raw_token = generate_refresh_token()

    new_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_raw_token),
        family_id=old_record.family_id,
        expires_at=get_refresh_token_expiry(),
    )

    try:
        old_record.revoked_at = now
        db.add(new_record)
        db.flush()

        old_record.replaced_by_token_id = new_record.id

        db.commit()
    except Exception:
        db.rollback()
        raise

    return _build_token_pair(user, new_raw_token)


def revoke_refresh_token(
    db: Session,
    raw_token: str,
) -> None:
    token_hash = hash_refresh_token(raw_token)

    record = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
    )

    if record and record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
        db.commit()


def revoke_all_user_tokens(
    db: Session,
    user_id: int,
) -> None:
    db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )
    db.commit()
