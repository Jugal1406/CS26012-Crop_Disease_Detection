# -*- coding: utf-8 -*-
"""
backend/test_auth_flow.py
=========================
Integration tests for Authentication & PostgreSQL user synchronization with Clerk.
Uses httpx.AsyncClient with ASGITransport to properly test async FastAPI routes
in a single unified event loop without asyncpg connection pool collisions.
"""

import asyncio
import os
import sys
from unittest.mock import patch

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, delete

from main import app
from database import AsyncSessionLocal, engine
from models import User
from repositories.user_repository import UserRepository
from services.auth_service import AuthService

TEST_UID_CLERK_1 = "user_test_clerk_farmer_001"
TEST_UID_CLERK_2 = "user_test_clerk_farmer_002"


async def cleanup_test_users():
    async with AsyncSessionLocal() as session:
        stmt = delete(User).where(
            User.auth_provider_user_id.in_([TEST_UID_CLERK_1, TEST_UID_CLERK_2])
        )
        await session.execute(stmt)
        await session.commit()


async def run_all_tests():
    print("\n" + "=" * 70)
    print("      AUTHENTICATION & CLERK USER SYNC TEST SUITE")
    print("=" * 70)

    transport = ASGITransport(app=app)
    results = []

    # Cleanup before starting
    await cleanup_test_users()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # -------------------------------------------------------------------
        # Test 1: Security gates (Reject missing & invalid tokens)
        # -------------------------------------------------------------------
        try:
            # Missing header
            res1 = await client.post("/api/v1/auth/sync", json={"display_name": "Test"})
            assert res1.status_code == 401, f"Expected 401, got {res1.status_code}"

            res_me1 = await client.get("/api/v1/auth/me")
            assert res_me1.status_code == 401, f"Expected 401, got {res_me1.status_code}"

            # Invalid format
            res_bad = await client.get("/api/v1/auth/me", headers={"Authorization": "Basic 12345"})
            assert res_bad.status_code == 401, f"Expected 401, got {res_bad.status_code}"

            # Invalid signature
            res_forged = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer forged_fake_token"})
            assert res_forged.status_code == 401, f"Expected 401, got {res_forged.status_code}"

            print("  [PASS] Test 1: Security gates rejected missing & invalid tokens (HTTP 401)")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 1: {exc}")
            results.append(False)

        # -------------------------------------------------------------------
        # Test 2: Clerk User Sync & Duplicate Prevention (Repository Layer)
        # -------------------------------------------------------------------
        try:
            async with AsyncSessionLocal() as session:
                user_repo = UserRepository(session)

                # First sign in (signup with display name)
                user1 = await user_repo.sync_clerk_user(
                    clerk_id=TEST_UID_CLERK_1,
                    display_name="Ramesh Patel",
                    email="ramesh@example.com",
                )
                await session.commit()

                assert user1.id is not None
                assert user1.auth_provider == "clerk"
                assert user1.auth_provider_user_id == TEST_UID_CLERK_1
                assert user1.display_name == "Ramesh Patel"
                assert user1.email == "ramesh@example.com"

                # Repeat sign in (login without name)
                user2 = await user_repo.sync_clerk_user(
                    clerk_id=TEST_UID_CLERK_1,
                    display_name=None,
                    email="ramesh@example.com",
                )
                await session.commit()

                # Must be same user PK, not duplicate row
                assert user1.id == user2.id, "Duplicate user created on second login!"
                assert user2.display_name == "Ramesh Patel"

                # Check row count
                stmt = select(User).where(User.auth_provider_user_id == TEST_UID_CLERK_1)
                count_res = await session.execute(stmt)
                all_users = count_res.scalars().all()
                assert len(all_users) == 1, f"Expected 1 user in DB, found {len(all_users)}"

            print("  [PASS] Test 2: New Clerk user synced & duplicates prevented on repeat login")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 2: {exc}")
            results.append(False)

        # -------------------------------------------------------------------
        # Test 3: Verified Email User Sync
        # -------------------------------------------------------------------
        try:
            async with AsyncSessionLocal() as session:
                user_repo = UserRepository(session)

                user = await user_repo.sync_clerk_user(
                    clerk_id=TEST_UID_CLERK_2,
                    display_name="Sunita Sharma",
                    email="sunita@example.com",
                )
                await session.commit()

                assert user.id is not None
                assert user.auth_provider == "clerk"
                assert user.auth_provider_user_id == TEST_UID_CLERK_2
                assert user.display_name == "Sunita Sharma"
                assert user.email == "sunita@example.com"

            print("  [PASS] Test 3: Verified email user created with Clerk identity")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 3: {exc}")
            results.append(False)

        # -------------------------------------------------------------------
        # Test 4: End-to-End API Router (/api/v1/auth/sync & /api/v1/auth/me)
        # -------------------------------------------------------------------
        try:
            mock_claims = {
                "uid": TEST_UID_CLERK_1,
                "user_id": TEST_UID_CLERK_1,
                "claims": {"sub": TEST_UID_CLERK_1, "exp": 9999999999},
            }
            mock_profile = {
                "user_id": TEST_UID_CLERK_1,
                "email": "ramesh@example.com",
                "display_name": "Ramesh Patel Updated",
                "phone_number": None,
            }

            with patch("services.auth_service.verify_clerk_token", return_value=mock_claims), \
                 patch("services.auth_service.get_clerk_user_profile", return_value=mock_profile), \
                 patch("dependencies.verify_clerk_token", return_value=mock_claims):

                # POST /api/v1/auth/sync
                res_sync = await client.post(
                    "/api/v1/auth/sync",
                    headers={"Authorization": "Bearer mock_valid_clerk_token_123"},
                    json={"display_name": "Ramesh Patel Updated"},
                )
                assert res_sync.status_code == 200, f"Expected 200, got {res_sync.status_code}: {res_sync.text}"
                data = res_sync.json()
                assert data["status"] == "success"
                assert data["user"]["auth_provider_user_id"] == TEST_UID_CLERK_1
                assert data["user"]["display_name"] == "Ramesh Patel Updated"
                assert data["user"]["email"] == "ramesh@example.com"

                # GET /api/v1/auth/me
                res_me = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": "Bearer mock_valid_clerk_token_123"},
                )
                assert res_me.status_code == 200, f"Expected 200, got {res_me.status_code}: {res_me.text}"
                me_data = res_me.json()
                assert me_data["auth_provider_user_id"] == TEST_UID_CLERK_1
                assert me_data["display_name"] == "Ramesh Patel Updated"

            print("  [PASS] Test 4: AuthService & /api/v1/auth API routes executed successfully with Clerk")
            results.append(True)
        except Exception as exc:
            print(f"  [FAIL] Test 4: {exc}")
            results.append(False)

    # Cleanup after finishing
    await cleanup_test_users()
    await engine.dispose()

    print("-" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Summary: {passed}/{total} tests passed.")
    if passed == total:
        print("[SUCCESS] Clerk Authentication & User Synchronization is fully verified!")
        return 0
    else:
        print("[FAIL] Some tests failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
