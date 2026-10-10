# -*- coding: utf-8 -*-
"""
test_api.py
===========
Comprehensive integration tests for Crop Disease Detection API.
Validates:
  - System health check & model load status
  - Pydantic response schemas
  - Module 6 Confidence & Rejection System (status: 'success' vs 'low_confidence', is_confident flag, threshold evaluation, actionable messaging)
  - Distinguishing all response types:
      1. Successful diagnosis (confidence >= threshold)
      2. Low-confidence diagnosis (confidence < threshold)
      3. Invalid input (HTTP 422 for corrupt bytes, HTTP 400 for missing fields)
      4. Unsupported crop / unavailable model (HTTP 503)
  - Backward compatibility routes (/predict, /)

Run from project root:
    python test_api.py
"""

import io
import json
import os
import sys
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from PIL import Image

BASE = "http://localhost:8000"
PASS = "[PASS]"
FAIL = "[FAIL]"
BOUNDARY = b"----FormBoundary7MA4YWxk"
BOUNDARY_STR = "----FormBoundary7MA4YWxk"

results = []


def check(name: str, passed: bool, detail: str = "") -> None:
    results.append(passed)
    icon = PASS if passed else FAIL
    print(f"  {icon}  {name}")
    if detail:
        print(f"        {detail}")


def make_valid_jpeg() -> bytes:
    """Create a small green-tinted JPEG in memory."""
    arr = np.zeros((300, 400, 3), dtype="uint8")
    arr[:, :, 1] = 100  # green channel
    buf = io.BytesIO()
    Image.fromarray(arr, "RGB").save(buf, "JPEG")
    return buf.getvalue()


def build_multipart(fields: dict, files: dict) -> bytes:
    """Build a multipart/form-data body."""
    body = b""
    for name, value in fields.items():
        body += b"--" + BOUNDARY + b"\r\n"
        body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body += value.encode() + b"\r\n"
    for name, (filename, content_type, data) in files.items():
        body += b"--" + BOUNDARY + b"\r\n"
        body += (
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
        body += data + b"\r\n"
    body += b"--" + BOUNDARY + b"--\r\n"
    return body


def post_predict(path: str, crop: str, image_bytes: bytes, filename: str = "leaf.jpg") -> tuple:
    """
    POST to prediction endpoint with given crop and image bytes.
    Returns (status_code, response_dict).
    """
    body = build_multipart(
        fields={"crop": crop},
        files={"image": (filename, "image/jpeg", image_bytes)},
    )
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY_STR}"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as he:
        return he.code, json.loads(he.read())


VALID_JPEG = make_valid_jpeg()


# ---------------------------------------------------------------------------
print("\n[1] GET /api/v1/health - versioned health check")
# ---------------------------------------------------------------------------
try:
    with urllib.request.urlopen(f"{BASE}/api/v1/health") as r:
        data = json.loads(r.read())
    ok = (
        data.get("status") == "running"
        and data.get("api_version") == "1.0.0"
        and data.get("models", {}).get("chili") == "loaded"
    )
    check("v1 health returns status='running', api_version='1.0.0', chili='loaded'", ok, str(data))
except Exception as exc:
    check("v1 health reachable", False, str(exc))


# ---------------------------------------------------------------------------
print("\n[2] GET / - legacy root health check")
# ---------------------------------------------------------------------------
try:
    with urllib.request.urlopen(f"{BASE}/") as r:
        data = json.loads(r.read())
    ok = (
        data.get("status") == "running"
        and data.get("models", {}).get("chili") == "loaded"
    )
    check("Legacy health check alias works seamlessly", ok, str(data))
except Exception as exc:
    check("Root health check reachable", False, str(exc))


# ---------------------------------------------------------------------------
print("\n[3] POST /api/v1/predict - confidence & rejection gating (Module 6)")
# ---------------------------------------------------------------------------
try:
    code, data = post_predict("/api/v1/predict", "chili", VALID_JPEG)
    pred = data.get("prediction", {})
    confidence = pred.get("confidence")
    threshold = data.get("threshold")
    is_confident = data.get("is_confident")
    status = data.get("status")
    message = data.get("message")

    # In Module 6:
    # If confidence >= threshold -> status == 'success', is_confident == True
    # If confidence < threshold -> status == 'low_confidence', is_confident == False
    expected_status = "success" if confidence >= threshold else "low_confidence"
    expected_confident = confidence >= threshold

    ok = (
        code == 200
        and data.get("crop") == "chili"
        and isinstance(threshold, float)
        and threshold == 0.70
        and is_confident == expected_confident
        and status == expected_status
        and isinstance(pred.get("disease"), str)
        and isinstance(confidence, float)
        and 0.0 <= confidence <= 1.0
        and isinstance(message, str)
        and len(message) > 0
    )
    check(
        f"Correctly gates prediction: status='{status}', is_confident={is_confident}, threshold={threshold}",
        ok,
        f"Confidence: {confidence*100:.1f}% vs Threshold: {threshold*100:.1f}% | Message: {message[:65]}...",
    )
except Exception as exc:
    check("Confidence & rejection gating", False, str(exc))


# ---------------------------------------------------------------------------
print("\n[4] POST /predict - legacy prediction endpoint alias")
# ---------------------------------------------------------------------------
try:
    code, data = post_predict("/predict", "chili", VALID_JPEG)
    ok = (
        code == 200
        and "status" in data
        and "prediction" in data
        and "threshold" in data
        and "is_confident" in data
    )
    check("Legacy /predict route delegates cleanly to v1 confidence contract", ok, f"HTTP {code}")
except Exception as exc:
    check("Legacy /predict alias", False, str(exc))


# ---------------------------------------------------------------------------
print("\n[5] POST /api/v1/predict - case-normalisation ('CHILI' -> 'chili')")
# ---------------------------------------------------------------------------
try:
    code, data = post_predict("/api/v1/predict", "CHILI", VALID_JPEG)
    ok = code == 200 and data.get("crop") == "chili"
    check("Uppercase 'CHILI' is normalised and succeeds", ok, str({"code": code, "crop": data.get("crop")}))
except Exception as exc:
    check("Case normalisation", False, str(exc))


# ---------------------------------------------------------------------------
print("\n[6] POST /api/v1/predict - potato (unsupported crop, no model)")
# ---------------------------------------------------------------------------
try:
    code, data = post_predict("/api/v1/predict", "potato", VALID_JPEG)
    ok = code == 503 and data.get("status") == "model_unavailable" and "message" in data
    check("Returns HTTP 503 with status='model_unavailable'", ok, f"HTTP {code}: {data}")
except Exception as exc:
    check("Potato unsupported crop", False, str(exc))


# ---------------------------------------------------------------------------
print("\n[7] POST /api/v1/predict - groundnut (unsupported crop, no model)")
# ---------------------------------------------------------------------------
try:
    code, data = post_predict("/api/v1/predict", "groundnut", VALID_JPEG)
    ok = code == 503 and data.get("status") == "model_unavailable" and "message" in data
    check("Returns HTTP 503 with status='model_unavailable'", ok, f"HTTP {code}: {data}")
except Exception as exc:
    check("Groundnut unsupported crop", False, str(exc))


# ---------------------------------------------------------------------------
print("\n[8] POST /api/v1/predict - non-image bytes (invalid input error)")
# ---------------------------------------------------------------------------
try:
    code, data = post_predict("/api/v1/predict", "chili", b"this is not an image at all")
    ok = code == 422 and data.get("status") == "invalid_image" and "message" in data
    check("Returns HTTP 422 with status='invalid_image'", ok, f"HTTP {code}: {data}")
except Exception as exc:
    check("Non-image file", False, str(exc))


# ---------------------------------------------------------------------------
print("\n[9] POST /api/v1/predict - blank crop field (validation error)")
# ---------------------------------------------------------------------------
try:
    code, data = post_predict("/api/v1/predict", "   ", VALID_JPEG)
    ok = code == 400
    check("Returns HTTP 400 for blank crop field", ok, f"HTTP {code}: {data}")
except Exception as exc:
    check("Blank crop field", False, str(exc))


# ---------------------------------------------------------------------------
print("\n[10] POST /api/v1/predict - completely unknown crop")
# ---------------------------------------------------------------------------
try:
    code, data = post_predict("/api/v1/predict", "mango", VALID_JPEG)
    ok = code == 503 and data.get("status") == "model_unavailable"
    check("Returns HTTP 503 for unknown crop 'mango'", ok, f"HTTP {code}: {data}")
except Exception as exc:
    check("Unknown crop", False, str(exc))


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
passed = sum(results)
total = len(results)
print(f"\n{'='*60}")
print(f"Results: {passed}/{total} tests passed")
if passed == total:
    print("All API tests passed. Module 6 is complete.")
else:
    print("Some tests failed. Review output above.")
print("=" * 60)
