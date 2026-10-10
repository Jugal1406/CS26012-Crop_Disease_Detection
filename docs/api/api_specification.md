# Backend REST API Specification

The backend provides versioned endpoints prefixed with `/api/v1/`. Interactive OpenAPI / Swagger documentation is available at `http://localhost:8000/docs`.

---

## 1. Authentication Endpoints (`/api/v1/auth`)

- **`POST /api/v1/auth/sync`**
  - Synchronizes Clerk authenticated identity with PostgreSQL.
  - Header: `Authorization: Bearer <clerk_jwt>`
  - Body: `{"display_name": "Farmer Name"}` (optional)
  - Returns: `{"status": "success", "user": {...}}`

- **`GET /api/v1/auth/me`**
  - Returns the current authenticated user's profile.

- **`PATCH /api/v1/auth/profile`**
  - Updates personal profile: `display_name`, `phone_number`, `preferred_language`.
  - Normalizes 10-digit Indian numbers to E.164 (`+91...`). Email is strictly read-only.

---

## 2. Diagnosis Endpoints (`/api/v1/diagnose` & `/api/v1/predict`)

- **`POST /api/v1/diagnose`**
  - Multipart upload for foliar disease diagnosis.
  - Form Fields: `crop` (e.g. `chili`), `image` (binary file), `farm_id` (optional), `language` (optional, default `en`).
  - Gated by confidence threshold (0.70):
    - Confident (`>= 0.70`): Returns accepted ML prediction, weather snapshot, and Groq LLM advisory.
    - Low-confidence (`< 0.70`): Returns `status: "low_confidence"` with instructions to retake photo.

- **`POST /predict`**
  - Backward-compatible lightweight prediction endpoint.

---

## 3. Farm Management Endpoints (`/api/v1/farms`)

- **`GET /api/v1/farms`**: List authenticated user's registered farms.
- **`POST /api/v1/farms`**: Register a new farm (name, village, district, state, area, GPS).
- **`GET /api/v1/farms/{id}`**: Get farm details.
- **`PUT /api/v1/farms/{id}`**: Update farm details.
- **`DELETE /api/v1/farms/{id}`**: Delete a farm plot.
- **`POST /api/v1/farms/{id}/primary`**: Set farm as primary.
- **`GET /api/v1/farms/{id}/weather`**: Retrieve micro-climate agro-weather.

---

## 4. Scan History & PDF Reports (`/api/v1/scans`)

- **`GET /api/v1/scans`**: Paginated scan history with filtering by crop, status, and date.
- **`GET /api/v1/scans/{id}`**: Retrieve detailed scan inspection and advisory report.
- **`GET /api/v1/scans/{id}/report`**: Retrieve advisory report with language translation.
- **`GET /api/v1/scans/{id}/pdf`**: Download ReportLab PDF report in English, Hindi, or Gujarati (`?lang=en|hi|gu`).

---

## 5. Dashboard Endpoints (`/api/v1/dashboard`)

- **`GET /api/v1/dashboard/overview`**: Aggregated farmer dashboard stats, recent scans, primary farm, and active agro-weather snapshot.
