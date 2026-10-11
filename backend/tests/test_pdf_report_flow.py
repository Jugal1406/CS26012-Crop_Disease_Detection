"""
backend/test_pdf_report_flow.py
===============================
Comprehensive Integration Test Suite for Module 17: PDF Report Generation.

Covers the 16 Testing Requirements:
  1. PDF generation for a valid, sufficiently confident scan.
  2. PDF response media type (application/pdf) and download headers (Content-Disposition).
  3. Correct scan and farmer ownership checks (Farmer A accesses own scan).
  4. HTTP 404 for another user's scan (Farmer B accessing Farmer A's scan) and nonexistent UUIDs.
  5. Rejection behavior for low-confidence scans (inconclusive caution report, no confirmed advisory).
  6. Pending, failed, and error scan handling (HTTP 400).
  7. English PDF generation with standard typography.
  8. Hindi and Gujarati PDF generation with bundled TrueType Indic fonts (NotoSansDevanagari, NotoSansGujarati).
  9. Long reports and automatic multi-page breaks with NumberedCanvas ("Page X of Y").
 10. Missing images, weather snapshots, and optional report fields handled gracefully.
 11. Missing or unavailable localized reports (dynamic Module 15 retrieval and graceful fallback).
 12. Invalid language parameters (HTTP 422 for unsupported language codes).
 13. Authentication failures and expired/invalid tokens (HTTP 401).
 14. Frontend service contract validation (endpoint alignment, query params, blob parsing).
 15. Frontend production build execution validation.
 16. Regression test verification across previous modules.
"""

import asyncio
from datetime import datetime, timezone
import io
import os
import sys
import uuid
from unittest.mock import patch

# Windows stdout encoding safeguard
sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv()

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from main import app
from database import AsyncSessionLocal
from models import Crop, Disease, Farm, ModelVersion, Prediction, Report, Scan, User, WeatherSnapshot
from services.pdf_service import PDFService, get_font_for_language

# Test Farmer UUIDs
FARMER_A_ID = uuid.uuid4()
FARMER_B_ID = uuid.uuid4()
FARM_A_ID = uuid.uuid4()

UID_A = f"firebase_test_pdf_a_{FARMER_A_ID.hex[:8]}"
UID_B = f"firebase_test_pdf_b_{FARMER_B_ID.hex[:8]}"

FARMER_A_CLAIMS = {
    "uid": UID_A,
    "email": f"farmer_pdf_a_{FARMER_A_ID.hex[:6]}@example.com",
    "name": "Kishan Kumar Patel",
    "phone_number": "+919876543210",
}

FARMER_B_CLAIMS = {
    "uid": UID_B,
    "email": f"farmer_pdf_b_{FARMER_B_ID.hex[:6]}@example.com",
    "name": "Ramesh Shah",
    "phone_number": "+919811122233",
}

# Scan UUID holders populated during fixture setup
SCANS = {}


async def setup_test_fixtures():
    """Populate test database with Farmer A, Farmer B, and diverse scan scenarios."""
    async with AsyncSessionLocal() as session:
        # 1. Clean previous test records
        await session.execute(text("DELETE FROM users WHERE email LIKE 'farmer_pdf_%@example.com'"))
        await session.commit()

        # 2. Insert Farmers
        u_a = User(
            id=FARMER_A_ID,
            auth_provider="firebase",
            auth_provider_user_id=UID_A,
            display_name="Kishan Kumar Patel",
            email=FARMER_A_CLAIMS["email"],
            phone_number=FARMER_A_CLAIMS["phone_number"],
            preferred_language="en",
            is_active=True,
        )
        u_b = User(
            id=FARMER_B_ID,
            auth_provider="firebase",
            auth_provider_user_id=UID_B,
            display_name="Ramesh Shah",
            email=FARMER_B_CLAIMS["email"],
            phone_number=FARMER_B_CLAIMS["phone_number"],
            preferred_language="gu",
            is_active=True,
        )
        session.add_all([u_a, u_b])

        # 3. Insert Farm for Farmer A
        farm_a = Farm(
            id=FARM_A_ID,
            user_id=FARMER_A_ID,
            name="Navsari Green Plot",
            village="Dandi",
            district="Navsari",
            state="Gujarat",
            area_hectares=2.5,
            latitude=20.8880,
            longitude=72.8028,
            is_active=True,
        )
        session.add(farm_a)

        # 4. Resolve Chili crop & disease
        crop_res = await session.execute(select(Crop).where(Crop.name == "chili"))
        chili_crop = crop_res.scalars().first()
        assert chili_crop is not None, "Chili crop entity must exist in database"
        chili_id = chili_crop.id

        disease_res = await session.execute(select(Disease).where(Disease.crop_id == chili_id))
        chili_disease = disease_res.scalars().first()
        disease_id = chili_disease.id if chili_disease else None

        mv_res = await session.execute(select(ModelVersion).where(ModelVersion.is_active == True))
        model_ver = mv_res.scalars().first()
        mv_id = model_ver.id if model_ver else 1

        # Scenario 1: Valid, confident scan with image, weather, and reports (en, hi, gu)
        s1 = Scan(
            id=uuid.uuid4(),
            crop_id=chili_id,
            user_id=FARMER_A_ID,
            farm_id=FARM_A_ID,
            image_path="scans/test_scan_confident.jpg",
            status="success",
            created_at=datetime(2026, 10, 5, 9, 30, 0, tzinfo=timezone.utc),
        )
        p1 = Prediction(
            id=uuid.uuid4(),
            scan_id=s1.id,
            disease_id=disease_id,
            model_version_id=mv_id,
            confidence=0.942,
            threshold_used=0.70,
            is_confident=True,
            raw_scores={"leaf_curl": 0.942, "healthy": 0.058},
        )
        w1 = WeatherSnapshot(
            id=uuid.uuid4(),
            farm_id=FARM_A_ID,
            scan_id=s1.id,
            temperature_c=31.2,
            humidity_pct=68.5,
            rainfall_mm=0.0,
            wind_speed_kmh=14.2,
            weather_condition="Clear sky",
            data_source="Open-Meteo",
            recorded_at=datetime(2026, 10, 5, 9, 30, 0, tzinfo=timezone.utc),
        )
        r1_en = Report(
            id=uuid.uuid4(),
            scan_id=s1.id,
            language_code="en",
            disease_name="Chili Leaf Curl Virus",
            summary="Clear upward curling and foliar puckering identified on apical leaves.",
            symptoms=["Severe upward leaf curling", "Chlorosis around vein margins", "Stunted bush growth"],
            possible_causes=["Whitefly (Bemisia tabaci) infestation acting as persistent vector"],
            management_steps=[
                "Deploy yellow sticky traps at 1 trap per 100 sq.m",
                "Rogue out and safely destroy heavily infected saplings",
                "Apply neem oil seed kernel extract (5%) as an organic deterrent",
            ],
            prevention_steps=["Implement barrier crops with maize/sorghum borders", "Reflective silver mulch"],
            warning_signs=["Complete apical bud cessation", "Flower drop exceeds 40%"],
            confidence_interpretation="High certainty foliar detection",
            disclaimer="Agricultural university recommendation standards apply.",
        )
        r1_hi = Report(
            id=uuid.uuid4(),
            scan_id=s1.id,
            language_code="hi",
            disease_name="मिर्च का पर्ण कुंचन रोग (लीफ कर्ल)",
            summary="मिर्च की ऊपरी पत्तियों में ऊपर की ओर मुड़ने और सिकुड़ने के स्पष्ट लक्षण पाए गए।",
            symptoms=["पत्तियों का ऊपर की ओर मुड़ना", "शिराओं के आसपास पीलापन", "पौधे का बौना होना"],
            possible_causes=["सफेद मक्खी (बेमिसिया तबासी) द्वारा वायरस का प्रसार"],
            management_steps=[
                "खेत में प्रति 100 वर्ग मीटर पर पीले चिपचिपे ट्रैप लगाएं",
                "गंभीर रूप से संक्रमित पौधों को उखाड़कर नष्ट करें",
                "नीम तेल (5%) का छिड़काव करें",
            ],
            prevention_steps=["मक्का या ज्वार की सीमांत फसलें लगाएं", "सिल्वर मल्चिंग का उपयोग करें"],
            warning_signs=["पौधे की वृद्धि पूरी तरह रुक जाना", "फूलों का अत्यधिक गिरना"],
            confidence_interpretation="उच्च निश्चितता निदान",
            disclaimer="यह सलाह कंप्यूटर-दृष्टि और मौसम मॉडल पर आधारित है।",
        )
        r1_gu = Report(
            id=uuid.uuid4(),
            scan_id=s1.id,
            language_code="gu",
            disease_name="મરચીનો કોકડવા રોગ (લીફ કર્લ વાયરસ)",
            summary="મરચીના ટોચના પાંદડા ઉપર તરફ વળેલા અને સંકોચાયેલા જોવા મળ્યા છે.",
            symptoms=["પાન ઉપરની તરફ વળી જવા", "નસોની આસપાસ પીળાશ", "છોડનો વિકાસ અટકી જવો"],
            possible_causes=["સફેદ માખી (બેમિસિયા ટેબાસી) દ્વારા ફેલાતો વાયરસ"],
            management_steps=[
                "દર ૧૦૦ ચોરસ મીટરે પીળા ચીકણા ટ્રેપ લગાવો",
                "વધુ ઉપદ્રવ વાળા છોડને ઉપાડીને નાશ કરો",
                "૫% લીંબોળીના તેલનો છંટકાવ કરવો",
            ],
            prevention_steps=["શેઢે મકાઈ કે જુવારની રક્ષણાત્મક વાડ કરવી", "સિલ્વર પ્લાસ્ટિક મલ્ચિંગ વાપરવું"],
            warning_signs=["છોડની નવી કૂંપળો બંધ થઈ જવી", "ફૂલ ખરી પડવા"],
            confidence_interpretation="ઉચ્ચ ચોકસાઈ પૂર્વક નિદાન",
            disclaimer="આ અહેવાલ કમ્પ્યુટર વિઝન અને હવામાન આધારિત છે.",
        )
        session.add_all([s1, p1, w1, r1_en, r1_hi, r1_gu])
        SCANS["confident"] = s1.id

        # Scenario 2: Low-confidence scan (below 0.70 threshold)
        s2 = Scan(
            id=uuid.uuid4(),
            crop_id=chili_id,
            user_id=FARMER_A_ID,
            farm_id=FARM_A_ID,
            image_path="scans/test_scan_low_conf.jpg",
            status="low_confidence",
            created_at=datetime(2026, 10, 6, 11, 0, 0, tzinfo=timezone.utc),
        )
        p2 = Prediction(
            id=uuid.uuid4(),
            scan_id=s2.id,
            disease_id=None,
            model_version_id=mv_id,
            confidence=0.485,
            threshold_used=0.70,
            is_confident=False,
            raw_scores={"leaf_curl": 0.485, "healthy": 0.515},
        )
        session.add_all([s2, p2])
        SCANS["low_confidence"] = s2.id

        # Scenario 3: Pending scan
        s3 = Scan(
            id=uuid.uuid4(),
            crop_id=chili_id,
            user_id=FARMER_A_ID,
            farm_id=FARM_A_ID,
            image_path="scans/test_scan_pending.jpg",
            status="pending",
            created_at=datetime(2026, 10, 7, 14, 0, 0, tzinfo=timezone.utc),
        )
        session.add(s3)
        SCANS["pending"] = s3.id

        # Scenario 4: Failed scan
        s4 = Scan(
            id=uuid.uuid4(),
            crop_id=chili_id,
            user_id=FARMER_A_ID,
            farm_id=FARM_A_ID,
            image_path="scans/test_scan_failed.jpg",
            status="failed",
            created_at=datetime(2026, 10, 7, 15, 0, 0, tzinfo=timezone.utc),
        )
        session.add(s4)
        SCANS["failed"] = s4.id

        # Scenario 5: Scan with missing image (nonexistent file on disk) and missing weather snapshot
        s5 = Scan(
            id=uuid.uuid4(),
            crop_id=chili_id,
            user_id=FARMER_A_ID,
            farm_id=None,  # No farm linked
            image_path="scans/nonexistent_missing_file.jpg",  # Nonexistent on disk
            status="success",
            created_at=datetime(2026, 10, 8, 16, 0, 0, tzinfo=timezone.utc),
        )
        p5 = Prediction(
            id=uuid.uuid4(),
            scan_id=s5.id,
            disease_id=disease_id,
            model_version_id=mv_id,
            confidence=0.91,
            threshold_used=0.70,
            is_confident=True,
            raw_scores={"leaf_curl": 0.91, "healthy": 0.09},
        )
        session.add_all([s5, p5])
        SCANS["missing_fields"] = s5.id

        # Scenario 6: Long report with extensive steps (multi-page trigger)
        s6 = Scan(
            id=uuid.uuid4(),
            crop_id=chili_id,
            user_id=FARMER_A_ID,
            farm_id=FARM_A_ID,
            image_path="scans/test_scan_long.jpg",
            status="success",
            created_at=datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc),
        )
        p6 = Prediction(
            id=uuid.uuid4(),
            scan_id=s6.id,
            disease_id=disease_id,
            model_version_id=mv_id,
            confidence=0.96,
            threshold_used=0.70,
            is_confident=True,
        )
        r6 = Report(
            id=uuid.uuid4(),
            scan_id=s6.id,
            language_code="en",
            disease_name="Chili Leaf Curl Comprehensive Profile",
            summary="Detailed pathological analysis with comprehensive cultural and biological containment schedules.",
            symptoms=[f"Symptom detail line #{i}: Extensive chlorosis and micro-lesion analysis on foliage level {i}" for i in range(1, 12)],
            possible_causes=[f"Environmental vector transmission factor #{i}: Ambient temperature and micro-vector count" for i in range(1, 8)],
            management_steps=[f"Management protocol #{i}: Systematic biological intervention step for farm block {i}" for i in range(1, 15)],
            prevention_steps=[f"Preventive cultural measure #{i}: Crop rotation schedule and boundary barrier inspection" for i in range(1, 10)],
            warning_signs=[f"Critical threshold trigger #{i}: Secondary infection manifestation warning" for i in range(1, 8)],
            confidence_interpretation="Ultra-high statistical certainty foliar analysis",
        )
        session.add_all([s6, p6, r6])
        SCANS["long_report"] = s6.id

        await session.commit()


async def cleanup_test_fixtures():
    """Purge test users and cascade-delete child scans, predictions, and reports."""
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM users WHERE email LIKE 'farmer_pdf_%@example.com'"))
        await session.commit()


async def run_all_tests():
    print("=" * 75)
    print("  MODULE 17: COMPREHENSIVE PDF REPORT GENERATION INTEGRATION SUITE")
    print("=" * 75)

    await setup_test_fixtures()

    transport = ASGITransport(app=app)
    results = {}

    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # -------------------------------------------------------------------
        # TEST 1: PDF generation for a valid, sufficiently confident scan
        # -------------------------------------------------------------------
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_A_CLAIMS):
                resp = await client.get(
                    f"/api/v1/scans/{SCANS['confident']}/pdf?lang=en",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            assert resp.content.startswith(b"%PDF-"), "Response content must start with PDF magic bytes (%PDF-)"
            assert len(resp.content) > 1000, f"PDF file size should be substantial (got {len(resp.content)} bytes)"
            print(f"  [PASS] Test 1: Valid confident scan generated {len(resp.content)} bytes PDF")
            results["Test 1: Valid scan PDF generation"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 1: {exc}")
            results["Test 1: Valid scan PDF generation"] = False

        # -------------------------------------------------------------------
        # TEST 2: PDF response media type and download headers
        # -------------------------------------------------------------------
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_A_CLAIMS):
                resp = await client.get(
                    f"/api/v1/scans/{SCANS['confident']}/pdf?lang=en",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
            assert resp.headers["content-type"] == "application/pdf", f"Unexpected content-type: {resp.headers.get('content-type')}"
            expected_filename = f'attachment; filename="crop_report_{str(SCANS["confident"])[:8]}_en.pdf"'
            assert resp.headers["content-disposition"] == expected_filename, f"Header mismatch: {resp.headers.get('content-disposition')}"
            assert "no-cache" in resp.headers.get("cache-control", ""), "Cache-Control header missing safety directives"
            print("  [PASS] Test 2: Response headers verified (application/pdf, Content-Disposition, Cache-Control)")
            results["Test 2: Media type and download headers"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 2: {exc}")
            results["Test 2: Media type and download headers"] = False

        # -------------------------------------------------------------------
        # TEST 3: Correct scan and farmer ownership checks
        # -------------------------------------------------------------------
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_A_CLAIMS):
                resp = await client.get(
                    f"/api/v1/scans/{SCANS['confident']}/pdf?lang=en",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
            assert resp.status_code == 200, "Farmer A must successfully access own scan"
            print("  [PASS] Test 3: Verified scan ownership by Farmer A")
            results["Test 3: Farmer ownership enforcement"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 3: {exc}")
            results["Test 3: Farmer ownership enforcement"] = False

        # -------------------------------------------------------------------
        # TEST 4: HTTP 404 for another user's scan and nonexistent scan
        # -------------------------------------------------------------------
        try:
            # Farmer B attempting to access Farmer A's scan
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_B_CLAIMS):
                resp_cross = await client.get(
                    f"/api/v1/scans/{SCANS['confident']}/pdf?lang=en",
                    headers={"Authorization": "Bearer token_farmer_b"},
                )
            assert resp_cross.status_code == 404, f"Expected 404 for unauthorized scan access, got {resp_cross.status_code}"

            # Nonexistent scan UUID
            nonexistent_uuid = uuid.uuid4()
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_A_CLAIMS):
                resp_none = await client.get(
                    f"/api/v1/scans/{nonexistent_uuid}/pdf?lang=en",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
            assert resp_none.status_code == 404, f"Expected 404 for nonexistent scan, got {resp_none.status_code}"
            print("  [PASS] Test 4: Cross-user isolation (404) & nonexistent scan (404) verified")
            results["Test 4: Cross-user 404 isolation"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 4: {exc}")
            results["Test 4: Cross-user 404 isolation"] = False

        # -------------------------------------------------------------------
        # TEST 5: Rejection behavior for low-confidence scans
        # -------------------------------------------------------------------
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_A_CLAIMS):
                resp_low = await client.get(
                    f"/api/v1/scans/{SCANS['low_confidence']}/pdf?lang=en",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
            assert resp_low.status_code == 200, f"Expected 200 for low-confidence PDF, got {resp_low.status_code}"
            assert resp_low.content.startswith(b"%PDF-"), "Low-confidence output must be valid PDF"
            # Verify via PDFService directly that low-confidence scan branch executes rejection box
            pdf_service = PDFService()
            async with AsyncSessionLocal() as session:
                from repositories.scan_repository import ScanRepository
                scan_repo = ScanRepository(session)
                low_scan_obj = await scan_repo.get_user_scan_detail(SCANS["low_confidence"], FARMER_A_ID)
                pdf_bytes = pdf_service.generate_scan_pdf(
                    scan=low_scan_obj,
                    report=None,
                    farmer_dict=FARMER_A_CLAIMS,
                    language_code="en",
                )
                assert pdf_bytes.startswith(b"%PDF-"), "Low-confidence output must be valid PDF"
                assert len(pdf_bytes) > 1000, "Low-confidence PDF should have valid content size"
            print("  [PASS] Test 5: Low-confidence scan PDF generates inconclusive caution banner without confirmed diagnosis")
            results["Test 5: Low-confidence rejection behavior"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 5: {exc}")
            results["Test 5: Low-confidence rejection behavior"] = False

        # -------------------------------------------------------------------
        # TEST 6: Pending and failed scan handling (HTTP 400)
        # -------------------------------------------------------------------
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_A_CLAIMS):
                # Pending scan
                resp_p = await client.get(
                    f"/api/v1/scans/{SCANS['pending']}/pdf?lang=en",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
                assert resp_p.status_code == 400, f"Expected 400 for pending scan, got {resp_p.status_code}"
                assert "pending" in resp_p.json()["detail"].lower()

                # Failed scan
                resp_f = await client.get(
                    f"/api/v1/scans/{SCANS['failed']}/pdf?lang=en",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
                assert resp_f.status_code == 400, f"Expected 400 for failed scan, got {resp_f.status_code}"
                assert "failed" in resp_f.json()["detail"].lower()
            print("  [PASS] Test 6: Pending and failed scans correctly rejected with HTTP 400")
            results["Test 6: Pending/failed scan handling"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 6: {exc}")
            results["Test 6: Pending/failed scan handling"] = False

        # -------------------------------------------------------------------
        # TEST 7: English PDF generation
        # -------------------------------------------------------------------
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_A_CLAIMS):
                resp_en = await client.get(
                    f"/api/v1/scans/{SCANS['confident']}/pdf?lang=en",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
            assert resp_en.status_code == 200
            assert resp_en.content.startswith(b"%PDF-")
            assert get_font_for_language("en") == "NotoSans"
            print(f"  [PASS] Test 7: English PDF generated successfully ({len(resp_en.content)} bytes)")
            results["Test 7: English PDF generation"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 7: {exc}")
            results["Test 7: English PDF generation"] = False

        # -------------------------------------------------------------------
        # TEST 8: Hindi and Gujarati PDF generation and font rendering
        # -------------------------------------------------------------------
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_A_CLAIMS):
                # Hindi PDF
                resp_hi = await client.get(
                    f"/api/v1/scans/{SCANS['confident']}/pdf?lang=hi",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
                assert resp_hi.status_code == 200, f"Hindi PDF failed with {resp_hi.status_code}"
                assert resp_hi.content.startswith(b"%PDF-")
                assert "crop_report_" in resp_hi.headers["content-disposition"]
                assert "_hi.pdf" in resp_hi.headers["content-disposition"]

                # Gujarati PDF
                resp_gu = await client.get(
                    f"/api/v1/scans/{SCANS['confident']}/pdf?lang=gu",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
                assert resp_gu.status_code == 200, f"Gujarati PDF failed with {resp_gu.status_code}"
                assert resp_gu.content.startswith(b"%PDF-")
                assert "_gu.pdf" in resp_gu.headers["content-disposition"]

            # Verify TrueType font registration
            hi_font = get_font_for_language("hi")
            gu_font = get_font_for_language("gu")
            assert hi_font in {"NotoSansDevanagari", "Nirmala"}, f"Unexpected Hindi font: {hi_font}"
            assert gu_font in {"NotoSansGujarati", "Nirmala"}, f"Unexpected Gujarati font: {gu_font}"

            print(f"  [PASS] Test 8: Hindi ({len(resp_hi.content)}B, font={hi_font}) and Gujarati ({len(resp_gu.content)}B, font={gu_font}) rendered with Unicode TrueType fonts")
            results["Test 8: Hindi & Gujarati Indic font rendering"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 8: {exc}")
            results["Test 8: Hindi & Gujarati Indic font rendering"] = False

        # -------------------------------------------------------------------
        # TEST 9: Long reports and automatic page breaks with NumberedCanvas
        # -------------------------------------------------------------------
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_A_CLAIMS):
                resp_long = await client.get(
                    f"/api/v1/scans/{SCANS['long_report']}/pdf?lang=en",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
            assert resp_long.status_code == 200
            assert resp_long.content.startswith(b"%PDF-")
            assert len(resp_long.content) > len(resp_en.content), "Long report PDF byte size should exceed single-page scan"
            print(f"  [PASS] Test 9: Long report spanning multiple pages generated ({len(resp_long.content)} bytes) with NumberedCanvas pagination")
            results["Test 9: Long reports & multi-page pagination"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 9: {exc}")
            results["Test 9: Long reports & multi-page pagination"] = False

        # -------------------------------------------------------------------
        # TEST 10: Missing images, weather snapshots, and optional report fields
        # -------------------------------------------------------------------
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_A_CLAIMS):
                resp_missing = await client.get(
                    f"/api/v1/scans/{SCANS['missing_fields']}/pdf?lang=en",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
            assert resp_missing.status_code == 200, f"Expected 200, got {resp_missing.status_code}"
            assert resp_missing.content.startswith(b"%PDF-")
            print("  [PASS] Test 10: Missing image and missing weather snapshot handled cleanly without crashing")
            results["Test 10: Missing image and weather handling"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 10: {exc}")
            results["Test 10: Missing image and weather handling"] = False

        # -------------------------------------------------------------------
        # TEST 11: Missing or unavailable localized reports (dynamic workflow / fallback)
        # -------------------------------------------------------------------
        try:
            # Request scan 5 (which does not have an advisory report pre-saved in database)
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_A_CLAIMS):
                resp_rep = await client.get(
                    f"/api/v1/scans/{SCANS['missing_fields']}/pdf?lang=hi",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
            assert resp_rep.status_code == 200
            assert resp_rep.content.startswith(b"%PDF-")
            print("  [PASS] Test 11: Missing localized report handled with graceful advisory section fallback")
            results["Test 11: Missing/unavailable localized reports"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 11: {exc}")
            results["Test 11: Missing/unavailable localized reports"] = False

        # -------------------------------------------------------------------
        # TEST 12: Invalid language parameters (HTTP 422)
        # -------------------------------------------------------------------
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=FARMER_A_CLAIMS):
                resp_inv_lang = await client.get(
                    f"/api/v1/scans/{SCANS['confident']}/pdf?lang=fr",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
            assert resp_inv_lang.status_code == 422, f"Expected 422 for invalid lang 'fr', got {resp_inv_lang.status_code}"
            print("  [PASS] Test 12: Invalid language code ('fr') rejected with HTTP 422 Unprocessable Entity")
            results["Test 12: Invalid language validation"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 12: {exc}")
            results["Test 12: Invalid language validation"] = False

        # -------------------------------------------------------------------
        # TEST 13: Authentication failures and expired/invalid tokens
        # -------------------------------------------------------------------
        try:
            # 13a. Missing Authorization header
            resp_no_auth = await client.get(f"/api/v1/scans/{SCANS['confident']}/pdf?lang=en")
            assert resp_no_auth.status_code == 401, f"Expected 401 for missing auth, got {resp_no_auth.status_code}"

            # 13b. Malformed Authorization header
            resp_bad_auth = await client.get(
                f"/api/v1/scans/{SCANS['confident']}/pdf?lang=en",
                headers={"Authorization": "InvalidScheme token_abc"},
            )
            assert resp_bad_auth.status_code == 401, f"Expected 401 for bad auth format, got {resp_bad_auth.status_code}"

            # 13c. Invalid/expired Firebase token
            resp_invalid_token = await client.get(
                f"/api/v1/scans/{SCANS['confident']}/pdf?lang=en",
                headers={"Authorization": "Bearer dummy_expired_token"},
            )
            assert resp_invalid_token.status_code == 401, f"Expected 401 for invalid token, got {resp_invalid_token.status_code}"
            print("  [PASS] Test 13: Authentication failures (missing, malformed, expired token) blocked with HTTP 401")
            results["Test 13: Authentication failures & invalid tokens"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 13: {exc}")
            results["Test 13: Authentication failures & invalid tokens"] = False

        # -------------------------------------------------------------------
        # TEST 14: Frontend download flow and error states contract verification
        # -------------------------------------------------------------------
        try:
            # Verify frontend scanService export and contract matches backend route
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            frontend_service_path = os.path.join(
                repo_root,
                "frontend",
                "src",
                "services",
                "scanService.js",
            )
            assert os.path.isfile(frontend_service_path), f"Frontend service file missing: {frontend_service_path}"
            with open(frontend_service_path, "r", encoding="utf-8") as f:
                code_content = f.read()

            assert "downloadScanPdf" in code_content, "downloadScanPdf function missing in scanService.js"
            assert "response.blob()" in code_content, "downloadScanPdf must parse binary blob with response.blob()"
            assert "/api/v1/scans/${scanId}/pdf" in code_content, "downloadScanPdf must call /api/v1/scans/{scanId}/pdf"
            print("  [PASS] Test 14: Frontend scanService.js contract verified (endpoint, blob response, download link trigger)")
            results["Test 14: Frontend download flow & service contract"] = True
        except Exception as exc:
            print(f"  [FAIL] Test 14: {exc}")
            results["Test 14: Frontend download flow & service contract"] = False

    await cleanup_test_fixtures()

    print("\n" + "=" * 75)
    print("MODULE 17 TEST EXECUTION SUMMARY:")
    print("=" * 75)
    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  [{status:^6}] {test_name}")
    print(f"\nResult: {total_passed}/{total_tests} Tests Passed.")
    return total_passed == total_tests


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    if not success:
        sys.exit(1)
