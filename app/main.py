from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from .api import router as api_router

app = FastAPI(title="Trip Splitter")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(api_router)


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
