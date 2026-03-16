from datetime import datetime, time

from pydantic import BaseModel, Field, model_validator


class ScheduleRuleRead(BaseModel):
    id: int
    weekday: int
    start_time: time
    end_time: time
    is_active: bool

    model_config = {"from_attributes": True}


class ScheduleRuleCreate(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    is_active: bool = True

    @model_validator(mode="after")
    def validate_interval(self) -> "ScheduleRuleCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self


class ScheduleRuleUpdate(BaseModel):
    weekday: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    is_active: bool | None = None


class BlockedIntervalRead(BaseModel):
    id: int
    start_at: datetime
    end_at: datetime
    reason: str | None

    model_config = {"from_attributes": True}


class BlockedIntervalCreate(BaseModel):
    start_at: datetime
    end_at: datetime
    reason: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_interval(self) -> "BlockedIntervalCreate":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be greater than start_at")
        return self


class BlockedIntervalUpdate(BaseModel):
    start_at: datetime | None = None
    end_at: datetime | None = None
    reason: str | None = Field(default=None, max_length=255)

