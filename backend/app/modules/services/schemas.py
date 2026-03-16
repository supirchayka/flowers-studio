from pydantic import BaseModel, Field


class ServiceRead(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    duration_minutes: int
    price_minor: int
    currency: str
    is_active: bool
    is_archived: bool

    model_config = {"from_attributes": True}


class ServiceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=10)
    duration_minutes: int = Field(ge=30, le=720)
    price_minor: int = Field(ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    is_active: bool = True


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, min_length=10)
    duration_minutes: int | None = Field(default=None, ge=30, le=720)
    price_minor: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    is_active: bool | None = None
    is_archived: bool | None = None

