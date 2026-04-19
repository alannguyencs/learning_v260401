"""Central API router aggregating all API endpoints."""

from fastapi import APIRouter

from src.api import auth, content, dashboard, login, root, slide_likes, slides

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(login.router, tags=["login"])
api_router.include_router(root.router, prefix="/api", tags=["root"])
api_router.include_router(content.router, prefix="/api", tags=["content"])
api_router.include_router(slides.router, prefix="/api", tags=["slides"])
api_router.include_router(slide_likes.router, prefix="/api", tags=["slide-likes"])
api_router.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
