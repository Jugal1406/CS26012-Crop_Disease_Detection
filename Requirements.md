# System Requirements Specification (SRS)

**Project:** CS26012 — Crop Disease Detection & Agricultural Advisory Platform  
**Document Type:** Formal System & Technical Requirements Specification  
**Version:** 2.0 (Updated October 2026)  

---

## A. Functional Requirements

| Req ID | Requirement Description | Implementation Status | Verification Method |
| :---: | :--- | :---: | :--- |
| **FR-01** | **User Registration & Authentication**: Farmers shall authenticate via email/password, OTP, or Google SSO using Clerk Auth. Sessions are secured via verified JWT tokens. | **Implemented** | Verified in `clerk_auth.py` and `AuthContext.jsx`. |
| **FR-02** | **Farmer Profile Management**: Authenticated users can view their email (read-only) and update their full name, phone number, and preferred language. Phone numbers are normalized to E.164 (`+91...`). | **Implemented** | Verified via `test_profile_and_groq_flow.py` (Test 1.2, 1.3, 1.4). |
| **FR-03** | **Farm Profile Management**: Users can register multiple farm plots with name, village, district, state, cultivated area (hectares), and GPS coordinates. One farm can be designated as primary. | **Implemented** | Verified in `routers/farms.py` and `Farms.jsx`. |
| **FR-04** | **Leaf Image Ingestion**: Users can upload image files or capture leaf photos using a camera. The system validates MIME type (`JPEG`, `PNG`, `WEBP`) and enforces a 10 MB payload ceiling. | **Implemented** | Verified in `inference.py` and `Diagnose.jsx`. |
| **FR-05** | **Crop-Specific Pathology Classification**: The system applies pre-trained deep learning models tailored to the selected crop to predict the specific foliar disease or confirm foliage health. | **Implemented (Chili)**<br>*Planned (Other crops)* | Verified in `inference.py` on Chili (12 classes). |
| **FR-06** | **Selective Classification & Confidence Gating**: Predictions with Softmax confidence $< 0.70$ are flagged as `low_confidence`, rejecting automatic treatment recommendations and advising a re-take. | **Implemented** | Verified in `inference.py` (Test 6, `test_inference.py`). |
| **FR-07** | **Micro-Climate Agro-Weather Context**: Ambient weather (temperature, relative humidity, precipitation, wind speed) is retrieved via Open-Meteo for the farm plot coordinates and cached for 30 min. | **Implemented** | Verified in `services/weather_service.py` (`test_weather_flow.py`). |
| **FR-08** | **Agronomic Advisory Generation**: For accepted predictions, Groq LLM generates structured cultural, biological, and preventive recommendations under strict directives prohibiting chemical hallucinations. | **Implemented** | Verified in `services/llm_service.py` (`test_profile_and_groq_flow.py`). |
| **FR-09** | **Groq Multi-Key Rotation**: The backend manages up to 3 Groq API keys, automatically rotating on HTTP 429 rate limit or quota exhaustion, with an offline agronomic fallback if all keys fail. | **Implemented** | Verified via `test_profile_and_groq_flow.py` (Tests 2.1–2.6). |
| **FR-10** | **Complete Trilingual Localization**: The user interface and diagnostic outputs support seamless switching between English, Hindi, and Gujarati without full page reloads. | **Implemented** | Verified across `en.js`, `hi.js`, `gu.js`, and form components. |
| **FR-11** | **Scan History & Inspection**: Authenticated farmers can review paginated past scan records, filter by crop or status, and inspect detailed diagnostic and weather logs. | **Implemented** | Verified in `routers/scans.py` (`test_scan_history_flow.py`). |
| **FR-12** | **PDF Report Export**: The system generates downloadable, printable PDF reports with embedded leaf images, weather parameters, and cultural guidance using Unicode TrueType fonts. | **Implemented** | Verified in `services/pdf_service.py` (`test_pdf_report_flow.py`). |
| **FR-13** | **Multi-Tenant Data Isolation**: Strict row-level ownership is enforced across all routes; farmers cannot view, update, or delete other users' scans, farms, or profile records. | **Implemented** | Verified in `test_dashboard_flow.py` (Test 4). |

---

## B. Non-Functional Requirements

### 1. Security & Privacy
- **Statutory Secrets Isolation**: Real API keys, database credentials, and service account secrets must reside in backend environment variables excluded from source control via `.gitignore`.
- **Cryptographic Token Verification**: Client requests must present valid Bearer JWTs verified against Clerk's JSON Web Key Set (JWKS). Client-supplied user IDs in query parameters are strictly disregarded.
- **Input Sanitization**: File uploads are verified via PIL image header decoding; raw byte injection or corrupt formats trigger an immediate HTTP 422 error.

### 2. Performance & Responsiveness
- **Inference Latency**: MobileNetV2 image inference executes in $\le 250\text{ ms}$ on commodity CPU backends.
- **Client Bundle Efficiency**: Vite client bundle is optimized with dynamic imports, producing assets $\le 600\text{ kB}$ minified.
- **Weather Caching**: Meteorological API requests are cached in memory for 30 minutes to reduce external network round-trips.

### 3. Reliability & Error Handling
- **Bounded Failover**: Groq LLM advisory calls use bounded retries and multi-key failover to prevent retry storms.
- **Graceful Offline Fallback**: If external LLMs or network services fail, the system serves local agronomic recommendations without altering the neural network's pathology prediction.

### 4. Localization & Accessibility
- **Unicode Font Rendering**: ReportLab PDF generator embeds Google Noto Sans (`NotoSans-Regular.ttf`, `NotoSansDevanagari-Regular.ttf`, `NotoSansGujarati-Regular.ttf`) preventing character corruption in Indic scripts.
- **Responsive Layout**: Fluid layouts with `text-wrap: balance` and relative font units prevent clipping of long Hindi and Gujarati compound words on mobile viewports.

---

## C. Technology Stack Specifications

| Technology | Selected Version | Role & Justification |
| :--- | :--- | :--- |
| **Python** | 3.10 – 3.12 (64-bit) | Core backend language; compatible with TensorFlow 2.21 and asyncpg |
| **FastAPI** | 0.142.2 | High-throughput asynchronous ASGI web framework |
| **Uvicorn** | 0.54.0 | Asynchronous ASGI server implementation |
| **TensorFlow / Keras** | 2.21.0 | Deep learning runtime for MobileNetV2 inference |
| **Pillow** | 12.3.0 | High-performance image decoding and tensor transformations |
| **PostgreSQL** | 14+ / 18+ | Primary relational database with ACID guarantees |
| **SQLAlchemy** | 2.0.36 | Modern asynchronous ORM |
| **Alembic** | 1.14.0 | Database schema migration engine |
| **Clerk Auth** | `@clerk/clerk-react` 5.61 | Production identity provider with session security |
| **Groq Cloud** | `openai/gpt-oss-120b` | High-speed LLM inference for agricultural extension reports |
| **ReportLab** | 5.0.1 | Programmatic PDF document layout and TrueType font rendering |
| **React** | 19.2.8 | Declarative component UI library |
| **Vite** | 8.3.0 | Next-generation frontend bundler and local development server |
| **Google Colab** | Cloud GPU (T4) | Model training environment for compute-heavy transfer learning |

---

## D. Hardware & Software Prerequisites

### Recommended Local Development Environment
- **Operating System**: Windows 10/11 (64-bit), Ubuntu 22.04 LTS+, or macOS 13+
- **Processor**: Intel Core i5 / AMD Ryzen 5 or higher (minimum 4 cores recommended)
- **Memory**: Minimum 8 GB RAM (16 GB recommended for concurrent backend + ML + PostgreSQL)
- **Disk Storage**: 5 GB free disk space (for Python venv, Node modules, and PostgreSQL database)
- **Network**: Internet connectivity for Clerk auth, Open-Meteo weather, and Groq LLM calls

### Model Training Environment (Optional)
- Model training is offloaded to **Google Colab** (free-tier Nvidia T4 GPU, 16 GB VRAM) as specified in `notebooks/train_crop_model.ipynb`.

---

## E. Configuration & Environment Variables

### Backend Configuration (`backend/.env`)
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crop_disease_db
DB_USER=postgres
DB_PASSWORD=your_secure_password
CONFIDENCE_THRESHOLD=0.70
MAX_UPLOAD_SIZE_BYTES=10485760
CLERK_SECRET_KEY=sk_test_...
CLERK_JWKS_URL=https://.../.well-known/jwks.json
CLERK_ISSUER=https://...
WEATHER_PROVIDER=open-meteo
GROQ_API_KEY_1=gsk_...
GROQ_API_KEY_2=gsk_...
GROQ_API_KEY_3=gsk_...
GROQ_MODEL=openai/gpt-oss-120b
```

### Frontend Configuration (`frontend/.env`)
```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```
