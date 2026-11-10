from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate


def create_post(
    db: Session,
    post_data: PostCreate,
    current_user: User,
) -> Post:
    """Create a post belonging to the authenticated user."""

    new_post = Post(
        user_id=current_user.id,
        content=post_data.content,
        image_url=post_data.image_url,
    )

    try:
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except Exception:
        db.rollback()
        raise


def get_post_by_id(
    db: Session,
    post_id: int,
) -> Post | None:
    """Retrieve a post by its ID."""

    return db.scalar(
        select(Post).where(Post.id == post_id)
    )


def get_posts(
    db: Session,
    skip: int = 0,
    limit: int = 20,
) -> list[Post]:
    """Retrieve posts with pagination, newest first."""

    statement = (
        select(Post)
        .order_by(Post.created_at.desc(), Post.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def update_post(
    db: Session,
    post_id: int,
    post_data: PostUpdate,
    current_user: User,
) -> Post | None:
    """Update a post only if it belongs to the authenticated user."""

    post = db.scalar(
        select(Post).where(
            Post.id == post_id,
            Post.user_id == current_user.id,
        )
    )

    if post is None:
        return None

    update_data = post_data.model_dump(exclude_unset=True)

    # Content cannot be null because the database requires it.
    if "content" in update_data and update_data["content"] is None:
        raise ValueError("Post content cannot be null.")

    for field, value in update_data.items():
        setattr(post, field, value)

    try:
        db.commit()
        db.refresh(post)
        return post
    except Exception:
        db.rollback()
        raise


def delete_post(
    db: Session,
    post_id: int,
    current_user: User,
) -> bool:
    """Delete a post only if it belongs to the authenticated user."""

    post = db.scalar(
        select(Post).where(
            Post.id == post_id,
            Post.user_id == current_user.id,
        )
    )

    if post is None:
        return False

    try:
        db.delete(post)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise