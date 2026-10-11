"""
backend/seed.py
===============
Seed script for reference / lookup tables.

Populates:
  1. crops      — the 8 supported crops (chili is currently production-ready)
  2. diseases   — disease class labels per crop (chili classes seeded now;
                   other crops to be added as models are trained)
  3. model_versions — registers Chili V1 as the active production model

Run once after the initial migration:
  python seed.py

Running again is safe — uses INSERT ... ON CONFLICT DO NOTHING so
existing rows are not duplicated or overwritten.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Ensure the backend directory is on sys.path when called from project root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from database import AsyncSessionLocal  # noqa: E402


# ===========================================================================
# Seed data
# ===========================================================================

CROPS = [
    {
        "id": 1,
        "name": "chili",
        "display_name": "Chili Pepper",
        "display_name_hi": "मिर्च",
        "display_name_gu": "મરચું",
        "model_key": "chili",
        "is_supported": True,
    },
    {
        "id": 2,
        "name": "potato",
        "display_name": "Potato",
        "display_name_hi": "आलू",
        "display_name_gu": "બટેટા",
        "model_key": "potato",
        "is_supported": True,
    },
    {
        "id": 3,
        "name": "groundnut",
        "display_name": "Groundnut",
        "display_name_hi": "मूंगफली",
        "display_name_gu": "મગફળી",
        "model_key": "groundnut",
        "is_supported": True,
    },
    {
        "id": 4,
        "name": "tomato",
        "display_name": "Tomato",
        "display_name_hi": "टमाटर",
        "display_name_gu": "ટામેટાં",
        "model_key": "tomato",
        "is_supported": False,
    },
    {
        "id": 5,
        "name": "rice",
        "display_name": "Rice",
        "display_name_hi": "चावल",
        "display_name_gu": "ચોખા",
        "model_key": "rice",
        "is_supported": False,
    },
    {
        "id": 6,
        "name": "wheat",
        "display_name": "Wheat",
        "display_name_hi": "गेहूं",
        "display_name_gu": "ઘઉં",
        "model_key": "wheat",
        "is_supported": False,
    },
    {
        "id": 7,
        "name": "banana",
        "display_name": "Banana",
        "display_name_hi": "केला",
        "display_name_gu": "કેળ",
        "model_key": "banana",
        "is_supported": False,
    },
    {
        "id": 8,
        "name": "soybean",
        "display_name": "Soybean",
        "display_name_hi": "सोयाबीन",
        "display_name_gu": "સોયાબીન",
        "model_key": "soybean",
        "is_supported": False,
    },
]

# Disease classes derived from the trained MobileNetV2 label dictionaries.
DISEASES = [
    # ---------------- Chili (crop_id: 1) ----------------
    {
        "crop_id": 1,
        "label": "Bacterial Spot",
        "display_name": "Chili Bacterial Spot",
        "description": "Bacterial leaf spots with water-soaked margins and yellow halos.",
        "severity": "high",
        "is_healthy": False,
    },
    {
        "crop_id": 1,
        "label": "Cercospora Leaf Spot",
        "display_name": "Cercospora Leaf Spot",
        "description": "Fungal leaf spots with distinct concentric rings.",
        "severity": "medium",
        "is_healthy": False,
    },
    {
        "crop_id": 1,
        "label": "Curl Virus",
        "display_name": "Chili Leaf Curl Virus",
        "description": "Upward curling and puckering of young leaves caused by viral infection.",
        "severity": "high",
        "is_healthy": False,
    },
    {
        "crop_id": 1,
        "label": "Healthy Leaf",
        "display_name": "Healthy Chili Leaf",
        "description": "Normal vigorous green chili foliage without visible disease symptoms.",
        "severity": "none",
        "is_healthy": True,
    },
    {
        "crop_id": 1,
        "label": "Nutrition Deficiency",
        "display_name": "Chili Nutrient Deficiency",
        "description": "Interveinal chlorosis or generalized yellowing due to nutrient imbalance.",
        "severity": "low",
        "is_healthy": False,
    },
    {
        "crop_id": 1,
        "label": "White spot",
        "display_name": "Chili Whitefly / White Spot",
        "description": "White powdery wax and sap-sucking nymphs on the underside of chili leaves.",
        "severity": "medium",
        "is_healthy": False,
    },

    # ---------------- Potato (crop_id: 2) ----------------
    {
        "crop_id": 2,
        "label": "Early Blight",
        "display_name": "Potato Early Blight",
        "description": "Early blight caused by Alternaria solani produces brown-to-black spots with concentric rings (target board pattern) on older leaves.",
        "severity": "medium",
        "is_healthy": False,
    },
    {
        "crop_id": 2,
        "label": "EB",
        "display_name": "Potato Early Blight",
        "description": "Early blight caused by Alternaria solani produces brown-to-black spots with concentric rings (target board pattern) on older leaves.",
        "severity": "medium",
        "is_healthy": False,
    },
    {
        "crop_id": 2,
        "label": "Healthy",
        "display_name": "Healthy Potato Leaf",
        "description": "Normal vigorous green potato foliage with no visible foliar lesions, spots, or blight.",
        "severity": "none",
        "is_healthy": True,
    },
    {
        "crop_id": 2,
        "label": "Late Blight",
        "display_name": "Potato Late Blight",
        "description": "Late blight caused by Phytophthora infestans causes water-soaked, dark lesions expanding rapidly under cool, wet conditions.",
        "severity": "high",
        "is_healthy": False,
    },
    {
        "crop_id": 2,
        "label": "LB",
        "display_name": "Potato Late Blight",
        "description": "Late blight caused by Phytophthora infestans causes water-soaked, dark lesions expanding rapidly under cool, wet conditions.",
        "severity": "high",
        "is_healthy": False,
    },

    # ---------------- Groundnut (crop_id: 3) ----------------
    {
        "crop_id": 3,
        "label": "Early Leaf Spot",
        "display_name": "Groundnut Early Leaf Spot",
        "description": "Early leaf spot caused by Passalora arachidicola causes circular brown spots with prominent yellow halos on leaflet surfaces.",
        "severity": "medium",
        "is_healthy": False,
    },
    {
        "crop_id": 3,
        "label": "groundnut_early_leaf_spot",
        "display_name": "Groundnut Early Leaf Spot",
        "description": "Early leaf spot caused by Passalora arachidicola causes circular brown spots with prominent yellow halos on leaflet surfaces.",
        "severity": "medium",
        "is_healthy": False,
    },
    {
        "crop_id": 3,
        "label": "Early Rust",
        "display_name": "Groundnut Early Rust",
        "description": "Early rust infection phase on groundnut characterized by initial orange-brown pustules on the lower epidermis.",
        "severity": "medium",
        "is_healthy": False,
    },
    {
        "crop_id": 3,
        "label": "groundnut_early_rust",
        "display_name": "Groundnut Early Rust",
        "description": "Early rust infection phase on groundnut characterized by initial orange-brown pustules on the lower epidermis.",
        "severity": "medium",
        "is_healthy": False,
    },
    {
        "crop_id": 3,
        "label": "Healthy Leaf",
        "display_name": "Healthy Groundnut Leaf",
        "description": "Vigorous green groundnut leaflets with uniform color and no visible fungal pustules or lesions.",
        "severity": "none",
        "is_healthy": True,
    },
    {
        "crop_id": 3,
        "label": "groundnut_healthy",
        "display_name": "Healthy Groundnut Leaf",
        "description": "Vigorous green groundnut leaflets with uniform color and no visible fungal pustules or lesions.",
        "severity": "none",
        "is_healthy": True,
    },
    {
        "crop_id": 3,
        "label": "Late Leaf Spot",
        "display_name": "Groundnut Late Leaf Spot",
        "description": "Late leaf spot caused by Nothopassalora personata produces darker brown-to-black circular spots without prominent halos.",
        "severity": "high",
        "is_healthy": False,
    },
    {
        "crop_id": 3,
        "label": "groundnut_late_leaf_spot",
        "display_name": "Groundnut Late Leaf Spot",
        "description": "Late leaf spot caused by Nothopassalora personata produces darker brown-to-black circular spots without prominent halos.",
        "severity": "high",
        "is_healthy": False,
    },
    {
        "crop_id": 3,
        "label": "Nutrition Deficiency",
        "display_name": "Groundnut Nutrient Deficiency",
        "description": "Nutrient deficiency symptoms including chlorosis, leaf paling, or marginal yellowing across foliage.",
        "severity": "low",
        "is_healthy": False,
    },
    {
        "crop_id": 3,
        "label": "groundnut_nutrition_deficiency",
        "display_name": "Groundnut Nutrient Deficiency",
        "description": "Nutrient deficiency symptoms including chlorosis, leaf paling, or marginal yellowing across foliage.",
        "severity": "low",
        "is_healthy": False,
    },
    {
        "crop_id": 3,
        "label": "Rust",
        "display_name": "Groundnut Rust",
        "description": "Foliar rust caused by Puccinia arachidis producing numerous reddish-brown pustules leading to premature defoliation.",
        "severity": "high",
        "is_healthy": False,
    },
    {
        "crop_id": 3,
        "label": "groundnut_rust",
        "display_name": "Groundnut Rust",
        "description": "Foliar rust caused by Puccinia arachidis producing numerous reddish-brown pustules leading to premature defoliation.",
        "severity": "high",
        "is_healthy": False,
    },
]

# Model versions registry — Chili, Potato, and Groundnut production models
MODEL_VERSIONS = [
    {
        "crop_id": 1,
        "version_tag": "v1.0.0",
        "architecture": "MobileNetV2",
        "artifact_path": "models/chili_mobilenetv2.keras",
        "num_classes": 6,
        "test_accuracy": 0.8785,
        "notes": (
            "Chili V1 — production baseline. "
            "MobileNetV2 transfer learning on field-collected chili dataset. "
            "6 classes: Bacterial Spot, Cercospora Leaf Spot, Curl Virus, Healthy Leaf, Nutrition Deficiency, White spot. "
            "Test accuracy: 87.85%."
        ),
        "is_active": True,
    },
    {
        "crop_id": 2,
        "version_tag": "v1.0.0",
        "architecture": "MobileNetV2",
        "artifact_path": "models/potato_mobilenetv2.keras",
        "num_classes": 3,
        "test_accuracy": 0.8011,
        "notes": (
            "Potato V1 MobileNetV2 transfer learning model. "
            "3 classes: Early Blight (EB), Healthy, Late Blight (LB). "
            "Test accuracy: 80.11% on held-out test split."
        ),
        "is_active": True,
    },
    {
        "crop_id": 3,
        "version_tag": "v1.0.0",
        "architecture": "MobileNetV2",
        "artifact_path": "models/groundnut_mobilenetv2_model_2.keras",
        "num_classes": 6,
        "test_accuracy": 0.9627,
        "notes": (
            "Groundnut V1 (model_2) MobileNetV2 transfer learning model. "
            "6 classes: early leaf spot, early rust, healthy, late leaf spot, nutrition deficiency, rust. "
            "Test accuracy: 96.27% on held-out test split."
        ),
        "is_active": True,
    },
]


# ===========================================================================
# Insertion helpers
# ===========================================================================

async def seed_crops(session: AsyncSession) -> None:
    print("Seeding crops...")
    for crop in CROPS:
        await session.execute(
            text("""
                INSERT INTO crops
                    (id, name, display_name, display_name_hi, display_name_gu,
                     model_key, is_supported, created_at)
                VALUES
                    (:id, :name, :display_name, :display_name_hi, :display_name_gu,
                     :model_key, :is_supported, NOW())
                ON CONFLICT (name) DO UPDATE SET
                    is_supported = EXCLUDED.is_supported,
                    display_name = EXCLUDED.display_name,
                    display_name_hi = EXCLUDED.display_name_hi,
                    display_name_gu = EXCLUDED.display_name_gu,
                    model_key = EXCLUDED.model_key
            """),
            crop,
        )
    print(f"  [OK] {len(CROPS)} crop rows processed.")


async def seed_diseases(session: AsyncSession) -> None:
    print("Seeding diseases...")
    for disease in DISEASES:
        await session.execute(
            text("""
                INSERT INTO diseases
                    (crop_id, label, display_name, description, severity,
                     is_healthy, created_at)
                VALUES
                    (:crop_id, :label, :display_name, :description, :severity,
                     :is_healthy, NOW())
                ON CONFLICT ON CONSTRAINT uq_disease_crop_label DO NOTHING
            """),
            disease,
        )
    print(f"  [OK] {len(DISEASES)} disease rows processed (skipped if already exist).")


async def seed_model_versions(session: AsyncSession) -> None:
    print("Seeding model versions...")
    for mv in MODEL_VERSIONS:
        await session.execute(
            text("""
                INSERT INTO model_versions
                    (crop_id, version_tag, architecture, artifact_path,
                     num_classes, test_accuracy, notes, is_active, created_at)
                VALUES
                    (:crop_id, :version_tag, :architecture, :artifact_path,
                     :num_classes, :test_accuracy, :notes, :is_active, NOW())
                ON CONFLICT ON CONSTRAINT uq_model_crop_version DO NOTHING
            """),
            mv,
        )
    print(f"  [OK] {len(MODEL_VERSIONS)} model version rows processed (skipped if already exist).")


# ===========================================================================
# Main
# ===========================================================================

async def main() -> None:
    print("=" * 55)
    print("  Crop Disease Detection -- Database Seed Script")
    print("=" * 55)
    async with AsyncSessionLocal() as session:
        try:
            await seed_crops(session)
            await seed_diseases(session)
            await seed_model_versions(session)
            await session.commit()
            print("\n[DONE] Seed complete - all reference data inserted successfully.")
        except Exception as exc:
            await session.rollback()
            print(f"\n[ERROR] Seed failed: {exc}")
            raise
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
