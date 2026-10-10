# Literature Survey: Deep Learning for Real-World Foliar Disease Detection

## 1. Introduction and Academic Context

Automated plant disease diagnosis via computer vision has advanced rapidly with deep convolutional neural networks (CNNs). However, translating laboratory models into effective decision-support systems for smallholder farmers requires overcoming significant practical barriers: domain shift from controlled to field photography, severe class imbalance, near-duplicate image contamination, overconfident misclassification, and lack of actionable, localized agronomic advice.

This literature survey reviews foundational works, empirical benchmarks, and methodological advancements that informed the architectural and engineering decisions of the **CS26012 Crop Disease Detection Platform**.

---

## 2. Foundational Benchmarks & The Lab-to-Field Domain Shift

### 2.1 Laboratory Benchmarks
- **Mohanty, Hughes, & Salathé (2016)**, *"Using Deep Learning for Image-Based Plant Disease Detection"*, *Frontiers in Plant Science*, 7:1419. [DOI: 10.3389/fpls.2016.01419](https://doi.org/10.3389/fpls.2016.01419)
  - Evaluated AlexNet and GoogLeNet on the **PlantVillage** dataset (~54,306 images across 14 crops and 38 classes). Reported test accuracies reaching **99.35%**.
  - **Identified Limitation**: When evaluated on independent images gathered outside the dataset, accuracy dropped to approximately **31.4%**, demonstrating that CNNs heavily exploit uniform laboratory backgrounds, standardized lighting, and specific camera profiles rather than purely learning biological disease lesions.

### 2.2 Field Generalization & Domain Shift
- **Ferentinos (2018)**, *"Deep Learning Models for Plant Disease Detection and Diagnosis"*, *Computers and Electronics in Agriculture*, 145, pp. 311–318. [DOI: 10.1016/j.compag.2018.01.009](https://doi.org/10.1016/j.compag.2018.01.009)
  - Tested VGG, AlexNet, and GoogLeNet across 87,848 images. Noted that training models on lab images and testing on field photos led to significant accuracy degradation, reinforcing that in-situ field photography is essential for real-world agricultural tools.
- **Barbedo (2018)**, *"Impact of Dataset Size and Variety on the Risks of Overfitting and Unreliability of Deep Learning Models for Plant Pathology"*, *Biosystems Engineering*, 170, pp. 17–27. [DOI: 10.1016/j.biosystemseng.2018.03.006](https://doi.org/10.1016/j.biosystemseng.2018.03.006)
  - Demonstrated that high classification accuracy is often an artifact of dataset redundancy and uniform leaf positioning. Emphasized that image acquisition must capture real field variability, including shadows, soil backgrounds, and complex multi-leaf canopies.

---

## 3. Lightweight CNN Architectures & Transfer Learning

Given the operational goal of low-latency inference on commodity web infrastructure, selecting compute-efficient architectures is paramount:

- **Howard et al. (2018)**, *"MobileNetV2: Inverted Residuals and Linear Bottlenecks"*, *IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, pp. 4510–4520. [arXiv:1801.04381](https://arxiv.org/abs/1801.04381)
  - Introduced inverted residual blocks and depthwise separable convolutions, drastically reducing floating-point operations (FLOPs) and parameter count (3.5M parameters) while maintaining high ImageNet feature extraction capability.
  - **Project Adoption**: MobileNetV2 was chosen as the primary backbone for the CS26012 platform. Its lightweight footprint enables sub-200ms CPU inference on FastAPI backends without requiring dedicated server GPUs.
- **Tan & Le (2019)**, *"EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks"*, *International Conference on Machine Learning (ICML)*, PMLR, 97, pp. 6105–6114.
  - Formulated compound scaling for network depth, width, and resolution. EfficientNet-Lite serves as a secondary candidate architecture within our Colab training pipeline.

---

## 4. Dataset Quality, Duplication & Data Leakage Prevention

A critical issue identified in academic plant disease datasets is data leakage resulting from near-duplicate images across train, validation, and test splits:

- **Birodkar et al. (2019)**, *"Mind the Pad -- CNNs Can Develop Spatial Bias"*, and related studies on agricultural image duplication.
  - Uncurated datasets often contain bursts of photos taken of the same leaf under identical angles, causing artificial inflation of test accuracy by 10–20%.
  - **Project Implementation**: In `notebooks/train_crop_model.ipynb`, we implement a strict 2-tier deduplication pipeline:
    1. **Exact MD5 Hash Matching**: Pruning identical byte-level image copies.
    2. **Perceptual Hashing (`imagehash` library)**: Computing 64-bit difference hashes (`dhash`) to detect and eliminate near-duplicate frames with Hamming distance $\le 2$ before creating stratified 70/15/15 splits.

---

## 5. Confidence Estimation & Selective Classification

In agronomy, false-positive recommendations can lead to unnecessary or incorrect pesticide applications:

- **Guo et al. (2017)**, *"On Calibration of Modern Neural Networks"*, *ICML*, PMLR, 70, pp. 1321–1330.
  - Modern deep CNNs tend to produce uncalibrated, overconfident softmax probabilities even on out-of-distribution or corrupted inputs.
- **Geifman & El-Yaniv (2017)**, *"Selective Classification for Deep Neural Networks"*, *Advances in Neural Information Processing Systems (NeurIPS)*, 30.
  - Formulated the rejection option: allowing a model to abstain when the risk of misclassification exceeds an acceptable threshold.
  - **Project Implementation**: Enforced in `inference.py` and `services/diagnosis_service.py` via a calibrated acceptance threshold ($T = 0.70$). Inputs yielding $\max P(y|x) < 0.70$ are flagged as `low_confidence`, suppressing automated advisory generation and instructing the farmer to retake a clear, well-focused photo.

---

## 6. Actionable Agronomic Advisory & Regional Context

Merely outputting a disease name (e.g. *"Cercospora"*) is insufficient for a farmer without actionable management steps:

- **Indian Council of Agricultural Research (ICAR)** & **State Agricultural Universities (SAUs)** Extension Bulletins:
  - Stress the priority of Integrated Pest Management (IPM), cultural field sanitation (pruning, row spacing, drip irrigation), and biological treatments (neem seed kernel extract, yellow sticky cards) over indiscriminate chemical applications.
  - **Project Implementation**: `services/llm_service.py` couples disease predictions with local ambient weather snapshots (Open-Meteo) and prompts Groq LLM (`openai/gpt-oss-120b`) under strict statutory constraints: the LLM is prohibited from overriding the ML diagnosis and cannot invent proprietary synthetic chemical formulations.

---

## 7. Identified Research Gap & Project Contribution

| Aspect | Typical Academic Research | CS26012 Implementation |
| :--- | :--- | :--- |
| **Data Setting** | Standardized lab images (PlantVillage) | Priority on Indian field datasets (Deccan Plateau, PLDD-UP) |
| **Data Hygiene** | Random splits without deduplication | Perceptual hashing deduplication + stratified splitting |
| **Prediction Policy** | Forced classification on all images | Calibrated 70% confidence rejection gate |
| **Context Integration**| Isolated image prediction | Fusion with real-time GPS agro-weather (Open-Meteo) |
| **Advisory Delivery** | Raw class label output | Trilingual IPM advisory (EN, HI, GU) + ReportLab PDF |
| **Architecture** | Heavy models (ResNet-152, DenseNet) | Lightweight MobileNetV2 optimized for low-latency web inference |
