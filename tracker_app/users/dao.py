from fastapi import HTTPException, status, Response

from tracker_app.BaseDao import BaseDao
from tracker_app.database import async_session_maker
from tracker_app.models import User, UserRole
from sqlalchemy import select, update


class UserDao(BaseDao):
    model = User

    @classmethod
    async def get_by_username(cls, username: str):
        async with async_session_maker() as session:
            query = select(User).filter_by(username=username)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def update_user_role(role: str, user_id: int):
        async with async_session_maker() as session:
            async with session.begin():
                # Обновляем роль пользователя в базе данных
                query = (
                    update(User)
                    .where(User.id == user_id)
                    .values(role=role)
                )
                await session.execute(query)
                await session.commit()

    @staticmethod
    async def update_user_name(user_id: int, username: str):
        async with async_session_maker() as session:
            async with session.begin():
                # Обновляем роль пользователя в базе данных
                stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(username=username)
                )
                await session.execute(stmt)
                await session.commit()

    @staticmethod
    async def update_user_password(response: Response, new_password: str, cur_user: User):
        async with async_session_maker() as session:
            query = update(User).where(User.id==cur_user.id).values(password=new_password)
            await session.execute(query)
            await session.commit()




