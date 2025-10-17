from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_db: str
    postgres_user: str
    postgres_password: str
    noodle_password: str

    database_url: str
    db_pool_size: int
    db_max_overflow: int

    model_config = {"env_file": ".env"}


settings = Settings()
