"""
backend/clerk_auth.py
=====================
Clerk token verification and identity resolution for FastAPI.
Provides secure cryptographic JWT validation using Clerk's JWKS
and server-side profile enrichment via Clerk REST API.

Security Rules Enforced:
  - NEVER trusts client-supplied user IDs directly
  - Cryptographically verifies RS256 signatures via Clerk JWKS
  - Validates token expiration (exp), issuer (iss), and required claims
  - Enriches user profile with verified email and name via Clerk API
  - Handles expired, revoked, or malformed tokens with standard AuthenticationError
"""

import logging
import os
from typing import Any, Dict, Optional

import jwt
from jwt import PyJWKClient
import httpx

from config import CLERK_SECRET_KEY, CLERK_JWKS_URL, CLERK_ISSUER

logger = logging.getLogger(__name__)

# Cached JWKS client for efficient cryptographic verification
_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(CLERK_JWKS_URL, cache_keys=True, max_cached_keys=16)
    return _jwks_client


class AuthenticationError(Exception):
    """Raised when token is invalid, expired, or missing."""
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def verify_clerk_token(token: str) -> Dict[str, Any]:
    """
    Verify a Clerk session JWT token against Clerk JWKS.

    Args:
        token: Bearer JWT string from Authorization header

    Returns:
        dict containing verified claims:
          - sub: Clerk user ID (e.g. 'user_...')
          - iss: Issuer URL
          - exp: Expiration time
          - claims: raw token payload

    Raises:
        AuthenticationError: If token is invalid, expired, or malformed
    """
    if not token or not token.strip():
        raise AuthenticationError("Authorization token is missing", 401)

    try:
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        decode_options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
            "require": ["exp", "sub"],
        }

        # If CLERK_ISSUER is specified, verify issuer claim
        kwargs = {}
        if CLERK_ISSUER:
            decode_options["verify_iss"] = True
            kwargs["issuer"] = CLERK_ISSUER
        else:
            decode_options["verify_iss"] = False

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options=decode_options,
            **kwargs,
        )

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Token missing 'sub' claim", 401)

        return {
            "uid": user_id,
            "user_id": user_id,
            "claims": payload,
        }

    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Session token has expired. Please log in again.", 401)
    except jwt.InvalidTokenError as exc:
        logger.warning("Clerk token verification failed: %s", exc)
        raise AuthenticationError(f"Invalid authentication token: {str(exc)}", 401)
    except Exception as exc:
        logger.error("Unexpected error during Clerk token verification: %s", exc)
        raise AuthenticationError("Token verification failed", 401)


async def get_clerk_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches verified user identity from Clerk REST API using CLERK_SECRET_KEY.
    Ensures that display name and verified email are populated from the source of truth.
    """
    if not CLERK_SECRET_KEY:
        logger.warning("CLERK_SECRET_KEY is not configured; cannot enrich user profile")
        return None

    url = f"https://api.clerk.com/v1/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {CLERK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                
                # Resolve verified email address
                primary_email_id = data.get("primary_email_address_id")
                email_addresses = data.get("email_addresses", [])
                verified_email = None

                for item in email_addresses:
                    if item.get("id") == primary_email_id:
                        ver_status = item.get("verification", {}).get("status")
                        if ver_status == "verified":
                            verified_email = item.get("email_address")
                        break

                if not verified_email and email_addresses:
                    for item in email_addresses:
                        if item.get("verification", {}).get("status") == "verified":
                            verified_email = item.get("email_address")
                            break

                # Resolve display name
                first_name = data.get("first_name") or ""
                last_name = data.get("last_name") or ""
                display_name = f"{first_name} {last_name}".strip() or None

                # Resolve primary phone
                primary_phone_id = data.get("primary_phone_number_id")
                phone_numbers = data.get("phone_numbers", [])
                phone_number = None
                for p in phone_numbers:
                    if p.get("id") == primary_phone_id:
                        phone_number = p.get("phone_number")
                        break

                return {
                    "user_id": user_id,
                    "email": verified_email,
                    "display_name": display_name,
                    "phone_number": phone_number,
                }
            else:
                logger.warning(
                    "Clerk API lookup for %s returned HTTP %s: %s",
                    user_id,
                    resp.status_code,
                    resp.text,
                )
                return None
    except Exception as exc:
        logger.error("Failed to query Clerk API for %s: %s", user_id, exc)
        return None
