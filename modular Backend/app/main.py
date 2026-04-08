from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.core.config import settings
from app.api.v1.router import api_router
from app.websocket.manager import websocket_manager
from app.schemas.ready import HealthResponse

load_dotenv()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} Backend is running",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        websocket_connections=websocket_manager.get_connection_count(),
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
    )
