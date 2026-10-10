# CS26012 — Crop Disease Detection & Agricultural Advisory Platform

An end-to-end web platform for intelligent crop leaf disease detection and localized agronomic advisory, designed specifically for Indian smallholder farmers and agricultural extension specialists.

**Team ID:** CS26012  
**Institution:** Chandubhai S. Patel Institute of Technology (CSPIT), CHARUSAT  

---

## 1. Project Overview & Problem Addressed

Crop foliar diseases cause significant yield loss across Indian agriculture (estimated between 20% and 40% annually). Traditional diagnosis relies on visual inspection by farmers or infrequent visits from agricultural extension officers. Most published computer vision benchmarks (e.g. PlantVillage) are trained on lab-condition leaf images against plain backgrounds, creating a well-documented **domain-shift accuracy drop** when used on real fields with cluttered backgrounds, natural lighting, and smartphone cameras.

This project addresses that gap by:
1. Providing an end-to-end diagnostic pipeline prioritizing **field-condition data from Indian agricultural regions**.
2. Enforcing a strict **confidence gating policy (70% threshold)** to reject ambiguous images rather than presenting false-positive guesses.
3. Combining neural network predictions with **ambient micro-climate agro-weather (Open-Meteo)** and **structured agronomic advisories (Groq LLM)** with strict chemical guardrails.
4. Delivering complete localization in **English, Hindi, and Gujarati**, along with downloadable multilingual PDF reports.

---

## 2. Supported Crops & Model Status

| Crop | Status | Classes | Model Architecture | Training Data Origin |
| :--- | :--- | :---: | :--- | :--- |
| **Chili Pepper** | **Active & Deployed** | 12 | MobileNetV2 Transfer Learning (`.keras`) | Field images · Krishna River Basin, Deccan Plateau (Mendeley) |
| **Potato** | Pipeline Ready | 3 | MobileNetV2 (Scheduled for retraining) | Field images · PLDD-UP, Uttar Pradesh |
| **Groundnut** | Pipeline Ready | 4 | MobileNetV2 (Scheduled for retraining) | Field images · VIT Chennai dataset |
| **Rice** | Planned | 4 | MobileNetV2 (Dataset cataloged) | Field images · Kaggle Rice Leaf Disease |
| **Tomato** | Planned | 10 | MobileNetV2 (Lab baseline evaluation) | PlantVillage comparison baseline |
| **Wheat** | Planned | — | Under dataset acquisition | Field images · North Indian wheat plots |
| **Banana** | Planned | 4 | MobileNetV2 (Dataset cataloged) | Multi-Crop Disease Dataset, Mendeley |
| **Soybean** | Planned | 4 | MobileNetV2 (Dataset cataloged) | MH-SoyaHealthVision (leaf subset) |

> **Note on Model Validation**: The currently deployed Chili model achieves an internal test accuracy of **94.2%** on a held-out test split of 1,200 field images. Real-world field accuracy may vary under extreme lighting, glare, or motion blur, which is managed via the 70% confidence rejection gate.

---

## 3. Technology Stack & Component Roles

| Layer | Technology | Version | Role in Application |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React + Vite | React 19, Vite 8 | Single-Page Application (SPA) with responsive CSS |
| **Authentication** | Clerk Auth | `@clerk/clerk-react` 5.61 | User sign-up, sign-in, MFA, and JWT session handling |
| **Localization** | Custom i18n Engine | — | Instant multilingual UI & reports (EN, HI, GU) |
| **Backend Framework** | FastAPI | 0.142.2 | High-performance asynchronous REST API |
| **ASGI Server** | Uvicorn | 0.54.0 | Asynchronous application server |
| **Database** | PostgreSQL | 14+ / 18+ | Primary relational database (9 tables) |
| **ORM & Migrations** | SQLAlchemy & Alembic | 2.0 / 1.14 | Async database queries and schema version control |
| **Deep Learning** | TensorFlow / Keras | 2.21.0 | MobileNetV2 image preprocessing & inference |
| **Weather Service** | Open-Meteo API | REST | Micro-climate meteorological snapshots (temp, humidity, rain, wind) |
| **Advisory LLM** | Groq Cloud | `openai/gpt-oss-120b` | Structured agronomic guidance with 3-key failover |
| **PDF Generation** | ReportLab | 5.0.1 | Multilingual Unicode PDF reports with Noto Sans fonts |

---

## 4. Key Implemented Features

1. **Leaf Disease Inference with Confidence Gating**:
   - Supports image upload or live camera capture (`JPEG`, `PNG`, `WEBP`, max 10 MB).
   - Softmax confidence threshold of 0.70. Low-confidence images are safely rejected with actionable guidance.
2. **Farm Profile & GPS Meteorological Context**:
   - Register multiple farm plots with name, village, district, state, area, and GPS coordinates.
   - GPS-linked ambient weather retrieval via Open-Meteo cached for 30 minutes.
3. **Groq Multi-Key Rotation & Safe Fallback**:
   - Supports 3 independent Groq API keys (`GROQ_API_KEY_1`, `GROQ_API_KEY_2`, `GROQ_API_KEY_3`).
   - Automatically fails over on HTTP 429 rate limit or quota exhaustion.
   - Provides safe offline agronomic fallback advisory if external LLMs are unavailable.
   - The ML model's disease prediction is immutable; the LLM cannot override the pathology diagnosis.
4. **Complete Trilingual Localization**:
   - Seamless language switching across English, Hindi (हिन्दी), and Gujarati (ગુજરાતી) without page reload.
   - All forms (Add Farm, Edit Profile, Diagnosis), error messages, and report cards follow the active language.
5. **Farmer Profile Management**:
   - Editable farmer display name, phone number (with Indian 10-digit to `+91` normalization), and language preference.
   - Email is read-only and secured by Clerk identity verification.
6. **Scan History & PDF Export**:
   - Filterable past diagnostic history by crop, status, and date.
   - One-click PDF download formatted with embedded leaf photos and localized Unicode typography.

---

## 5. Repository Structure

```text
CS26012-Crop_Disease_Detection/
├── .gitignore                         # Comprehensive Git ignore rules
├── README.md                          # Main project documentation (this file)
├── requirements.txt                   # Root Python dependencies
├── Problem Statement.md               # Problem definition & project goals
├── Literature Survey.md               # Academic research review
├── Project Timeline.md                # Milestone schedule & progress tracking
├── Requirements.md                    # System & functional requirements specification
│
├── docs/                              # Project Documentation
│   ├── architecture/                  # System architecture diagrams & technical flows
│   ├── setup/                         # Local development setup guide
│   ├── api/                           # Backend REST API specification
│   ├── database/                      # PostgreSQL relational schema & migrations
│   └── project-records/               # Academic records and semester reports
│
├── backend/                           # FastAPI Application Service
│   ├── .env.example                   # Backend environment configuration template
│   ├── alembic.ini                    # Alembic migration configuration
│   ├── config.py                      # App settings loader
│   ├── database.py                    # SQLAlchemy async engine & session
│   ├── dependencies.py                # FastAPI auth dependencies
│   ├── clerk_auth.py                  # Clerk JWT verification service
│   ├── inference.py                   # Leaf image preprocessing & ML inference
│   ├── main.py                        # FastAPI entry point & CORS
│   ├── models.py                      # SQLAlchemy ORM models (9 tables)
│   ├── requirements.txt               # Backend Python dependencies
│   ├── schemas.py                     # Pydantic request/response schemas
│   ├── seed.py                        # Reference crops & diseases seed script
│   ├── test_chili_leaf.jpg            # Integration test fixture
│   ├── alembic/                       # Database migration versions
│   ├── fonts/                         # NotoSans Unicode TTF fonts (EN, HI, GU)
│   ├── repositories/                  # Data access layer
│   ├── routers/                       # API route controllers
│   ├── services/                      # Business logic services
│   ├── tests/                         # Backend flow integration tests
│   └── uploads/                       # Runtime uploaded leaf images
│
├── frontend/                          # React 19 + Vite Frontend
│   ├── .env.example                   # Frontend environment configuration template
│   ├── package.json                   # NPM dependencies & scripts
│   ├── vite.config.js                 # Vite bundler configuration
│   ├── public/                        # Static web assets
│   └── src/
│       ├── App.jsx                    # Route layout & ClerkProvider
│       ├── components/                # Reusable UI & Modal components
│       ├── context/                   # Global AuthContext & LanguageContext
│       ├── locales/                   # Translation dictionaries (en, hi, gu)
│       ├── pages/                     # Application views (Home, Login, Dashboard, Farms, Diagnose)
│       ├── services/                  # Frontend API service clients
│       └── styles/                    # Modular Vanilla CSS stylesheets
│
├── models/                            # Trained ML Model Weights & Metadata
│   ├── chili_mobilenetv2.keras        # Trained Keras MobileNetV2 model
│   ├── chili_mobilenetv2_meta.json    # Class label mappings & input specs
│   └── chili_mobilenetv2_metrics.json # Internal validation metrics
│
├── notebooks/                         # ML Training Pipelines
│   └── train_crop_model.ipynb         # 10-phase transfer learning Colab notebook
│
├── tests/                             # Root E2E Diagnostic Tests
│   ├── test_api.py                    # E2E live backend endpoint test
│   └── test_inference.py              # Standalone inference engine test
│
└── archive/                           # Preserved Historical Artifacts
    ├── README.md                      # Archive explanation
    ├── development-artifacts/         # Old repository snapshot archive
    └── obsolete-experiments/          # Legacy Firebase prototypes
```

---

## 6. Quick Start & Installation

### Step 1: Clone & Python Environment
```powershell
git clone https://github.com/Jugal1406/CS26012-Crop_Disease_Detection.git
cd CS26012-Crop_Disease_Detection

# Create virtual environment:
python -m venv .venv
.\.venv\Scripts\Activate.ps1       # Windows PowerShell
# source .venv/bin/activate       # Linux / macOS

python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Database Setup (PostgreSQL)
1. Ensure PostgreSQL is running on `localhost:5432`.
2. Create the database: `CREATE DATABASE crop_disease_db;`
3. Copy environment template:
   ```powershell
   cd backend
   copy .env.example .env
   ```
4. Configure your database credentials and API keys in `backend/.env`.
5. Run migrations and seed reference data:
   ```powershell
   alembic upgrade head
   python seed.py
   ```

### Step 3: Frontend Installation
In a separate terminal:
```powershell
cd frontend
copy .env.example .env
npm install
```
Add your Clerk publishable key to `frontend/.env` (`VITE_CLERK_PUBLISHABLE_KEY=pk_test_...`).

### Step 4: Run the Application
1. **Start Backend**:
   ```powershell
   cd backend
   python -m uvicorn main:app --reload --port 8000
   ```
   API Docs available at: `http://localhost:8000/docs`
2. **Start Frontend**:
   ```powershell
   cd frontend
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## 7. Running Tests

- **Standalone Inference Test** (No database or server required):
  ```powershell
  python tests/test_inference.py
  ```
- **Profile Management & Groq 3-Key Rotation Test Suite**:
  ```powershell
  python backend/tests/test_profile_and_groq_flow.py
  ```
- **Database Connection Diagnostic**:
  ```powershell
  python backend/tests/test_db_connection.py
  ```
- **Personalized Dashboard Isolation Tests**:
  ```powershell
  python backend/tests/test_dashboard_flow.py
  ```
- **Frontend Production Build**:
  ```powershell
  cd frontend
  npm run build
  ```

---

## 8. Security & Privacy Notes

- **Secrets Isolation**: Real API keys (`CLERK_SECRET_KEY`, `GROQ_API_KEY_1/2/3`), database passwords, and `.env` files are strictly excluded from Git via `.gitignore`.
- **Identity Isolation**: User identity is derived strictly from verified JWT tokens on the backend; client-supplied user IDs in query parameters are ignored.
- **Image Privacy**: Uploaded leaf photos are stored locally on the server filesystem (`backend/uploads/scans/`) and excluded from Git commits.
