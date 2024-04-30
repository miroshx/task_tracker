from urllib import request

from fastapi import APIRouter, HTTPException, status, Response, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt

from tracker_app.database import async_session_maker
from tracker_app.models import User, UserRole
from tracker_app.users.dao import UserDao
from tracker_app.users.dependencies import get_current_user
from tracker_app.users.schemas import SUser, SUserChangePassword
from sqlalchemy import select, insert, text

from tracker_app.users.utils import get_hashed_password, verify_password, authenticate_user, create_access_token

router = APIRouter(
    prefix="/users",
    tags=['Auth'],
)


@router.post('/register')
async def register_user(user_data: SUser):
    user = await UserDao.get_by_username(user_data.username)
    if user:
        raise HTTPException(status_code=500)
    async with async_session_maker() as session:
        hashed_password = get_hashed_password(user_data.password)
        query = insert(User).values(username=user_data.username, password=hashed_password)
        await session.execute(query)
        await session.commit()


@router.post('/login')
async def login_user(response: Response, user_data: SUser):
    user = await authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    access_token = create_access_token({'sub': str(user.id)})
    response.set_cookie('access_token', access_token, httponly=True)
    return access_token


@router.post('/logout')
async def logout(response: Response):
    response.delete_cookie('access_token')


@router.post('/change_role/{id}')
async def change_role(id: str, role: str = Body(...), cur_user: User = Depends(get_current_user)):
    if cur_user.role != UserRole.manager:
        raise HTTPException(status.HTTP_403_FORBIDDEN)

    change_user = await UserDao.get_by_id(id)
    if change_user:
        if role not in [r.value for r in UserRole]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST)

        change_user.role = UserRole(role)
        await UserDao.update_user_role(change_user)
        return Response(status_code=status.HTTP_200_OK)
    else:
        raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.post('/change_username/{id}')
async def change_role(id: str, new_username: str, cur_user: User = Depends(get_current_user)):
    if cur_user.role != UserRole.manager:
        raise HTTPException(status.HTTP_403_FORBIDDEN)

    change_user = await UserDao.get_by_id(int(id))
    if change_user:
        change_user.username = new_username
        await UserDao.update_user_name(change_user)
        return Response(status_code=status.HTTP_200_OK)
    else:
        raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.post('/change_password')
async def change_password(response: Response, password_data: SUserChangePassword,
                          cur_user: User = Depends(get_current_user)):
    if not cur_user or not get_hashed_password(password_data.password) != cur_user.password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    new_password = get_hashed_password(password_data.new_password)
    await UserDao.update_user_password(response, new_password, cur_user)
