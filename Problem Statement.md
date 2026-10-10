# Problem Statement: Field-Condition Crop Disease Detection & Localized Agronomic Advisory

**Project Title:** CS26012 — Crop Disease Detection & Agricultural Advisory Platform  
**Team ID:** CS26012  
**Author:** Jugal Kshatriya (24CS042)  
**Institution:** CSPIT, CHARUSAT  

---

## 1. Background & Practical Problem

Crop diseases account for an estimated **20% to 40% of agricultural yield loss worldwide**, presenting a severe threat to smallholder farmer livelihoods and regional food security in India. 

In day-to-day farming operations, early detection of foliar pathogens is critical to prevent field-wide devastation. However, smallholder and marginal farmers face several critical bottlenecks:
1. **Limited Access to Agronomists**: With extension worker-to-farmer ratios often exceeding 1:1,000, physical field visits by plant pathologists are infrequent.
2. **Visual Ambiguity**: Early-stage foliar symptoms (e.g. distinguishing nutritional deficiencies from early viral or fungal spotting) are difficult to diagnose accurately by unassisted visual inspection.
3. **Delayed or Inappropriate Chemical Interventions**: When diagnosis is uncertain, farmers frequently resort to broad-spectrum chemical sprays, resulting in unnecessary financial costs, pesticide resistance, and environmental damage.

---

## 2. The Core Academic & Engineering Gap: Lab vs. Field Domain Shift

Computer vision researchers have achieved high reported accuracy (>98%) on laboratory benchmarks such as **PlantVillage**. However, these models fail in practice due to the **lab-to-field domain shift**:
- **Controlled Lab Conditions**: Perfectly lit, detached leaves photographed flat against uniform white or grey backgrounds.
- **Real Field Conditions**: Varied sun glare, shadows, cluttered backgrounds (soil, weeds, overlapping foliage), camera motion blur, and diverse smartphone lens qualities.

When lab-trained CNNs encounter real-world farm photographs, classification accuracy drops dramatically (often below 40%), eroding farmer trust and rendering theoretical lab models unusable in production.

---

## 3. Project Aim & Specific Objectives

### Project Aim
To design, implement, and validate an end-to-end, trilingual web platform that provides **accurate, field-resilient leaf disease diagnosis** and **statutory, localized agronomic advice** using convolutional neural networks trained on genuine Indian field datasets.

### Specific Objectives
1. **Curate Field-First Datasets**: Assemble and clean in-situ leaf image datasets for regionally significant Indian crops, applying perceptual hashing (`imagehash`) to prune burst-shot near-duplicates.
2. **Deploy Compute-Efficient Deep Learning**: Train and optimize a lightweight **MobileNetV2** backbone for fast foliar classification with sub-250ms CPU inference latency.
3. **Enforce Calibrated Confidence Gating**: Implement a 70% confidence threshold that abstains from forced guesses on out-of-distribution or ambiguous inputs, protecting crops from erroneous treatments.
4. **Integrate Real-Time Meteorological Context**: Connect diagnosis with localized agro-weather (temperature, humidity, precipitation, wind speed via Open-Meteo) based on farmer GPS coordinates.
5. **Synthesize Actionable IPM Guidance**: Generate structured cultural and biological treatment advisories using Groq LLM with a 3-key auto-failover mechanism, adhering strictly to non-hallucinatory chemical guidelines.
6. **Deliver Full Trilingual Accessibility**: Ensure complete localized workflows across English, Hindi (हिन्दी), and Gujarati (ગુજરાતી), including downloadable PDF advisory reports.

---

## 4. Project Scope & Supported Crops

The project focuses on priority crops of national and regional agricultural significance in India:

| Crop | Operational Status | Model Status | Dataset Source |
| :--- | :--- | :--- | :--- |
| **Chili Pepper** (*Capsicum annuum*) | **Active in Production** | MobileNetV2 (12 classes, 94.2% test acc) | Deccan Plateau, Krishna River Basin (Mendeley) |
| **Potato** (*Solanum tuberosum*) | Architecture & Pipeline Ready | Scheduled for retraining | PLDD-UP, Uttar Pradesh |
| **Groundnut** (*Arachis hypogaea*) | Architecture & Pipeline Ready | Scheduled for retraining | Multi-Crop Disease Dataset, VIT Chennai |
| **Rice** (*Oryza sativa*) | Cataloged | Scheduled for training | Kaggle Rice Leaf Disease Dataset |
| **Tomato** (*Solanum lycopersicum*) | Cataloged | Lab baseline comparison | PlantVillage baseline |
| **Banana** (*Musa acuminata*) | Cataloged | Scheduled for training | Multi-Crop Disease Dataset, Mendeley |
| **Soybean** (*Glycine max*) | Cataloged | Scheduled for training | MH-SoyaHealthVision (leaf subset) |

---

## 5. Explicit Boundaries & What This Project Does Not Attempt

1. **Not a Plant Doctor Replacement**: The application is an automated **decision-support tool** for preliminary field screening. It does not replace certified agronomists or Krishi Vigyan Kendra (KVK) laboratory assays.
2. **No Hallucinated Chemical Prescriptions**: The platform does not prescribe synthetic commercial chemical brands or proprietary dosages. All advisory content prioritizes cultural sanitation, pruning, and safe biological alternatives (e.g. neem cake, yellow sticky cards).
3. **Not a Multi-Million Image Commercial Enterprise**: Unlike commercial offerings (e.g. Plantix), this project does not claim universal coverage of hundreds of crops. It is an academically rigorous, transparent, end-to-end pipeline deliberately focused on high-quality Indian field crops.

---

## 6. Evaluation Methodology

1. **In-Distribution Evaluation**: Rigorous stratified 70/15/15 train/validation/test hold-out metrics (accuracy, precision, recall, F1-score, and confusion matrices).
2. **Selective Classification Reliability**: Verifying that false-positive rates drop significantly when the 70% confidence rejection policy is enforced.
3. **Integration Robustness**: End-to-end automated test suites verifying PostgreSQL persistence, multi-tenant isolation, Groq key rotation under HTTP 429 rate limits, and ReportLab PDF document compilation.
