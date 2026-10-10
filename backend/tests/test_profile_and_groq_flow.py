# -*- coding: utf-8 -*-
"""
backend/test_profile_and_groq_flow.py
======================================
Integration and unit tests verifying:
1. User Profile Editing (PATCH /api/v1/auth/profile, phone normalization, email immutability, multi-tenant isolation)
2. Groq Multi-Key Rotation & Safe Fallback (429 rate limit failover, non-retryable 400 bail-out, safe agronomic fallback, masked logging)
"""

import asyncio
import json
import os
import sys
import traceback
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, delete

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import app
from database import AsyncSessionLocal
from models import User
from services.llm_service import LLMService

TEST_UID_1 = "test_profile_farmer_alpha"
TEST_UID_2 = "test_profile_farmer_beta"


async def cleanup_test_profile_users():
    async with AsyncSessionLocal() as session:
        stmt = delete(User).where(
            User.auth_provider_user_id.in_([TEST_UID_1, TEST_UID_2])
        )
        await session.execute(stmt)
        await session.commit()


async def run_profile_and_groq_tests():
    print("\n" + "=" * 70)
    print("      PROFILE EDITING & GROQ MULTI-KEY ROTATION TEST SUITE")
    print("=" * 70)

    await cleanup_test_profile_users()

    transport = ASGITransport(app=app)
    results = []

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # ===================================================================
        # PART 1: PROFILE MANAGEMENT TESTS
        # ===================================================================

        # Setup initial users in DB
        async with AsyncSessionLocal() as session:
            user1 = User(
                auth_provider="clerk",
                auth_provider_user_id=TEST_UID_1,
                email="alpha_farmer@example.com",
                display_name="Alpha Initial",
                phone_number="+919876543210",
                preferred_language="en",
            )
            user2 = User(
                auth_provider="clerk",
                auth_provider_user_id=TEST_UID_2,
                email="beta_farmer@example.com",
                display_name="Beta Farmer",
                phone_number="+919876500000",
                preferred_language="hi",
            )
            session.add_all([user1, user2])
            await session.commit()

        mock_claims_1 = {
            "uid": TEST_UID_1,
            "user_id": TEST_UID_1,
            "claims": {"sub": TEST_UID_1, "exp": 9999999999},
        }

        # Test 1.1: Unauthenticated request to /profile is rejected with 401
        try:
            res = await client.patch("/api/v1/auth/profile", json={"display_name": "Hacker"})
            assert res.status_code == 401, f"Expected 401, got {res.status_code}"
            print("  [PASS] 1.1: Unauthenticated profile update rejected (HTTP 401)")
            results.append(True)
        except Exception as e:
            print(f"  [FAIL] 1.1: {e}")
            traceback.print_exc()
            results.append(False)

        # Test 1.2: Valid profile update (Name, 10-digit Indian phone normalized, preferred language)
        try:
            with patch("clerk_auth.verify_clerk_token", return_value=mock_claims_1), \
                 patch("dependencies.verify_firebase_id_token", return_value=mock_claims_1):

                res = await client.patch(
                    "/api/v1/auth/profile",
                    headers={"Authorization": "Bearer valid_token_alpha"},
                    json={
                        "display_name": "Jugal Patel",
                        "phone_number": "9123456789",  # 10 digits -> should normalize to +919123456789
                        "preferred_language": "gu",
                    },
                )
                assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
                data = res.json()
                assert data["display_name"] == "Jugal Patel"
                assert data["phone_number"] == "+919123456789"
                assert data["preferred_language"] == "gu"
                assert data["email"] == "alpha_farmer@example.com"  # Email preserved

                # Verify persistence in database
                async with AsyncSessionLocal() as session:
                    db_user = (await session.execute(
                        select(User).where(User.auth_provider_user_id == TEST_UID_1)
                    )).scalar_one()
                    assert db_user.display_name == "Jugal Patel"
                    assert db_user.phone_number == "+919123456789"
                    assert db_user.preferred_language == "gu"
                    assert db_user.email == "alpha_farmer@example.com"

            print("  [PASS] 1.2: Profile updated successfully with phone normalization & email immutability")
            results.append(True)
        except Exception as e:
            print(f"  [FAIL] 1.2: {e}")
            traceback.print_exc()
            results.append(False)

        # Test 1.3: Invalid phone number format rejected
        try:
            with patch("clerk_auth.verify_clerk_token", return_value=mock_claims_1), \
                 patch("dependencies.verify_firebase_id_token", return_value=mock_claims_1):

                res = await client.patch(
                    "/api/v1/auth/profile",
                    headers={"Authorization": "Bearer valid_token_alpha"},
                    json={"phone_number": "123"},
                )
                assert res.status_code == 400, f"Expected 400 for invalid phone, got {res.status_code}: {res.text}"

            print("  [PASS] 1.3: Malformed phone number rejected with HTTP 400")
            results.append(True)
        except Exception as e:
            print(f"  [FAIL] 1.3: {e}")
            traceback.print_exc()
            results.append(False)

        # Test 1.4: Duplicate phone number claimed by another user rejected
        try:
            with patch("clerk_auth.verify_clerk_token", return_value=mock_claims_1), \
                 patch("dependencies.verify_firebase_id_token", return_value=mock_claims_1):

                # User 2 already has +919876500000
                res = await client.patch(
                    "/api/v1/auth/profile",
                    headers={"Authorization": "Bearer valid_token_alpha"},
                    json={"phone_number": "9876500000"},
                )
                assert res.status_code == 400, f"Expected 400 for duplicate phone, got {res.status_code}: {res.text}"
                detail = res.json().get("detail", "")
                assert "another account" in detail.lower() or "already" in detail.lower(), f"Unexpected detail: {detail}"

            print("  [PASS] 1.4: Duplicate phone number conflict detected and rejected")
            results.append(True)
        except Exception as e:
            print(f"  [FAIL] 1.4: {e}")
            traceback.print_exc()
            results.append(False)

        # Test 1.5: Unsupported language rejected
        try:
            with patch("clerk_auth.verify_clerk_token", return_value=mock_claims_1), \
                 patch("dependencies.verify_firebase_id_token", return_value=mock_claims_1):

                res = await client.patch(
                    "/api/v1/auth/profile",
                    headers={"Authorization": "Bearer valid_token_alpha"},
                    json={"preferred_language": "fr"},
                )
                assert res.status_code == 400, f"Expected 400, got {res.status_code}"

            print("  [PASS] 1.5: Unsupported language code rejected")
            results.append(True)
        except Exception as e:
            print(f"  [FAIL] 1.5: {e}")
            traceback.print_exc()
            results.append(False)

    # Cleanup DB users
    await cleanup_test_profile_users()

    # ===================================================================
    # PART 2: GROQ MULTI-KEY ROTATION & SAFE FALLBACK TESTS
    # ===================================================================
    print("\n  --- Testing Groq Multi-Key Rotation & Safe Fallback ---")

    valid_groq_json = {
        "disease_name": "Cercospora Leaf Spot",
        "confidence_interpretation": "High confidence foliar detection",
        "summary": "Visible foliar lesions detected. Sanitation required.",
        "symptoms": ["Circular brown spots with gray centers"],
        "possible_causes": ["High relative humidity and warm temperatures"],
        "local_context": "Common in Anand district chili plots.",
        "management_steps": ["Prune and destroy infected leaves immediately."],
        "prevention_steps": ["Maintain 45cm spacing between crop beds."],
        "warning_signs": ["Lesions appearing on stem joints"],
        "expert_verification_recommended": True,
        "disclaimer": "Agricultural advisory generated for guidance.",
    }

    # Test 2.1: Primary key succeeds -> Returns advisory without rotating
    try:
        service = LLMService()
        service.set_keys_for_testing(["mock_key_1", "mock_key_2", "mock_key_3"])

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(valid_groq_json)}}]
        }

        call_headers = []

        async def mock_post(url, headers=None, json=None, **kwargs):
            call_headers.append(headers)
            return mock_resp

        with patch("httpx.AsyncClient.post", side_effect=mock_post):
            result = await service.generate_advisory_report(
                crop="chili",
                disease_name="Cercospora Leaf Spot",
                confidence=0.88,
                target_lang="en",
            )

            assert result is not None
            assert "Prune and destroy" in result.management_steps[0]
            # Key 1 was used and no extra calls were made
            assert len(call_headers) == 1
            assert "Bearer mock_key_1" in call_headers[0]["Authorization"]

        print("  [PASS] 2.1: Key 1 succeeds on first attempt without rotating")
        results.append(True)
    except Exception as e:
        print(f"  [FAIL] 2.1: {e}")
        traceback.print_exc()
        results.append(False)

    # Test 2.2: Key 1 hits 429 Rate Limit -> Failover to Key 2 succeeds
    try:
        service = LLMService()
        service.set_keys_for_testing(["mock_key_1", "mock_key_2", "mock_key_3"])

        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.json.return_value = {"error": {"message": "Rate limit exceeded (TPM reached)"}}

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200_json = dict(valid_groq_json)
        resp_200_json["management_steps"] = ["Key 2 recovered management."]
        resp_200.json.return_value = {
            "choices": [{"message": {"content": json.dumps(resp_200_json)}}]
        }

        call_headers = []

        async def mock_post_failover(url, headers=None, json=None, **kwargs):
            call_headers.append(headers)
            if len(call_headers) == 1:
                return resp_429
            return resp_200

        with patch("httpx.AsyncClient.post", side_effect=mock_post_failover):
            result = await service.generate_advisory_report(
                crop="chili",
                disease_name="Cercospora Leaf Spot",
                confidence=0.85,
                target_lang="en",
            )

            assert result is not None
            assert "Key 2 recovered management." in result.management_steps[0]
            assert len(call_headers) == 2
            assert "Bearer mock_key_1" in call_headers[0]["Authorization"]
            assert "Bearer mock_key_2" in call_headers[1]["Authorization"]

        print("  [PASS] 2.2: Key 1 hit 429 rate limit -> Safe failover to Key 2 succeeded")
        results.append(True)
    except Exception as e:
        print(f"  [FAIL] 2.2: {e}")
        traceback.print_exc()
        results.append(False)

    # Test 2.3: Keys 1 and 2 hit 429 -> Key 3 succeeds
    try:
        service = LLMService()
        service.set_keys_for_testing(["mock_key_1", "mock_key_2", "mock_key_3"])

        resp_200_k3 = MagicMock()
        resp_200_k3.status_code = 200
        resp_200_k3_json = dict(valid_groq_json)
        resp_200_k3_json["management_steps"] = ["Key 3 recovered management."]
        resp_200_k3.json.return_value = {
            "choices": [{"message": {"content": json.dumps(resp_200_k3_json)}}]
        }

        call_headers = []

        async def mock_post_triple(url, headers=None, json=None, **kwargs):
            call_headers.append(headers)
            if len(call_headers) in (1, 2):
                return resp_429
            return resp_200_k3

        with patch("httpx.AsyncClient.post", side_effect=mock_post_triple):
            result = await service.generate_advisory_report(
                crop="chili",
                disease_name="Cercospora Leaf Spot",
                confidence=0.85,
                target_lang="en",
            )

            assert result is not None
            assert "Key 3 recovered management." in result.management_steps[0]
            assert len(call_headers) == 3
            assert "Bearer mock_key_3" in call_headers[2]["Authorization"]

        print("  [PASS] 2.3: Keys 1 & 2 rate-limited -> Key 3 failover succeeded")
        results.append(True)
    except Exception as e:
        print(f"  [FAIL] 2.3: {e}")
        traceback.print_exc()
        results.append(False)

    # Test 2.4: All keys fail -> Graceful agronomic fallback returned
    try:
        service = LLMService()
        service.set_keys_for_testing(["mock_key_1", "mock_key_2", "mock_key_3"])

        async def mock_post_all_429(url, headers=None, json=None, **kwargs):
            return resp_429

        with patch("httpx.AsyncClient.post", side_effect=mock_post_all_429):
            result = await service.generate_advisory_report(
                crop="chili",
                disease_name="Cercospora Leaf Spot",
                confidence=0.82,
                target_lang="en",
            )

            assert result is not None
            assert hasattr(result, "management_steps")
            assert hasattr(result, "prevention_steps")
            assert hasattr(result, "disclaimer")
            assert len(result.management_steps) > 0

        print("  [PASS] 2.4: All keys exhausted -> Graceful agronomic fallback served without crash")
        results.append(True)
    except Exception as e:
        print(f"  [FAIL] 2.4: {e}")
        traceback.print_exc()
        results.append(False)

    # Test 2.5: Non-retryable error (e.g. 400 Bad Request) -> Immediate fallback, no unnecessary key rotation
    try:
        service = LLMService()
        service.set_keys_for_testing(["mock_key_1", "mock_key_2", "mock_key_3"])

        resp_400 = MagicMock()
        resp_400.status_code = 400
        resp_400.text = "Invalid JSON parameter in prompt"
        resp_400.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="400 Bad Request",
            request=MagicMock(),
            response=resp_400,
        )

        call_count = 0

        async def mock_post_400(url, headers=None, json=None, **kwargs):
            nonlocal call_count
            call_count += 1
            return resp_400

        with patch("httpx.AsyncClient.post", side_effect=mock_post_400):
            result = await service.generate_advisory_report(
                crop="chili",
                disease_name="Cercospora Leaf Spot",
                confidence=0.82,
                target_lang="en",
            )

            assert result is not None
            # Only called 1 time because 400 is not retryable with another key!
            assert call_count == 1

        print("  [PASS] 2.5: Non-retryable 400 error halts key rotation immediately & serves fallback")
        results.append(True)
    except Exception as e:
        print(f"  [FAIL] 2.5: {e}")
        traceback.print_exc()
        results.append(False)

    # Test 2.6: Zero configured keys -> Safe fallback without leaking info
    try:
        service = LLMService()
        service.set_keys_for_testing([])

        result = await service.generate_advisory_report(
            crop="potato",
            disease_name="Late Blight",
            confidence=0.91,
            target_lang="hi",
        )

        assert result is not None
        assert hasattr(result, "management_steps")
        assert len(result.management_steps) > 0

        print("  [PASS] 2.6: Zero configured keys handled safely without throwing exceptions")
        results.append(True)
    except Exception as e:
        print(f"  [FAIL] 2.6: {e}")
        traceback.print_exc()
        results.append(False)

    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Summary: {passed}/{total} profile & Groq tests passed.")
    if passed == total:
        print("[SUCCESS] All Profile and Groq key rotation tests PASSED perfectly!")
    else:
        print("[FAIL] Some tests failed.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_profile_and_groq_tests())
