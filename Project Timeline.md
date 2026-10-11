# Project Timeline & Milestone Tracking

**Project:** CS26012 — Crop Disease Detection & Agricultural Advisory Platform  
**Academic Semester:** Semester 5 (Institutional Development Period: Weeks 1–12)  
**Author:** Jugal Kshatriya (24CS042)  
**Institution:** CSPIT, CHARUSAT  

---

## 1. Development Milestone Schedule

| Institutional Week | Dev Phase | Focus Area | Status | Key Deliverables & Verified Evidence |
| :---: | :---: | :--- | :---: | :--- |
| **Week 1–2** | Milestone 1 | **Problem Definition & Literature Review** | **Completed** | • Formulated `Problem Statement.md` focusing on the lab-vs-field accuracy gap.<br>• Curated literature on CNN plant pathology and domain shift in `Literature Survey.md`. |
| **Week 3** | Milestone 2 | **Dataset Acquisition & Multi-Crop Sourcing** | **Completed** | • Sourced Indian field datasets for Chili, Potato, Groundnut, Banana, Soybean.<br>• Selected PlantVillage Tomato as lab-condition baseline.<br>• Cataloged initial disease classes and identified data gaps. |
| **Week 4** | Milestone 3 | **Data Cleansing, Deduplication & Pipeline Design** | **Completed** | • Designed 10-phase Colab pipeline in `notebooks/train_crop_model.ipynb`.<br>• Implemented MD5 and perceptual hashing (`imagehash`) to prune duplicate leaf bursts.<br>• Generated stratified 70/15/15 train/validation/test splits. |
| **Week 5** | Milestone 4 | **Model Training & Chili Model Evaluation** | **Completed** | • Trained MobileNetV2 backbone on Chili leaf disease dataset.<br>• Serialized trained weights to `models/chili_mobilenetv2.keras` (12 classes).<br>• Evaluated internal test accuracy (94.2%) and saved `models/chili_mobilenetv2_meta.json`. |
| **Week 6** | Milestone 5 | **FastAPI Backend & Inference Engine Scaffolding** | **Completed** | • Built `backend/inference.py` with image decoding, center crop, and tensor normalization.<br>• Implemented 70% confidence threshold rejection gate.<br>• Created `tests/test_inference.py` (8/8 standalone inference tests passing). |
| **Week 7** | Milestone 6 | **Frontend Architecture & Landing Page** | **Completed** | • Built React 19 + Vite SPA with modular styling (`landing.css`).<br>• Designed procedural SVG leaf growth visualizer (`PlantScene.jsx`, `FieldRows.jsx`).<br>• Built interactive demo, crop catalog cards, and responsive hero layout. |
| **Week 8** | Milestone 7 | **PostgreSQL Relational Layer & Migrations** | **Completed** | • Architected 9-table schema (`models.py`) with foreign keys and check constraints.<br>• Created Alembic migrations in `backend/alembic/versions/`.<br>• Created `backend/seed.py` for reference crops and disease classes.<br>• Created `backend/repositories/` data access layer. |
| **Week 9** | Milestone 8 | **Authentication & Clerk Identity Synchronization** | **Completed** | • Integrated Clerk authentication (`@clerk/clerk-react` and `backend/clerk_auth.py`).<br>• Implemented idempotent `/api/v1/auth/sync` and `/me` routes.<br>• Built protected client routing (`ProtectedRoute.jsx`) and safe redirect guards. |
| **Week 10** | Milestone 9 | **Farm Plot Context & Open-Meteo Agro-Weather** | **Completed** | • Built Farm profile management (`backend/routers/farms.py` and `frontend/src/pages/Farms.jsx`).<br>• Integrated Open-Meteo REST API (`services/weather_service.py`) with 30-min in-memory cache.<br>• Implemented GPS auto-locate and weather snapshots for farm plots. |
| **Week 11** | Milestone 10 | **Groq Advisory, Multi-Key Rotation & PDF Reports** | **Completed** | • Integrated Groq LLM (`openai/gpt-oss-120b`) in `services/llm_service.py`.<br>• Implemented 3-key auto-failover (`GROQ_API_KEY_1/2/3`) for HTTP 429 rate limits.<br>• Added localized offline agronomic fallback report.<br>• Built ReportLab multilingual PDF engine (`services/pdf_service.py`) with Noto fonts. |
| **Week 12** | Milestone 11 | **Full Trilingual Localization & Profile Management** | **Completed** | • Complete translation dictionaries in `en.js`, `hi.js`, `gu.js`.<br>• Localized all forms (Add/Edit Farm, Profile, Diagnosis) and scan modals.<br>• Implemented Profile Editing (`PATCH /api/v1/auth/profile`) with phone normalization.<br>• Created logout confirmation dialog (`LogoutConfirmModal.jsx`). |
| **Post-W12** | Milestone 12 | **Multi-Crop Expansion (Potato & Groundnut) & Profile Bug Fix** | **Completed** | • Integrated trained MobileNetV2 models for Potato (3 classes: Early Blight, Late Blight, Healthy) and Groundnut (6 classes: Early/Late Leaf Spot, Rust, Nutrition Deficiency).<br>• Standardized clinical taxonomy (expanded abbreviations EB/LB to Early Blight and Late Blight).<br>• Repaired profile persistence bug in Dashboard state and auth sync clobbering.<br>• Seeded all 23 crop-disease relational rows into PostgreSQL database. |
| **Post-W12** | Milestone 13 | **Lab vs. Field Domain Shift Benchmark Study** | **Planned / Next Steps** | • Empirical evaluation comparing PlantVillage lab models against field datasets (Tomato/Rice).<br>• Generate comparative confusion matrix report for academic defense. |

---

## 2. Checkpoint Review & Status Verification

- **Production Core**: Fully operational and passing all integration tests (database, inference, profile management, Groq multi-key rotation, PDF export, frontend production build).
- **Active ML Models**: Chili (`chili_mobilenetv2.keras`), Potato (`potato_mobilenetv2.keras`), and Groundnut (`groundnut_mobilenetv2_model_2.keras`) are fully integrated and serving live predictions.
- **Pipeline Ready**: Colab training pipeline (`notebooks/train_crop_model.ipynb`) is ready for execution on additional cataloged crop datasets (Rice, Tomato, Banana, Soybean).
