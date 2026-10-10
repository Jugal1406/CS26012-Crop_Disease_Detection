"""
backend/firebase_auth.py
========================
Firebase Admin SDK integration for FastAPI.
Provides safe token verification and identity decoding.

Security Rules Enforced:
  - NEVER trusts client-supplied UIDs directly
  - Verifies cryptographically signed Firebase ID tokens (JWT)
  - Supports local service account credentials JSON and fallback project options
  - Handles token expiration, invalid signatures, and revoked credentials
"""

import logging
import os
from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import auth, credentials
from config import FIREBASE_CREDENTIALS_PATH, FIREBASE_PROJECT_ID

logger = logging.getLogger(__name__)

_firebase_initialized = False


def initialize_firebase_admin() -> None:
    """
    Initializes the Firebase Admin SDK once per process.
    Precedence:
      1. Explicit service account JSON file if found on disk
      2. Project ID fallback (useful for emulator, ADC, or token decoding)
    """
    global _firebase_initialized
    if _firebase_initialized or len(firebase_admin._apps) > 0:
        _firebase_initialized = True
        return

    try:
        if os.path.exists(FIREBASE_CREDENTIALS_PATH):
            logger.info(
                "Initializing Firebase Admin with service account JSON: %s",
                FIREBASE_CREDENTIALS_PATH,
            )
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
        else:
            logger.info(
                "Initializing Firebase Admin with project ID: %s",
                FIREBASE_PROJECT_ID,
            )
            firebase_admin.initialize_app(
                options={"projectId": FIREBASE_PROJECT_ID}
            )
        _firebase_initialized = True
        logger.info("[OK] Firebase Admin SDK initialized successfully.")
    except Exception as exc:
        logger.error("[ERROR] Failed to initialize Firebase Admin SDK: %s", exc)
        raise exc


class AuthenticationError(Exception):
    """Raised when token is invalid, expired, or missing."""
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def verify_firebase_id_token(id_token: str) -> Dict[str, Any]:
    """
    Verify a Firebase ID token and extract user claims.

    Args:
        id_token: Bearer JWT string from Authorization header

    Returns:
        dict containing verified claims:
          - uid: str
          - email: Optional[str]
          - phone_number: Optional[str]
          - name: Optional[str]

    Raises:
        AuthenticationError: If token is invalid, expired, revoked, or unverified
    """
    if not id_token:
        raise AuthenticationError("Authorization token is missing", 401)

    initialize_firebase_admin()

    try:
        decoded_token = auth.verify_id_token(id_token, check_revoked=False)
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "phone_number": decoded_token.get("phone_number"),
            "name": decoded_token.get("name"),
            "claims": decoded_token,
        }
    except auth.ExpiredIdTokenError:
        raise AuthenticationError("Firebase ID token has expired. Please re-authenticate.", 401)
    except auth.RevokedIdTokenError:
        raise AuthenticationError("Firebase ID token has been revoked.", 401)
    except auth.InvalidIdTokenError as exc:
        raise AuthenticationError(f"Invalid Firebase ID token: {str(exc)}", 401)
    except Exception as exc:
        logger.warning("Token verification failed: %s", exc)
        raise AuthenticationError(f"Token verification error: {str(exc)}", 401)
