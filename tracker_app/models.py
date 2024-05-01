# app/db/models.py

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, func, JSON
from enum import Enum as PyEnum

from sqlalchemy.orm import relationship

from tracker_app.database import Base


class UserRole(PyEnum):
    manager = "manager"
    team_lead = "team_lead"
    developer = "developer"
    test_engineer = "test_engineer"


class TaskPriority(PyEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = 'low'


class TaskStatus(PyEnum):
    to_do = "to_do"
    in_progress = "in_progress"
    code_review = "code_review"
    dev_test = "dev_test"
    testing = "testing"
    done = "done"
    wontfix = "wontfix"


class TaskType(PyEnum):
    task = 'task'
    bug = 'bug'


class TaskChangeType(PyEnum):
    create = 'create'
    update = 'update'


class TaskHistory(Base):
    __tablename__ = 'task_history'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    change_type = Column(Enum(TaskChangeType, name='task_change_type', create_type=False), nullable=False)
    change_data = Column(JSON)
    timestamp = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey('users.id'))


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, index=True)
    type = Column(Enum(TaskType, name='task_type', create_type=False), default=TaskType.task, nullable=False)
    priority = Column(Enum(TaskPriority, name='task_priority', create_type=False), default=TaskPriority.low,
                      nullable=False)
    status = Column(Enum(TaskStatus, name='task_status', create_type=False), default=TaskStatus.to_do, nullable=False)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    last_updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    assignee_id = Column(Integer, ForeignKey("users.id"))
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", foreign_keys=[creator_id])
    assignee = relationship("User", foreign_keys=[assignee_id])

    parent_id = Column(Integer, ForeignKey('tasks.id'))
    children = relationship("Task", lazy="joined")
    parent = relationship("Task", back_populates="children", remote_side=[id], overlaps="children")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole, name='user_role', create_status=False))

    tasks_created = relationship("Task", back_populates="creator", foreign_keys="Task.creator_id")
    tasks_assigned = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")
