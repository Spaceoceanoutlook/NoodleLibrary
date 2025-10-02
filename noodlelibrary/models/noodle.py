# class Noodles:
#     id: int
#     title: str
#     description: str
#     recommendation: int
#     country_id: int
#     manufacture_id: int
#     image: str
from .base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class Noodle(Base):
    __tablename__ = "noodles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
