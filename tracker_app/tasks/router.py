from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response

from tracker_app.database import async_session_maker
from tracker_app.models import User, UserRole, TaskChangeType, TaskStatus, Task, TaskHistory
from tracker_app.tasks.TaskDao import TaskDao
from tracker_app.tasks.schemas import STask, STaskCreate, STaskCreateChild
from tracker_app.users.dao import UserDao
from tracker_app.users.dependencies import get_current_user

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@router.post('/create_task')
async def create_task(task: STaskCreate, cur_user: User = Depends(get_current_user)):
    """
        Create a new task.

        Args:
            task (STaskCreate): Data for creating the task.
            cur_user (User, optional): Current user. Defaults to Depends(get_current_user).

        Raises:
            HTTPException: If the assigned user is invalid or there's an error in creating the task.

        Returns:
            None
        """
    if not await TaskDao.is_valid_assignee('to_do', task.assignee_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    await TaskDao.create_task(task, cur_user)
    data = task.dict()
    await TaskDao.save_history(data, cur_user, TaskChangeType.create)


@router.post('/create_child_task/{id}')
async def create_child_task(task: STaskCreateChild, cur_user: User = Depends(get_current_user)):
    """
        Create a child task for a given parent task ID.

        Args:
            task (STaskCreateChild): Data for creating the child task.
            cur_user (User, optional): Current user. Defaults to Depends(get_current_user).

        Raises:
            HTTPException: If the current user is not authorized, invalid data, or there's an error in creating the task.

        Returns:
            None
        """
    if not cur_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    is_valid_assignee = await TaskDao.is_valid_assignee('to_do', task.assignee_id)
    is_valid_parent = await TaskDao.is_valid_parent(task.parent_id)
    if not is_valid_assignee or not is_valid_parent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    data = task.dict()
    data.pop('parent_id')
    await TaskDao.create_child_task(task, cur_user)
    await TaskDao.save_history(data, cur_user, TaskChangeType.create)


@router.get('/get_task/{t_id}')
async def get_task(t_id: int):
    """
       Retrieve a task by its ID.

       Args:
           t_id (int): Task ID.

       Returns:
           Task: Task data.
       """
    return await TaskDao.get_by_id(t_id=t_id)


@router.get('/get_tasks')
async def get_tasks(filter_type: str):
    """
        Get all tasks based on a filter type.

        Args:
            filter_type (str): Type of filter.

        Returns:
            List[Task]: List of tasks.
        """
    return await TaskDao.get_all_tasks(filter_type)


@router.put('/update_task/{id}')
async def update_task(task: STask, t_id: int, cur_user: User = Depends(get_current_user)):
    """
       Update a task by its ID.

       Args:
           task (STask): Updated task data.
           t_id (int): Task ID.
           cur_user (User, optional): Current user. Defaults to Depends(get_current_user).

       Raises:
           HTTPException: If the status or assignee is invalid, or there's an error in updating the task.

       Returns:
           None
       """
    is_valid_status = False
    cur_task = await TaskDao.get_by_id(t_id)
    t_next_status = TaskDao.get_next_status(cur_task)
    if task.status not in TaskStatus.__members__:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if TaskStatus[task.status] in [TaskStatus.wontfix, TaskStatus.to_do] or TaskStatus[task.status] == t_next_status or \
            TaskStatus[task.status] == cur_task.status:
        is_valid_status = True
    is_valid_assignee = await TaskDao.is_valid_assignee(TaskStatus[task.status], task.assignee_id)
    if not is_valid_status or not is_valid_assignee:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    await TaskDao.update_task(task, t_id)
    data = task.dict()
    await TaskDao.save_history(data, cur_user, TaskChangeType.update)


@router.delete('/delete_task/{id}')
async def delete_task(t_id: int, cur_user: User = Depends(get_current_user)):
    """
        Delete a task by its ID.

        Args:
            t_id (int): Task ID.
            cur_user (User, optional): Current user. Defaults to Depends(get_current_user).

        Raises:
            HTTPException: If the current user is not authorized or there's an error in deleting the task.

        Returns:
            Response: Response with the status code 204
        """
    if cur_user.role != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    await TaskDao.delete_task(t_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch('/next_status/{id}')
async def next_status(t_id: int, assignee_id: int = 0):
    """
        Move a task to the next status.

        Args:
            t_id (int): Task ID.
            assignee_id (int, optional): Assignee ID. Defaults to 0.

        Raises:
            HTTPException: If the next status is invalid or there's an error in updating the status.

        Returns:
            Response: Response with the code 200
        """
    task = await TaskDao.get_by_id(t_id)
    t_next_status: TaskStatus = TaskDao.get_next_status(task)

    if t_next_status == TaskStatus.wontfix:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    assignee = await UserDao.get_by_id(assignee_id)
    if not await TaskDao.is_valid_assignee(t_next_status, assignee):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    await TaskDao.update_status(t_id, t_next_status, assignee_id)
    return Response(status_code=status.HTTP_200_OK)


@router.get('/search_task/')
async def search_task(text: str = None, t_id: int = None, creator: str = None, assignee: str = None):
    """
      Search for tasks based on provided parameters.

      Args:
          text (str, optional): Search text. Defaults to None.
          t_id (int, optional): Task ID. Defaults to None.
          creator (str, optional): Creator username. Defaults to None.
          assignee (str, optional): Assignee username. Defaults to None.

      Returns:
          List[Task]: List of tasks matching the search criteria.
      """
    return await TaskDao.search_task(text, t_id, creator, assignee)


@router.get('/task_history/{t_id}')
async def task_history(t_id: int):
    """
      Retrieve the history of changes for a task by its ID.

      Args:
          t_id (int): Task ID.

      Returns:
          List[TaskHistory]: List of task change history.
      """
    return await TaskDao.get_task_history(t_id)
