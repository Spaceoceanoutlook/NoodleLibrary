import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# from noodlelibrary.routers import pages

app = FastAPI(title="Movie Library API", version="0.1.0")
app.mount("/static", StaticFiles(directory="noodlelibrary/static"), name="static")
# app.include_router(pages.router, tags=["Web Pages"], include_in_schema=False)


if __name__ == "__main__":
    uvicorn.run("noodlelibrary.main:app", host="0.0.0.0", port=8000, reload=True)
