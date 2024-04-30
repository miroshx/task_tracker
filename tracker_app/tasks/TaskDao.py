from fastapi import status, HTTPException
from sqlalchemy import insert, select, update, delete, text, or_, and_
from sqlalchemy.orm import selectinload
from tracker_app.database import async_session_maker
from tracker_app.models import Task, User, UserRole, TaskStatus, TaskChangeType, TaskHistory
from tracker_app.tasks.schemas import STask, STaskCreate, STaskCreateChild
from tracker_app.tasks.utils import convert_filter_type
from tracker_app.users.dao import UserDao
import logging


class TaskDao:
    model = Task

    @staticmethod
    async def save_history(data: dict, cur_user: User, action: TaskChangeType) -> None:
        """
            Saves the history of changes made to a task.

            Args:
                data (dict): Data representing the changes made to the task.
                cur_user (User): The user who made the changes.
                action (TaskChangeType): Type of action performed on the task (create, update, etc.).

            Returns:
                None
        """
        task_created = await TaskDao.get_last_updated_task()
        if action == TaskChangeType.create:
            data['status'] = 'to_do'
        change_data = {'changes': data}
        async with async_session_maker() as session:
            history_item = TaskHistory(task_id=task_created.id,
                                       change_type=action,
                                       user_id=cur_user.id,
                                       change_data=change_data)
            session.add(history_item)
            await session.commit()

    @staticmethod
    async def is_valid_parent(parent_id: int):
        """
                Checks if the given parent task ID is valid.

                Args:
                    parent_id (int): ID of the parent task.

                Returns:
                    bool: True if the parent task is valid, False otherwise.
                """
        task = await TaskDao.get_by_id(parent_id)
        if task is None:
            return False
        return True

    @staticmethod
    async def is_valid_status(task: STask):
        """
            Checks if the status of the task is valid.

            Args:
                task (STask): The task object.

            Returns:
                bool: True if the status is valid, False otherwise.
        """
        if status in ['to_do', 'wontfix']:
            return True
        status_index = 0
        statuses = [r.value for r in TaskStatus]
        for i in range(len(statuses) - 1):
            if statuses[i] == task.status:
                status_index = i
                break
        if status_index < len(statuses) - 2:
            return True
        return False

    @staticmethod
    async def is_valid_assignee(task_status: TaskStatus, assignee: User):
        """
            Checks if the assigned user for the task is valid.

            Args:
                task_status (TaskStatus): Current status of the task.
                assignee (int): ID of the assigned user.

            Returns:
                bool: True if the assignee is valid, False otherwise.
        """
        if assignee is None and task_status != TaskStatus.in_progress:
            return True
        elif assignee:
            if assignee.role == UserRole.team_lead:
                return True
            elif assignee.role == UserRole.test_engineer and task_status not in [TaskStatus.in_progress,
                                                                                 TaskStatus.code_review,
                                                                                 TaskStatus.dev_test]:
                return True
            elif assignee.role == UserRole.developer and task_status != TaskStatus.testing:
                return True
        elif assignee is None and TaskStatus.in_progress:
            return False
        return False

    @staticmethod
    async def get_last_updated_task() -> Task:
        """
            Retrieves the last updated task.

            Returns:
                Task: The last updated task.
            """
        async with async_session_maker() as session:
            query = select(Task).order_by(Task.last_updated_at.desc())
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def create_task(task: STaskCreate, cur_user: User):
        """
            Creates a new task.

            Args:
                task (STaskCreate): Data for creating the task.
                cur_user (User): Current user creating the task.

            Returns:
                None
        """
        async with async_session_maker() as session:
            query = insert(Task).values(number=task.number,
                                        type=task.type,
                                        priority=task.priority,
                                        status=TaskStatus.to_do,
                                        title=task.title,
                                        description=task.description,
                                        creator_id=cur_user.id,
                                        assignee_id=task.assignee_id if task.assignee_id != 0 else None, )
            await session.execute(query)
            await session.commit()

    @staticmethod
    async def create_child_task(task: STaskCreateChild, cur_user: User):
        """
            Creates a child task for a given parent task.

            Args:
                task (STaskCreateChild): Data for creating the child task.
                cur_user (User): Current user creating the child task.

            Returns:
                None
        """
        async with async_session_maker() as session:
            query = insert(Task).values(number=task.number,
                                        type=task.type,
                                        priority=task.priority,
                                        status=TaskStatus.to_do,
                                        title=task.title,
                                        description=task.description,
                                        creator_id=cur_user.id,
                                        assignee_id=task.assignee_id if task.assignee_id != 0 else None,
                                        parent_id=task.parent_id)
            await session.execute(query)
            await session.commit()

    @staticmethod
    async def get_all_tasks(filter_type: str):
        """
            Retrieves all tasks based on the given filter type.

            Args:
                filter_type (str): Type of filter to apply.

            Returns:
                List[Task]: List of tasks.
        """
        async with async_session_maker() as session:
            filter_method = convert_filter_type(filter_type)

            query = select(Task).options(selectinload(Task.children)).order_by(
                filter_method)
            result = await session.execute(query)
            return result.scalars().unique().all()

    @staticmethod
    async def get_by_id(t_id: int):
        """
            Retrieves a task by its ID.

            Args:
                t_id (int): ID of the task.

            Returns:
                Task: Task object.
        """
        async with async_session_maker() as session:
            query = select(Task).filter_by(id=t_id).options(selectinload(Task.children))
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def update_task(task: STask, id: int):
        """
            Updates a task with the provided data.

            Args:
                task (STask): Updated task data.
                id (int): ID of the task to update.

            Returns:
                None
        """
        async with async_session_maker() as session:
            query = (
                update(Task)
                .where(Task.id == id)
                .values(number=task.number,
                        type=task.type,
                        priority=task.priority,
                        status=task.status,
                        title=task.title,
                        description=task.description,
                        assignee_id=None if task.assignee_id == 0 else task.assignee_id, )
            )
            await session.execute(query)
            await session.commit()

    @staticmethod
    async def delete_task(id: int):
        """
            Deletes a task by its ID.

            Args:
                id (int): ID of the task to delete.

            Returns:
                None
        """
        async with async_session_maker() as session:
            query = delete(Task).where(Task.id == id)
            await session.execute(query)
            await session.commit()

    @staticmethod
    def get_next_status(task: Task):
        """
            Determines the next status of a task based on its current status.

            Args:
                task (Task): The task object.

            Returns:
                TaskStatus: Next status of the task.
        """
        i = 0
        status_index = 0
        statuses = [r.value for r in TaskStatus]
        for task_status in statuses:
            if task_status == task.status.value:
                status_index = i
            i += 1
        next_status = statuses[status_index + 1]
        return TaskStatus[next_status]

    @staticmethod
    async def update_status(id: int, t_status: TaskStatus, assignee_id: int):
        """
            Updates the status and assignee of a task.

            Args:
                id (int): ID of the task to update.
                t_status (str): New status of the task.
                assignee_id (int): ID of the new assignee.

            Returns:
                None
        """
        async with async_session_maker() as session:
            query = update(Task).where(Task.id == id).values(status=t_status,
                                                             assignee_id=assignee_id if assignee_id != 0 else None)
            await session.execute(query)
            await session.commit()

    @staticmethod
    async def update_assignee(id: int):
        """
            Updates the assignee of a task.

            Args:
                id (int): ID of the task to update.

            Raises:
                HTTPException: If the assignee is not found.

            Returns:
                None
        """
        async with async_session_maker() as session:
            task = await TaskDao.get_by_id(id=id)
            assignee = task.assignee
            if not assignee:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found")
            assignee = UserDao.get_by_id(id=assignee.id)

    @staticmethod
    async def search_task(text: str = None, id: int = None, creator: str = None, assignee: str = None):
        """
            Searches for tasks based on provided criteria.

            Args:
                text (str, optional): Text to search within task title or description. Defaults to None.
                id (int, optional): ID of the task to search. Defaults to None.
                creator (str, optional): Username of the task creator to search. Defaults to None.
                assignee (str, optional): Username of the task assignee to search. Defaults to None.

            Returns:
                List[Task]: List of tasks matching the search criteria.
        """
        async with async_session_maker() as session:
            query = select(Task).order_by(Task.last_updated_at)
            filters = []
            if text:
                filters.append(or_(Task.title.ilike(f'%{text}%'), Task.description.ilike(f'%{text}%')))
            if id:
                filters.append(Task.id == id)
            if creator:
                filters.append(Task.creator.has(User.username.ilike(f'%{creator}%')))
            if assignee:
                filters.append(Task.assignee.has(User.username.ilike(f'%{assignee}%')))

            if filters:
                query = query.filter(and_(*filters))

            # Выполняем запрос и возвращаем результат
            result = await session.execute(query)
            return result.scalars().unique().all()

    @staticmethod
    async def get_task_history(id: int):
        """
            Retrieves the history of changes made to a task.

            Args:
                id (int): ID of the task.

            Returns:
                List[TaskHistory]: List of historical changes made to the task.
        """
        async with async_session_maker() as session:
            query = select(TaskHistory).filter_by(task_id=id).order_by(TaskHistory.timestamp)

            result = await session.execute(query)
            return result.scalars().all()
