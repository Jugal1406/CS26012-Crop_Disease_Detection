import { getAuthToken as getAuthTokenFromService } from "./authService";

const BACKEND_URL = "http://localhost:8000";

async function getAuthToken() {
  const token = await getAuthTokenFromService();
  if (!token) {
    throw new Error("You must be logged in to access scan history.");
  }
  return token;
}

/**
 * Fetch paginated list of scans for the authenticated user.
 * Supports filtering by crop, status, and stable date sorting.
 */
export async function fetchUserScans({
  page = 1,
  pageSize = 10,
  crop = "",
  status = "",
  sortOrder = "desc",
} = {}) {
  const token = await getAuthToken();

  const params = new URLSearchParams();
  params.append("page", page.toString());
  params.append("page_size", pageSize.toString());
  if (crop && crop.trim()) {
    params.append("crop", crop.trim().toLowerCase());
  }
  if (status && status.trim()) {
    params.append("status", status.trim().toLowerCase());
  }
  if (sortOrder) {
    params.append("sort_order", sortOrder.toLowerCase());
  }

  const response = await fetch(`${BACKEND_URL}/api/v1/scans?${params.toString()}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch scan history (HTTP ${response.status})`);
  }

  return await response.json();
}

/**
 * Fetch detailed diagnostic data for a specific scan owned by the user.
 * Supports on-demand localized advisory report retrieval in 'en', 'hi', or 'gu'.
 */
export async function fetchScanDetail(scanId, language = "en") {
  const token = await getAuthToken();

  const response = await fetch(
    `${BACKEND_URL}/api/v1/scans/${scanId}?lang=${encodeURIComponent(language)}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to load scan details (HTTP ${response.status})`);
  }

  return await response.json();
}

/**
 * Fetch the authenticated image blob URL for a specific scan.
 */
export async function fetchScanImageBlobUrl(scanId) {
  const token = await getAuthToken();

  const response = await fetch(`${BACKEND_URL}/api/v1/scans/${scanId}/image`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to load scan image (HTTP ${response.status})`);
  }

  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

/**
 * Download professional agricultural PDF report for a scan.
 * Creates an in-memory object URL, triggers download, and cleanly revokes object URL.
 */
export async function downloadScanPdf(scanId, language = "en") {
  const token = await getAuthToken();

  const response = await fetch(
    `${BACKEND_URL}/api/v1/scans/${scanId}/pdf?lang=${encodeURIComponent(language)}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to generate PDF report (HTTP ${response.status})`);
  }

  const blob = await response.blob();
  const downloadUrl = URL.createObjectURL(blob);
  const tempLink = document.createElement("a");
  tempLink.href = downloadUrl;
  tempLink.download = `crop_report_${scanId.slice(0, 8)}_${language}.pdf`;
  document.body.appendChild(tempLink);
  tempLink.click();
  document.body.removeChild(tempLink);
  setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
}
