
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password
from app.schemas.user import UserUpdate


def register_user(
    db: Session, 
    user_data: UserCreate
) -> User:
    # Check whether the username or email already exists.
    existing_user = db.scalar(
        select(User).where(
            (User.username == user_data.username)
            | (User.email == user_data.email)
        )
    )

    if existing_user:
        if existing_user.username == user_data.username:
            raise ValueError("Username is already taken.")

        raise ValueError("Email is already registered.")

    # Hash the password before storing it.
    hashed_password = hash_password(user_data.password)

    new_user = User(
        username=user_data.username,
        email=str(user_data.email),
        hashed_password=hashed_password,
        full_name=user_data.full_name,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    return new_user


def update_user_profile(
    db: Session,
    user: User,
    user_data: UserUpdate,
) -> User:
    updates = user_data.model_dump(exclude_unset=True)

    if not updates:
        raise ValueError("No profile fields provided.")

    for field, value in updates.items():
        setattr(user, field, value)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return user


def change_user_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    if not verify_password(
        current_password,
        user.hashed_password,
    ):
        raise ValueError("Current password is incorrect.")

    user.hashed_password = hash_password(new_password)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise
