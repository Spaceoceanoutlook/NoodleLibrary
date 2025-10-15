from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from noodlelibrary.database import get_db
from noodlelibrary.models import Country, Manufacture, Noodle
from noodlelibrary.schemas import CountryBase, ManufactureBase, NoodleBase
from settings import settings

router = APIRouter()
templates = Jinja2Templates(directory="noodlelibrary/templates")


async def get_all_country(db: AsyncSession):
    result = await db.execute(select(Country))
    return result.scalars().all()


async def get_all_manufacture(db: AsyncSession):
    result = await db.execute(select(Manufacture))
    return result.scalars().all()


async def get_or_create_manufacture(
    db: AsyncSession,
    new_manufacture: Optional[str] = None,
    manufacture_id: Optional[int] = None,
) -> int:
    """
    Возвращает id производителя.
    - Если указан new_manufacture, создаёт нового производителя и возвращает его id.
    - Иначе возвращает существующий manufacture_id.
    """
    if new_manufacture:
        schema = ManufactureBase(name=new_manufacture.strip())
        obj = Manufacture(name=schema.name)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj.id

    if manufacture_id is None:
        raise ValueError("Не указан существующий manufacture_id")

    return int(manufacture_id)


async def get_or_create_country(
    db: AsyncSession,
    new_country: Optional[str] = None,
    country_id: Optional[int] = None,
) -> int:
    """
    Возвращает id страны.
    - Если указан new_country, создаёт новую страну и возвращает её id.
    - Иначе возвращает существующий country_id.
    """
    if new_country:
        schema = CountryBase(name=new_country.strip())
        obj = Country(name=schema.name)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj.id

    if country_id is None:
        raise ValueError("Не указан существующий country_id")

    return int(country_id)


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
    manufacture_id: str = Form(...),
    country_id: str = Form(...),
    code: str = Form(...),
    recommendation: Optional[str] = Form(None),
    new_manufacture: Optional[str] = Form(None),
    new_country: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    is_recommended = recommendation == "true"

    if code != settings.noodle_password:
        raise HTTPException(status_code=400, detail="Неверный код доступа")

    manufacture_id = await get_or_create_manufacture(
        db, new_manufacture, manufacture_id
    )
    country_id = await get_or_create_country(db, new_country, country_id)

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
    manufacturers = {
        noodle.manufacture.name for noodle in noodles if noodle.manufacture
    }
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
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "noodles": noodles,
            "countries": countries,
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
