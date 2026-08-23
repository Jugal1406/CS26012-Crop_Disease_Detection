# Literature Survey

## 1. Foundational Datasets and Benchmarks

**PlantVillage (Hughes & Salathé, Penn State University)** — the dominant public benchmark for crop disease classification, containing approximately 54,000 lab-condition leaf images across 14 crop species and 38 disease/healthy classes. Most published CNN-based classifiers report 95%+ accuracy on this dataset. However, its images are captured under controlled conditions (plain background, consistent lighting), which do not represent real field photography.

**Mohanty, Hughes & Salathé (2016), "Using Deep Learning for Image-Based Plant Disease Detection"** — one of the earliest large-scale demonstrations of CNN-based plant disease classification using PlantVillage, establishing the transfer-learning approach commonly used since.

## 2. The Lab-to-Field Domain Shift Problem

A well-documented limitation in agricultural computer vision literature: models trained purely on lab-condition datasets like PlantVillage show a measurable accuracy drop when evaluated on real field-condition images (cluttered backgrounds, variable lighting, multiple leaves in frame, phone-camera quality). This domain-shift problem motivates the increasing number of India-specific, field-collected datasets referenced below, and is the empirical basis for this project's decision to prioritize field-condition data.

## 3. India-Specific Field-Condition Datasets Used in This Project

- **Multi-Crop Disease Dataset (Mendeley, VIT Chennai)** — field-collected images across Banana, Chilli, Radish, Groundnut, and Cauliflower from Tamil Nadu, India, with documented collection methodology (specific districts, date range, annotation via Roboflow).
- **PLDD-UP: Potato Leaf Disease Dataset (Mendeley)** — field-condition potato leaf images collected from Uttar Pradesh, India.
- **Rice Leaf Disease Image Dataset (Kaggle)** — field-condition rice disease images, supplemented with a separate healthy-class source containing both lab and field images.
- **Chili Leaf Disease Dataset, Krishna River Basin, Deccan Plateau (Mendeley)** — regionally documented field-condition chili disease images.
- **MH-SoyaHealthVision (Mendeley)** — Indian UAV and leaf-image dataset for soybean crop health; only the standard leaf-image subset is used in this project (UAV imagery excluded).

## 4. Architecture Choices

**MobileNetV2 (Howard et al., 2018)** and **EfficientNet-Lite** are used as candidate backbone architectures via transfer learning. Both are designed for a strong accuracy-to-compute tradeoff, originally intended for mobile/embedded deployment, making them well suited to a resource-constrained student project trained on free-tier GPU compute (Google Colab) and eventually served via a lightweight backend.

Transfer learning (reusing ImageNet-pretrained convolutional layers and retraining only a new classification head, with optional fine-tuning of later layers) is used instead of training from scratch, given the comparatively limited size of several disease classes in the collected datasets (as low as 50–150 images for some classes) relative to what training a CNN from scratch would typically require.

## 5. Existing Commercial Tools and Positioning

**Plantix** is the most prominent existing commercial tool in this space, drawing on a database of over 100 million farmer-contributed field images across 69 crops and 950+ diseases/pests/deficiencies, with claimed 90%+ accuracy on real field images and support for 19 languages. This project does not attempt to match Plantix's scale or accuracy; it is positioned instead as an academically rigorous, transparent, and regionally-grounded pipeline — a deliberately narrower, fully explainable system built and understood end-to-end by the author, rather than a commercial-scale competitor.

## 6. Identified Gap This Project Addresses

Despite the domain-shift problem being well documented in the literature, a large share of student and open-source crop-disease projects continue to train and evaluate exclusively on PlantVillage due to its size and convenience. This project's contribution is a deliberately field-first data strategy across the majority of its crop scope, sourced specifically from Indian agricultural contexts, combined with an explicit lab-vs-field case study (using Tomato and Rice) to empirically demonstrate the gap rather than merely citing it.

