from fastapi import FastAPI

from tracker_app.users.router import router as user_router
from tracker_app.tasks.router import router as task_router

app = FastAPI()
app.include_router(user_router)
app.include_router(task_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
