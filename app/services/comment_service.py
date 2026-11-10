from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentUpdate


def create_comment(
    db: Session,
    post_id: int,
    comment_data: CommentCreate,
    current_user: User,
) -> Comment:
    """Create a comment on an existing post."""

    post = db.get(Post, post_id)

    if post is None:
        raise ValueError("Post not found.")

    new_comment = Comment(
        user_id=current_user.id,
        post_id=post_id,
        content=comment_data.content,
    )

    try:
        db.add(new_comment)
        db.commit()
        db.refresh(new_comment)
        return new_comment
    except Exception:
        db.rollback()
        raise


def get_comments(
    db: Session,
    post_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[Comment]:
    """Retrieve comments for a post with pagination."""

    post = db.get(Post, post_id)

    if post is None:
        raise ValueError("Post not found.")

    statement = (
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def update_comment(
    db: Session,
    comment_id: int,
    comment_data: CommentUpdate,
    current_user: User,
) -> Comment | None:
    """Update a comment only if it belongs to the current user."""

    comment = db.scalar(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.user_id == current_user.id,
        )
    )

    if comment is None:
        return None

    update_data = comment_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(comment, field, value)

    try:
        db.commit()
        db.refresh(comment)
        return comment
    except Exception:
        db.rollback()
        raise


def delete_comment(
    db: Session,
    comment_id: int,
    current_user: User,
) -> bool:
    """Delete a comment only if it belongs to the current user."""

    comment = db.scalar(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.user_id == current_user.id,
        )
    )

    if comment is None:
        return False

    try:
        db.delete(comment)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise