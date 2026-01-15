from typing import Optional, Type, TypeVar

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ValidationError
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, selectinload

from noodlelibrary.database import get_db
from noodlelibrary.models import Country, Manufacture, Noodle
from noodlelibrary.schemas import CountryBase, ManufactureBase, NoodleBase
from settings import settings

router = APIRouter()
templates = Jinja2Templates(directory="noodlelibrary/templates")

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
SchemaType = TypeVar("SchemaType", bound=BaseModel)


async def get_all_country(db: AsyncSession):
    result = await db.execute(select(Country))
    return result.scalars().all()


async def get_all_manufacture(db: AsyncSession):
    result = await db.execute(select(Manufacture))
    return result.scalars().all()


async def get_or_create(
    db: AsyncSession,
    model: Type[ModelType],
    schema: Type[SchemaType],
    new_name: Optional[str] = None,
    obj_id: Optional[int] = None,
) -> int:
    """
    Универсальная функция для получения или создания объекта по названию или ID.
    - Если передан new_name, создается объект с этим именем и возвращается его obj_id.
    - Если передан только obj_id, то он и возвращается.
    """
    if new_name:
        schema = schema(name=new_name.strip())
        obj = model(name=schema.name)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj.id

    if obj_id is not None:
        return obj_id


@router.get("/", response_class=HTMLResponse, summary="Home Page")
async def homepage(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    countries = await get_all_country(db)
    manufacturers = await get_all_manufacture(db)

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "countries": countries, "manufacturers": manufacturers},
    )


@router.get("/create", response_class=HTMLResponse, summary="Show Create Noodle Form")
async def create_noodle_form(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    countries = await get_all_country(db)
    manufacturers = await get_all_manufacture(db)

    return templates.TemplateResponse(
        "create.html",
        {"request": request, "countries": countries, "manufacturers": manufacturers},
    )


@router.post("/create", summary="Create Noodle")
async def create_noodle_post(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    image: str = Form(...),
    manufacture_id: int = Form(...),
    country_id: int = Form(...),
    code: str = Form(...),
    recommendation: Optional[str] = Form(None),
    new_manufacture: Optional[str] = Form(None),
    new_country: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    is_recommended = recommendation == "true"

    if code != settings.noodle_password:
        raise HTTPException(status_code=400, detail="Неверный код доступа")

    manufacture_id = await get_or_create(
        db=db,
        model=Manufacture,
        schema=ManufactureBase,
        new_name=new_manufacture,
        obj_id=manufacture_id,
    )
    country_id = await get_or_create(
        db=db,
        model=Country,
        schema=CountryBase,
        new_name=new_country,
        obj_id=country_id,
    )

    try:
        noodle_schemas = NoodleBase(
            title=title,
            description=description,
            image=image,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from None

    new_noodle = Noodle(
        title=noodle_schemas.title,
        description=noodle_schemas.description,
        image=noodle_schemas.image,
        manufacture_id=manufacture_id,
        country_id=country_id,
        recommendation=is_recommended,
    )

    db.add(new_noodle)
    await db.commit()
    await db.refresh(new_noodle)

    return RedirectResponse(url="/", status_code=303)


@router.get(
    "/countries/{country}",
    response_class=HTMLResponse,
    summary="Read Noodles By Country",
)
async def read_noodles_by_country(
    country: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    countries = await get_all_country(db)

    stmt = (
        select(Noodle)
        .join(Noodle.country)
        .filter(Country.name == country)
        .options(selectinload(Noodle.country))
        .options(selectinload(Noodle.manufacture))
        .order_by(desc(Noodle.id))
    )

    result = await db.execute(stmt)
    noodles = result.scalars().all()
    manufacturers = sorted({
        noodle.manufacture.name for noodle in noodles if noodle.manufacture
    }, key=str.lower)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "noodles": noodles,
            "countries": countries,
            "manufacturers": manufacturers,
        },
    )


@router.get(
    "/manufacturers/{manufacture}",
    response_class=HTMLResponse,
    summary="Read Noodles By Manufacture",
)
async def read_noodles_by_manufacture(
    manufacture: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    countries = await get_all_country(db)

    stmt = (
        select(Noodle)
        .join(Noodle.manufacture)
        .filter(Manufacture.name == manufacture)
        .options(selectinload(Noodle.country))
        .options(selectinload(Noodle.manufacture))
        .order_by(desc(Noodle.id))
    )

    result = await db.execute(stmt)
    noodles = result.scalars().all()

    country = [noodle.country.name for noodle in noodles if noodle.country][0]

    stmt_manufacturers = (
        select(Manufacture.name)
        .select_from(Noodle)
        .join(Noodle.manufacture)
        .join(Noodle.country)
        .filter(Country.name == country)
        .distinct()
    )
    result_mf = await db.execute(stmt_manufacturers)
    manufacturer_names = [row[0] for row in result_mf.fetchall() if row[0]]
    manufacturers_from_country = sorted(manufacturer_names, key=str.lower)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "noodles": noodles,
            "countries": countries,
            "manufacturers": manufacturers_from_country,
        },
    )


@router.get("/noodle/{id}", response_class=HTMLResponse, summary="Read Noodle By Id")
async def read_noodle(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Noodle)
        .filter(Noodle.id == id)
        .options(selectinload(Noodle.country))
        .options(selectinload(Noodle.manufacture))
        .order_by(desc(Noodle.id))
    )
    result = await db.execute(stmt)
    noodle = result.scalars().first()
    page_title = noodle.title
    countries = await get_all_country(db)
    return templates.TemplateResponse(
        "noodle_details.html",
        {
            "request": request,
            "noodle": noodle,
            "countries": countries,
            "page_title": page_title,
        },
    )


@router.post("/noodle/{id}/edit", summary="Edit Noodle")
async def edit_noodle(
    id: int,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Обновляет описание и флаг рекомендации лапши.
    payload = {
        "description": str,
        "recommendation": bool,
        "password": str
    }
    """
    stmt = select(Noodle).filter(Noodle.id == id)
    result = await db.execute(stmt)
    noodle = result.scalars().first()

    password = payload.get("password")
    if password != settings.noodle_password:
        raise HTTPException(status_code=403, detail="Неверный пароль")

    noodle.description = payload.get("description", noodle.description)
    noodle.recommendation = payload.get("recommendation", noodle.recommendation)

    db.add(noodle)
    await db.commit()
    await db.refresh(noodle)

    return {"status": "ok"}


@router.get(
    "/recommendation",
    response_class=HTMLResponse,
    summary="Read Noodles By Recommendation",
)
async def read_noodles_by_recommendation(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    countries = await get_all_country(db)

    stmt = (
        select(Noodle)
        .where(Noodle.recommendation.is_(True))
        .options(selectinload(Noodle.country))
        .options(selectinload(Noodle.manufacture))
        .order_by(desc(Noodle.id))
    )

    result = await db.execute(stmt)
    noodles = result.scalars().all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "noodles": noodles,
            "countries": countries,
        },
    )


@router.get(
    "/statistics",
    summary="Noodle statistics",
)
async def noodle_statistics(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(func.count(Noodle.id))

    result = await db.execute(stmt)
    total_count = result.scalar()

    return {"total_noodles": total_count}
