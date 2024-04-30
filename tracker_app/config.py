from pydantic import root_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_NAME: str
    DB_PASS: str

    class Config:
        env_file = ".env"

    @property
    def DATABASE_URL(self):
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'


settings = Settings()

print(settings.DATABASE_URL)
