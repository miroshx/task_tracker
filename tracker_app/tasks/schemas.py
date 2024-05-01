from pydantic import BaseModel, ConfigDict


class STaskCreate(BaseModel):
    number: int
    type: str
    priority: str
    title: str
    description: str
    assignee_id: int

    class Config:
        orm_mode = True


class STask(STaskCreate):
    status: str

    class Config:
        orm_mode = True


class STaskCreateChild(STaskCreate):
    parent_id: int

    class Config:
        orm_mode = True
