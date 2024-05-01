from fastapi import FastAPI

from tracker_app.users.router import router as user_router
from tracker_app.tasks.router import router as task_router

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis

app = FastAPI()
app.include_router(user_router)
app.include_router(task_router)


@app.on_event("startup")
def startup():
    redis = aioredis.from_url("redis://localhost:6379")
    FastAPICache.init(RedisBackend(redis), prefix="cache")
