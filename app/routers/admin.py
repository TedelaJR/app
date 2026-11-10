from fastapi import APIRouter, Depends

from app.dependencies.permissions import require_role
from app.models.user import User

router = APIRouter()


@router.get("/dashboard")
def admin_dashboard(
    current_user: User = Depends(require_role("admin")),
):
    return {
        "message": "Welcome to the admin dashboard.",
        "admin_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
    }