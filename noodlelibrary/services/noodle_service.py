from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from noodlelibrary.models import Country, Manufacture, Noodle
from noodlelibrary.repositories.noodle_repository import (
    get_noodle_by_id,
)
from noodlelibrary.schemas import CountryBase, ManufactureBase, NoodleBase

ModelType = type[DeclarativeBase]
SchemaType = type[BaseModel]

async def get_or_create(
    db: AsyncSession,
    model: ModelType,
    schema: SchemaType,
    new_name: str = None,
    obj_id: int = None,
) -> int:
    """
    Функция для получения или создания объекта по названию или ID.
    - Если передан new_name, создается объект с этим именем и возвращается его obj_id.
    - Если передан только obj_id, то он и возвращается.
    """
    if new_name:
        obj = model(name=new_name.strip())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj.id
    if obj_id is not None:
        return obj_id
    return None

async def create_noodle(
    db: AsyncSession,
    title: str,
    description: str,
    image: str,
    manufacture_id: int,
    country_id: int,
    recommendation: bool,
    new_manufacture: str = None,
    new_country: str = None,
):
    manufacture_id = await get_or_create(
        db, Manufacture, ManufactureBase, new_name=new_manufacture, obj_id=manufacture_id
    )
    country_id = await get_or_create(
        db, Country, CountryBase, new_name=new_country, obj_id=country_id
    )

    try:
        noodle_schema = NoodleBase(title=title, description=description, image=image)
    except ValidationError as e:
        raise ValueError(e.errors()) from None

    new_noodle = Noodle(
        title=noodle_schema.title,
        description=noodle_schema.description,
        image=noodle_schema.image,
        manufacture_id=manufacture_id,
        country_id=country_id,
        recommendation=recommendation,
    )
    db.add(new_noodle)
    await db.commit()
    await db.refresh(new_noodle)
    return new_noodle

async def update_noodle(
    db: AsyncSession,
    noodle_id: int,
    description: str = None,
    recommendation: bool = None
):
    noodle = await get_noodle_by_id(db, noodle_id)
    if not noodle:
        raise ValueError("Noodle not found")

    if description is not None:
        noodle.description = description
    if recommendation is not None:
        noodle.recommendation = recommendation

    await db.commit()
    await db.refresh(noodle)
    return noodle
