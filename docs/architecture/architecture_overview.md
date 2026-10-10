# System Architecture & Technical Flow

## High-Level Architecture

The **CS26012 Crop Disease Detection Platform** is a decoupled full-stack application designed for smallholder farmers and agricultural extension specialists across India:

```
[ React 19 + Vite Frontend ]
       │
       ├── Clerk Auth SDK (Authentication, Session Tokens, MFA)
       ├── Custom i18n Localization Engine (English, Hindi, Gujarati)
       │
       ▼ (REST API / JSON / Multipart HTTP)
[ FastAPI Async Backend Service ]
       │
       ├── Clerk JWT Verification (Cryptographic token validation & user sync)
       ├── TensorFlow / Keras Engine (MobileNetV2 Leaf Pathology Inference)
       ├── Open-Meteo Weather Client (Micro-climate agro-meteorological snapshots)
       ├── Groq LLM Client (openai/gpt-oss-120b with 3-key auto-failover & agronomic fallback)
       ├── ReportLab PDF Engine (Multilingual Unicode PDF rendering with Noto fonts)
       │
       ▼ (SQLAlchemy 2.0 Async / asyncpg)
[ PostgreSQL Relational Database (crop_disease_db) ]
       ├── users
       ├── crops
       ├── disease_classes
       ├── models
       ├── farms
       ├── scans
       ├── weather_snapshots
       ├── reports
       └── audit_logs
```

## Detailed Processing Flow (Leaf Diagnosis)

1. **Upload & Preprocessing**:
   - The user selects a target crop (`chili`) and uploads a leaf photograph (`JPEG`, `PNG`, `WEBP`, max 10 MB).
   - `inference.py` validates image integrity, performs a center-crop, resizes to `224x224`, normalizes pixel tensors `[0, 1]`, and evaluates the MobileNetV2 classification head.
2. **Confidence Gating**:
   - Softmax probabilities are checked against `CONFIDENCE_THRESHOLD = 0.70`.
   - If confidence is `< 0.70`, the system rejects the prediction as `low_confidence`, saves the scan for record-keeping, and instructs the user to take a well-lit photograph centered on symptoms.
3. **Contextual Enrichment**:
   - If the user links a registered farm plot, GPS coordinates are used to query Open-Meteo for ambient weather (temperature, relative humidity, precipitation, wind speed).
4. **Agronomic Advisory Generation**:
   - `llm_service.py` sends a structured prompt to Groq LLM (`openai/gpt-oss-120b`).
   - The LLM receives strict directives: it is **forbidden from altering the ML disease diagnosis** and must focus on cultural management, field sanitation, and non-chemical biological controls (e.g. neem cake, yellow sticky cards).
   - If Groq returns HTTP 429 rate limit or quota exhaustion, `llm_service.py` rotates to `GROQ_API_KEY_2` and `GROQ_API_KEY_3`. If all keys fail, an offline localized agronomic fallback report is served.
5. **Persistence & Export**:
   - Scan records, weather snapshots, and advisory reports are persisted to PostgreSQL.
   - Users can view reports interactively or generate an offline downloadable PDF report in English, Hindi, or Gujarati via ReportLab.
