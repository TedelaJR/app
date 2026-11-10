
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FollowRequestResponse(BaseModel):
    id: int
    requester_id: int
    target_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FollowRequestActionResponse(BaseModel):
    message: str
