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
        logger.warning("Model not found — training now. This will take ~2 minutes.")
        from train_model import main as train_model_main

        train_model_main()
        logger.info("Model training complete.")
    yield


app = FastAPI(
    title="Lagos Smart Weather Prediction System",
    description="Live Lagos atmospheric data + Random Forest rain prediction, validated against NASA POWER.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "lagos-weather-prediction"}
