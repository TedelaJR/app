
from sqlalchemy.orm import Session

from app.models.user import User


def update_account_privacy(
    db: Session,
    user: User,
    is_private: bool,
) -> User:
    user.is_private = is_private

    try:
        db.commit()
        db.refresh(user)
        return user

    except Exception:
        db.rollback()
        raise
