"""Main FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.configs import settings
from src.api.api_router import api_router
from src.database import Base, engine, SessionLocal  # noqa: F401  # pylint: disable=unused-import
from src import models  # noqa: F401  # pylint: disable=unused-import

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Learning App API",
    description="Backend API for the Learning App",
    version="1.0.0",
)

# Session middleware must be added before CORS
app.add_middleware(SessionMiddleware, secret_key=settings.middleware_secret_key)

origins = [origin.strip() for origin in settings.allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {"message": "Learning App API", "status": "running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
