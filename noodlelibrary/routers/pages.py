from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from noodlelibrary.database import get_db
from noodlelibrary.models.country import Country
from noodlelibrary.models.manufacture import Manufacture
from noodlelibrary.models.noodle import Noodle
from noodlelibrary.schemas.noodle import NoodleBase

router = APIRouter()
templates = Jinja2Templates(directory="noodlelibrary/templates")


async def get_all_country(db: AsyncSession):
    result = await db.execute(select(Country))
    return result.scalars().all()


async def get_all_manufacture(db: AsyncSession):
    result = await db.execute(select(Manufacture))
    return result.scalars().all()


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

    return templates.TemplateResponse(
        "create.html",
        {
            "request": request,
            "countries": countries,
        },
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
    db: AsyncSession = Depends(get_db),
):
    is_recommended = recommendation == "true"
    if code != "456321":
        raise HTTPException(status_code=400, detail="Неверный код доступа")

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
    "/countries/{country_name}",
    response_class=HTMLResponse,
    summary="Read Noodles By Country",
)
async def read_noodles_by_country(
    country_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    countries = await get_all_country(db)

    stmt = (
        select(Noodle)
        .join(Noodle.country)
        .filter(Country.name == country_name)
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
