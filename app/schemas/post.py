from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    image_url: str | None = Field(default=None, max_length=500)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Post content cannot be empty.")

        return value


class PostUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    image_url: str | None = Field(default=None, max_length=500)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("Post content cannot be empty.")

        return value

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")

        return self


class PostResponse(BaseModel):
    id: int
    user_id: int
    content: str
    image_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)