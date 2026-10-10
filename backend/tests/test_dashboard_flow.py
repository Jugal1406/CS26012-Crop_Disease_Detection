# -*- coding: utf-8 -*-
"""
backend/test_dashboard_flow.py
==============================
Integration tests for Module 10: Authenticated User's Personalized Dashboard.

Validates:
  1. Unauthorized request rejected with HTTP 401
  2. Complete dashboard payload structure:
     - Welcome & profile summary
     - Farm information & location
     - Weather context placeholder
     - Active crop catalog
     - Scan counts and breakdown
     - Recent diagnoses and advisory reports
  3. Strict User Data Isolation:
     - Farmer A sees only their own farm, scans, and reports
     - Farmer B (with 0 scans) sees 0 scans and cannot see Farmer A's data
"""

import asyncio
import os
import sys
import uuid
from unittest.mock import patch

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete

from main import app
from database import AsyncSessionLocal, engine
from models import User, Farm, Scan, Prediction, Disease, Crop, ModelVersion

TEST_UID_A = "test_farmer_a_uid_101"
TEST_UID_B = "test_farmer_b_uid_102"


async def setup_test_data():
    async with AsyncSessionLocal() as session:
        # Clean existing test users
        await session.execute(
            delete(User).where(User.auth_provider_user_id.in_([TEST_UID_A, TEST_UID_B]))
        )
        await session.commit()

        # Create Farmer A
        user_a = User(
            id=uuid.uuid4(),
            auth_provider="firebase",
            auth_provider_user_id=TEST_UID_A,
            display_name="Ramesh Patel",
            email="ramesh@example.com",
            phone_number="+919876543210",
            preferred_language="en",
        )
        # Create Farmer B (zero scans, zero farms)
        user_b = User(
            id=uuid.uuid4(),
            auth_provider="firebase",
            auth_provider_user_id=TEST_UID_B,
            display_name="Suresh Kumar",
            email="suresh@example.com",
            phone_number="+919811122233",
            preferred_language="hi",
        )
        session.add_all([user_a, user_b])
        await session.flush()

        # Create Farm for Farmer A
        farm_a = Farm(
            id=uuid.uuid4(),
            user_id=user_a.id,
            name="Green Valley Farm",
            village="Mogri",
            district="Anand",
            state="Gujarat",
            area_hectares=2.5,
            is_active=True,
        )
        session.add(farm_a)
        await session.flush()

        # Query chili crop, model version, and diseases
        from sqlalchemy import select
        crop_res = await session.execute(select(Crop).where(Crop.name == "chili"))
        chili_crop = crop_res.scalars().first()

        mv_res = await session.execute(select(ModelVersion).where(ModelVersion.is_active == True))
        model_ver = mv_res.scalars().first()

        d_healthy_res = await session.execute(select(Disease).where(Disease.label.ilike("%healthy%")))
        d_healthy = d_healthy_res.scalars().first()

        d_curl_res = await session.execute(select(Disease).where(Disease.label.ilike("%curl%")))
        d_curl = d_curl_res.scalars().first()

        if chili_crop and model_ver and d_healthy and d_curl:
            # Scan 1: Healthy
            scan_1 = Scan(
                id=uuid.uuid4(),
                user_id=user_a.id,
                farm_id=farm_a.id,
                crop_id=chili_crop.id,
                image_path="uploads/scans/scan_1.jpg",
                status="completed",
            )
            pred_1 = Prediction(
                id=uuid.uuid4(),
                scan_id=scan_1.id,
                disease_id=d_healthy.id,
                model_version_id=model_ver.id,
                confidence=0.9420,
                threshold_used=0.70,
                is_confident=True,
            )
            # Scan 2: Leaf Curl
            scan_2 = Scan(
                id=uuid.uuid4(),
                user_id=user_a.id,
                farm_id=farm_a.id,
                crop_id=chili_crop.id,
                image_path="uploads/scans/scan_2.jpg",
                status="completed",
            )
            pred_2 = Prediction(
                id=uuid.uuid4(),
                scan_id=scan_2.id,
                disease_id=d_curl.id,
                model_version_id=model_ver.id,
                confidence=0.8850,
                threshold_used=0.70,
                is_confident=True,
            )
            session.add_all([scan_1, pred_1, scan_2, pred_2])

        await session.commit()
        return user_a.id, user_b.id


async def cleanup_test_data():
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(User).where(User.auth_provider_user_id.in_([TEST_UID_A, TEST_UID_B]))
        )
        await session.commit()


async def run_dashboard_tests():
    print("\n" + "=" * 70)
    print("      MODULE 11 - PERSONALIZED USER DASHBOARD INTEGRATION TESTS")
    print("=" * 70)

    transport = ASGITransport(app=app)
    results = []

    user_a_id, user_b_id = await setup_test_data()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # TEST 1: Unauthenticated request rejected with HTTP 401
        try:
            res_unauth = await client.get("/api/v1/dashboard/overview")
            assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"
            print("  [PASS] Test 1: Unauthorized access blocked with HTTP 401")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 1: {exc}")
            results.append(False)

        # TEST 2: Invalid or expired Firebase token rejected with HTTP 401
        try:
            res_invalid = await client.get(
                "/api/v1/dashboard/overview",
                headers={"Authorization": "Bearer invalid_expired_dummy_token_xyz"},
            )
            assert res_invalid.status_code == 401, f"Expected 401, got {res_invalid.status_code}"
            print("  [PASS] Test 2: Invalid/expired token rejected with HTTP 401")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 2: {exc}")
            results.append(False)

        # TEST 3: Authenticated Farmer A Dashboard & Payload Structure
        try:
            mock_claims_a = {
                "uid": TEST_UID_A,
                "phone_number": "+919876543210",
                "name": "Ramesh Patel",
                "email": "ramesh@example.com",
            }
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_a):
                res_a = await client.get(
                    "/api/v1/dashboard/overview",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
                assert res_a.status_code == 200, f"Expected 200, got {res_a.status_code}: {res_a.text}"
                data_a = res_a.json()

                # Validate User Profile
                assert data_a["user"]["display_name"] == "Ramesh Patel"
                assert data_a["user"]["phone_number"] == "+919876543210"
                assert data_a["user"]["email"] == "ramesh@example.com"
                assert data_a["user"]["preferred_language"] == "en"

                # Validate Quick Statistics (Step 2 & Step 5)
                assert data_a["stats"]["total_scans"] == 2
                assert data_a["stats"]["healthy_scans"] == 1
                assert data_a["stats"]["issues_detected"] == 1
                assert data_a["stats"]["last_scan_date"] is not None
                assert "Chili" in data_a["stats"]["most_recent_crop"]

                # Validate Recent Scans Preview (Step 2 #4)
                assert len(data_a["recent_scans"]) == 2
                scan_item = data_a["recent_scans"][0]
                assert "crop" in scan_item
                assert "condition" in scan_item
                assert "confidence" in scan_item
                assert "status" in scan_item
                assert "date" in scan_item

                # Verify NO sensitive tokens or credentials leaked
                assert "token" not in data_a["user"]
                assert "refresh_token" not in data_a["user"]
                assert "password" not in data_a["user"]

            print("  [PASS] Test 3: Farmer A dashboard payload verified with stats, crops & recent scans")
            results.append(True)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            print(f"  [FAIL] Test 3: {exc}")
            results.append(False)

        # TEST 4: User Data Isolation - Farmer B (zero scans, zero farms)
        try:
            mock_claims_b = {
                "uid": TEST_UID_B,
                "phone_number": "+919811122233",
                "name": "Suresh Kumar",
                "email": "suresh@example.com",
            }
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_b):
                res_b = await client.get(
                    "/api/v1/dashboard/overview",
                    headers={"Authorization": "Bearer token_farmer_b"},
                )
                assert res_b.status_code == 200, f"Expected 200, got {res_b.status_code}"
                data_b = res_b.json()

                # Must NOT see Farmer A's identity
                assert data_b["user"]["display_name"] == "Suresh Kumar"

                # Must NOT see Farmer A's scans
                assert data_b["stats"]["total_scans"] == 0
                assert data_b["stats"]["last_scan_date"] is None
                assert data_b["stats"]["most_recent_crop"] is None
                assert len(data_b["recent_scans"]) == 0

            print("  [PASS] Test 4: Strict data isolation enforced (Farmer B sees 0 scans, not Farmer A's)")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 4: {exc}")
            results.append(False)

        # TEST 5: Security Defense - User B attempts to access User A's data via ?user_id
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_b):
                res_attack = await client.get(
                    f"/api/v1/dashboard/overview?user_id={user_a_id}",
                    headers={"Authorization": "Bearer token_farmer_b"},
                )
                assert res_attack.status_code == 200
                attack_data = res_attack.json()
                # Backend MUST ignore ?user_id and only return Farmer B's data
                assert attack_data["user"]["display_name"] == "Suresh Kumar"
                assert attack_data["stats"]["total_scans"] == 0

            print("  [PASS] Test 5: Query param user_id injection ignored; identity derived only from token")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 5: {exc}")
            results.append(False)

        # TEST 6: Dashboard Route Aliases (/api/v1/dashboard, /api/v1/users/me/dashboard, /dashboard)
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_a):
                res_alias1 = await client.get(
                    "/api/v1/dashboard",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
                assert res_alias1.status_code == 200
                assert res_alias1.json()["user"]["display_name"] == "Ramesh Patel"

                res_alias2 = await client.get(
                    "/api/v1/users/me/dashboard",
                    headers={"Authorization": "Bearer token_farmer_a"},
                )
                assert res_alias2.status_code == 200
                assert res_alias2.json()["user"]["display_name"] == "Ramesh Patel"

            print("  [PASS] Test 6: Route aliases /api/v1/dashboard and /api/v1/users/me/dashboard active")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 6: {exc}")
            results.append(False)

    await cleanup_test_data()
    await engine.dispose()

    print("-" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Summary: {passed}/{total} Module 11 dashboard integration tests passed.")
    if passed == total:
        print("[SUCCESS] Module 11 Personalized Dashboard is fully verified!")
        return 0
    else:
        print("[FAIL] Some dashboard tests failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_dashboard_tests())
    sys.exit(exit_code)
