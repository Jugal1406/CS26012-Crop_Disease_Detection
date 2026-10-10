"""
backend/test_multilingual_flow.py
=================================
Automated verification test suite for Module 15: Multilingual Support.

Tests:
  1. English, Hindi, and Gujarati report retrieval & generation with authentic chili leaf image.
  2. Separate language-specific Report records for the same scan in PostgreSQL.
  3. Cached responses do not unnecessarily invoke Groq again.
  4. Tenant security: unauthorized farmers cannot access another user's reports.
  5. Language preference persistence in PostgreSQL user profile.
  6. Confidence gate policy: low-confidence scans never receive normal advisory reports.
  7. Resilient fallback behavior in Hindi, Gujarati, and English when Groq is unavailable.
"""

import asyncio
from datetime import datetime, timezone
import os
import sys
import uuid

# Windows CP1252 stdout encoding safety
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from fastapi import HTTPException
from sqlalchemy import select, text
from database import AsyncSessionLocal, engine
from models import Crop, Disease, Farm, ModelVersion, Prediction, Report, Scan, User
from services.auth_service import AuthService
from services.diagnosis_service import DiagnosisService
from services.llm_service import LLMService

REAL_CHILI_IMAGE_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "test_chili_leaf.jpg")

farmer_1_id = uuid.uuid4()
farmer_2_id = uuid.uuid4()
farm_1_id = uuid.uuid4()

farmer_1_dict = {
    "id": str(farmer_1_id),
    "auth_provider": "firebase",
    "auth_provider_user_id": f"test_fb_ml_1_{farmer_1_id.hex[:8]}",
    "email": f"farmer1_{farmer_1_id.hex[:6]}@example.com",
    "display_name": "Ramesh Patel",
    "preferred_language": "en",
    "is_active": True,
}

farmer_2_dict = {
    "id": str(farmer_2_id),
    "auth_provider": "firebase",
    "auth_provider_user_id": f"test_fb_ml_2_{farmer_2_id.hex[:8]}",
    "email": f"farmer2_{farmer_2_id.hex[:6]}@example.com",
    "display_name": "Suresh Shah",
    "preferred_language": "en",
    "is_active": True,
}


async def setup_test_fixtures():
    async with AsyncSessionLocal() as session:
        # 1. Clean previous test artifacts
        await session.execute(
            text("DELETE FROM users WHERE email LIKE 'farmer%@example.com'")
        )

        # 2. Insert test farmers
        u1 = User(
            id=farmer_1_id,
            auth_provider=farmer_1_dict["auth_provider"],
            auth_provider_user_id=farmer_1_dict["auth_provider_user_id"],
            display_name=farmer_1_dict["display_name"],
            email=farmer_1_dict["email"],
            preferred_language=farmer_1_dict["preferred_language"],
            is_active=True,
        )
        u2 = User(
            id=farmer_2_id,
            auth_provider=farmer_2_dict["auth_provider"],
            auth_provider_user_id=farmer_2_dict["auth_provider_user_id"],
            display_name=farmer_2_dict["display_name"],
            email=farmer_2_dict["email"],
            preferred_language=farmer_2_dict["preferred_language"],
            is_active=True,
        )
        session.add_all([u1, u2])

        # 3. Insert test farm
        f1 = Farm(
            id=farm_1_id,
            user_id=farmer_1_id,
            name="Anand Organic Chili Plot",
            village="Samarkha",
            district="Anand",
            state="Gujarat",
            area_hectares=2.5,
            latitude=22.5645,
            longitude=72.9289,
            is_active=True,
        )
        session.add(f1)
        await session.commit()


async def cleanup_test_fixtures():
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(f"DELETE FROM users WHERE id IN ('{farmer_1_id}', '{farmer_2_id}')")
        )
        await session.commit()


async def run_tests():
    print("=================================================================")
    print("RUNNING MODULE 15 INTEGRATION TESTS: MULTILINGUAL SUPPORT")
    print("=================================================================")

    import inference
    inference.load_all_available_models()

    with open(REAL_CHILI_IMAGE_PATH, "rb") as f:
        chili_image_bytes = f.read()
    print(f"  [INFO] Loaded real chili leaf photo: {len(chili_image_bytes)} bytes")

    await setup_test_fixtures()

    scan_id_created = None

    try:
        # -------------------------------------------------------------
        # TEST 1 & 2: Diagnosis in English, then on-demand Hindi & Gujarati reports
        # -------------------------------------------------------------
        print("\n--- TEST 1 & 2: Multilingual Report Generation & Multi-Row Persistence ---")
        async with AsyncSessionLocal() as session:
            diag_service = DiagnosisService(session)
            
            # 1. Run initial diagnosis with target_lang = 'en'
            diag_result = await diag_service.diagnose_leaf(
                user_dict=farmer_1_dict,
                crop_name="chili",
                image_bytes=chili_image_bytes,
                farm_id=farm_1_id,
                language_code="en",
            )

            assert diag_result["status"] == "success", "Expected confident diagnosis"
            scan_id = uuid.UUID(diag_result["scan_id"])
            scan_id_created = scan_id
            en_report = diag_result["report"]
            assert en_report["language_code"] == "en", "Report must be in 'en'"
            print(f"  [PASS] Initial scan created: {scan_id}")
            print(f"         English Report: '{en_report['disease_name']}'")

            # 2. Retrieve report in Hindi ('hi') via get_or_generate_report_for_scan
            hi_report = await diag_service.get_or_generate_report_for_scan(
                scan_id=scan_id,
                language_code="hi",
                user_dict=farmer_1_dict,
            )
            assert hi_report["language_code"] == "hi", "Report must be in 'hi'"
            assert len(hi_report["symptoms"]) > 0, "Hindi symptoms must not be empty"
            assert "KVK" in hi_report["disclaimer"] or "कृषि" in hi_report["disclaimer"], "Regulatory disclaimer must be grounded"
            print(f"  [PASS] Hindi Report Generated & Stored: '{hi_report['disease_name']}'")
            print(f"         Hindi Summary preview: {hi_report['summary'][:60]}...")

            # 3. Retrieve report in Gujarati ('gu') via get_or_generate_report_for_scan
            gu_report = await diag_service.get_or_generate_report_for_scan(
                scan_id=scan_id,
                language_code="gu",
                user_dict=farmer_1_dict,
            )
            assert gu_report["language_code"] == "gu", "Report must be in 'gu'"
            assert len(gu_report["management_steps"]) > 0, "Gujarati management steps must not be empty"
            assert "KVK" in gu_report["disclaimer"] or "કૃષિ" in gu_report["disclaimer"], "Regulatory disclaimer must be grounded"
            print(f"  [PASS] Gujarati Report Generated & Stored: '{gu_report['disease_name']}'")
            print(f"         Gujarati Summary preview: {gu_report['summary'][:60]}...")

        # Verify Test 2: Check database has 3 distinct Report rows for this single scan_id
        async with AsyncSessionLocal() as session:
            stmt = select(Report).where(Report.scan_id == scan_id).order_by(Report.language_code.asc())
            reports = (await session.execute(stmt)).scalars().all()
            lang_codes = [r.language_code for r in reports]
            assert sorted(lang_codes) == ["en", "gu", "hi"], f"Expected ['en', 'gu', 'hi'], got {lang_codes}"
            print(f"  [PASS] Verified 3 distinct Report records for scan {scan_id}: {lang_codes}")

        # -------------------------------------------------------------
        # TEST 3: Caching Check (Groq is NOT called again on cache hit)
        # -------------------------------------------------------------
        print("\n--- TEST 3: Report Caching Verification (No Redundant LLM Calls) ---")
        async with AsyncSessionLocal() as session:
            diag_service = DiagnosisService(session)
            
            # Monkeypatch generate_advisory_report to ensure it is NOT called
            def forbidden_llm_call(*args, **kwargs):
                raise AssertionError("Groq LLM was called on a cached report lookup!")

            diag_service.llm_service.generate_advisory_report = forbidden_llm_call

            cached_hi = await diag_service.get_or_generate_report_for_scan(
                scan_id=scan_id,
                language_code="hi",
                user_dict=farmer_1_dict,
            )
            assert cached_hi["language_code"] == "hi"
            assert cached_hi["id"] == hi_report["id"], "Cached report ID must match"
            print("  [PASS] Cached report retrieved without calling Groq LLM again.")

        # -------------------------------------------------------------
        # TEST 4: Tenant Security (Farmer 2 cannot access Farmer 1's scan report)
        # -------------------------------------------------------------
        print("\n--- TEST 4: Cross-Tenant Security on Multilingual Reports ---")
        async with AsyncSessionLocal() as session:
            diag_service = DiagnosisService(session)
            try:
                await diag_service.get_or_generate_report_for_scan(
                    scan_id=scan_id,
                    language_code="hi",
                    user_dict=farmer_2_dict,  # Farmer 2 attempting to access Farmer 1's scan
                )
                assert False, "Should have thrown HTTPException 404"
            except HTTPException as exc:
                assert exc.status_code == 404, f"Expected 404, got {exc.status_code}"
                print(f"  [PASS] Unauthorized access blocked: HTTP {exc.status_code} - '{exc.detail}'")

        # -------------------------------------------------------------
        # TEST 5: Language Preference Persistence in PostgreSQL
        # -------------------------------------------------------------
        print("\n--- TEST 5: User Language Preference Persistence ---")
        async with AsyncSessionLocal() as session:
            auth_service = AuthService(session)
            
            # 1. Update preferred language to 'gu'
            updated_profile = await auth_service.update_language_preference(
                user_id=farmer_1_id,
                language_code="gu",
            )
            assert updated_profile["preferred_language"] == "gu"

            # 2. Re-read from database
            reloaded_user = await session.get(User, farmer_1_id)
            assert reloaded_user.preferred_language == "gu"
            print(f"  [PASS] Farmer 1 language preference persisted to PostgreSQL: '{reloaded_user.preferred_language}'")

            # 3. Update to 'hi'
            updated_profile_hi = await auth_service.update_language_preference(
                user_id=farmer_1_id,
                language_code="hi",
            )
            assert updated_profile_hi["preferred_language"] == "hi"
            await session.refresh(reloaded_user)
            assert reloaded_user.preferred_language == "hi"
            print(f"  [PASS] Farmer 1 language preference updated to: '{reloaded_user.preferred_language}'")

        # -------------------------------------------------------------
        # TEST 6: Confidence Gate Policy (Low-confidence rejected scans)
        # -------------------------------------------------------------
        print("\n--- TEST 6: Confidence Gate Enforcement (No Reports on Rejected Scans) ---")
        unconfident_scan_id = uuid.uuid4()
        async with AsyncSessionLocal() as session:
            # Create a scan with status="low_confidence"
            crop_chili = (await session.execute(select(Crop).where(Crop.name == "chili"))).scalars().first()
            bad_scan = Scan(
                id=unconfident_scan_id,
                user_id=farmer_1_id,
                crop_id=crop_chili.id,
                image_path="scans/low_conf_test.jpg",
                status="low_confidence",
            )
            session.add(bad_scan)
            await session.commit()

            diag_service = DiagnosisService(session)
            try:
                await diag_service.get_or_generate_report_for_scan(
                    scan_id=unconfident_scan_id,
                    language_code="hi",
                    user_dict=farmer_1_dict,
                )
                assert False, "Should have rejected request with HTTPException 400"
            except HTTPException as exc:
                assert exc.status_code == 400, f"Expected 400, got {exc.status_code}"
                assert "low-confidence" in exc.detail or "rejected" in exc.detail
                print(f"  [PASS] Low-confidence scan properly rejected: HTTP {exc.status_code} - '{exc.detail}'")

        # -------------------------------------------------------------
        # TEST 7: Resilient Fallback in Hindi, Gujarati, and English
        # -------------------------------------------------------------
        print("\n--- TEST 7: Agronomic Multilingual Fallback when Groq is Unavailable ---")
        llm_svc = LLMService()
        # Force offline by clearing API key temporarily
        llm_svc.api_key = ""

        # Test Hindi fallback
        hi_fb = await llm_svc.generate_advisory_report(
            crop="chili",
            disease_name="White spot",
            confidence=0.85,
            farm_info={"district": "Anand"},
            weather_info={"temperature_c": 29.0},
            target_lang="hi",
        )
        assert "White spot" in hi_fb.disease_name
        assert "सटीकता" in hi_fb.confidence_interpretation or "विश्वास" in hi_fb.confidence_interpretation
        assert len(hi_fb.management_steps) > 0
        assert "KVK" in hi_fb.disclaimer
        print(f"  [PASS] Hindi Fallback generated: '{hi_fb.disease_name}'")

        # Test Gujarati fallback
        gu_fb = await llm_svc.generate_advisory_report(
            crop="chili",
            disease_name="White spot",
            confidence=0.85,
            farm_info={"district": "Anand"},
            weather_info={"temperature_c": 29.0},
            target_lang="gu",
        )
        assert "White spot" in gu_fb.disease_name
        assert "ચોકસાઈ" in gu_fb.confidence_interpretation or "વિશ્વસનીયતા" in gu_fb.confidence_interpretation
        assert len(gu_fb.management_steps) > 0
        assert "KVK" in gu_fb.disclaimer
        print(f"  [PASS] Gujarati Fallback generated: '{gu_fb.disease_name}'")

        # Test English fallback
        en_fb = await llm_svc.generate_advisory_report(
            crop="chili",
            disease_name="White spot",
            confidence=0.85,
            farm_info={"district": "Anand"},
            weather_info={"temperature_c": 29.0},
            target_lang="en",
        )
        assert "White spot" in en_fb.disease_name
        assert len(en_fb.management_steps) > 0
        assert "KVK" in en_fb.disclaimer
        print(f"  [PASS] English Fallback generated: '{en_fb.disease_name}'")

    finally:
        await cleanup_test_fixtures()
        print("\n  [CLEANUP] Successfully cleaned up test database fixtures.")

    print("\n=================================================================")
    print("ALL MODULE 15 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=================================================================")


if __name__ == "__main__":
    asyncio.run(run_tests())
