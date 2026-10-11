"""
backend/inference.py
====================
ML inference layer for the Crop Disease Detection API.

Responsibilities:
  - Load Keras models once at application startup (not per-request).
  - Apply the exact image preprocessing used during training.
  - Run model inference and return structured prediction data.

This module has NO knowledge of:
  - FastAPI routes or HTTP
  - Database operations
  - Disease treatment information
  - Authentication

Adding a new crop model requires only:
  1. Place <crop>_mobilenetv2.keras and <crop>_mobilenetv2_meta.json in models/
  2. Add an entry to CROP_MODEL_FILES below.
  No other code changes needed.
"""

import io
import json
import logging
import os
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, UnidentifiedImageError

# Suppress verbose TensorFlow startup logs.
# Must be set BEFORE importing tensorflow.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Directory containing .keras model files and their _meta.json counterparts.
# Resolved relative to this file's location so it works from any working dir.
MODELS_DIR: Path = Path(__file__).parent.parent / "models"

# Maps the crop identifier (what the frontend sends) to the model file stem.
CROP_MODEL_FILES: dict[str, str] = {
    "chili": "chili_mobilenetv2",
    "groundnut": "groundnut_mobilenetv2_model_2",
    "potato": "potato_mobilenetv2",
}

# Full-form / human-friendly display mappings for model class labels.
# Specifically, Potato dataset classes "EB" and "LB" correspond to Early Blight and Late Blight.
# Groundnut dataset classes use snake_case identifiers which map to standard pathology names.
CLASS_NAME_FULL_FORMS: dict[str, dict[str, str]] = {
    "potato": {
        "EB": "Early Blight",
        "Healthy": "Healthy",
        "LB": "Late Blight",
    },
    "groundnut": {
        "groundnut_early_leaf_spot": "Early Leaf Spot",
        "groundnut_early_rust": "Early Rust",
        "groundnut_healthy": "Healthy Leaf",
        "groundnut_late_leaf_spot": "Late Leaf Spot",
        "groundnut_nutrition_deficiency": "Nutrition Deficiency",
        "groundnut_rust": "Rust",
    },
}

# Maximum accepted upload size to prevent abuse / memory exhaustion.
MAX_IMAGE_BYTES: int = 10 * 1024 * 1024  # 10 MB

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class ModelNotAvailableError(Exception):
    """
    Raised when the requested crop has no loaded model.

    Two distinct causes:
      a) The crop is not in CROP_MODEL_FILES → genuinely unsupported.
      b) The crop is listed but the model failed to load at startup
         (missing file, corrupt .keras, version mismatch, etc.).

    The caller (API layer) should handle these by returning a clear
    "model not available" response rather than a 500 error.
    """


class ModelLoadError(Exception):
    """
    Raised during startup when a model file cannot be loaded.
    Not exposed to API callers directly; caught by load_all_available_models().
    """


class InvalidImageError(Exception):
    """
    Raised when the uploaded image cannot be opened or preprocessed.
    The caller should return an HTTP 422 with the error message.
    """


# ---------------------------------------------------------------------------
# Internal model registry
# ---------------------------------------------------------------------------

# Populated at startup by load_all_available_models().
# Structure: { crop_name: { "model": tf.keras.Model, "class_names": [...], "img_size": int } }
_REGISTRY: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------------------------


def _prepare_image(pil_img: Image.Image, img_size: int) -> np.ndarray:
    """
    Preprocess a PIL image into the exact tensor format expected by the model.

    This function replicates the prepare_image() function from Part J of
    train_crop_model.ipynb — the reference inference implementation written
    by the same notebook that trained the model.

    Steps
    -----
    1. Convert to RGB  (handles RGBA, palette, grayscale, CMYK uploads)
    2. Center-crop to a square using the shorter dimension
       Reason: phone photos are rarely 1:1; squashing a 4:3 photo would
       distort leaf geometry. Training images were square (1000×1000).
    3. Resize to (img_size × img_size) using bilinear interpolation
    4. Cast to float32 numpy array, add batch dimension → (1, H, W, 3)

    IMPORTANT: Do NOT normalize pixel values here.
    The model contains a Rescaling(1/127.5, offset=-1) layer that converts
    0–255 → [−1, +1] internally. Normalizing before calling model.predict()
    would double-normalize and completely destroy predictions.

    Parameters
    ----------
    pil_img : PIL.Image.Image
        Already-opened image object.
    img_size : int
        Target square side length (224 for MobileNetV2).

    Returns
    -------
    np.ndarray  shape (1, img_size, img_size, 3), dtype float32, values 0–255
    """
    img = pil_img.convert("RGB")

    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    img = img.resize((img_size, img_size), Image.BILINEAR)

    arr = np.asarray(img, dtype=np.float32)  # (img_size, img_size, 3), 0–255
    return arr[None, ...]  # (1, img_size, img_size, 3)


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------


def _load_single_model(crop: str) -> None:
    """
    Load one crop model and its metadata into _REGISTRY.

    Parameters
    ----------
    crop : str  The crop key from CROP_MODEL_FILES.

    Raises
    ------
    ModelLoadError  if any file is missing or the model cannot be parsed.
    """
    stem = CROP_MODEL_FILES[crop]
    model_path = MODELS_DIR / f"{stem}.keras"
    meta_path = MODELS_DIR / f"{stem}_meta.json"

    if not model_path.exists():
        raise ModelLoadError(
            f"Model file not found: {model_path}. "
            "Place the trained .keras file in the models/ directory."
        )
    if not meta_path.exists():
        raise ModelLoadError(
            f"Model metadata not found: {meta_path}. "
            "The _meta.json file is required to determine class names and input size."
        )

    # Import tensorflow here (not at module top level) so that the module can
    # be imported and its exceptions used even if TF is not installed, allowing
    # the API to start and return a clear "model unavailable" response.
    import tensorflow as tf  # noqa: PLC0415

    tf.get_logger().setLevel("ERROR")

    logger.info("Loading model for crop '%s' from %s ...", crop, model_path)
    try:
        model = tf.keras.models.load_model(str(model_path))
    except Exception as exc:
        raise ModelLoadError(
            f"Failed to load Keras model for crop '{crop}': {exc}"
        ) from exc

    try:
        meta: dict = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ModelLoadError(
            f"Failed to parse metadata JSON for crop '{crop}': {exc}"
        ) from exc

    raw_class_names: list[str] = meta.get("class_names", [])
    img_size: int = meta.get("img_size", 224)

    if not raw_class_names:
        raise ModelLoadError(
            f"Metadata for crop '{crop}' contains no class_names."
        )

    # Resolve full forms for abbreviations (e.g. EB -> Early Blight, LB -> Late Blight)
    full_forms = CLASS_NAME_FULL_FORMS.get(crop, {})
    class_names = [full_forms.get(name, name) for name in raw_class_names]

    _REGISTRY[crop] = {
        "model": model,
        "class_names": class_names,
        "raw_class_names": raw_class_names,
        "img_size": img_size,
    }

    logger.info(
        "Model '%s' loaded successfully. Classes: %s (Raw: %s). Input size: %d×%d.",
        crop,
        class_names,
        raw_class_names,
        img_size,
        img_size,
    )


def load_all_available_models() -> dict[str, str]:
    """
    Attempt to load every model listed in CROP_MODEL_FILES.

    Called once during FastAPI application startup (lifespan handler).

    A failure loading one crop does NOT prevent others from loading.
    The application starts regardless; unsupported/failed crops return
    a ModelNotAvailableError at inference time rather than crashing startup.

    Returns
    -------
    dict[str, str]
        { crop_name: "loaded" | "failed: <reason>" }
        Intended for startup logging and the health-check endpoint.
    """
    statuses: dict[str, str] = {}
    for crop in CROP_MODEL_FILES:
        try:
            _load_single_model(crop)
            statuses[crop] = "loaded"
        except ModelLoadError as exc:
            logger.error("Could not load model for crop '%s': %s", crop, exc)
            statuses[crop] = f"failed: {exc}"
    return statuses


def get_model_statuses() -> dict[str, str]:
    """
    Return current load status for all defined crops.
    Used by the health-check endpoint.
    """
    return {
        crop: ("loaded" if crop in _REGISTRY else "not loaded")
        for crop in CROP_MODEL_FILES
    }


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------


def predict(crop: str, image_bytes: bytes) -> dict[str, Any]:
    """
    Run disease prediction for the given crop on raw image bytes.

    Parameters
    ----------
    crop : str
        Crop identifier matching a key in CROP_MODEL_FILES (e.g. "chili").
        Case-sensitive; the API layer is responsible for normalising case.
    image_bytes : bytes
        Raw bytes of the uploaded image file.

    Returns
    -------
    dict with the following keys:
        crop          str    Crop identifier.
        disease       str    Predicted class name (e.g. "Curl Virus").
        confidence    float  Top-class softmax probability, rounded to 6 dp (0.0–1.0).
        all_probs     list   All classes sorted by confidence descending.
                             Each item: {"class": str, "confidence": float}.

    Notes on confidence values
    --------------------------
    The returned confidence is a raw softmax probability, NOT a calibrated
    real-world probability. A value of 0.95 does not mean the diagnosis is
    correct 95% of the time. The model was not post-hoc calibrated.
    Confidence thresholding (Module 6) should treat this as a relative
    signal of certainty, not an absolute accuracy guarantee.

    Raises
    ------
    ModelNotAvailableError
        Crop is not in CROP_MODEL_FILES (unsupported), or the model for
        this crop failed to load at startup.
    InvalidImageError
        Image bytes are too large, cannot be decoded, or preprocessing fails.
    """
    # ------------------------------------------------------------------
    # 1. Check model availability
    # ------------------------------------------------------------------
    if crop not in CROP_MODEL_FILES:
        raise ModelNotAvailableError(
            f"Crop '{crop}' is not supported. "
            f"Currently supported crops: {sorted(CROP_MODEL_FILES.keys())}."
        )

    if crop not in _REGISTRY:
        raise ModelNotAvailableError(
            f"The model for crop '{crop}' is defined but failed to load at "
            "application startup. Check the server logs for the specific error."
        )

    # ------------------------------------------------------------------
    # 2. Validate raw bytes
    # ------------------------------------------------------------------
    if len(image_bytes) == 0:
        raise InvalidImageError("Received an empty image file.")

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise InvalidImageError(
            f"Image size ({len(image_bytes) / (1024 * 1024):.1f} MB) exceeds "
            f"the maximum allowed size of {MAX_IMAGE_BYTES // (1024 * 1024)} MB."
        )

    # ------------------------------------------------------------------
    # 3. Decode and validate image
    # ------------------------------------------------------------------
    try:
        # verify() checks for file corruption without fully decoding.
        Image.open(io.BytesIO(image_bytes)).verify()
    except UnidentifiedImageError:
        raise InvalidImageError(
            "The uploaded file does not appear to be a valid image. "
            "Accepted formats: JPEG, PNG, BMP, WEBP."
        )
    except Exception as exc:
        raise InvalidImageError(f"Image validation failed: {exc}") from exc

    # verify() closes/invalidates the image object; must re-open for actual use.
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
    except Exception as exc:
        raise InvalidImageError(f"Could not open image for processing: {exc}") from exc

    # ------------------------------------------------------------------
    # 4. Preprocess
    # ------------------------------------------------------------------
    entry = _REGISTRY[crop]
    try:
        input_tensor = _prepare_image(pil_img, entry["img_size"])
    except Exception as exc:
        raise InvalidImageError(f"Image preprocessing failed: {exc}") from exc

    # ------------------------------------------------------------------
    # 5. Run inference
    # ------------------------------------------------------------------
    model = entry["model"]
    class_names: list[str] = entry["class_names"]
    raw_class_names: list[str] = entry.get("raw_class_names", class_names)

    # model.predict() returns shape (1, num_classes) — softmax probabilities.
    # verbose=0 suppresses the per-batch progress bar.
    probs: np.ndarray = model.predict(input_tensor, verbose=0)[0]

    # ------------------------------------------------------------------
    # 6. Structure results
    # ------------------------------------------------------------------
    top_idx: int = int(np.argmax(probs))
    top_confidence: float = float(probs[top_idx])

    sorted_indices = np.argsort(probs)[::-1]
    all_probs = [
        {
            "class": class_names[int(i)],
            "raw_class": raw_class_names[int(i)],
            "confidence": round(float(probs[i]), 6),
        }
        for i in sorted_indices
    ]

    return {
        "crop": crop,
        "disease": class_names[top_idx],
        "raw_disease": raw_class_names[top_idx],
        "confidence": round(top_confidence, 6),
        "all_probs": all_probs,
    }
