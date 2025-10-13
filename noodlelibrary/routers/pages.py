from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.get("/", response_class=HTMLResponse, summary="Read Noodles")
async def read_noodles(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Noodle).order_by(desc(Noodle.id))
    result = await db.execute(stmt)
    noodles = result.scalars().all()
    noodles_for_template = [NoodleBase.model_validate(noodle) for noodle in noodles]
    country_for_template = await get_all_country(db)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "noodles": noodles_for_template,
            "countries": country_for_template,
        },
    )


@router.get("/create", response_class=HTMLResponse, summary="Show Create Noodle Form")
async def create_noodle_form(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    stmt_manufacture = select(Manufacture)
    result_manufacture = await db.execute(stmt_manufacture)
    manufacture_list = result_manufacture.scalars().all()

    stmt_country = select(Country)
    result_country = await db.execute(stmt_country)
    country_list = result_country.scalars().all()

    return templates.TemplateResponse(
        "create.html",
        {
            "request": request,
            "manufacture_list": manufacture_list,
            "country_list": country_list,
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
    recommendation: str = Form("false"),
    db: AsyncSession = Depends(get_db),
):
    is_recommended = recommendation == "true"
    if code != "456321":
        raise HTTPException(status_code=400, detail="Неверный код доступа")
    new_noodle = Noodle(
        title=title,
        description=description,
        image=image,
        manufacture_id=manufacture_id,
        country_id=country_id,
        recommendation=is_recommended,
    )

    db.add(new_noodle)
    await db.commit()
    await db.refresh(new_noodle)

    return RedirectResponse(url="/", status_code=303)
