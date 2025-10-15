from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    noodle_password: str

    class Config:
        env_file = ".env"


settings = Settings()
