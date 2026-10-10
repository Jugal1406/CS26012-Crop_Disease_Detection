# Project Work Done & System Overview Report
**Project Name:** CS26012 — Crop Disease Detection  
**Team ID:** CS26012  
**Author:** Jugal Kshatriya (24CS042)  
**Institution:** CSPIT, CHARUSAT  
**Repository:** [CS26012-Crop_Disease_Detection](file:///d:/sem-5/Project-1/CS26012-Crop_Disease_Detection)  
**Document Generation Date:** October 2026  

---

## 1. Executive Summary & Work Completed Till Now

This project focuses on building a crop disease diagnosis and advisory web platform tailored specifically for Indian agricultural contexts. Unlike common academic baselines trained on uniform lab images (e.g., PlantVillage), this project addresses the **lab-vs-field accuracy gap** by training models primarily on real, in-situ, on-field datasets across 8 priority crops (Groundnut, Banana, Tomato, Potato, Rice, Wheat, Chili, and Soybean).

### Key Accomplishments:
1. **System & Requirements Specification**:
   - Outlined complete functional requirements: user leaf upload/camera capture, crop selection, CNN classification, confidence score thresholding (rejecting low-confidence predictions to prevent erroneous treatment), structured actionable reports (disease name, description, organic treatment, chemical treatment, prevention), scan history, and regional language translation support.
   - Formalized dataset balance criteria (minimum 100 images per class, maximum 5:1 majority/minority class ratio or weighted sampling) in `Requirements.md`.
   - Conducted comprehensive literature review and comparative study in `Literature Survey.md` and `Problem Statement.md`.
   - Structured a 10-week institutional development roadmap in `Project Timeline.md`.

2. **Frontend Architecture & Implementation (React + Vite)**:
   - Built a landing page with custom CSS (`landing.css`), interactive SVG and procedural HTML5 Canvas visualizations (`PlantScene.jsx`, `FieldRows.jsx`, `LeafArt.jsx`) rendering growth stages and leaf graphics.
   - Structured component layout: sticky navigation bar (`Navbar.jsx`), hero section (`Hero.jsx`), how-it-works process steps (`HowItWorks.jsx`), supported crop cards (`CropCards.jsx`), neural network & tech stack overview (`Technology.jsx`), interactive UI demo (`DemoSection.jsx`), and footer (`Footer.jsx`).
   - Configured client-side routing via `react-router-dom` in `App.jsx` for `/` (Home), `/diagnose` (Diagnosis portal), and `/login` (Phone/OTP auth placeholder).
   - Developed the working diagnosis client in `Diagnose.jsx`, enabling users to select crop types, preview image uploads, submit `multipart/form-data` to the backend, and view the diagnostic result card.

3. **Backend API Scaffolding (Python + FastAPI)**:
   - Initialized a modular FastAPI application in `backend/main.py`.
   - Configured CORS middleware to allow communication with the Vite frontend (`http://localhost:5173`).
   - Implemented an operational `POST /predict` endpoint that receives the crop name and image file, handles payload parsing, and returns structured diagnostic JSON.
   - Tested and verified end-to-end communication between the frontend client and FastAPI backend.

4. **Machine Learning Pipeline (TensorFlow / Keras + MobileNetV2)**:
   - Developed `notebooks/train_crop_model.ipynb`, defining an end-to-end 10-phase pipeline:
     - **Part A:** Google Drive mounting, GitHub repository synchronization, and dependency setup.
     - **Part B:** Dataset exploration (class distribution, corrupt file detection, image dimensions).
     - **Part C:** Duplicate detection (exact MD5 hash + perceptual hashing via `imagehash`).
     - **Part D:** Dataset cleansing (cross-class conflict elimination and near-duplicate pruning).
     - **Part E:** Stratified 70/15/15 train/validation/test splitting with manifest generation.
     - **Part F:** `tf.data` input pipeline with on-the-fly augmentation and balanced class weighting.
     - **Part G:** Transfer learning using MobileNetV2 (frozen pre-trained backbone + custom dense classification head).
     - **Part H:** Rigorous in-distribution test-set evaluation (accuracy, loss, confusion matrices).
     - **Part I:** Model artifact and metadata serialization to Google Drive / local storage.
     - **Part J:** Model reload verification and out-of-distribution (OOD) testing on real-world photos.
   - Created the `models/` directory for saving trained weights (`.h5` / SavedModel format) and class label mappings.

---

## 2. Directory & File Structure

```text
CS26012-Crop_Disease_Detection/
├── .gitignore                      # Git exclusion rules (venv, node_modules, cache, large datasets)
├── README.md                       # High-level project summary, crop list, and tech stack overview
├── Problem Statement.md            # Problem motivation, lab-vs-field gap, and crop dataset sources
├── Literature Survey.md            # Academic review of existing deep learning methods in agriculture
├── Requirements.md                 # Complete functional, non-functional, and dataset requirements
├── Project Timeline.md             # 10-week institutional development roadmap
├── work_done.md                    # Detailed progress report, architecture, and file guide
│
├── backend/
│   ├── main.py                     # FastAPI application entry point, CORS config, and inference routing
│   └── venv/                       # Local Python virtual environment
│
├── frontend/
│   ├── index.html                  # HTML entry point with metadata and root div
│   ├── package.json                # Project dependencies, build scripts, and dev tools
│   ├── vite.config.js              # Vite bundler configuration
│   ├── public/                     # Static assets (favicons, icons)
│   └── src/
│       ├── main.jsx                # Application mounting point
│       ├── App.jsx                 # Route definitions (BrowserRouter, Routes, Route)
│       ├── App.css                 # Base application styles
│       ├── index.css               # Global typography, color variables, and CSS resets
│       ├── pages/
│       │   ├── Home.jsx            # Landing page aggregating all landing components
│       │   ├── Diagnose.jsx        # Leaf image upload, crop selection, and prediction UI
│       │   └── Login.jsx           # Phone/OTP authentication page placeholder
│       ├── components/
│       │   ├── Navbar.jsx          # Header navigation with routing links
│       │   ├── Hero.jsx            # Hero section with interactive animations and CTA buttons
│       │   ├── PlantJourney.jsx    # Visual plant growth life-cycle scroll sequence
│       │   ├── HowItWorks.jsx      # Three-step guide on how the AI diagnosis works
│       │   ├── CropCards.jsx       # Grid display of supported crops with metadata
│       │   ├── Technology.jsx      # Explanatory cards on the CNN model & dataset approach
│       │   ├── DemoSection.jsx     # UI preview of diagnostic results
│       │   ├── FinalCTA.jsx        # Bottom call-to-action banner
│       │   ├── Footer.jsx          # Footer with institutional credits and links
│       │   ├── Icons.jsx           # Reusable SVG icon collection
│       │   ├── Reveal.jsx          # Scroll-triggered animation wrapper
│       │   ├── ScrollToTop.jsx     # Scroll position reset helper on page transition
│       │   └── plant/              # Procedural graphics and canvas utilities
│       │       ├── PlantScene.jsx  # 2D/3D organic plant canvas coordinator
│       │       ├── FieldRows.jsx   # Perspective field lines generator
│       │       ├── LeafArt.jsx     # Procedural leaf vector drawings
│       │       ├── geometry.js     # Mathematical curve and angle calculations
│       │       └── noise.js        # Simplex/Perlin noise generation
│       ├── content/
│       │   └── landing.js          # Centralized data, copy, and crop card lists
│       ├── hooks/
│       │   ├── useInView.js        # Intersection Observer hook for scroll animations
│       │   ├── useScrollProgress.js# Page scroll progress calculator
│       │   ├── useElementSize.js   # Dynamic element bounding box tracker
│       │   └── usePrefersReducedMotion.js # Accessibility preference hook
│       └── styles/
│           └── landing.css         # Styling, glassmorphism, responsive grid, and keyframes
│
├── models/
│   └── .gitkeep                    # Directory to store trained model weights and class labels
│
└── notebooks/
    ├── .gitkeep
    └── train_crop_model.ipynb      # Complete Colab/Jupyter model training pipeline
```

---

## 3. Comprehensive File-by-File Breakdown

### A. Root Documentation
| File | Description & Purpose |
|---|---|
| `README.md` | Provides a high-level summary of the repository, the 8 supported crops with dataset origins, project tech stack, and quickstart notes. |
| `Problem Statement.md` | Details the fundamental research problem: models trained on pristine lab backgrounds (e.g. PlantVillage) fail in natural Indian farm environments. Defines target crops and the planned lab-vs-field benchmark for Tomato and Rice. |
| `Requirements.md` | Formal specifications covering functional requirements (upload, inference, confidence checks, bilingual reports, scan history), non-functional requirements (speed, privacy, no mandatory logins), and dataset constraints. |
| `Literature Survey.md` | Explores prior research in CNN-based agricultural pathology, highlighting shortcomings in current literature regarding domain transfer and field clutter. |
| `Project Timeline.md` | A structured 10-week schedule tracking progress from dataset aggregation (Weeks 1–3), model development (Weeks 4–6), backend/knowledge base setup (Weeks 7–8), to full frontend integration and lab-vs-field evaluation (Weeks 9–10). |
| `work_done.md` | This document; comprehensive reference manual detailing system status, architecture, and component duties. |

---

### B. Backend (`backend/`)
| File | Description & Purpose |
|---|---|
| `backend/main.py` | Primary FastAPI server. Configures CORS middleware for frontend communication (`http://localhost:5173`), provides a root health probe (`GET /`), and exposes `POST /predict` to accept `crop` (form field) and `image` (file upload) for inference testing. |
| `backend/venv/` | Python local virtual environment for development and testing. |

---

### C. Machine Learning (`notebooks/` & `models/`)
| File | Description & Purpose |
|---|---|
| `notebooks/train_crop_model.ipynb` | Comprehensive Google Colab notebook for MobileNetV2 transfer learning. Covers data mounting, corrupt image removal, MD5 and perceptual hashing deduplication, 70/15/15 stratified partitioning, augmentation, weighted class training, test evaluation, and out-of-distribution verification. |
| `models/.gitkeep` | Preserves the `models/` directory in version control, designated for exported TensorFlow/Keras models, label dictionaries, and evaluation reports. |

---

### D. Frontend (`frontend/src/`)
| File | Description & Purpose |
|---|---|
| `frontend/src/main.jsx` | React entry point that binds the `App` component into the DOM root (`#root`). |
| `frontend/src/App.jsx` | Top-level routing router configuring URL paths (`/`, `/diagnose`, `/login`) and managing scroll reset behavior. |
| `frontend/src/index.css` | Global styling including typography, CSS variables, resets, and utility classes. |
| `frontend/src/App.css` | Base application styles and layout containers. |
| `frontend/src/pages/Home.jsx` | Main landing page combining Hero, HowItWorks, CropCards, Tech, Demo, and Footer sections. |
| `frontend/src/pages/Diagnose.jsx` | Interactive diagnostic workbench: allows crop selection, leaf photo upload/preview, submits data via `fetch` to `http://localhost:8000/predict`, and renders results (disease name, confidence score). |
| `frontend/src/pages/Login.jsx` | Dedicated placeholder for future mobile number and OTP authentication. |
| `frontend/src/components/Navbar.jsx` | Header component featuring brand navigation and quick-access links to the diagnosis tool. |
| `frontend/src/components/Hero.jsx` | Landing hero component with title text, CTAs, and background canvas plant animations. |
| `frontend/src/components/PlantJourney.jsx`| Visual storytelling component detailing healthy crop growth progression. |
| `frontend/src/components/HowItWorks.jsx` | Instructional section breaking down the 3-stage user workflow (Photograph, Diagnose, Treat). |
| `frontend/src/components/CropCards.jsx` | Grid displaying individual crop profiles and disease categories supported by the platform. |
| `frontend/src/components/Technology.jsx` | Explains the underlying deep learning architecture, on-field dataset rationale, and model speed. |
| `frontend/src/components/DemoSection.jsx`| Live interactive mockup simulating diagnosis outputs. |
| `frontend/src/components/FinalCTA.jsx` | High-conversion banner driving users to test the diagnosis tool. |
| `frontend/src/components/Footer.jsx` | Footer component with copyright, institution details (CSPIT, CHARUSAT), and navigation links. |
| `frontend/src/components/Icons.jsx` | SVG icon library supplying visual iconography across the landing components. |
| `frontend/src/components/Reveal.jsx` | Smooth scroll reveal wrapper utilizing intersection observer triggers. |
| `frontend/src/components/ScrollToTop.jsx`| Utility that scrolls the window back to `(0, 0)` upon route changes. |
| `frontend/src/components/plant/` | Directory housing procedural canvas rendering algorithms: `PlantScene.jsx` (scene manager), `FieldRows.jsx` (field visuals), `LeafArt.jsx` (leaf geometries), `geometry.js` (math calculations), and `noise.js` (organic noise generator). |
| `frontend/src/content/landing.js` | Centralized data dictionary containing marketing copy, crop descriptions, feature lists, and stats. |
| `frontend/src/hooks/` | Custom hooks: `useInView.js` (viewport visibility), `useScrollProgress.js` (scroll tracking), `useElementSize.js` (resize listener), `usePrefersReducedMotion.js` (accessibility). |
| `frontend/src/styles/landing.css`| Custom stylesheet defining modern dark/green aesthetics, animations, and responsive breakpoints. |

---

## 4. Current vs. Planned System Workflows

### A. Current Implemented Workflow (Prototype)
```text
[User Browser]
      │
      ▼
1. Visits /diagnose in React Frontend
2. Selects Crop (e.g. Potato, Groundnut, Chili)
3. Uploads Leaf Image (JPG/PNG)
      │
      ▼ (HTTP POST multipart/form-data)
[FastAPI Server: http://localhost:8000/predict]
      │
      ▼
4. Endpoint extracts crop string and image file
5. Returns JSON response:
   {
     "crop": "potato",
     "filename": "leaf_sample.jpg",
     "disease": "Test Disease",
     "confidence": 95.2
   }
      │
      ▼ (JSON)
[Frontend UI]
6. Renders Diagnostic Result Box showing crop, filename, disease name, and confidence score.
```

### B. Target End-to-End Workflow (Planned Architecture)
```text
[User Mobile / Browser]
      │
      ▼
1. Camera Capture or Image Upload with Crop Selection
      │
      ▼ (HTTP POST multipart/form-data)
[FastAPI Backend Pipeline]
      │
      ├─► 2. Input Validation (Verify image format, resolution, valid crop)
      │
      ├─► 3. Image Preprocessing (Resize to 224x224, normalize RGB tensors)
      │
      ├─► 4. Deep Learning Inference (Trained MobileNetV2 Model)
      │      └─► Computes class softmax probabilities
      │
      ├─► 5. Confidence Threshold Validation
      │      ├─► Confidence >= 70%: Proceed to diagnosis
      │      └─► Confidence < 70%: Return "Low confidence / Please retake photo"
      │
      ├─► 6. Knowledge Base Lookup (SQLite Database)
      │      └─► Retrieve: Disease Description, Organic Remedy, Chemical Remedy, Prevention Tip
      │
      ├─► 7. Regional Language Translation (LibreTranslate / Google Cloud)
      │      └─► Translate advisory content if non-English preference is selected
      │
      └─► 8. Scan History Persistence (SQLite)
             └─► Save anonymous session ID, timestamp, crop, disease, and image file path
      │
      ▼ (Complete Diagnostic Report JSON)
[Frontend Client]
9. Interactive Report Card Display:
   - Disease banner with severity & confidence score
   - Side-by-side tabs: Organic vs. Chemical remedies
   - Prevention checklist
   - Option to download/share advisory or save to scan history
```
