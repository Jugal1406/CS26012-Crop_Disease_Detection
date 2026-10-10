# -*- coding: utf-8 -*-
"""
backend/test_farm_flow.py
=========================
Integration tests for Module 12: Farm Profile & Location.

Validates:
  1. Unauthorized access blocked (HTTP 401)
  2. Farm creation with valid metadata & optional GPS
  3. Farm creation without GPS coordinates (optional GPS)
  4. Multiple farms per user (list returns all active farms)
  5. Farm update (PUT /farms/{farm_id})
  6. Soft deactivation (DELETE /farms/{farm_id}) hides from list
  7. Strict tenant isolation (Farmer B cannot GET/PUT/DELETE Farmer A's farm -> 404)
  8. Parameter injection defense: payload 'user_id' ignored
  9. Validation gates:
     - Negative area rejected (HTTP 422)
     - Latitude out of range [-90, 90] rejected (HTTP 422)
     - Longitude out of range [-180, 180] rejected (HTTP 422)
     - Empty name / village / district / state rejected (HTTP 422)
 10. Route aliases (/farms and /api/v1/farms)
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
from models import User, Farm

TEST_FARMER_A_UID = "test_farmer_a_farm_uid_1201"
TEST_FARMER_B_UID = "test_farmer_b_farm_uid_1202"


async def setup_test_users():
    async with AsyncSessionLocal() as session:
        # Clean existing test data
        await session.execute(
            delete(User).where(
                User.auth_provider_user_id.in_([TEST_FARMER_A_UID, TEST_FARMER_B_UID])
            )
        )
        await session.commit()

        user_a = User(
            id=uuid.uuid4(),
            auth_provider="firebase",
            auth_provider_user_id=TEST_FARMER_A_UID,
            display_name="Ramesh Patel",
            email="ramesh@example.com",
            phone_number="+919876543210",
            preferred_language="en",
        )
        user_b = User(
            id=uuid.uuid4(),
            auth_provider="firebase",
            auth_provider_user_id=TEST_FARMER_B_UID,
            display_name="Suresh Kumar",
            email="suresh@example.com",
            phone_number="+919811122233",
            preferred_language="hi",
        )
        session.add_all([user_a, user_b])
        await session.commit()
        return user_a.id, user_b.id


async def cleanup_test_users():
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(User).where(
                User.auth_provider_user_id.in_([TEST_FARMER_A_UID, TEST_FARMER_B_UID])
            )
        )
        await session.commit()


async def run_farm_tests():
    print("\n" + "=" * 70)
    print("      MODULE 12 - FARM PROFILE & LOCATION INTEGRATION TESTS")
    print("=" * 70)

    transport = ASGITransport(app=app)
    results = []

    user_a_id, user_b_id = await setup_test_users()

    mock_claims_a = {
        "uid": TEST_FARMER_A_UID,
        "name": "Ramesh Patel",
        "email": "ramesh@example.com",
    }
    mock_claims_b = {
        "uid": TEST_FARMER_B_UID,
        "name": "Suresh Kumar",
        "email": "suresh@example.com",
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # TEST 1: Unauthenticated request rejected (HTTP 401)
        try:
            res_unauth = await client.get("/api/v1/farms")
            assert res_unauth.status_code == 401
            print("  [PASS] Test 1: Unauthorized access blocked with HTTP 401")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 1: {exc}")
            results.append(False)

        # TEST 2: Authenticated Farmer A creates Farm 1 with GPS
        farm_1_id = None
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_a):
                payload_1 = {
                    "name": "Main Farm",
                    "village": "Petlad",
                    "district": "Anand",
                    "state": "Gujarat",
                    "area_hectares": 2.5,
                    "latitude": 22.4731,
                    "longitude": 72.8028,
                }
                res_create = await client.post(
                    "/api/v1/farms",
                    json=payload_1,
                    headers={"Authorization": "Bearer token_a"},
                )
                assert res_create.status_code == 201, f"Expected 201, got {res_create.status_code}: {res_create.text}"
                data_create = res_create.json()
                farm_1_id = data_create["id"]
                assert data_create["name"] == "Main Farm"
                assert data_create["village"] == "Petlad"
                assert data_create["district"] == "Anand"
                assert data_create["state"] == "Gujarat"
                assert data_create["area_hectares"] == 2.5
                assert abs(data_create["latitude"] - 22.4731) < 0.001
                assert abs(data_create["longitude"] - 72.8028) < 0.001
                assert data_create["has_location"] is True
                assert data_create["is_active"] is True

            print("  [PASS] Test 2: Farm 1 created with metadata and GPS coordinates")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 2: {exc}")
            results.append(False)

        # TEST 3: Authenticated Farmer A creates Farm 2 without GPS coordinates (GPS is optional)
        farm_2_id = None
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_a):
                payload_2 = {
                    "name": "Family Farm",
                    "village": "Mogri",
                    "district": "Anand",
                    "state": "Gujarat",
                    "area_hectares": 1.2,
                }
                res_create_2 = await client.post(
                    "/api/v1/farms",
                    json=payload_2,
                    headers={"Authorization": "Bearer token_a"},
                )
                assert res_create_2.status_code == 201
                data_create_2 = res_create_2.json()
                farm_2_id = data_create_2["id"]
                assert data_create_2["name"] == "Family Farm"
                assert data_create_2["latitude"] is None
                assert data_create_2["longitude"] is None
                assert data_create_2["has_location"] is False

            print("  [PASS] Test 3: Farm 2 created without GPS (GPS is strictly optional)")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 3: {exc}")
            results.append(False)

        # TEST 4: Multiple Farms listed for Farmer A
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_a):
                res_list = await client.get(
                    "/api/v1/farms",
                    headers={"Authorization": "Bearer token_a"},
                )
                assert res_list.status_code == 200
                list_data = res_list.json()
                assert list_data["count"] == 2
                farm_names = [f["name"] for f in list_data["farms"]]
                assert "Main Farm" in farm_names
                assert "Family Farm" in farm_names

            print("  [PASS] Test 4: Multiple farms retrieved successfully for user")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 4: {exc}")
            results.append(False)

        # TEST 5: Update Farm 1 (PUT /api/v1/farms/{farm_id})
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_a):
                update_payload = {
                    "name": "Main Farm Updated",
                    "area_hectares": 3.0,
                }
                res_update = await client.put(
                    f"/api/v1/farms/{farm_1_id}",
                    json=update_payload,
                    headers={"Authorization": "Bearer token_a"},
                )
                assert res_update.status_code == 200
                data_update = res_update.json()
                assert data_update["name"] == "Main Farm Updated"
                assert data_update["area_hectares"] == 3.0
                assert data_update["village"] == "Petlad"  # Unchanged fields preserved

            print("  [PASS] Test 5: Farm updated successfully")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 5: {exc}")
            results.append(False)

        # TEST 6: Parameter injection defense (payload 'user_id' ignored)
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_a):
                malicious_payload = {
                    "name": "Malicious Spoof Farm",
                    "village": "Unknown",
                    "district": "Unknown",
                    "state": "Gujarat",
                    "user_id": str(user_b_id),  # Attempt to spoof ownership to Farmer B
                }
                res_spoof = await client.post(
                    "/api/v1/farms",
                    json=malicious_payload,
                    headers={"Authorization": "Bearer token_a"},
                )
                assert res_spoof.status_code == 201
                spoof_farm_id = res_spoof.json()["id"]

            # Verify that Farmer B does NOT see this farm
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_b):
                res_b_list = await client.get(
                    "/api/v1/farms",
                    headers={"Authorization": "Bearer token_b"},
                )
                assert res_b_list.status_code == 200
                b_farm_ids = [f["id"] for f in res_b_list.json()["farms"]]
                assert spoof_farm_id not in b_farm_ids

            print("  [PASS] Test 6: Parameter injection defense verified (client user_id ignored)")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 6: {exc}")
            results.append(False)

        # TEST 7: Cross-tenant isolation (Farmer B attempts to access/update/delete Farmer A's farm)
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_b):
                # GET Farmer A's farm
                res_cross_get = await client.get(
                    f"/api/v1/farms/{farm_1_id}",
                    headers={"Authorization": "Bearer token_b"},
                )
                assert res_cross_get.status_code == 404, f"Expected 404, got {res_cross_get.status_code}"

                # PUT Farmer A's farm
                res_cross_put = await client.put(
                    f"/api/v1/farms/{farm_1_id}",
                    json={"name": "Hacked Farm"},
                    headers={"Authorization": "Bearer token_b"},
                )
                assert res_cross_put.status_code == 404, f"Expected 404, got {res_cross_put.status_code}"

                # DELETE Farmer A's farm
                res_cross_del = await client.delete(
                    f"/api/v1/farms/{farm_1_id}",
                    headers={"Authorization": "Bearer token_b"},
                )
                assert res_cross_del.status_code == 404, f"Expected 404, got {res_cross_del.status_code}"

            print("  [PASS] Test 7: Strict tenant isolation enforced (cross-user access returns 404)")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 7: {exc}")
            results.append(False)

        # TEST 8: Validation rejections (area <= 0, latitude out of bounds, longitude out of bounds, empty name)
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_a):
                # 8a: Negative area
                res_bad_area = await client.post(
                    "/api/v1/farms",
                    json={"name": "X", "village": "Y", "district": "Z", "state": "W", "area_hectares": -2.0},
                    headers={"Authorization": "Bearer token_a"},
                )
                assert res_bad_area.status_code == 422, f"Expected 422 for negative area, got {res_bad_area.status_code}"

                # 8b: Invalid latitude (> 90)
                res_bad_lat = await client.post(
                    "/api/v1/farms",
                    json={"name": "X", "village": "Y", "district": "Z", "state": "W", "latitude": 95.0},
                    headers={"Authorization": "Bearer token_a"},
                )
                assert res_bad_lat.status_code == 422, f"Expected 422 for lat > 90, got {res_bad_lat.status_code}"

                # 8c: Invalid longitude (< -180)
                res_bad_lon = await client.post(
                    "/api/v1/farms",
                    json={"name": "X", "village": "Y", "district": "Z", "state": "W", "longitude": -195.0},
                    headers={"Authorization": "Bearer token_a"},
                )
                assert res_bad_lon.status_code == 422, f"Expected 422 for lon < -180, got {res_bad_lon.status_code}"

                # 8d: Empty whitespace name
                res_blank_name = await client.post(
                    "/api/v1/farms",
                    json={"name": "   ", "village": "Y", "district": "Z", "state": "W"},
                    headers={"Authorization": "Bearer token_a"},
                )
                assert res_blank_name.status_code == 422, f"Expected 422 for blank name, got {res_blank_name.status_code}"

            print("  [PASS] Test 8: Validation gates rejected invalid area, coordinates & blank fields (HTTP 422)")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 8: {exc}")
            results.append(False)

        # TEST 9: Soft deactivation hides farm from active list
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_a):
                res_del = await client.delete(
                    f"/api/v1/farms/{farm_2_id}",
                    headers={"Authorization": "Bearer token_a"},
                )
                assert res_del.status_code == 200
                assert res_del.json()["status"] == "success"

                # Check list no longer includes farm_2
                res_list_after = await client.get(
                    "/api/v1/farms",
                    headers={"Authorization": "Bearer token_a"},
                )
                remaining_ids = [f["id"] for f in res_list_after.json()["farms"]]
                assert farm_2_id not in remaining_ids

            print("  [PASS] Test 9: Soft deactivation successful; deactivated farm omitted from active list")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 9: {exc}")
            results.append(False)

        # TEST 10: Route aliases (/farms and /api/v1/farms)
        try:
            with patch("dependencies.verify_firebase_id_token", return_value=mock_claims_a):
                res_alias = await client.get(
                    "/farms",
                    headers={"Authorization": "Bearer token_a"},
                )
                assert res_alias.status_code == 200
                assert "farms" in res_alias.json()

            print("  [PASS] Test 10: Root route alias /farms functional")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 10: {exc}")
            results.append(False)

    await cleanup_test_users()
    await engine.dispose()

    print("-" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Summary: {passed}/{total} Module 12 Farm integration tests passed.")
    if passed == total:
        print("[SUCCESS] Module 12 Farm Profile & Location is fully verified on the backend!")
        return 0
    else:
        print("[FAIL] Some farm integration tests failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_farm_tests())
    sys.exit(exit_code)
