from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from tracker_app.users.dao import UserDao

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=10)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, 'hehe', 'HS256')
    return encoded_jwt


async def authenticate_user(username: str, password: str):
    user = await UserDao.get_by_username(username)
    if not user and not verify_password(password, user.hashed_password):
        return None
    return user
