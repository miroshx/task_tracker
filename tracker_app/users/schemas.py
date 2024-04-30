from typing import Optional

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
