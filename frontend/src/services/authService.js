// frontend/src/services/authService.js
/**
 * Authentication Service
 * Manages Clerk authentication tokens and backend synchronization.
 * Securely communicates with FastAPI backend via Authorization: Bearer <Clerk JWT>.
 */

const BACKEND_URL = "http://localhost:8000";

let _tokenGetter = null;

/**
 * Register a token getter function from Clerk's useAuth() hook.
 * @param {Function} getter - async function returning token string
 */
export function setClerkTokenGetter(getter) {
  _tokenGetter = getter;
}

/**
 * Get current Clerk session JWT token for API calls.
 * @returns {Promise<string|null>}
 */
export async function getAuthToken() {
  if (typeof _tokenGetter === "function") {
    try {
      const token = await _tokenGetter();
      if (token) return token;
    } catch (e) {
      console.warn("Clerk token getter error:", e);
    }
  }

  // Fallback to global window.Clerk object if available
  if (window.Clerk && window.Clerk.session) {
    try {
      return await window.Clerk.session.getToken();
    } catch (e) {
      console.warn("Window Clerk token retrieval error:", e);
    }
  }

  return null;
}

/**
 * Backward compatibility alias for existing code calling getCurrentIdToken.
 */
export async function getCurrentIdToken() {
  return await getAuthToken();
}

/**
 * Synchronize the authenticated Clerk user identity with PostgreSQL.
 * @param {string|null} [displayName]
 * @param {string} [preferredLanguage="en"]
 * @returns {Promise<Object>}
 */
export async function syncUserWithBackend(displayName = null, preferredLanguage = "en") {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("No active authentication session available for sync.");
  }

  const payload = { preferred_language: preferredLanguage };
  if (displayName && displayName.trim()) {
    payload.display_name = displayName.trim();
  }

  const response = await fetch(`${BACKEND_URL}/api/v1/auth/sync`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Server synchronization failed (HTTP ${response.status})`
    );
  }

  const data = await response.json();
  return data.user;
}

/**
 * Update authenticated user profile on PostgreSQL.
 * @param {Object} profileData - { displayName, phoneNumber, preferredLanguage }
 * @returns {Promise<Object>} updated user profile
 */
export async function updateUserProfileOnBackend(profileData) {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("No active authentication session available.");
  }

  const payload = {};
  if (profileData.displayName !== undefined) {
    payload.display_name = profileData.displayName ? profileData.displayName.trim() : "";
  }
  if (profileData.phoneNumber !== undefined) {
    payload.phone_number = profileData.phoneNumber ? profileData.phoneNumber.trim() : "";
  }
  if (profileData.preferredLanguage !== undefined) {
    payload.preferred_language = profileData.preferredLanguage;
  }

  const response = await fetch(`${BACKEND_URL}/api/v1/auth/profile`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Profile update failed (HTTP ${response.status})`
    );
  }

  return await response.json();
}
