from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from noodlelibrary.models.country import Country
from noodlelibrary.models.manufacture import Manufacture

from .base import Base


class Noodle(Base):
    __tablename__ = "noodles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    recommendation: Mapped[bool] = mapped_column(Boolean, nullable=False)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)
    manufacture_id: Mapped[int] = mapped_column(
        ForeignKey("manufactures.id"), nullable=False
    )
    image: Mapped[str] = mapped_column(String(500), nullable=False)

    country: Mapped["Country"] = relationship("Country", backref="noodles")
    manufacture: Mapped["Manufacture"] = relationship("Manufacture", backref="noodles")
