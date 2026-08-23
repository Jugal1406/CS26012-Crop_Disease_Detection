# CS26012 — Crop Disease Detection

A web application that classifies plant leaf diseases from an uploaded or captured photo and returns a structured diagnostic report with locally-adapted treatment recommendations, built for both farmers and home/terrace gardeners across India.

**Team ID:** CS26012
**Author:** Jugal Kshatriya (24CS042)
**Institution:** CSPIT, CHARUSAT

## Project Summary

Most existing crop-disease classifiers are trained and benchmarked almost entirely on lab-condition images (e.g., PlantVillage), which do not reflect the cluttered backgrounds, variable lighting, and natural photography conditions of real farm and garden use. This project builds a crop disease detection system trained primarily on **real, on-field Indian crop images**, covering 8 pan-India staple and regionally significant crops, rather than defaulting to lab-condition data.

As a secondary case study, the project also includes a **lab-vs-field comparison** for Tomato and Rice — two crops where both lab-condition and field-condition data are available — to explicitly demonstrate the accuracy gap between models trained on lab images versus field images, and how it affects real-world usability.

## Crops Covered

| Crop | Data Type | Source |
|---|---|---|
| Groundnut | On-field (India) | Multi-Crop Disease Dataset, Mendeley |
| Banana | On-field (India) | Multi-Crop Disease Dataset, Mendeley |
| Tomato | Lab-condition | PlantVillage (used as the lab-vs-field comparison baseline) |
| Potato | On-field (India) | PLDD-UP (Uttar Pradesh), Mendeley |
| Rice | On-field (India) + Lab (kept separate) | Kaggle (Rice Leaf Disease Images + Healthy class) |
| Wheat | On-field (India) | Pending — dataset access requested from authors |
| Chili | On-field (India) | Krishna River Basin, Deccan Plateau dataset, Mendeley |
| Soyabean | On-field (India) | MH-SoyaHealthVision (leaf images only, UAV images excluded) |

See [`Problem Statement.md`](./Problem%20Statement.md) for the full motivation and [`Literature Survey.md`](./Literature%20Survey.md) for related work.

## Tech Stack

- **Frontend:** React (Vite)
- **Backend:** Python, FastAPI
- **Model training:** PyTorch / TensorFlow (Keras), transfer learning on MobileNetV2 / EfficientNet-Lite
- **Database:** SQLite (scan history, treatment knowledge base)
- **Training compute:** Google Colab (free-tier GPU)
- **Regional language:** Translation API (LibreTranslate / Google Cloud Translation)

## Repository Structure

```
├── data/                  # Dataset prep scripts (not committed - see .gitignore)
├── notebooks/              # Colab/Jupyter training experiments
├── backend/                # FastAPI app, inference endpoints
├── frontend/                # React app
├── knowledge_base/          # Disease -> treatment structured content
├── Literature Survey.md
├── Problem Statement.md
├── Project Timeline.md
├── Requirements.md
└── README.md
```

## Status

Actively in development. See [`Project Timeline.md`](./Project%20Timeline.md) for current progress and weekly plan.
