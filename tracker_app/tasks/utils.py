from fastapi import HTTPException, status
from sqlalchemy import asc, desc, column

from tracker_app.models import User, TaskType, TaskPriority


def convert_filter_type(filter_type: str):
    """
    Converts the filter type string into SQLAlchemy order_by expressions.

    Args:
        filter_type (str): The type of filter.

    Returns:
        SQLAlchemy Expression: The SQLAlchemy expression for ordering the query result.

    Raises:
        HTTPException: If the provided filter type is not supported.
    """
    filter_mapping = {
        'number_asc': asc(column('number')),
        'number_desc': desc(column('number')),
        'status_asc': asc(column('status')),
        'status_desc': desc(column('status')),
        'type_asc': asc(column('type')),
        'type_desc': desc(column('type')),
        'created_at_asc': asc(column('created_at')),
        'created_at_desc': desc(column('created_at')),
        'last_updated_at_asc': asc(column('last_updated_at')),
        'last_updated_at_desc': desc(column('last_updated_at')),
        'assignee_asc': asc(column('assignee_id')),
        'assignee_desc': desc(column('assignee_id')),
    }

    result = filter_mapping.get(filter_type)
    return result


def user_type_priority_validator(user: User, t_type: str, t_priority: str):
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if t_type not in TaskType.__members__ or t_priority not in TaskPriority.__members__:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return True
