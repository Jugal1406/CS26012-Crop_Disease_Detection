"""
backend/models.py
=================
SQLAlchemy ORM models for the Crop Disease Detection platform.

Models (9 tables — matches the approved Module 7 schema):
  1. User            — application user identity (auth via external provider)
  2. Farm            — user's farm / land plot with regional location
  3. Crop            — supported crop reference data (seed-time only)
  4. Disease         — ML model disease class reference data (seed-time only)
  5. Scan            — central transaction record (one per image upload)
  6. Prediction      — ML model output per scan (MobileNetV2 result)
  7. WeatherSnapshot — optional weather context at scan time (LLM enrichment)
  8. Report          — structured LLM advisory output (per scan, per language)
  9. ModelVersion    — model artifact registry for reproducibility / traceability

Design rules enforced here:
  - NO passwords, OTPs, or auth tokens stored
  - NO raw image bytes stored (image_path is an object-storage key / path)
  - ML prediction (Prediction) is always separate from LLM output (Report)
  - Weather is optional enrichment — never part of the classifier
  - All timestamps are TIMESTAMPTZ via DateTime(timezone=True)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database import Base


# ---------------------------------------------------------------------------
# Helper — UTC-aware default for created_at / updated_at
# ---------------------------------------------------------------------------
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ===========================================================================
# 1. User
# ===========================================================================
class User(Base):
    """
    Application user identity.

    Authentication is fully delegated to an external provider (Firebase or
    equivalent). This table stores the application-level profile only.

    NEVER stored here: OTPs, passwords, hashed passwords, tokens, secrets.
    The backend verifies the provider token and maps auth_provider_user_id
    to this table's primary key (id).
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Internal application user UUID",
    )
    auth_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="External auth provider name, e.g. 'firebase'",
    )
    auth_provider_user_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique user ID issued by the external provider (Firebase UID etc.)",
    )
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Farmer's preferred display name",
    )
    email: Mapped[str | None] = mapped_column(
        String(254),
        nullable=True,
        unique=True,
        index=True,
        comment="User email — unique when present; sourced from auth provider",
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
        index=True,
        comment="E.164 phone number e.g. +919876543210 — unique when present",
    )
    preferred_language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
        server_default="en",
        comment="BCP-47 language tag for report generation e.g. 'en', 'hi', 'gu'",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Soft-delete flag; set to FALSE to deactivate without data loss",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
    )

    # Relationships
    farms: Mapped[list["Farm"]] = relationship(
        "Farm", back_populates="user", cascade="all, delete-orphan"
    )
    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} provider={self.auth_provider}>"


# ===========================================================================
# 2. Farm
# ===========================================================================
class Farm(Base):
    """
    A named farm or land plot owned by a user.

    Location fields (village, district, state) are used to:
      1. Provide regional context to the Weather API
      2. Generate a human-readable location string for the LLM
         e.g. "Anand, Gujarat, India"

    latitude / longitude are OPTIONAL and are used ONLY for the Weather API.
    They are NEVER sent to the LLM.
    """

    __tablename__ = "farms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Farm name e.g. 'North Field'"
    )
    village: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    area_hectares: Mapped[float | None] = mapped_column(
        Numeric(8, 2), nullable=True, comment="Farm size in hectares"
    )
    latitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
        comment="Optional GPS latitude — used for Weather API only, never sent to LLM",
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
        comment="Optional GPS longitude — used for Weather API only, never sent to LLM",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="farms")
    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="farm")
    weather_snapshots: Mapped[list["WeatherSnapshot"]] = relationship(
        "WeatherSnapshot", back_populates="farm", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Farm id={self.id} name='{self.name}' user={self.user_id}>"


# ===========================================================================
# 3. Crop
# ===========================================================================
class Crop(Base):
    """
    Supported crop reference table.

    Populated once at seed time. Not user-editable.
    Defines the valid set of crops for scans, disease classes, and model versions.

    is_supported = True  ↔  a production model is loaded for this crop.
    is_supported = False ↔  model in training; inference will be rejected.
    """

    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True,
        comment="Internal key used by the API e.g. 'chili'"
    )
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="English display name e.g. 'Chili Pepper'"
    )
    display_name_hi: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Hindi display name"
    )
    display_name_gu: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Gujarati display name"
    )
    model_key: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True,
        comment="Key used in inference.py model registry lookup"
    )
    is_supported: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
        comment="True once a production model is available for this crop"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, server_default=func.now()
    )

    # Relationships
    diseases: Mapped[list["Disease"]] = relationship("Disease", back_populates="crop")
    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="crop")
    model_versions: Mapped[list["ModelVersion"]] = relationship(
        "ModelVersion", back_populates="crop"
    )

    def __repr__(self) -> str:
        return f"<Crop id={self.id} name='{self.name}' supported={self.is_supported}>"


# ===========================================================================
# 4. Disease
# ===========================================================================
class Disease(Base):
    """
    ML model disease class reference table.

    Represents the disease/class labels that the MobileNetV2 model knows.
    Contains GENERAL disease metadata only — description and severity.

    Does NOT contain:
      - organic_treatment
      - chemical_treatment
      - prevention_tips
    Those are context-dependent and are generated by the LLM per scan,
    then stored in the Report table.
    """

    __tablename__ = "diseases"
    __table_args__ = (
        UniqueConstraint("crop_id", "label", name="uq_disease_crop_label"),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    crop_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("crops.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Raw model class label e.g. 'Chili__Healthy'"
    )
    display_name: Mapped[str] = mapped_column(
        String(150), nullable=False,
        comment="Clean human-readable name e.g. 'Healthy Chili Leaf'"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="General disease background and visible symptoms"
    )
    severity: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
        comment="General severity level: none | low | medium | high"
    )
    is_healthy: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
        comment="True if this class represents a healthy / disease-free leaf"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, server_default=func.now()
    )

    # Relationships
    crop: Mapped["Crop"] = relationship("Crop", back_populates="diseases")
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction", back_populates="disease"
    )

    def __repr__(self) -> str:
        return f"<Disease id={self.id} label='{self.label}' crop={self.crop_id}>"


# ===========================================================================
# 5. Scan
# ===========================================================================
class Scan(Base):
    """
    Central transaction record — one row per image uploaded by a user.

    Primary workflow:  authenticated user → user_id → optional farm_id → scan
    Fallback workflow: anonymous/guest scan — user_id is NULL, session_token used

    Status lifecycle:
      pending       → ML inference in progress
      success       → confident prediction + report generated
      low_confidence → below threshold; no report or weather snapshot created
      error         → processing failure

    image_path is an object-storage key or relative filesystem path.
    Raw image bytes are NEVER stored in PostgreSQL.
    """

    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="NULL = anonymous/guest scan (fallback only; authenticated is primary flow)",
    )
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional farm link; user may scan without specifying a farm",
    )
    crop_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("crops.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    image_path: Mapped[str] = mapped_column(
        String(512), nullable=False,
        comment="Object storage key or relative path — NOT raw image bytes"
    )
    image_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_mime_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="e.g. 'image/jpeg', 'image/png'"
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending",
        comment="pending | success | low_confidence | error"
    )
    session_token: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True,
        comment="Anonymous session identifier — used only for guest/fallback scans"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
        server_default=func.now(), index=True,
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="scans")
    farm: Mapped["Farm | None"] = relationship("Farm", back_populates="scans")
    crop: Mapped["Crop"] = relationship("Crop", back_populates="scans")
    prediction: Mapped["Prediction | None"] = relationship(
        "Prediction", back_populates="scan", uselist=False,
        cascade="all, delete-orphan"
    )
    weather_snapshot: Mapped["WeatherSnapshot | None"] = relationship(
        "WeatherSnapshot", back_populates="scan", uselist=False,
        cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="scan", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Scan id={self.id} crop={self.crop_id} status='{self.status}'>"


# ===========================================================================
# 6. Prediction
# ===========================================================================
class Prediction(Base):
    """
    ML model output for a scan.

    This is the AUTHORITATIVE record of what MobileNetV2 produced.
    The LLM NEVER changes or overrides this prediction.

    Confidence gate:
      is_confident = True  → disease_id is set; LLM report generation proceeds
      is_confident = False → disease_id is NULL; no report or weather snapshot created

    raw_scores (JSONB): full softmax probability vector for analytics / retraining.
    """

    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # 1-to-1 with Scan
        index=True,
    )
    disease_id: Mapped[int | None] = mapped_column(
        SmallInteger,
        ForeignKey("diseases.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="NULL when confidence < threshold (low-confidence rejection)",
    )
    model_version_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("model_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Pinned to the exact model artifact that produced this result",
    )
    confidence: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False,
        comment="Softmax probability of the top class (0.0000–1.0000)"
    )
    threshold_used: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False,
        comment="CONFIDENCE_THRESHOLD value at the time of this scan"
    )
    is_confident: Mapped[bool] = mapped_column(
        Boolean, nullable=False,
        comment="True when confidence >= threshold_used"
    )
    raw_scores: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Full softmax vector e.g. {\"Chili__Healthy\": 0.92, ...} — for analytics"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, server_default=func.now()
    )

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan", back_populates="prediction")
    disease: Mapped["Disease | None"] = relationship("Disease", back_populates="predictions")
    model_version: Mapped["ModelVersion"] = relationship(
        "ModelVersion", back_populates="predictions"
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction scan={self.scan_id} "
            f"confidence={self.confidence} confident={self.is_confident}>"
        )


# ===========================================================================
# 7. WeatherSnapshot
# ===========================================================================
class WeatherSnapshot(Base):
    """
    Optional weather context recorded at scan time.

    Data flow:
      farm location → FastAPI → Weather API → WeatherSnapshot → LLM context

    All measurement columns are nullable — weather is enrichment, not a
    classifier input. A scan may have zero or one weather snapshot.

    Privacy:
      GPS coordinates are used ONLY to call the Weather API.
      The LLM receives a regional text string, NOT coordinates.
    """

    __tablename__ = "weather_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    temperature_c: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="Ambient temperature in °C"
    )
    humidity_pct: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="Relative humidity %"
    )
    rainfall_mm: Mapped[float | None] = mapped_column(
        Numeric(6, 2), nullable=True, comment="Recent rainfall in mm"
    )
    wind_speed_kmh: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="Wind speed in km/h"
    )
    weather_condition: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="e.g. 'Partly Cloudy', 'Heavy Rain'"
    )
    data_source: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="e.g. 'Open-Meteo', 'OpenWeatherMap', 'manual'"
    )
    recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Actual weather observation time from the API response"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, server_default=func.now()
    )

    # Relationships
    scan: Mapped["Scan | None"] = relationship("Scan", back_populates="weather_snapshot")
    farm: Mapped["Farm | None"] = relationship("Farm", back_populates="weather_snapshots")

    def __repr__(self) -> str:
        return (
            f"<WeatherSnapshot farm={self.farm_id} scan={self.scan_id} "
            f"temp={self.temperature_c}°C condition='{self.weather_condition}'>"
        )


# ===========================================================================
# 8. Report
# ===========================================================================
class Report(Base):
    """
    Structured LLM advisory report for a successful scan.

    Generated ONLY when is_confident = True in the corresponding Prediction.
    Low-confidence scans produce NO report row.

    The LLM receives:
      - disease display name + description (from Disease)
      - confidence score (from Prediction)
      - weather context (from WeatherSnapshot)
      - regional location string e.g. "Anand, Gujarat, India" (from Farm)
      - preferred language (from User)

    One scan can have multiple Report rows — one per language code.
    UNIQUE(scan_id, language_code) prevents duplicates.

    JSONB fields (symptoms, possible_causes, management_steps,
    prevention_steps, warning_signs) store LLM-validated JSON arrays,
    enabling structured frontend rendering without client-side parsing.

    The LLM is an advisory content generator ONLY.
    It does NOT determine or override the disease classification.
    """

    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("scan_id", "language_code", name="uq_report_scan_language"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    language_code: Mapped[str] = mapped_column(
        String(10), nullable=False,
        comment="BCP-47 language tag e.g. 'en', 'hi', 'gu'"
    )
    disease_name: Mapped[str] = mapped_column(
        String(150), nullable=False,
        comment="Translated disease display name used in this report"
    )
    confidence_interpretation: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="LLM plain-language explanation of what the confidence score means"
    )
    summary: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="2–3 sentence actionable diagnosis summary"
    )
    symptoms: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="JSONB array of visible symptom descriptions"
    )
    possible_causes: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="JSONB array of contributing factors / environmental causes"
    )
    local_context: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Region/season-specific agricultural context from the LLM"
    )
    management_steps: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="JSONB ordered list of management and treatment actions"
    )
    prevention_steps: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="JSONB ordered list of prevention recommendations"
    )
    warning_signs: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="JSONB list of signs indicating the farmer should escalate / seek expert help"
    )
    expert_verification_recommended: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
        comment="True if the LLM recommends consulting an agricultural expert"
    )
    disclaimer: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Standard advisory disclaimer appended to every report"
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
        comment="Timestamp when the LLM produced this report"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, server_default=func.now()
    )

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan", back_populates="reports")

    def __repr__(self) -> str:
        return (
            f"<Report scan={self.scan_id} lang='{self.language_code}' "
            f"disease='{self.disease_name}'>"
        )


# ===========================================================================
# 9. ModelVersion
# ===========================================================================
class ModelVersion(Base):
    """
    Model artifact registry.

    Every Prediction is pinned to the ModelVersion that produced it.
    This enables full reproducibility — historical predictions remain
    traceable even after the production model is upgraded.

    Only ONE version per crop should have is_active = True at any time.
    Promotion workflow:
      1. Set current active version is_active = False
      2. Set new version is_active = True
      Historical predictions remain linked to their original version.

    Example state:
      Chili V1 (v1.0.0): is_active = True  ← production baseline
      Chili V2 (v2.0-aug): is_active = False ← experimental; not promoted yet
      Potato V1: is_active = True
    """

    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("crop_id", "version_tag", name="uq_model_crop_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crop_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("crops.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    version_tag: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Human-readable version tag e.g. 'v1.0.0', 'chili-v2-aug'"
    )
    architecture: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Model architecture name e.g. 'MobileNetV2'"
    )
    artifact_path: Mapped[str] = mapped_column(
        String(512), nullable=False,
        comment="Path to the .h5 file or SavedModel directory"
    )
    num_classes: Mapped[int] = mapped_column(
        SmallInteger, nullable=False,
        comment="Number of output classes in the model"
    )
    test_accuracy: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True,
        comment="Test-set accuracy from training evaluation (0.0000–1.0000)"
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Training notes, dataset version used, augmentation details"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
        comment="True = currently serving production inference for this crop",
        index=True,
    )
    deployed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Timestamp when this version was promoted to production"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, server_default=func.now()
    )

    # Relationships
    crop: Mapped["Crop"] = relationship("Crop", back_populates="model_versions")
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction", back_populates="model_version"
    )

    def __repr__(self) -> str:
        return (
            f"<ModelVersion id={self.id} crop={self.crop_id} "
            f"tag='{self.version_tag}' active={self.is_active}>"
        )
