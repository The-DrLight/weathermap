import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.ml.predictor import rain_predictor

logger = logging.getLogger("uvicorn.error")


async def _train_in_background() -> None:
    from train_model import main as train_model_main

    try:
        await asyncio.to_thread(train_model_main)
        rain_predictor.reload()
        logger.info("Background model training complete.")
    except Exception:
        logger.exception("Background model training failed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = Path(settings.model_path)
    if model_path.exists():
        logger.info("Model found at '%s'. Loading.", model_path)
    else:
        logger.warning(
            "Model not found at '%s'. Starting server now and training in the "
            "background — /predict and /weather/live return 503 until it's ready.",
            model_path,
        )
        asyncio.create_task(_train_in_background())
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
