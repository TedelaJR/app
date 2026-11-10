
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.follow_request import (
    FollowRequestResponse,
    FollowRequestActionResponse,
)
from app.schemas.follow import FollowResponse
from app.schemas.user import UserResponse, PrivacyUpdate
from app.services.follow_request_service import (
    send_follow_request,
    get_pending_requests,
    accept_follow_request,
    reject_follow_request,
    cancel_follow_request,
)
from app.services.privacy_service import update_account_privacy


router = APIRouter(tags=["Private Accounts & Follow Requests"])


@router.patch(
    "/users/me/privacy",
    response_model=UserResponse,
)
def update_privacy(
    privacy_data: PrivacyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_account_privacy(
        db,
        current_user,
        privacy_data.is_private,
    )


@router.post(
    "/users/{user_id}/follow-request",
    response_model=FollowRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_follow_request(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return send_follow_request(db, current_user, user_id)

    except ValueError as exc:
        message = str(exc)

        if message == "User not found.":
            code = status.HTTP_404_NOT_FOUND
        else:
            code = status.HTTP_409_CONFLICT

        raise HTTPException(status_code=code, detail=message)


@router.get(
    "/users/me/follow-requests",
    response_model=list[FollowRequestResponse],
)
def list_pending_requests(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_pending_requests(
        db,
        current_user.id,
        skip,
        limit,
    )


@router.post(
    "/follow-requests/{request_id}/accept",
    response_model=FollowResponse,
)
def accept_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return accept_follow_request(
            db,
            request_id,
            current_user,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post(
    "/follow-requests/{request_id}/reject",
    response_model=FollowRequestActionResponse,
)
def reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not reject_follow_request(db, request_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow request not found.",
        )

    return {"message": "Follow request rejected."}


@router.delete(
    "/follow-requests/{request_id}",
    response_model=FollowRequestActionResponse,
)
def cancel_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not cancel_follow_request(db, request_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow request not found.",
        )

    return {"message": "Follow request cancelled."}
