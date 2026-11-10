from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.refresh_token import RefreshToken


def deactivate_account(db: Session, user: User) -> User:
    user.is_active = False

    db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )

    db.commit()
    db.refresh(user)

    return user


def reactivate_account(db: Session, user: User) -> User:
    user.is_active = True

    db.commit()
    db.refresh(user)

    return user

def delete_account(db: Session, user: User) -> None:
    try:
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise