from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict


class STaskCreate(BaseModel):
    number: int
    type: Literal['task', 'bug']
    priority: Optional[Literal['low', 'medium', 'high', 'critical']] = None
    title: str
    description: Optional[str] = None
    assignee_id: Optional[int] = None

    class Config:
        orm_mode = True


class STaskCreateChild(STaskCreate):
    parent_id: int

    class Config:
        orm_mode = True


class STaskUpdate(BaseModel):
    number: int
    type: Literal['task', 'bug']
    status: Literal['to_do', 'in_progress', 'code_review', 'dev_test', 'testing', 'done', 'wontfix']
    priority: Optional[Literal['low', 'medium', 'high', 'critical']] = None
    title: str
    description: str
    assignee_id: int

    class Config:
        orm_mode = True
