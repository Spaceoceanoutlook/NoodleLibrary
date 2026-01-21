from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from noodlelibrary.database import get_db
from noodlelibrary.models import Country, Manufacture, Noodle
from noodlelibrary.repositories.noodle_repository import (
    get_all_countries,
    get_all_manufactures,
    get_count_noodles,
    get_noodle_by_id,
    get_noodles_by_country,
    get_noodles_by_manufacture,
    get_recommended_noodles,
)
from noodlelibrary.services.noodle_service import (
    create_noodle,
    update_noodle,
)
from settings import settings

router = APIRouter()
templates = Jinja2Templates(directory="noodlelibrary/templates")

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db: AsyncSession = Depends(get_db)):
    countries = await get_all_countries(db)
    manufacturers = await get_all_manufactures(db)
    count_noodles = await get_count_noodles(db)

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "countries": countries, "manufacturers": manufacturers, "count_noodles": count_noodles}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_noodle_form(request: Request, db: AsyncSession = Depends(get_db)):
    countries = await get_all_countries(db)
    manufacturers = await get_all_manufactures(db)

    return templates.TemplateResponse(
        "create.html",
        {"request": request, "countries": countries, "manufacturers": manufacturers}
    )

@router.post("/create")
async def create_noodle_post(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    image: str = Form(...),
    manufacture_id: int = Form(...),
    country_id: int = Form(...),
    code: str = Form(...),
    recommendation: str = Form(None),
    new_manufacture: str = Form(None),
    new_country: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    if code != settings.noodle_password:
        raise HTTPException(status_code=400, detail="Неверный код доступа")

    is_recommended = recommendation == "true"

    await create_noodle(
        db, title, description, image, manufacture_id, country_id, is_recommended,
        new_manufacture, new_country
    )

    return RedirectResponse(url="/", status_code=303)

@router.get("/countries/{country}", response_class=HTMLResponse)
async def read_noodles_by_country(
    country: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    countries = await get_all_countries(db)
    noodles = await get_noodles_by_country(db, country)
    manufacturers = sorted({n.manufacture.name for n in noodles if n.manufacture}, key=str.lower)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "noodles": noodles,
            "countries": countries,
            "manufacturers": manufacturers,
        },
    )

@router.get("/manufacturers/{manufacture}", response_class=HTMLResponse)
async def read_noodles_by_manufacture(
    manufacture: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    countries = await get_all_countries(db)
    noodles = await get_noodles_by_manufacture(db, manufacture)
    country = noodles[0].country.name if noodles else None

    manufacturers_from_country = []
    if country:
        stmt = (
            select(Manufacture.name)
            .join(Noodle.manufacture)
            .join(Noodle.country)
            .filter(Country.name == country)
            .distinct()
        )
        result = await db.execute(stmt)
        manufacturer_names = [row[0] for row in result.fetchall()]
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

@router.get("/noodle/{id}", response_class=HTMLResponse)
async def read_noodle(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    noodle = await get_noodle_by_id(db, id)
    if not noodle:
        raise HTTPException(status_code=404, detail="Noodle not found")
    page_title = noodle.title
    countries = await get_all_countries(db)

    return templates.TemplateResponse(
        "noodle_details.html",
        {
            "request": request,
            "noodle": noodle,
            "countries": countries,
            "page_title": page_title,
        },
    )

@router.post("/noodle/{id}/edit")
async def edit_noodle(
    id: int,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    password = payload.get("password")
    if password != settings.noodle_password:
        raise HTTPException(status_code=403, detail="Неверный пароль")

    await update_noodle(
        db, id,
        description=payload.get("description"),
        recommendation=payload.get("recommendation")
    )
    return {"status": "ok"}

@router.get("/recommendation", response_class=HTMLResponse)
async def read_noodles_by_recommendation(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    countries = await get_all_countries(db)
    noodles = await get_recommended_noodles(db)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "noodles": noodles,
            "countries": countries,
        },
    )
