import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = Path(settings.model_path)
    if not model_path.exists():
        logger.warning(
            "Model not found at '%s'. Server starting without a trained model — "
            "POST /admin/train to train it.",
            model_path,
        )
    yield


app = FastAPI(
    title="Lagos Smart Weather Prediction System",
    description="Live Lagos atmospheric data + Random Forest rain prediction, validated against NASA POWER.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=86400,
)

app.include_router(router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "lagos-weather-prediction"}
