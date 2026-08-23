# Project Timeline

Institutional Weeks 1–2 were used for problem identification and defining the problem statement. Development work began in **Institutional Week 3**, treated here as **Development Week 1** of a 10-week build plan.

| Dev Week | Institutional Week | Focus | Status |
|---|---|---|---|
| 1 | Week 3 | Initial dataset collection for all 8 crops; identified missing Wheat dataset and missing Rice Healthy class | Complete |
| 2 | Week 4 | Merged train/valid/test splits per class; built and validated a duplicate/augmentation audit tool; defined class-imbalance handling strategy (weighted sampling + augmentation); rescoped Chili to its 2 strongest classes; sourced additional on-field data for Potato, Chili, Soyabean, Rice Healthy; replaced Corn with Soyabean due to lack of a strong on-field Indian Corn dataset | Complete |
| 3 | Week 5 | Finalize remaining dataset gaps (Wheat pending author response); run deduplication cleanup on flagged classes (Rice diseases, Potato Healthy); build final stratified train/valid/test splits per crop from cleaned data | In progress |
| 4 | Week 6 | Set up training pipeline (Colab); run small-scale exploratory training (a few epochs, 2–3 candidate architectures) on one crop to validate the pipeline end-to-end before scaling | Planned |
| 5 | Week 7 | Train baseline models for the crops with fully ready data; begin backend (FastAPI) scaffolding | Planned |
| 6 | Week 8 | Extend training to remaining crops (Wheat, if sourced in time); rigorous per-class evaluation (accuracy, confusion matrices, confidence calibration) | Planned |
| 7 | Week 9 | Knowledge base curation — disease-to-treatment content for all trained classes, sourced from ICAR/agricultural extension material | Planned |
| 8 | Week 10 | Backend inference endpoint, image upload handling, report assembly logic; begin React frontend | Planned |
| 9 | Week 11 | Complete frontend (upload/capture, crop selector, report display, scan history); regional language integration | Planned |
| 10 | Week 12 | Lab-vs-field case study (Tomato and Rice); end-to-end testing, polish, documentation, and final report/demo preparation | Planned |

## Checkpoint Policy

At the end of Dev Week 8 (Institutional Week 6), a scope checkpoint will be made: if Wheat's dataset is not available and integrated by this point, the project will proceed with a clean, deliberate 7-crop scope rather than delaying the full pipeline further, with Wheat noted as future work if it arrives later.

