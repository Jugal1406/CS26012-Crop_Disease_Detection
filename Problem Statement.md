# Problem Statement

## Background

Crop diseases are responsible for an estimated 20–40% of global agricultural yield loss annually. In India, the majority of farmers are smallholders with limited access to timely agronomic expertise, and diagnosis often depends on the farmer's own experience or infrequent visits from agricultural extension officers. While experienced farmers and gardeners can often recognize diseases they have seen before, early-stage symptoms, visually similar diseases, and unfamiliar or region-shifting pathogens remain difficult to diagnose confidently — and even a correct diagnosis is frequently not paired with locally relevant, affordable treatment guidance.

## The Core Gap This Project Addresses

Most published crop-disease classifiers, and many existing mobile/web tools, are trained and benchmarked almost entirely on **lab-condition datasets** (most commonly PlantVillage) — images captured against plain, controlled backgrounds under consistent lighting. This does not reflect how a real farmer or gardener photographs a leaf: cluttered backgrounds, natural and inconsistent lighting, varied camera quality, and multiple leaves in frame. Models trained purely on lab-condition images are known to generalize poorly to this real-world "field" setting — a well-documented domain-shift problem in agricultural computer vision.

This project addresses that gap directly by building its primary system on **real, on-field images sourced specifically from Indian agricultural conditions**, rather than defaulting to lab-condition data for convenience.

## Scope

The project covers 8 crops selected for their pan-India relevance and the availability of genuine field-condition Indian datasets:

Groundnut, Banana, Tomato, Potato, Rice, Wheat, Chili, and Soyabean.

Tomato is a deliberate, explicitly stated exception: no sufficiently large, well-documented on-field Indian tomato dataset was found during data collection, so PlantVillage (lab-condition) data is used for this crop. Rice includes both an on-field and a separately-kept lab-condition source.

## Secondary Case Study: Lab vs. Field Accuracy Gap

Using the lab-condition data available for Tomato (PlantVillage) and the paired lab/field data available for Rice, the project includes a dedicated evaluation comparing model accuracy when trained on lab-condition images versus field-condition images, and tested against the other condition. This is presented as a supporting case study demonstrating the real-world impact of the domain-shift problem — not as the project's primary deliverable, but as evidence for why the field-first approach used for the other 6 crops matters.

## Target Users

- Smallholder and marginal farmers
- Home and terrace/kitchen garden enthusiasts
- Agricultural students and extension workers (secondary reference use)

## What This Project Does Not Attempt

This project does not aim to outperform commercial-scale tools such as Plantix, which are built on over 100 million crowd-contributed images and years of production refinement. Instead, it aims to demonstrate a transparent, end-to-end, field-condition-first pipeline for a deliberately chosen set of pan-India crops — genuine methodological rigor and honest evaluation, rather than commercial-scale coverage.

