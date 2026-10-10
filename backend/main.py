"""
backend/main.py
===============
FastAPI application entry point for the Crop Disease Detection API.

Responsibilities (this file only):
  - Application lifecycle (startup model loading, shutdown cleanup)
  - HTTP route definitions
  - Request validation and parsing
  - Mapping inference-layer exceptions to appropriate HTTP responses
  - CORS configuration

This file deliberately contains NO:
  - ML model logic  (see inference.py)
  - Database logic  (future module)
  - Treatment/knowledge-base logic  (future module)
  - Authentication logic  (future module)
  - Business rules beyond routing and HTTP contract
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user

import inference
from inference import (
    InvalidImageError,
    ModelNotAvailableError,
    get_model_statuses,
    load_all_available_models,
)
from config import CONFIDENCE_THRESHOLD, MAX_UPLOAD_SIZE_BYTES
from schemas import (
    ErrorResponse,
    HealthResponse,
    PredictionDetails,
    PredictionResponse,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
# Configure logging before anything else runs.
# In production this would be replaced with a structured logging setup.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler.

    Startup:  load all available crop models into memory once.
              A model loading failure is logged but does NOT prevent startup —
              the app still serves other crops and returns a clear error for
              the failed one.

    Shutdown: nothing to clean up currently; placeholder for future use
              (e.g. closing DB connection pools).
    """
    logger.info("=== Crop Disease Detection API starting up ===")
    statuses = load_all_available_models()
    for crop, status in statuses.items():
        if status == "loaded":
            logger.info("  [OK]   Model ready: %s", crop)
        else:
            logger.error("  [FAIL] Model failed: %s — %s", crop, status)
    logger.info("=== Startup complete. Model statuses: %s ===", statuses)

    # Validate database connection asynchronously
    from services.system_service import SystemService
    db_status = await SystemService.get_database_status()
    if db_status.get("connected"):
        logger.info("  [OK]   Database ready: %s (latency: %sms)", db_status.get("database"), db_status.get("latency_ms"))
    else:
        logger.warning("  [WARN] Database connection error: %s", db_status.get("error"))

    # Verify Clerk Authentication configuration
    from clerk_auth import CLERK_SECRET_KEY, CLERK_JWKS_URL
    if CLERK_SECRET_KEY:
        logger.info("  [OK]   Clerk Authentication ready (JWKS: %s)", CLERK_JWKS_URL)
    else:
        logger.warning("  [WARN] CLERK_SECRET_KEY is not set in environment.")

    yield

    # Clean up database connection pool on shutdown
    from database import engine
    await engine.dispose()
    logger.info("=== Crop Disease Detection API shutting down ===")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Crop Disease Detection API",
    description=(
        "Production-ready Agricultural Disease Detection API. "
        "Provides leaf disease classification using deep learning models (MobileNetV2). "
        "Currently supports Chili. Potato and Groundnut models will become available as training concludes."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
_ALLOWED_ORIGINS = [
    "http://localhost:5173",   # Vite dev server
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(ModelNotAvailableError)
async def model_not_available_handler(
    request: Request, exc: ModelNotAvailableError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(
            status="model_unavailable",
            message=str(exc),
        ).model_dump(),
    )


@app.exception_handler(InvalidImageError)
async def invalid_image_handler(
    request: Request, exc: InvalidImageError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            status="invalid_image",
            message=str(exc),
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
from routers.auth import router as auth_router
from routers.dashboard import router as dashboard_router
from routers.diagnose import router as diagnose_router, reports_router
from routers.scans import router as scans_router
from routers.farms import (
    router as farms_router,
    create_farm,
    list_farms,
    get_farm,
    update_farm,
    deactivate_farm,
    get_farm_weather,
)

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(farms_router)
app.include_router(diagnose_router)
app.include_router(reports_router)
app.include_router(scans_router)

# Root-level aliases for /farms
alias_farms_router = APIRouter(prefix="/farms", tags=["Farms"], include_in_schema=False)
alias_farms_router.add_api_route("", create_farm, methods=["POST"])
alias_farms_router.add_api_route("/", create_farm, methods=["POST"])
alias_farms_router.add_api_route("", list_farms, methods=["GET"])
alias_farms_router.add_api_route("/", list_farms, methods=["GET"])
alias_farms_router.add_api_route("/{farm_id}", get_farm, methods=["GET"])
alias_farms_router.add_api_route("/{farm_id}", update_farm, methods=["PUT"])
alias_farms_router.add_api_route("/{farm_id}", deactivate_farm, methods=["DELETE"])
alias_farms_router.add_api_route("/{farm_id}/weather", get_farm_weather, methods=["GET"])
app.include_router(alias_farms_router)

# Aliases for dashboard
@app.get(
    "/dashboard",
    tags=["Dashboard"],
    include_in_schema=False,
)
@app.get(
    "/api/v1/users/me/dashboard",
    tags=["Dashboard"],
    summary="Get user dashboard (alias)",
)
async def get_user_dashboard_alias(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from services.dashboard_service import DashboardService
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_dashboard_overview(current_user)



# ---------------------------------------------------------------------------
# Route Handlers
# ---------------------------------------------------------------------------


@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="Health check (v1)",
    description="Returns API status and load state for all crop models.",
    tags=["System"],
)
@app.get(
    "/",
    response_model=HealthResponse,
    summary="Root health check (Legacy alias)",
    description="Maintains backward compatibility with root health check.",
    tags=["System"],
)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="running",
        api_version=app.version,
        models=get_model_statuses(),
    )


@app.get(
    "/api/v1/health/db",
    summary="Database health check (v1)",
    description="Returns PostgreSQL connection status, response latency, and database version.",
    tags=["System"],
)
async def db_health_check():
    from services.system_service import SystemService
    return await SystemService.get_database_status()



_STANDARD_PREDICT_RESPONSES = {
    400: {
        "model": ErrorResponse,
        "description": "Validation error (missing crop or image parameter)",
    },
    422: {
        "model": ErrorResponse,
        "description": "Unprocessable image (corrupt file, wrong dimensions, or unreadable format)",
    },
    503: {
        "model": ErrorResponse,
        "description": "Crop model unavailable (not yet supported or failed to load)",
    },
}


@app.post(
    "/api/v1/predict",
    response_model=PredictionResponse,
    responses=_STANDARD_PREDICT_RESPONSES,
    summary="Predict crop disease from a leaf image (v1)",
    description=(
        "Accepts a crop name and leaf image via multipart/form-data. "
        "Returns the predicted disease condition and softmax confidence score within a structured prediction object."
    ),
    tags=["Disease Diagnosis"],
)
@app.post(
    "/predict",
    response_model=PredictionResponse,
    responses=_STANDARD_PREDICT_RESPONSES,
    summary="Predict crop disease from a leaf image (Legacy alias)",
    description="Backward-compatible endpoint routing to the v1 prediction pipeline.",
    tags=["Disease Diagnosis"],
)
async def predict_disease(
    crop: str = Form(
        ...,
        description="Crop identifier. Supported values: 'chili'.",
        examples=["chili"],
    ),
    image: UploadFile = File(
        ...,
        description="Leaf image file. Accepted formats: JPEG, PNG, BMP, WEBP. Max 10 MB.",
    ),
) -> PredictionResponse:
    # 1. Validate and normalise the crop field
    crop = crop.strip().lower()
    if not crop:
        raise HTTPException(
            status_code=400,
            detail="The 'crop' field must not be blank.",
        )

    # 2. Validate the uploaded file
    if image.filename == "" or image.filename is None:
        raise HTTPException(
            status_code=400,
            detail="No image file was uploaded.",
        )

    # 3. Read image bytes
    image_bytes = await image.read()

    logger.info(
        "Prediction request — crop: '%s', file: '%s', size: %d bytes",
        crop,
        image.filename,
        len(image_bytes),
    )

    # 4. Run inference
    result = inference.predict(crop, image_bytes)

    confidence = float(result["confidence"])
    is_confident = confidence >= CONFIDENCE_THRESHOLD

    if is_confident:
        status = "success"
        message = "Diagnosis accepted with high confidence."
    else:
        status = "low_confidence"
        message = (
            f"Prediction confidence ({confidence * 100:.1f}%) is below the acceptable certainty "
            f"threshold ({CONFIDENCE_THRESHOLD * 100:.1f}%). The leaf image may be blurry, uncentered, "
            f"or showing ambiguous symptoms. Please upload a clearer, well-lit photo focusing directly on the leaf."
        )

    logger.info(
        "Prediction result — crop: '%s', disease: '%s', confidence: %.4f, status: '%s' (threshold: %.2f)",
        crop,
        result["disease"],
        confidence,
        status,
        CONFIDENCE_THRESHOLD,
    )

    # 5. Return standardized Pydantic contract
    return PredictionResponse(
        status=status,
        crop=crop,
        is_confident=is_confident,
        threshold=CONFIDENCE_THRESHOLD,
        prediction=PredictionDetails(
            disease=result["disease"],
            confidence=confidence,
        ),
        message=message,
        # Legacy aliases for smooth migration
        disease=result["disease"],
        confidence=confidence,
    )