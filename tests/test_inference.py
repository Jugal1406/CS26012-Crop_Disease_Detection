# -*- coding: utf-8 -*-
"""
test_inference.py
=================
Standalone test for backend/inference.py.
Run from the project root:

    python test_inference.py

Does NOT require FastAPI, the frontend, or a database.
Tests:
  1. Model loads successfully
  2. Valid image bytes - correct output structure
  3. Synthetic leaf-coloured image - prediction runs end-to-end
  4. Empty bytes - InvalidImageError
  5. Non-image bytes - InvalidImageError
  6. Oversized bytes - InvalidImageError
  7. Unsupported crop - ModelNotAvailableError
  8. Unloaded-but-defined crop - ModelNotAvailableError
"""
import sys
# Force UTF-8 output on Windows so the test can be run without env vars
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import io
import os

# Suppress TF noise for cleaner test output
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Add backend/ to path so we can import inference directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import inference
from inference import (
    load_all_available_models,
    predict,
    get_model_statuses,
    ModelNotAvailableError,
    InvalidImageError,
)
from PIL import Image
import numpy as np


PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"


def make_synthetic_image_bytes(width: int = 400, height: int = 300) -> bytes:
    """Create a small green-tinted JPEG in memory (simulates a leaf photo)."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :, 1] = 120  # green channel
    arr[:, :, 0] = 40   # some red
    pil = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def run_tests():
    results = []

    # ------------------------------------------------------------------
    # TEST 1: Model loading
    # ------------------------------------------------------------------
    print("\n[1] Loading all available models ...")
    try:
        statuses = load_all_available_models()
        assert statuses.get("chili") == "loaded", f"Expected 'loaded', got: {statuses}"
        print(f"    Model statuses: {statuses}")
        print(f" {PASS} Model loaded for chili")
        results.append(True)
    except Exception as exc:
        print(f" {FAIL} Model loading failed: {exc}")
        results.append(False)
        print("\nCannot continue tests without a loaded model. Exiting.")
        return results

    # ------------------------------------------------------------------
    # TEST 2: get_model_statuses()
    # ------------------------------------------------------------------
    print("\n[2] get_model_statuses() ...")
    try:
        s = get_model_statuses()
        assert "chili" in s
        assert s["chili"] == "loaded"
        print(f"    Statuses: {s}")
        print(f" {PASS} get_model_statuses returns correct result")
        results.append(True)
    except Exception as exc:
        print(f" {FAIL} {exc}")
        results.append(False)

    # ------------------------------------------------------------------
    # TEST 3: Valid synthetic image → full output structure
    # ------------------------------------------------------------------
    print("\n[3] Valid synthetic image → predict('chili', ...) ...")
    try:
        img_bytes = make_synthetic_image_bytes()
        result = predict("chili", img_bytes)

        assert "crop" in result,       "Missing key: crop"
        assert "disease" in result,    "Missing key: disease"
        assert "confidence" in result, "Missing key: confidence"
        assert "all_probs" in result,  "Missing key: all_probs"

        assert result["crop"] == "chili"
        assert isinstance(result["disease"], str)
        assert 0.0 <= result["confidence"] <= 1.0
        assert len(result["all_probs"]) == 6  # Chili has 6 classes
        assert result["all_probs"][0]["confidence"] >= result["all_probs"][1]["confidence"]

        print(f"    Predicted: {result['disease']} ({result['confidence']*100:.1f}%)")
        print(f"    All probs: {[(p['class'][:12], round(p['confidence']*100,1)) for p in result['all_probs']]}")
        print(f" {PASS} Valid image prediction succeeded with correct structure")
        results.append(True)
    except Exception as exc:
        print(f" {FAIL} {exc}")
        results.append(False)

    # ------------------------------------------------------------------
    # TEST 4: Empty bytes → InvalidImageError
    # ------------------------------------------------------------------
    print("\n[4] Empty bytes → should raise InvalidImageError ...")
    try:
        predict("chili", b"")
        print(f" {FAIL} No exception raised — expected InvalidImageError")
        results.append(False)
    except InvalidImageError as exc:
        print(f"    Caught correctly: {exc}")
        print(f" {PASS} InvalidImageError raised for empty bytes")
        results.append(True)
    except Exception as exc:
        print(f" {FAIL} Wrong exception type {type(exc).__name__}: {exc}")
        results.append(False)

    # ------------------------------------------------------------------
    # TEST 5: Non-image bytes → InvalidImageError
    # ------------------------------------------------------------------
    print("\n[5] Non-image bytes (PDF header) → should raise InvalidImageError ...")
    try:
        predict("chili", b"%PDF-1.4 fake document content that is not an image")
        print(f" {FAIL} No exception raised — expected InvalidImageError")
        results.append(False)
    except InvalidImageError as exc:
        print(f"    Caught correctly: {exc}")
        print(f" {PASS} InvalidImageError raised for non-image bytes")
        results.append(True)
    except Exception as exc:
        print(f" {FAIL} Wrong exception type {type(exc).__name__}: {exc}")
        results.append(False)

    # ------------------------------------------------------------------
    # TEST 6: Oversized image → InvalidImageError
    # ------------------------------------------------------------------
    print("\n[6] Oversized bytes (11 MB) → should raise InvalidImageError ...")
    try:
        predict("chili", b"x" * (11 * 1024 * 1024))
        print(f" {FAIL} No exception raised — expected InvalidImageError")
        results.append(False)
    except InvalidImageError as exc:
        print(f"    Caught correctly: {exc}")
        print(f" {PASS} InvalidImageError raised for oversized bytes")
        results.append(True)
    except Exception as exc:
        print(f" {FAIL} Wrong exception type {type(exc).__name__}: {exc}")
        results.append(False)

    # ------------------------------------------------------------------
    # TEST 7: Unsupported crop → ModelNotAvailableError
    # ------------------------------------------------------------------
    print("\n[7] Unsupported crop 'mango' → should raise ModelNotAvailableError ...")
    try:
        predict("mango", make_synthetic_image_bytes())
        print(f" {FAIL} No exception raised — expected ModelNotAvailableError")
        results.append(False)
    except ModelNotAvailableError as exc:
        print(f"    Caught correctly: {exc}")
        print(f" {PASS} ModelNotAvailableError raised for unsupported crop")
        results.append(True)
    except Exception as exc:
        print(f" {FAIL} Wrong exception type {type(exc).__name__}: {exc}")
        results.append(False)

    # ------------------------------------------------------------------
    # TEST 8: Defined but not-yet-loaded crop → ModelNotAvailableError
    # ------------------------------------------------------------------
    print("\n[8] Defined-but-unloaded crop 'potato' → should raise ModelNotAvailableError ...")
    try:
        # 'potato' is in CROP_MODEL_FILES (commented out) — but since it's
        # not in the file map as-is, we simulate by temporarily adding it
        # to the file map without loading it into the registry.
        inference.CROP_MODEL_FILES["_test_unloaded"] = "_test_unloaded_mobilenetv2"
        predict("_test_unloaded", make_synthetic_image_bytes())
        print(f" {FAIL} No exception raised — expected ModelNotAvailableError")
        results.append(False)
    except ModelNotAvailableError as exc:
        print(f"    Caught correctly: {exc}")
        print(f" {PASS} ModelNotAvailableError raised for defined-but-unloaded crop")
        results.append(True)
    except Exception as exc:
        print(f" {FAIL} Wrong exception type {type(exc).__name__}: {exc}")
        results.append(False)
    finally:
        inference.CROP_MODEL_FILES.pop("_test_unloaded", None)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} tests passed")
    if passed == total:
        print("All tests passed. inference.py is ready for Module 3.")
    else:
        print("Some tests failed. Review output above before proceeding.")
    print('='*50)
    return results


if __name__ == "__main__":
    run_tests()
