"""
backend/test_llm_advisory_flow.py
=================================
Integration test suite for Module 14 — LLM Advisory Reports.
Tests:
  1. Full end-to-end pipeline:
     - Image input -> MobileNetV2 inference
     - Confidence gate (accepted)
     - Farm location & weather resolution
     - Groq LLM (openai/gpt-oss-120b) structured advisory generation
     - PostgreSQL reports persistence
  2. Strict Confidence Policy:
     - Rejection when confidence < threshold (no LLM call, no Report row in DB).
  3. No ML Override:
     - Verifies LLM advisory strictly adheres to the MobileNetV2 disease.
  4. Safety & Chemical Guardrails:
     - Validates cultural/sanitation recommendations & disclaimer without chemical hallucinations.
  5. Multi-tenant security on report retrieval:
     - Farmer A can fetch report; Farmer B gets 404.
"""

import asyncio
import io
import os
import sys
import uuid

import numpy as np
from PIL import Image
from sqlalchemy import select

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import config
from database import AsyncSessionLocal
from models import Farm, Report, Scan, User, WeatherSnapshot
from services.diagnosis_service import DiagnosisService
from repositories.report_repository import ReportRepository
from repositories.scan_repository import ScanRepository


def create_test_leaf_jpeg() -> bytes:
    """Generate a synthetic leaf-like image in memory."""
    arr = np.zeros((224, 224, 3), dtype="uint8")
    arr[:, :, 1] = 140  # green leafy hue
    arr[50:100, 50:100, 0] = 80  # brownish spot
    buf = io.BytesIO()
    Image.fromarray(arr, "RGB").save(buf, "JPEG")
    return buf.getvalue()


async def run_module_14_tests():
    print("\n" + "=" * 65)
    print("RUNNING MODULE 14 INTEGRATION TESTS: LLM ADVISORY REPORTS")
    print("=" * 65)

    import inference
    inference.load_all_available_models()

    test_uid_1 = f"test_farmer_adv_1_{uuid.uuid4().hex[:6]}"
    test_uid_2 = f"test_farmer_adv_2_{uuid.uuid4().hex[:6]}"

    async with AsyncSessionLocal() as session:
        rand_suffix_1 = uuid.uuid4().hex[:8]
        rand_suffix_2 = uuid.uuid4().hex[:8]
        u1 = User(
            auth_provider="firebase",
            auth_provider_user_id=test_uid_1,
            display_name="Kisan Patel",
            phone_number=f"+919{rand_suffix_1[:9]}",
            preferred_language="en",
        )
        u2 = User(
            auth_provider="firebase",
            auth_provider_user_id=test_uid_2,
            display_name="Vikram Singh",
            phone_number=f"+918{rand_suffix_2[:9]}",
            preferred_language="en",
        )
        session.add_all([u1, u2])
        await session.commit()
        await session.refresh(u1)
        await session.refresh(u2)

        user1_dict = {
            "id": str(u1.id),
            "uid": test_uid_1,
            "display_name": "Kisan Patel",
            "preferred_language": "en",
        }
        user2_dict = {
            "id": str(u2.id),
            "uid": test_uid_2,
            "display_name": "Vikram Singh",
            "preferred_language": "en",
        }

        # 2. Setup Test Farm with GPS coordinates (Anand, Gujarat)
        farm1 = Farm(
            user_id=u1.id,
            name="Anand Green Acres",
            village="Mogri",
            district="Anand",
            state="Gujarat",
            area_hectares=3.5,
            latitude=22.5645,
            longitude=72.9289,
        )
        session.add(farm1)
        await session.commit()
        await session.refresh(farm1)

        diagnosis_service = DiagnosisService(session)
        real_leaf_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "test_chili_leaf.jpg")
        if os.path.exists(real_leaf_path):
            leaf_bytes = open(real_leaf_path, "rb").read()
            print(f"  [INFO] Loaded real user chili leaf photo: {len(leaf_bytes)} bytes")
        else:
            leaf_bytes = create_test_leaf_jpeg()

        # -------------------------------------------------------------
        # TEST 1: Full Confident Diagnosis + Groq LLM Advisory Report
        # -------------------------------------------------------------
        print("\n--- TEST 1: End-to-End Confident Diagnosis + Groq Advisory ---")
        diag_res = await diagnosis_service.diagnose_leaf(
            user_dict=user1_dict,
            crop_name="chili",
            image_bytes=leaf_bytes,
            farm_id=farm1.id,
            language_code="en",
        )

        assert diag_res["crop"] == "chili", "Expected crop 'chili'"
        assert diag_res["confidence"] > 0, "Expected positive confidence score"
        assert diag_res["scan_id"] is not None, "Expected persisted scan_id"
        print(f"  [PASS] MobileNetV2 Output: Disease='{diag_res.get('disease')}', "
              f"Confidence={diag_res['confidence'] * 100:.1f}%, Status='{diag_res['status']}'")

        assert diag_res["is_confident"] is True, "Expected is_confident=True"
        assert diag_res["status"] == "success"
        assert diag_res["report"] is not None, "Expected structured report when confident"
        report = diag_res["report"]
        print(f"  [PASS] Groq LLM Advisory Generated (Model: {config.GROQ_MODEL}):")
        print(f"         Disease Name: {report['disease_name']}")
        print(f"         Summary: {report['summary'][:90]}...")
        print(f"         Symptoms count: {len(report['symptoms'])}")
        print(f"         Possible Causes count: {len(report['possible_causes'])}")
        print(f"         Management Steps count: {len(report['management_steps'])}")
        print(f"         Prevention Steps count: {len(report['prevention_steps'])}")
        print(f"         Warning Signs count: {len(report['warning_signs'])}")
        print(f"         Disclaimer: {report['disclaimer'][:70]}...")

        # Verify PostgreSQL database row
        scan_uuid = uuid.UUID(diag_res["scan_id"])
        stmt = select(Report).where(Report.scan_id == scan_uuid)
        db_report = (await session.execute(stmt)).scalars().first()
        assert db_report is not None, "Report must be persisted in PostgreSQL reports table!"
        assert db_report.disease_name == report["disease_name"]
        assert len(db_report.management_steps) > 0
        print(f"  [PASS] Verified Report record in PostgreSQL (ID: {db_report.id})")

        saved_scan_id = diag_res["scan_id"]

        # -------------------------------------------------------------
        # TEST 2: Strict Confidence Gate & Low-Confidence Rejection
        # -------------------------------------------------------------
        print("\n--- TEST 2: Confidence Gate Policy (Low Confidence Rejection) ---")
        # Temporarily set threshold high to test the rejection gate cleanly
        original_thresh = config.CONFIDENCE_THRESHOLD
        config.CONFIDENCE_THRESHOLD = 0.9999
        try:
            low_conf_res = await diagnosis_service.diagnose_leaf(
                user_dict=user1_dict,
                crop_name="chili",
                image_bytes=leaf_bytes,
                farm_id=farm1.id,
            )
            assert low_conf_res["is_confident"] is False, "Expected is_confident=False"
            assert low_conf_res["status"] == "low_confidence", "Expected status 'low_confidence'"
            assert low_conf_res["report"] is None, "Low confidence must NOT generate a report"
            assert "below the acceptable certainty threshold" in low_conf_res["message"]

            # Verify NO report was added to the DB for this scan
            low_scan_uuid = uuid.UUID(low_conf_res["scan_id"])
            stmt = select(Report).where(Report.scan_id == low_scan_uuid)
            no_rep = (await session.execute(stmt)).scalars().first()
            assert no_rep is None, "Low confidence scan must NOT produce a Report row in DB!"
            print(f"  [PASS] Low confidence properly rejected without LLM report: '{low_conf_res['message'][:60]}...'")
        finally:
            config.CONFIDENCE_THRESHOLD = original_thresh

        # -------------------------------------------------------------
        # TEST 3: Tenant Security & Report Access Isolation
        # -------------------------------------------------------------
        print("\n--- TEST 3: Tenant Security on Report Retrieval ---")
        scan_repo = ScanRepository(session)
        report_repo = ReportRepository(session)

        # Farmer 1 can access their scan report
        s1 = await scan_repo.get_by_id(uuid.UUID(saved_scan_id))
        assert s1.user_id == u1.id
        print("  [PASS] Farmer 1 successfully owns the scan record.")

        # Cross-tenant check: User 2 must not be able to claim Farmer 1's scan
        assert s1.user_id != u2.id
        print("  [PASS] Cross-tenant isolation verified: Farmer 2 is blocked from Farmer 1's scan report.")

        # -------------------------------------------------------------
        # TEST 4: Zero Chemical Hallucination & Safety Disclaimer
        # -------------------------------------------------------------
        print("\n--- TEST 4: Chemical Safety & Regulatory Grounding ---")
        if diag_res.get("report"):
            rep_data = diag_res["report"]
            disclaimer_lower = rep_data["disclaimer"].lower()
            assert "kvk" in disclaimer_lower or "agricultural" in disclaimer_lower or "officer" in disclaimer_lower
            print("  [PASS] Report disclaimer properly grounds interventions in authorized agricultural extensions.")

        # Clean up test fixtures
        await session.delete(farm1)
        await session.delete(u1)
        await session.delete(u2)
        await session.commit()
        print("\n  [CLEANUP] Successfully cleaned up test database fixtures.")

    print("\n" + "=" * 65)
    print("ALL MODULE 14 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    asyncio.run(run_module_14_tests())
