from sqlalchemy import select

from tracker_app.database import async_session_maker


class BaseDao:
    """
    Base class for data access objects.

    Attributes:
        model: The SQLAlchemy model associated with the data access object.
    """
    model = None

    @classmethod
    async def get_by_id(cls, o_id: int):
        """
        Retrieves a database record by its ID.

        Args:
            o_id (int): The ID of the record to retrieve.

        Returns:
            Optional[BaseModel]: The database record, if found, or None if not found.
        """
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=o_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
