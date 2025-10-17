from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_db: str
    postgres_user: str
    postgres_password: str
    noodle_password: str

    model_config = {"env_file": ".env"}


settings = Settings()
