import { getAuthToken as getAuthTokenFromService } from "./authService";

const BACKEND_URL = "http://localhost:8000";

async function getAuthToken() {
  const token = await getAuthTokenFromService();
  if (!token) {
    throw new Error("You must be logged in to perform diagnosis.");
  }
  return token;
}

/**
 * Submit leaf photo for MobileNetV2 disease prediction and Groq LLM advisory.
 * @param {Object} params
 * @param {string} params.crop - e.g. "chili"
 * @param {File} params.imageFile - Image file from file input
 * @param {string|null} params.farmId - Optional farm UUID for localized context
 * @param {string} params.language - Language code ('en', 'hi', 'gu')
 */
export async function diagnoseLeaf({ crop, imageFile, farmId = null, language = "en" }) {
  const token = await getAuthToken();

  const formData = new FormData();
  formData.append("crop", crop);
  formData.append("image", imageFile);
  if (farmId) {
    formData.append("farm_id", farmId);
  }
  if (language) {
    formData.append("language", language);
  }

  const response = await fetch(`${BACKEND_URL}/api/v1/diagnose`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Diagnosis request failed (HTTP ${response.status})`);
  }

  return await response.json();
}

/**
 * Fetch existing advisory report for a previously completed scan.
 */
export async function fetchScanReport(scanId, language = "en") {
  const token = await getAuthToken();

  const response = await fetch(
    `${BACKEND_URL}/api/v1/scans/${scanId}/report?lang=${encodeURIComponent(language)}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch report (HTTP ${response.status})`);
  }

  return await response.json();
}
