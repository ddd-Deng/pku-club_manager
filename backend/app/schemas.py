from datetime import UTC, date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

Category = Literal["学术科技", "文化艺术", "体育竞技", "志愿服务"]
ActivityStatus = Literal["draft", "published", "unpublished", "finished"]
ActivityType = Literal["讲座", "比赛", "演出", "实践", "志愿活动"]
ApplicationStatus = Literal["pending", "approved", "rejected"]
NotificationType = Literal["application", "activity", "venue"]
Name = Annotated[str, Field(min_length=1, max_length=100)]
Password = Annotated[str, Field(min_length=6, max_length=128)]
StudentNo = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")]


class Payload(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="forbid", str_strip_whitespace=True
    )

    @model_validator(mode="before")
    @classmethod
    def reject_null(cls, data):
        if isinstance(data, dict) and any(value is None for value in data.values()):
            raise ValueError("字段不可为 null；无需修改时请省略字段")
        return data


class EmailPayload(Payload):
    @field_validator("email", check_fields=False)
    @classmethod
    def email_format(cls, value):
        if value is None:
            return value
        local, sep, domain = value.partition("@")
        if (
            not sep
            or not local
            or "." not in domain
            or "@" in domain
            or any(char.isspace() for char in value)
        ):
            raise ValueError("邮箱格式不正确")
        return value.lower()


class LoginPayload(Payload):
    account: Annotated[str, Field(min_length=1, max_length=254)]
    password: Annotated[str, Field(min_length=1, max_length=128)]
    remember: bool = False


class VerifyPayload(EmailPayload):
    student_no: StudentNo
    email: Annotated[str, Field(max_length=254)]


class RegisterPayload(VerifyPayload):
    name: Name
    password: Password


class ProfilePayload(EmailPayload):
    name: Name | None = None
    email: Annotated[str, Field(max_length=254)] | None = None
    avatar: Annotated[str, Field(min_length=1, max_length=2048)] | None = None


class PasswordPayload(Payload):
    old_password: Annotated[str, Field(min_length=1, max_length=128)]
    new_password: Password


class ClubPayload(Payload):
    name: Name | None = None
    description: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    introduction: Annotated[str, Field(max_length=50000)] | None = None
    logo: Annotated[str, Field(min_length=1, max_length=2048)] | None = None
    tags: (
        Annotated[list[Annotated[str, Field(min_length=1, max_length=30)]], Field(max_length=5)]
        | None
    ) = None


class ApplyPayload(Payload):
    message: Annotated[str, Field(max_length=200)] = ""


class ReviewPayload(Payload):
    action: Literal["approve", "reject"]
    comment: Annotated[str, Field(max_length=500)] | None = None


class MemberPayload(Payload):
    role: Literal["member", "officer"] | None = None
    action: Literal["remove"] | None = None

    @model_validator(mode="after")
    def exclusive(self):
        if (self.role is None) == (self.action is None):
            raise ValueError("role 与 action 必须且只能提供一个")
        return self


class RecruitmentPayload(Payload):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    content: Annotated[str, Field(min_length=1, max_length=50000)]
    deadline: date


class ActivityFields(Payload):
    @field_validator("start_time", "end_time", check_fields=False)
    @classmethod
    def utc_time(cls, value):
        if value is not None:
            if value.tzinfo is None:
                raise ValueError("时间必须包含时区，例如 Z 或 +08:00")
            return value.astimezone(UTC).replace(tzinfo=None)
        return value


class ActivityPayload(ActivityFields):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(min_length=1, max_length=50000)]
    location: Annotated[str, Field(min_length=1, max_length=200)]
    start_time: datetime
    end_time: datetime
    capacity: Annotated[int, Field(gt=0, le=100000)]
    type: ActivityType
    cover: Annotated[str, Field(min_length=1, max_length=2048)] = "🎯"
    club_id: Annotated[str, Field(min_length=1, max_length=36)] | None = None


class ActivityPatch(ActivityFields):
    title: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    description: Annotated[str, Field(min_length=1, max_length=50000)] | None = None
    location: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    capacity: Annotated[int, Field(gt=0, le=100000)] | None = None
    type: ActivityType | None = None
    cover: Annotated[str, Field(min_length=1, max_length=2048)] | None = None
    club_id: Annotated[str, Field(min_length=1, max_length=36)] | None = None
