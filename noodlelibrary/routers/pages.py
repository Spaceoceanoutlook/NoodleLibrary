from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
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


@router.get("/", response_class=HTMLResponse, summary="Read Films")
async def read_films(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Noodle)
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
