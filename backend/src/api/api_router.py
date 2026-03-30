"""Central API router aggregating all API endpoints."""

from fastapi import APIRouter

from src.api import auth, login, root

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(login.router, tags=["login"])
api_router.include_router(root.router, prefix="/api", tags=["root"])
