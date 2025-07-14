from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.v1.router import router as v1_router
from app.core.config.env import get_env
from app.core.db.setup import setup_db

DEBUG = get_env("DEBUG", "True") == "True"
PORT = int(get_env("PORT", "8000")) or 8000


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    setup_db()
    yield


app = FastAPI(
    lifespan=lifespan,
    docs_url=("/docs" if DEBUG is True else None),
    redoc_url=("/redoc" if DEBUG is True else None),
    openapi_url=("/openapi.json" if DEBUG is True else None),
)

app.include_router(v1_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://loslc.tech",
        "https://forms.loslc.tech",
    ],  # Or ["http://localhost:3000"] for stricter control
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_app():
    uvicorn.run("app:app", reload=DEBUG, port=PORT, host="0.0.0.0")
