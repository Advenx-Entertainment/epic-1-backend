from fastapi import APIRouter
from app.modules.arena_hud.router import router as arena_hud_router
from app.modules.commanding_officer.router import router as commanding_officer_router
from app.modules.god.router import router as god_router

api_router = APIRouter()

api_router.include_router(arena_hud_router, prefix="/arena", tags=["Arena HUD"])
api_router.include_router(commanding_officer_router, prefix="/co", tags=["Commanding Officer"])
api_router.include_router(god_router, prefix="/god", tags=["GOD"])
