
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FollowResponse(BaseModel):
    id: int
    follower_id: int
    following_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FollowStatusResponse(BaseModel):
    user_id: int
    is_following: bool


class FollowCountResponse(BaseModel):
    user_id: int
    followers_count: int
    following_count: int
