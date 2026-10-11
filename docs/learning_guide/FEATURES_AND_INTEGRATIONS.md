# Features & External Integrations Guide

## 1. Generative AI Advisory Integration (Groq LLM)

### Decoupling Classification From Generative Advisory
A core architectural pillar is that **the deep learning model and the LLM are separate systems**:
- **MobileNetV2**: Deterministic computer vision classifier. It analyzes leaf pixels and outputs an authoritative class label (e.g., `Curl Virus`).
- **Groq LLM (`openai/gpt-oss-120b`)**: Natural language agronomist. It receives the confirmed disease label, farm location, and live weather to generate actionable management steps.
- **Rule of Truth**: The LLM is **never allowed to change or second-guess the disease classification**.

### Multi-Key Rotating Pool
In `backend/services/llm_service.py`, the system implements a **multi-key rotation pool**:
```python
GROQ_API_KEY_1=...
GROQ_API_KEY_2=...
GROQ_API_KEY_3=...
```
If an active key encounters rate limits (`HTTP 429`), the service automatically switches to the next configured key alias (`key_2`, `key_3`), maintaining high availability.

### Anti-Hallucination Chemical Directive
To protect crops and soil health, the system prompt in `backend/services/llm_service.py` enforces strict agronomic constraints:
1. **Chemical Regulation Rule**: Strictly forbids fabricating proprietary chemical brand names or dosages.
2. **Prioritize Bio-Friendly & Cultural Management**: Focuses on field sanitation, pruning, airflow, yellow sticky traps, and neem cake/oil.
3. **Institutional Referral**: Directs farmers to consult local **Krishi Vigyan Kendra (KVK)** extension officers before applying scheduled chemical sprays.
4. **Structured JSON Output**: Mandates output conforming strictly to Pydantic `ReportStructuredResponse`.

### Offline Fallback Engine
If the Groq API experiences network timeouts or quota exhaustion across all keys, `LLMService._generate_fallback_report()` returns a curated agronomic management template based on the confirmed disease class, preventing crashing 500 error screens.

---

## 2. Automated Agro-Weather Integration (Open-Meteo)

### Free, Reliable Meteorological Observations
The project utilizes **Open-Meteo** (`WEATHER_PROVIDER="open-meteo"`):
- Free open-access weather API requiring no proprietary API keys.
- Accurate GPS coordinates-based observations derived from high-resolution global numerical models.

### Parameters Captured & Agronomic Significance
- **`temperature_c`**: Ambient air temperature.
- **`humidity_pct`**: Relative humidity. (Warm temperatures + humidity $>80\%$ accelerate fungal spore germination).
- **`rainfall_mm`**: Precipitation. (Rain splash disperses bacterial cells like *Xanthomonas*).
- **`wind_speed_kmh`**: Wind speed. (Disperses viral insect vectors like whiteflies).
- **WMO Weather Code Translation**: Maps numerical WMO codes (e.g. 2 -> "Partly cloudy", 61 -> "Slight rain") into farmer-friendly text.

### Database Caching Policy (30 Minutes)
In `backend/services/weather_service.py`, snapshots recorded within the last **30 minutes** (`WEATHER_CACHE_MINUTES=30`) are loaded directly from the PostgreSQL `weather_snapshots` table, eliminating redundant network calls.

---

## 3. Multilingual Localization Architecture

The application supports three languages:
1. **English (`en`)**
2. **Hindi (`hi`)** — हिन्दी
3. **Gujarati (`gu`)** — ગુજરાતી

### Frontend Dictionary Resolution
- Translations reside in `frontend/src/locales/en.js`, `hi.js`, `gu.js`.
- `LanguageContext.jsx` exposes the `t(key, fallback)` helper supporting dot-notation keys (e.g. `t("diagnose.title")`).
- Missing keys cleanly fall back to English defaults.

### On-Demand In-Place Advisory Translation
When viewing a scan report, farmers can toggle language buttons (`🇬🇧 English`, `🇮🇳 हिन्दी`, `🌾 ગુજરાતી`). 
The frontend calls `GET /api/v1/scans/{id}/report?lang=hi`:
- If the report already exists in Hindi in the `reports` table, it is served from the database.
- If not, `DiagnosisService` prompts the LLM with Hindi instructions, stores the new `Report` row in PostgreSQL, and returns it dynamically.

---

## 4. Bilingual Vector PDF Report Generation (ReportLab)

### Technology: ReportLab 5.0
`backend/services/pdf_service.py` programmatically compiles an A4 vector diagnostic report.

### Key Capabilities
1. **Unicode TrueType Font Registration**: Standard PDF fonts (Helvetica) cannot render Devanagari or Gujarati scripts. The service registers bundled TrueType fonts in `backend/fonts/`:
   - `NotoSans-Regular.ttf`
   - `NotoSansDevanagari-Regular.ttf`
   - `NotoSansGujarati-Regular.ttf`
   - Fallback: Windows `C:/Windows/Fonts/Nirmala.ttc`
2. **Dynamic Numbered Canvas**: A custom canvas subclass (`NumberedCanvas`) performs a two-pass layout to print exact "Page X of Y" page counts and statutory disclaimers in the footer.
3. **Aspect-Ratio Leaf Image Scaling**: Decodes the original leaf image using Pillow, computes the exact aspect ratio, and scales it cleanly into a bounded table cell without distortion.
4. **Confidence Distinction**:
   - High-confidence scans render a green-accented "CONFIDENT DIAGNOSIS" certificate with full symptoms and advisory sections.
   - Low-confidence scans render an amber-accented "DIAGNOSTIC INCONCLUSIVE" warning report with retake instructions and no treatment steps.
