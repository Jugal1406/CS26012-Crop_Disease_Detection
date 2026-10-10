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

export async function fetchFarms() {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BACKEND_URL}/api/v1/farms`, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch farms (HTTP ${response.status})`);
  }

  const data = await response.json();
  return data.farms || [];
}

export async function fetchFarm(farmId) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BACKEND_URL}/api/v1/farms/${farmId}`, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch farm (HTTP ${response.status})`);
  }

  return await response.json();
}

export async function createFarm(farmData) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BACKEND_URL}/api/v1/farms`, {
    method: "POST",
    headers,
    body: JSON.stringify(farmData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to register farm (HTTP ${response.status})`);
  }

  return await response.json();
}

export async function updateFarm(farmId, farmData) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BACKEND_URL}/api/v1/farms/${farmId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(farmData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to update farm (HTTP ${response.status})`);
  }

  return await response.json();
}

export async function deleteFarm(farmId) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BACKEND_URL}/api/v1/farms/${farmId}`, {
    method: "DELETE",
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to deactivate farm (HTTP ${response.status})`);
  }

  return await response.json();
}
