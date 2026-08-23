# Requirements

## Functional Requirements

1. The system shall allow a user to upload an image file or capture a photo directly via the browser camera.
2. The system shall allow the user to select the crop being diagnosed prior to classification.
3. The system shall classify the uploaded leaf image into a disease category (or healthy) for the selected crop, using a trained CNN model.
4. The system shall display a confidence score alongside the prediction.
5. If the prediction confidence falls below a defined threshold, the system shall inform the user the result is uncertain and suggest retaking the photo, rather than presenting a low-confidence guess as a definitive diagnosis.
6. The system shall generate a structured report containing: disease name, a plain-language description, the confidence score, an organic/low-cost treatment option, a chemical treatment option, and a prevention tip.
7. The system shall support displaying the report in at least one regional Indian language in addition to English.
8. The system shall store a history of past scans, retrievable by the user in a later session.

## Non-Functional Requirements

1. The system shall return a diagnostic report within a few seconds of image submission under normal network conditions.
2. The system shall not store raw images directly inside the database; images are stored as files with a referenced file path.
3. The system shall not require user account creation/login for core functionality; an anonymous session identifier is used to support scan history.
4. Any third-party API keys (e.g., translation service) shall be stored as environment variables and never committed to version control.
5. The knowledge base content shall be sourced from verifiable agricultural references (e.g., ICAR advisories, agricultural university extension material) rather than generated automatically, to ensure treatment accuracy.

## Dataset Requirements

1. Each disease class used for training should have a minimum of 100 images; classes below this threshold are to be rescoped, merged, or excluded, with the decision documented.
2. Where feasible, majority-to-minority class image count ratio within a single crop should not exceed approximately 5:1 without applying weighted sampling and augmentation.
3. All dataset sources must be documented with their origin, license, and collection methodology in the project report.

## Software and Library Requirements

| Category | Tool / Library |
|---|---|
| Language (ML, backend) | Python 3.10+ |
| Model training | PyTorch or TensorFlow/Keras |
| Image processing | Pillow, OpenCV |
| Data augmentation | Albumentations / torchvision.transforms |
| Duplicate/augmentation detection | imagehash, numpy |
| Backend framework | FastAPI |
| Database | SQLite, SQLAlchemy |
| Frontend | React (Vite) |
| Frontend language | JavaScript / Node.js tooling |
| Translation | LibreTranslate or Google Cloud Translation API |
| Training compute | Google Colab (free-tier GPU) |
| Version control | Git, GitHub |

## Hardware Requirements

- A machine capable of running a modern web browser for development and testing (model training is offloaded to Google Colab, not local hardware).
- A device with a camera (mobile or desktop) for testing the image capture feature.

