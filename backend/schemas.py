"""
backend/schemas.py
==================
Pydantic data contracts for the Crop Disease Detection API.

Defines request/response data models and standardized error formats for all
endpoints. Ensures predictable JSON responses, automated data validation,
and clean OpenAPI documentation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    """Schema for GET / and GET /api/v1/health."""

    status: str = Field(
        default="running",
        description="Current server operational status",
        examples=["running"],
    )
    api_version: str = Field(
        ...,
        description="Semantic version of the Crop Disease Detection API",
        examples=["1.0.0"],
    )
    models: Dict[str, str] = Field(
        ...,
        description="Map of registered crop names to their model loading status ('loaded' or error detail)",
        examples=[{"chili": "loaded", "potato": "unsupported", "groundnut": "unsupported"}],
    )


class PredictionDetails(BaseModel):
    """Encapsulates the core ML diagnostic output."""

    disease: str = Field(
        ...,
        description="Diagnosed plant disease or healthy condition name",
        examples=["Healthy Leaf"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Softmax output probability score of the diagnosed class (0.0 to 1.0)",
        examples=[0.9421],
    )


class PredictionResponse(BaseModel):
    """
    Standardized response schema for disease predictions with confidence gating.

    Provides a clean, predictable envelope:
    {
        "status": "success",          # "success" or "low_confidence"
        "crop": "chili",
        "is_confident": true,
        "threshold": 0.70,
        "prediction": {
            "disease": "Healthy Leaf",
            "confidence": 0.9421
        },
        "message": "Diagnosis accepted with high confidence."
    }
    """

    status: str = Field(
        ...,
        description="Response status: 'success' for accepted diagnosis, 'low_confidence' when below threshold",
        examples=["success", "low_confidence"],
    )
    crop: str = Field(
        ...,
        description="Normalized crop identifier",
        examples=["chili"],
    )
    is_confident: bool = Field(
        ...,
        description="Whether the prediction confidence meets or exceeds the configured decision threshold",
        examples=[True],
    )
    threshold: float = Field(
        ...,
        description="The confidence decision threshold used to screen this prediction (e.g. 0.70)",
        examples=[0.70],
    )
    prediction: PredictionDetails = Field(
        ...,
        description="Diagnostic prediction details",
    )
    message: Optional[str] = Field(
        default=None,
        description="Actionable explanation or user guidance, particularly when confidence is below threshold",
        examples=["Diagnosis accepted with high confidence."],
    )

    # Backward compatibility aliases for seamless client migration
    disease: Optional[str] = Field(
        default=None,
        description="[Legacy alias] Primary disease name for older API consumers",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="[Legacy alias] Primary confidence score for older API consumers",
    )


class ErrorResponse(BaseModel):
    """Standardized error envelope for API exceptions and validation failures."""

    status: str = Field(
        ...,
        description="Machine-readable error category (e.g. 'model_unavailable', 'invalid_image', 'validation_error')",
        examples=["model_unavailable"],
    )
    message: str = Field(
        ...,
        description="Human-readable explanation of the error",
        examples=["Crop 'potato' is not supported. Currently supported crops: ['chili']."],
    )


# ===========================================================================
# Module 12: Farm Profile & Location Schemas
# ===========================================================================


class FarmCreateRequest(BaseModel):
    """Schema for POST /api/v1/farms to register a new farm."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Farm name e.g. 'Main Farm'",
        examples=["Main Farm"],
    )
    village: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Village or town where the farm is located",
        examples=["Petlad"],
    )
    district: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="District e.g. 'Anand'",
        examples=["Anand"],
    )
    state: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="State e.g. 'Gujarat'",
        examples=["Gujarat"],
    )
    area_hectares: Optional[float] = Field(
        default=None,
        gt=0.0,
        le=100000.0,
        description="Optional farm land area in hectares (> 0)",
        examples=[2.5],
    )
    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Optional GPS latitude (-90.0 to 90.0)",
        examples=[22.5645],
    )
    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Optional GPS longitude (-180.0 to 180.0)",
        examples=[72.9289],
    )

    @field_validator("name", "village", "district", "state")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or blank")
        return stripped


class FarmUpdateRequest(BaseModel):
    """Schema for PUT /api/v1/farms/{farm_id} to update an existing farm."""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated farm name",
    )
    village: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated village",
    )
    district: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated district",
    )
    state: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated state",
    )
    area_hectares: Optional[float] = Field(
        default=None,
        gt=0.0,
        le=100000.0,
        description="Updated farm land area in hectares (> 0)",
    )
    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Updated GPS latitude (-90.0 to 90.0)",
    )
    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Updated GPS longitude (-180.0 to 180.0)",
    )

    @field_validator("name", "village", "district", "state")
    @classmethod
    def validate_non_empty_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Field cannot be empty or blank")
            return stripped
        return v


class FarmResponse(BaseModel):
    """Standardized response schema for a farm entity."""

    id: str = Field(..., description="Unique UUID identifier of the farm")
    name: str = Field(..., description="Farm name")
    village: Optional[str] = Field(None, description="Village or town")
    district: Optional[str] = Field(None, description="District")
    state: Optional[str] = Field(None, description="State")
    area_hectares: Optional[float] = Field(None, description="Area in hectares")
    latitude: Optional[float] = Field(None, description="GPS latitude")
    longitude: Optional[float] = Field(None, description="GPS longitude")
    location_text: Optional[str] = Field(None, description="Human-readable location summary")
    has_location: bool = Field(False, description="True if GPS coordinates are available")
    is_active: bool = Field(True, description="Active status")
    created_at: Optional[str] = Field(None, description="ISO timestamp of creation")
    updated_at: Optional[str] = Field(None, description="ISO timestamp of last update")


class FarmListResponse(BaseModel):
    """Response containing a list of farms owned by the authenticated user."""

    status: str = "success"
    count: int = Field(..., description="Total number of active farms")
    farms: List[FarmResponse] = Field(default_factory=list, description="List of farms")


# ---------------------------------------------------------------------------
# Weather Integration Schemas (Module 13)
# ---------------------------------------------------------------------------
class WeatherResponse(BaseModel):
    """Normalized weather response for a farm."""

    status: str = "success"
    farm_id: str = Field(..., description="Farm UUID")
    farm_name: str = Field(..., description="Farm name")
    has_location: bool = Field(..., description="Whether farm has valid GPS coordinates")
    message: Optional[str] = Field(None, description="Status/guidance message")
    temperature_c: Optional[float] = Field(None, description="Ambient temperature in °C")
    humidity_pct: Optional[float] = Field(None, description="Relative humidity %")
    rainfall_mm: Optional[float] = Field(None, description="Rainfall / precipitation in mm")
    wind_speed_kmh: Optional[float] = Field(None, description="Wind speed in km/h")
    weather_condition: Optional[str] = Field(None, description="Weather condition description")
    data_source: Optional[str] = Field(None, description="Data source provider name")
    recorded_at: Optional[str] = Field(None, description="ISO timestamp of weather observation")
    cached: bool = Field(False, description="Whether snapshot was retrieved from database cache")
    snapshot_id: Optional[str] = Field(None, description="Database snapshot UUID")


# ---------------------------------------------------------------------------
# LLM Advisory Report Schemas (Module 14)
# ---------------------------------------------------------------------------
class ReportStructuredResponse(BaseModel):
    """Strict schema validated against Groq LLM JSON output."""

    disease_name: str = Field(..., description="Localized/translated disease name")
    confidence_interpretation: Optional[str] = Field(
        None, description="Plain-language explanation of what the confidence score means"
    )
    summary: str = Field(..., description="Actionable 2-3 sentence overview")
    symptoms: List[str] = Field(
        default_factory=list, description="Observed symptom descriptions"
    )
    possible_causes: List[str] = Field(
        default_factory=list, description="Environmental and biological contributing factors"
    )
    local_context: Optional[str] = Field(
        None, description="Region and weather-aware agricultural context"
    )
    management_steps: List[str] = Field(
        default_factory=list,
        description="Actionable non-chemical and cultural management steps",
    )
    prevention_steps: List[str] = Field(
        default_factory=list, description="Preventative and cultural agronomic practices"
    )
    warning_signs: List[str] = Field(
        default_factory=list, description="Critical warning signs requiring urgent escalation"
    )
    expert_verification_recommended: bool = Field(
        False, description="Whether formal in-person agricultural extension verification is advised"
    )
    disclaimer: str = Field(
        ...,
        description="Standard advisory and chemical disclaimer (recommending KVK/certified extension)",
    )


class ReportResponse(BaseModel):
    """Full database representation of an advisory report returned to client."""

    id: str = Field(..., description="Report UUID")
    scan_id: str = Field(..., description="Scan UUID")
    language_code: str = Field(..., description="BCP-47 language tag (en, hi, gu)")
    disease_name: str = Field(..., description="Disease display name in report")
    confidence_interpretation: Optional[str] = None
    summary: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    possible_causes: List[str] = Field(default_factory=list)
    local_context: Optional[str] = None
    management_steps: List[str] = Field(default_factory=list)
    prevention_steps: List[str] = Field(default_factory=list)
    warning_signs: List[str] = Field(default_factory=list)
    expert_verification_recommended: bool = False
    disclaimer: Optional[str] = None
    generated_at: Optional[str] = None
    created_at: Optional[str] = None


class DiagnosisResponse(BaseModel):
    """Complete diagnostic + localized advisory report response contract."""

    status: str = Field(..., description="Diagnosis status: success | low_confidence | error")
    crop: str = Field(..., description="Diagnosed crop name")
    is_confident: bool = Field(..., description="True if ML confidence exceeds threshold")
    confidence: float = Field(..., description="Authoritative MobileNetV2 confidence score")
    threshold: float = Field(..., description="Confidence threshold used")
    disease: Optional[str] = Field(None, description="Raw ML disease label")
    disease_display_name: Optional[str] = Field(None, description="Clean disease display name")
    scan_id: Optional[str] = Field(None, description="Persisted Scan UUID")
    message: str = Field(..., description="Guidance or diagnostic outcome message")
    farm: Optional[Dict[str, Any]] = Field(None, description="Associated farm details")
    weather: Optional[Dict[str, Any]] = Field(None, description="Linked weather snapshot")
    report: Optional[ReportResponse] = Field(
        None, description="Structured LLM advisory report (only present when confident)"
    )


# ===========================================================================
# Module 16: Scan History and Pagination Schemas
# ===========================================================================


class ScanPredictionSummary(BaseModel):
    """Summarized ML prediction details for scan history cards and lists."""

    disease_label: Optional[str] = Field(None, description="Raw ML class label")
    disease_display_name: Optional[str] = Field(None, description="Human-readable disease name")
    confidence: Optional[float] = Field(None, description="Softmax confidence score (0.0 to 1.0)")
    confidence_percentage: Optional[float] = Field(None, description="Confidence as percentage (0 to 100)")
    is_confident: bool = Field(False, description="True if confidence >= threshold")
    is_healthy: bool = Field(False, description="True if diagnosed as healthy leaf")


class ScanFarmSummary(BaseModel):
    """Brief farm information associated with a historical scan."""

    id: str = Field(..., description="Farm UUID")
    name: str = Field(..., description="Farm name")
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    location_text: Optional[str] = None


class ScanSummaryItem(BaseModel):
    """Scan history item representation."""

    id: str = Field(..., description="Scan UUID")
    crop: str = Field(..., description="Crop identifier e.g. 'chili'")
    crop_display_name: str = Field(..., description="Display name e.g. 'Chili Pepper'")
    status: str = Field(..., description="Scan status: success | low_confidence | pending | error")
    image_path: str = Field(..., description="Relative storage path or key")
    image_url: Optional[str] = Field(None, description="Authenticated API endpoint to stream image bytes")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    date_formatted: str = Field(..., description="Localized formatted date string")
    prediction: Optional[ScanPredictionSummary] = None
    farm: Optional[ScanFarmSummary] = None
    has_report: bool = Field(False, description="True if at least one advisory report exists")
    available_report_languages: List[str] = Field(
        default_factory=list, description="List of generated report language codes (e.g. ['en', 'hi'])"
    )


class ScanPaginationResponse(BaseModel):
    """Standard pagination envelope for scan history queries."""

    items: List[ScanSummaryItem]
    total: int = Field(..., description="Total count of matching scans")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total pages available")
    has_next: bool = Field(..., description="True if there is a next page")
    has_prev: bool = Field(..., description="True if there is a previous page")


class ScanDetailResponse(BaseModel):
    """Complete diagnostic scan inspection record."""

    id: str
    crop: str
    crop_display_name: str
    status: str
    image_path: str
    image_url: Optional[str] = None
    created_at: str
    date_formatted: str
    prediction: Optional[ScanPredictionSummary] = None
    farm: Optional[ScanFarmSummary] = None
    weather: Optional[Dict[str, Any]] = None
    has_report: bool = False
    available_report_languages: List[str] = Field(default_factory=list)
    report: Optional[ReportResponse] = None
    rejection_guidance: Optional[str] = None
