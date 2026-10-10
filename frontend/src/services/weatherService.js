import { getAuthToken } from "./authService";

const BACKEND_URL = "http://localhost:8000";

async function getAuthHeaders() {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("User is not authenticated. Please log in.");
  }
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

/**
 * Fetch current weather snapshot for a farm.
 * @param {string} farmId - UUID of the farm.
 * @param {boolean} forceRefresh - If true, requests backend to query external API and bypass cache.
 */
export async function fetchFarmWeather(farmId, forceRefresh = false) {
  const headers = await getAuthHeaders();
  const url = `${BACKEND_URL}/api/v1/farms/${farmId}/weather${
    forceRefresh ? "?force_refresh=true" : ""
  }`;

  const response = await fetch(url, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Failed to fetch weather (HTTP ${response.status})`
    );
  }

  return await response.json();
}
