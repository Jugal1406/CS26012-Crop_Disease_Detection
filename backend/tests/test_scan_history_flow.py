"""
backend/test_scan_history_flow.py
=================================
Automated verification test suite for Module 16: Scan History and Pagination.

Test Requirements Covered:
  1. Pagination metadata & boundary cases (page, page_size, total_pages, has_next, has_prev, out-of-range pages).
  2. Crop and status filters & ascending/descending sorting.
  3. Stable ordering when timestamps match (secondary sort key Scan.id).
  4. Cross-user isolation for list and detail endpoints (returns 404 for unauthorized scan access).
  5. Low-confidence, pending, and failed scan handling (never generates normal advisory for low confidence).
  6. Missing or unavailable reports and weather handled gracefully.
  7. Authorized image access (user isolation and directory traversal protection).
  8. Multilingual report retrieval integration (Module 15 cache/generator).
"""

import asyncio
from datetime import datetime, timezone
import os
import sys
import uuid

# Windows CP1252 stdout encoding safety
sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv()

from fastapi import HTTPException
from sqlalchemy import select, text
import config
from database import AsyncSessionLocal, engine
from models import Crop, Disease, Farm, ModelVersion, Prediction, Report, Scan, User, WeatherSnapshot
from repositories.scan_repository import ScanRepository
from routers.scans import get_scan_detail, get_scan_image, list_scans
from services.diagnosis_service import DiagnosisService

REAL_CHILI_IMAGE_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "test_chili_leaf.jpg")

farmer_a_id = uuid.uuid4()
farmer_b_id = uuid.uuid4()
farm_a_id = uuid.uuid4()

farmer_a_dict = {
    "id": str(farmer_a_id),
    "auth_provider": "firebase",
    "auth_provider_user_id": f"test_fb_m16_a_{farmer_a_id.hex[:8]}",
    "email": f"farmer_m16_a_{farmer_a_id.hex[:6]}@example.com",
    "display_name": "Kishan Kumar",
    "preferred_language": "en",
    "is_active": True,
}

farmer_b_dict = {
    "id": str(farmer_b_id),
    "auth_provider": "firebase",
    "auth_provider_user_id": f"test_fb_m16_b_{farmer_b_id.hex[:8]}",
    "email": f"farmer_m16_b_{farmer_b_id.hex[:6]}@example.com",
    "display_name": "Bharat Patel",
    "preferred_language": "gu",
    "is_active": True,
}


async def setup_test_fixtures():
    async with AsyncSessionLocal() as session:
        # 1. Clean previous test artifacts
        await session.execute(text("DELETE FROM users WHERE email LIKE 'farmer_m16_%@example.com'"))
        await session.commit()

        # 2. Insert test farmers
        u1 = User(
            id=farmer_a_id,
            auth_provider=farmer_a_dict["auth_provider"],
            auth_provider_user_id=farmer_a_dict["auth_provider_user_id"],
            display_name=farmer_a_dict["display_name"],
            email=farmer_a_dict["email"],
            preferred_language=farmer_a_dict["preferred_language"],
            is_active=True,
        )
        u2 = User(
            id=farmer_b_id,
            auth_provider=farmer_b_dict["auth_provider"],
            auth_provider_user_id=farmer_b_dict["auth_provider_user_id"],
            display_name=farmer_b_dict["display_name"],
            email=farmer_b_dict["email"],
            preferred_language=farmer_b_dict["preferred_language"],
            is_active=True,
        )
        session.add_all([u1, u2])

        # 3. Insert test farm for farmer A
        f1 = Farm(
            id=farm_a_id,
            user_id=farmer_a_id,
            name="Navsari Chili Field",
            village="Dandi",
            district="Navsari",
            state="Gujarat",
            area_hectares=1.8,
            latitude=20.8880,
            longitude=72.8028,
            is_active=True,
        )
        session.add(f1)
        await session.commit()


async def cleanup_test_fixtures():
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(f"DELETE FROM users WHERE id IN ('{farmer_a_id}', '{farmer_b_id}')")
        )
        await session.commit()


async def run_tests():
    print("=================================================================")
    print("RUNNING MODULE 16 INTEGRATION TESTS: SCAN HISTORY & PAGINATION")
    print("=================================================================")

    await setup_test_fixtures()

    try:
        # Obtain crop entity (chili)
        async with AsyncSessionLocal() as session:
            crop_stmt = select(Crop).where(Crop.name == "chili")
            chili_crop = (await session.execute(crop_stmt)).scalars().first()
            assert chili_crop is not None, "Chili crop entity must exist in database"
            chili_id = chili_crop.id

            disease_stmt = select(Disease).where(Disease.crop_id == chili_id)
            chili_disease = (await session.execute(disease_stmt)).scalars().first()
            disease_id = chili_disease.id if chili_disease else None

        # -------------------------------------------------------------------
        # TEST 1: Seed Diverse Historical Scans for Farmer A and Farmer B
        # -------------------------------------------------------------------
        print("\n[TEST 1] Populating diverse test scans for Farmer A & Farmer B...")
        scan_ids_farmer_a = []
        scan_ids_farmer_b = []

        async with AsyncSessionLocal() as session:
            # 1a. Farmer A Scan 1: High confidence success with weather & report
            s1 = Scan(
                crop_id=chili_id,
                user_id=farmer_a_id,
                farm_id=farm_a_id,
                image_path="scans/test_scan_1.jpg",
                status="success",
                created_at=datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc),
            )
            session.add(s1)
            await session.flush()
            p1 = Prediction(
                scan_id=s1.id,
                disease_id=disease_id,
                model_version_id=1,
                confidence=0.94,
                threshold_used=0.70,
                is_confident=True,
                raw_scores={"leaf_curl": 0.94, "healthy": 0.06},
            )
            w1 = WeatherSnapshot(
                farm_id=farm_a_id,
                scan_id=s1.id,
                temperature_c=29.5,
                humidity_pct=72.0,
                rainfall_mm=0.0,
                wind_speed_kmh=12.0,
                weather_condition="Clear sky",
                data_source="Open-Meteo",
                recorded_at=datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc),
            )
            r1 = Report(
                scan_id=s1.id,
                language_code="en",
                disease_name="Chili Leaf Curl",
                summary="Foliar fungal symptoms detected on chili leaves.",
                symptoms=["Curled leaves", "Chlorosis"],
                possible_causes=["High relative humidity."],
                management_steps=["Isolate affected foliage", "Improve airflow"],
                prevention_steps=["Crop rotation"],
                warning_signs=["Lesions spread to stems"],
                confidence_interpretation="High certainty foliar diagnosis",
            )
            session.add_all([p1, w1, r1])
            scan_ids_farmer_a.append(s1.id)

            # 1b. Farmer A Scan 2: Low-confidence scan (no report, rejected)
            s2 = Scan(
                crop_id=chili_id,
                user_id=farmer_a_id,
                farm_id=farm_a_id,
                image_path="scans/test_scan_2.jpg",
                status="low_confidence",
                created_at=datetime(2026, 10, 2, 11, 0, 0, tzinfo=timezone.utc),
            )
            session.add(s2)
            await session.flush()
            p2 = Prediction(
                scan_id=s2.id,
                disease_id=None,
                model_version_id=1,
                confidence=0.48,
                threshold_used=0.70,
                is_confident=False,
                raw_scores={"leaf_curl": 0.48, "healthy": 0.52},
            )
            session.add(p2)
            scan_ids_farmer_a.append(s2.id)

            # 1c. Farmer A Scan 3: Scan with identical timestamp to Scan 4 (to test stable sorting)
            same_time = datetime(2026, 10, 3, 14, 0, 0, tzinfo=timezone.utc)
            s3 = Scan(
                crop_id=chili_id,
                user_id=farmer_a_id,
                farm_id=None,
                image_path="scans/test_scan_3.jpg",
                status="success",
                created_at=same_time,
            )
            s4 = Scan(
                crop_id=chili_id,
                user_id=farmer_a_id,
                farm_id=None,
                image_path="scans/test_scan_4.jpg",
                status="success",
                created_at=same_time,
            )
            session.add_all([s3, s4])
            await session.flush()
            p3 = Prediction(
                scan_id=s3.id,
                disease_id=disease_id,
                model_version_id=1,
                confidence=0.88,
                threshold_used=0.70,
                is_confident=True,
            )
            p4 = Prediction(
                scan_id=s4.id,
                disease_id=disease_id,
                model_version_id=1,
                confidence=0.89,
                threshold_used=0.70,
                is_confident=True,
            )
            session.add_all([p3, p4])
            scan_ids_farmer_a.extend([s3.id, s4.id])

            # 1d. Farmer A Scan 5: Pending scan with missing weather and missing report
            s5 = Scan(
                crop_id=chili_id,
                user_id=farmer_a_id,
                farm_id=None,
                image_path="scans/test_scan_5.jpg",
                status="pending",
                created_at=datetime(2026, 10, 4, 15, 0, 0, tzinfo=timezone.utc),
            )
            session.add(s5)
            scan_ids_farmer_a.append(s5.id)

            # 1e. Farmer B Scan 1: Owned strictly by Farmer B
            sb = Scan(
                crop_id=chili_id,
                user_id=farmer_b_id,
                farm_id=None,
                image_path="scans/test_scan_b.jpg",
                status="success",
                created_at=datetime(2026, 10, 5, 16, 0, 0, tzinfo=timezone.utc),
            )
            session.add(sb)
            await session.flush()
            pb = Prediction(
                scan_id=sb.id,
                disease_id=disease_id,
                model_version_id=1,
                confidence=0.91,
                threshold_used=0.70,
                is_confident=True,
            )
            session.add(pb)
            scan_ids_farmer_b.append(sb.id)

            await session.commit()

        print(f"  [PASS] Successfully seeded 5 scans for Farmer A and 1 scan for Farmer B.")

        # -------------------------------------------------------------------
        # TEST 2: Pagination Metadata & Boundary Cases
        # -------------------------------------------------------------------
        print("\n[TEST 2] Verifying Pagination Metadata & Boundary Cases...")
        async with AsyncSessionLocal() as session:
            # Page 1, page_size 2 (Total should be 5 for Farmer A)
            res_p1 = await list_scans(
                page=1, page_size=2, crop=None, status=None, sort_order="desc",
                current_user=farmer_a_dict, db=session,
            )
            assert res_p1.total == 5, f"Expected total 5, got {res_p1.total}"
            assert len(res_p1.items) == 2, f"Expected 2 items on page 1, got {len(res_p1.items)}"
            assert res_p1.page == 1
            assert res_p1.page_size == 2
            assert res_p1.total_pages == 3
            assert res_p1.has_next is True, "Page 1 of 3 should have next page"
            assert res_p1.has_prev is False, "Page 1 should not have previous page"
            print("  [OK] Page 1 metadata verified (total=5, total_pages=3, has_next=True, has_prev=False)")

            # Page 2, page_size 2
            res_p2 = await list_scans(
                page=2, page_size=2, crop=None, status=None, sort_order="desc",
                current_user=farmer_a_dict, db=session,
            )
            assert len(res_p2.items) == 2
            assert res_p2.has_next is True
            assert res_p2.has_prev is True
            print("  [OK] Page 2 metadata verified (has_next=True, has_prev=True)")

            # Page 3, page_size 2 (last page with 1 item)
            res_p3 = await list_scans(
                page=3, page_size=2, crop=None, status=None, sort_order="desc",
                current_user=farmer_a_dict, db=session,
            )
            assert len(res_p3.items) == 1
            assert res_p3.has_next is False
            assert res_p3.has_prev is True
            print("  [OK] Page 3 (boundary last page) verified (items=1, has_next=False, has_prev=True)")

            # Out-of-bounds page (page 999)
            res_oob = await list_scans(
                page=999, page_size=2, crop=None, status=None, sort_order="desc",
                current_user=farmer_a_dict, db=session,
            )
            assert len(res_oob.items) == 0, "Out-of-bounds page should return empty list"
            assert res_oob.total == 5
            assert res_oob.has_next is False
            print("  [OK] Out-of-bounds page (page=999) returns empty items with total preserved.")

        print("  [PASS] Test 2: Pagination metadata and boundary handling passed.")

        # -------------------------------------------------------------------
        # TEST 3: Crop and Status Filters & Sorting
        # -------------------------------------------------------------------
        print("\n[TEST 3] Verifying Crop & Status Filters and Date Sorting...")
        async with AsyncSessionLocal() as session:
            # Filter by crop 'chili'
            res_crop = await list_scans(
                page=1, page_size=10, crop="chili", status=None, sort_order="desc",
                current_user=farmer_a_dict, db=session,
            )
            assert res_crop.total == 5
            for it in res_crop.items:
                assert it.crop == "chili"
            print("  [OK] Crop filter 'chili' returned matching records.")

            # Filter by status 'low_confidence'
            res_low = await list_scans(
                page=1, page_size=10, crop=None, status="low_confidence", sort_order="desc",
                current_user=farmer_a_dict, db=session,
            )
            assert res_low.total == 1
            assert res_low.items[0].status == "low_confidence"
            print("  [OK] Status filter 'low_confidence' returned exactly 1 record.")

            # Filter by status 'pending'
            res_pend = await list_scans(
                page=1, page_size=10, crop=None, status="pending", sort_order="desc",
                current_user=farmer_a_dict, db=session,
            )
            assert res_pend.total == 1
            assert res_pend.items[0].status == "pending"
            print("  [OK] Status filter 'pending' returned exactly 1 record.")

            # Sorting ascending vs descending
            res_desc = await list_scans(
                page=1, page_size=10, crop=None, status=None, sort_order="desc",
                current_user=farmer_a_dict, db=session,
            )
            res_asc = await list_scans(
                page=1, page_size=10, crop=None, status=None, sort_order="asc",
                current_user=farmer_a_dict, db=session,
            )
            # Most recent in desc should match oldest in asc
            assert res_desc.items[0].id == res_asc.items[-1].id
            assert res_desc.items[-1].id == res_asc.items[0].id
            print("  [OK] Ascending and descending date sorting verified.")

            # Invalid status filter raises 400
            try:
                await list_scans(
                    page=1, page_size=10, crop=None, status="invalid_status_xyz", sort_order="desc",
                    current_user=farmer_a_dict, db=session,
                )
                assert False, "Invalid status should have raised HTTPException 400"
            except HTTPException as exc:
                assert exc.status_code == 400
                print("  [OK] Invalid status rejected with HTTP 400.")

        print("  [PASS] Test 3: Filters and sorting verified successfully.")

        # -------------------------------------------------------------------
        # TEST 4: Stable Ordering When Timestamps Match (Secondary Sort Key)
        # -------------------------------------------------------------------
        print("\n[TEST 4] Verifying Stable Ordering with Matching Timestamps...")
        async with AsyncSessionLocal() as session:
            # Run same query multiple times; order of s3 and s4 must be 100% deterministic
            res1 = await list_scans(
                page=1, page_size=10, crop=None, status=None, sort_order="desc",
                current_user=farmer_a_dict, db=session,
            )
            res2 = await list_scans(
                page=1, page_size=10, crop=None, status=None, sort_order="desc",
                current_user=farmer_a_dict, db=session,
            )
            ids1 = [it.id for it in res1.items]
            ids2 = [it.id for it in res2.items]
            assert ids1 == ids2, "Ordering must be strictly deterministic across queries"

            # Check that secondary sort key (Scan.id) properly ordered s3 and s4
            idx_s3 = next(i for i, it in enumerate(res1.items) if it.id == str(s3.id))
            idx_s4 = next(i for i, it in enumerate(res1.items) if it.id == str(s4.id))
            if str(s3.id) > str(s4.id):
                assert idx_s3 < idx_s4, "Secondary sort key (id desc) should order greater UUID first"
            else:
                assert idx_s4 < idx_s3, "Secondary sort key (id desc) should order greater UUID first"
            print("  [OK] Stable secondary sort key (Scan.id) verified.")

        print("  [PASS] Test 4: Stable pagination ordering verified.")

        # -------------------------------------------------------------------
        # TEST 5: Cross-User Isolation (List & Detail endpoints return 404)
        # -------------------------------------------------------------------
        print("\n[TEST 5] Verifying Strict Tenant / Cross-User Isolation...")
        async with AsyncSessionLocal() as session:
            # 5a. Farmer B list contains only Farmer B scans
            res_b = await list_scans(
                page=1, page_size=10, crop=None, status=None, sort_order="desc",
                current_user=farmer_b_dict, db=session,
            )
            assert res_b.total == 1, f"Farmer B should have 1 scan, got {res_b.total}"
            assert res_b.items[0].id == str(sb.id)
            print("  [OK] Farmer B list is strictly scoped to Farmer B (total=1).")

            # 5b. Farmer B requesting Farmer A's scan returns 404 (NOT 403 or data leak)
            try:
                await get_scan_detail(
                    scan_id=s1.id, lang="en", current_user=farmer_b_dict, db=session
                )
                assert False, "Unauthorized scan detail access must raise 404"
            except HTTPException as exc:
                assert exc.status_code == 404, f"Expected 404, got {exc.status_code}"
                print("  [OK] Farmer B requesting Farmer A's scan returned HTTP 404.")

            # 5c. Farmer A requesting non-existent scan returns 404
            random_scan_id = uuid.uuid4()
            try:
                await get_scan_detail(
                    scan_id=random_scan_id, lang="en", current_user=farmer_a_dict, db=session
                )
                assert False, "Non-existent scan must raise 404"
            except HTTPException as exc:
                assert exc.status_code == 404
                print("  [OK] Non-existent scan ID returned HTTP 404.")

        print("  [PASS] Test 5: Strict cross-user isolation confirmed.")

        # -------------------------------------------------------------------
        # TEST 6: Low-Confidence, Pending, and Failed Scan Handling
        # -------------------------------------------------------------------
        print("\n[TEST 6] Verifying Low-Confidence, Pending & Inconclusive Scan Handling...")
        async with AsyncSessionLocal() as session:
            # 6a. Low-confidence scan detail
            detail_low = await get_scan_detail(
                scan_id=s2.id, lang="en", current_user=farmer_a_dict, db=session
            )
            assert detail_low.status == "low_confidence"
            assert detail_low.prediction is not None
            assert detail_low.prediction.is_confident is False
            assert detail_low.prediction.confidence_percentage == 48.0
            assert detail_low.rejection_guidance is not None
            # Crucial requirement: Never generate a normal advisory for low-confidence scans
            assert detail_low.report is None, "Low confidence scan MUST NOT have normal advisory report"
            print("  [OK] Low-confidence scan has rejection guidance and strictly NO advisory report.")

            # 6b. Pending scan detail (missing prediction, missing weather, missing report)
            detail_pend = await get_scan_detail(
                scan_id=s5.id, lang="en", current_user=farmer_a_dict, db=session
            )
            assert detail_pend.status == "pending"
            assert detail_pend.prediction is None
            assert detail_pend.weather is None
            assert detail_pend.report is None
            print("  [OK] Pending scan handled gracefully without errors.")

        print("  [PASS] Test 6: Inconclusive, low-confidence, and pending scans handled properly.")

        # -------------------------------------------------------------------
        # TEST 7: Authorized Image Streaming & Safety Against Path Traversal
        # -------------------------------------------------------------------
        print("\n[TEST 7] Verifying Authorized Image Access & Path Traversal Guards...")
        async with AsyncSessionLocal() as session:
            # 7a. Farmer A can access own scan image
            img_res = await get_scan_image(
                scan_id=s1.id, current_user=farmer_a_dict, db=session
            )
            assert img_res is not None
            print("  [OK] Farmer A authorized to stream scan image.")

            # 7b. Farmer B requesting Farmer A's image gets 404
            try:
                await get_scan_image(
                    scan_id=s1.id, current_user=farmer_b_dict, db=session
                )
                assert False, "Farmer B should not be able to access Farmer A scan image"
            except HTTPException as exc:
                assert exc.status_code == 404
                print("  [OK] Farmer B attempting to access Farmer A scan image returned HTTP 404.")

            # 7c. Path traversal attack prevented
            # Create a mock malicious scan with path traversal attempt
            s_malicious = Scan(
                crop_id=chili_id,
                user_id=farmer_a_id,
                farm_id=None,
                image_path="../../windows/system32/cmd.exe",
                status="completed",
            )
            session.add(s_malicious)
            await session.commit()

            try:
                await get_scan_image(
                    scan_id=s_malicious.id, current_user=farmer_a_dict, db=session
                )
                assert False, "Path traversal attempt should be rejected with 403"
            except HTTPException as exc:
                assert exc.status_code == 403
                print("  [OK] Path traversal attempt correctly blocked with HTTP 403.")

        print("  [PASS] Test 7: Authorized image access and directory traversal guards verified.")

        # -------------------------------------------------------------------
        # TEST 8: Multilingual Advisory Report Integration
        # -------------------------------------------------------------------
        print("\n[TEST 8] Verifying Multilingual Advisory Report Integration...")
        async with AsyncSessionLocal() as session:
            # 8a. Fetch detail in English (already cached)
            detail_en = await get_scan_detail(
                scan_id=s1.id, lang="en", current_user=farmer_a_dict, db=session
            )
            assert detail_en.has_report is True
            assert detail_en.report is not None
            assert detail_en.report.language_code == "en"
            print("  [OK] Scan detail successfully returned cached English advisory report.")

            # 8b. Fetch detail in Hindi ('hi') - should invoke Module 15 multilingual generator/cache
            detail_hi = await get_scan_detail(
                scan_id=s1.id, lang="hi", current_user=farmer_a_dict, db=session
            )
            assert detail_hi.report is not None
            assert detail_hi.report.language_code == "hi"
            print(f"  [OK] Scan detail in Hindi returned: {detail_hi.report.summary[:50]}...")

            # 8c. Available languages should now include both 'en' and 'hi'
            assert "en" in detail_hi.available_report_languages
            assert "hi" in detail_hi.available_report_languages
            print(f"  [OK] Available report languages dynamically updated: {detail_hi.available_report_languages}")

        print("  [PASS] Test 8: Multilingual report integration verified successfully.")

        print("\n=================================================================")
        print("ALL 8 BACKEND MODULE 16 TESTS PASSED SUCCESSFULLY!")
        print("=================================================================")

    finally:
        await cleanup_test_fixtures()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_tests())
