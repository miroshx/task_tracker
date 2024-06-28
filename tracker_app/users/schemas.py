from typing import Optional, Literal

from pydantic import BaseModel

from tracker_app.models import UserRole


class SUser(BaseModel):
    username: str
    password: str

    class Config:
        orm_mode = True


class SUserChangePassword(BaseModel):
    password: str
    new_password: str

    class Config:
        orm_mode = True


class SUserChangeRole(BaseModel):
    role: Literal['manager', 'team_lead', 'developer', 'test_engineer']
