// frontend/src/context/AuthContext.jsx
import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useAuth as useClerkAuth, useUser as useClerkUser, useClerk } from "@clerk/clerk-react";
import { setClerkTokenGetter } from "../services/authService";

const AuthContext = createContext(null);

const BACKEND_URL = "http://localhost:8000";

export function AuthProvider({ children }) {
  const { isLoaded, isSignedIn, getToken, signOut } = useClerkAuth();
  const { user: clerkUser } = useClerkUser();
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Bind Clerk token getter to authService so all downstream services have access
  useEffect(() => {
    setClerkTokenGetter(getToken);
  }, [getToken]);

  /**
   * Syncs the authenticated Clerk user identity with PostgreSQL backend.
   * Sends Authorization: Bearer <Clerk JWT>
   * @param {string} [displayName] - Optional name specified during registration
   */
  const syncWithBackend = useCallback(async (displayName = null) => {
    if (!isSignedIn) return null;

    try {
      const token = await getToken();
      if (!token) return null;

      const payload = {};
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
      setUserProfile(data.user);
      setError(null);
      return data.user;
    } catch (err) {
      console.error("Backend synchronization error:", err);
      setError(err.message);
      return null;
    }
  }, [isSignedIn, getToken]);

  useEffect(() => {
    if (!isLoaded) {
      setLoading(true);
      return;
    }

    if (isSignedIn && clerkUser) {
      syncWithBackend(clerkUser.fullName || null).finally(() => {
        setLoading(false);
      });
    } else {
      setUserProfile(null);
      setLoading(false);
    }
  }, [isLoaded, isSignedIn, clerkUser, syncWithBackend]);

  const logout = async () => {
    setLoading(true);
    try {
      await signOut();
      setUserProfile(null);
      setError(null);
    } catch (err) {
      console.error("Logout error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async ({ displayName, phoneNumber, preferredLanguage }) => {
    const { updateUserProfileOnBackend } = await import("../services/authService");
    const updated = await updateUserProfileOnBackend({
      displayName,
      phoneNumber,
      preferredLanguage,
    });
    setUserProfile(updated);
    return updated;
  };

  const value = {
    user: clerkUser,
    userProfile,
    loading: !isLoaded || loading,
    error,
    isAuthenticated: Boolean(isLoaded && isSignedIn),
    syncWithBackend,
    updateProfile,
    logout,
    getToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
