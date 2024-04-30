from datetime import datetime

from fastapi import Request, HTTPException, Depends
from jose import jwt, JWTError

from tracker_app.config import settings
from tracker_app.users.dao import UserDao


def get_token(request: Request):
    token = request.cookies.get('access_token')
    if not token:
        raise HTTPException(status_code=401)
    return token


async def get_current_user(token: str = Depends(get_token)):
    try:
        payload = jwt.decode(
            token, 'hehe', 'HS256'
        )
    except JWTError:
        raise HTTPException(status_code=401)
    exp: str = payload.get('exp')
    if not exp or (int(exp) < datetime.utcnow().timestamp()):
        raise HTTPException(status_code=401)

    user_id: str = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=401)

    user = await UserDao.get_by_id(id=int(user_id))
    if not user:
        raise HTTPException(status_code=401)
    return user

