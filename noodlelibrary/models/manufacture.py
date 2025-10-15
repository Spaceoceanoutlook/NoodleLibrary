from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Manufacture(Base):
    __tablename__ = "manufactures"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
