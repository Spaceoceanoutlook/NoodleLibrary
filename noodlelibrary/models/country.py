from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
