// frontend/src/pages/Dashboard.jsx
import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "../context/LanguageContext";
import { getAuthToken } from "../services/authService";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import ScanDetailModal from "../components/ScanDetailModal";
import LogoutConfirmModal from "../components/LogoutConfirmModal";
import { fetchFarmWeather } from "../services/weatherService";
import { fetchUserScans } from "../services/scanService";
import "../styles/landing.css";
import "../styles/dashboard.css";

const BACKEND_URL = "http://localhost:8000";

function getTimeGreeting(t) {
  const hour = new Date().getHours();
  if (hour < 12) return t("dashboard.greetingMorning", "Good morning");
  if (hour < 17) return t("dashboard.greetingAfternoon", "Good afternoon");
  return t("dashboard.greetingEvening", "Good evening");
}

export default function Dashboard({ defaultTab = "overview" }) {
  const { user, userProfile, updateProfile, logout } = useAuth();
  const { t, language, changeLanguage, supportedLanguages } = useTranslation();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState(defaultTab);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Profile Edit State
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [editName, setEditName] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editLanguage, setEditLanguage] = useState(language || "en");
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState(null);
  const [profileSuccess, setProfileSuccess] = useState(null);
  const [showLogoutConfirmModal, setShowLogoutConfirmModal] = useState(false);

  // Weather state (Module 13)
  const [weatherData, setWeatherData] = useState(null);
  const [weatherRefreshing, setWeatherRefreshing] = useState(false);

  // Scan History state (Module 16)
  const [historyScans, setHistoryScans] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState(null);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyPageSize, setHistoryPageSize] = useState(10);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyTotalPages, setHistoryTotalPages] = useState(0);
  const [historyHasNext, setHistoryHasNext] = useState(false);
  const [historyHasPrev, setHistoryHasPrev] = useState(false);
  const [filterCrop, setFilterCrop] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [sortOrder, setSortOrder] = useState("desc");
  const [selectedScanId, setSelectedScanId] = useState(null);

  // Fetch authenticated personalized overview from backend
  useEffect(() => {
    let isMounted = true;

    async function fetchDashboard() {
      try {
        setLoading(true);
        const token = await getAuthToken();
        if (!token) return;

        const response = await fetch(`${BACKEND_URL}/api/v1/dashboard/overview`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to load dashboard data (HTTP ${response.status})`);
        }

        const data = await response.json();
        if (isMounted) {
          setDashboardData(data);
          setError(null);
          if (data.weather) {
            setWeatherData(data.weather);
          } else if (data.farm?.has_location) {
            fetchFarmWeather(data.farm.id)
              .then((wx) => {
                if (isMounted && wx.has_location) setWeatherData(wx);
              })
              .catch((e) => console.log("Initial weather fetch:", e));
          }
        }
      } catch (err) {
        console.error("Dashboard overview fetch error:", err);
        if (isMounted) {
          setError(err.message);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchDashboard();

    return () => {
      isMounted = false;
    };
  }, [user]);

  // Fetch paginated scan history (Module 16) with race condition & stale cancellation protection
  useEffect(() => {
    if (activeTab !== "diagnoses") return;
    let isCancelled = false;

    async function loadScans() {
      try {
        setHistoryLoading(true);
        setHistoryError(null);
        const res = await fetchUserScans({
          page: historyPage,
          pageSize: historyPageSize,
          crop: filterCrop,
          status: filterStatus,
          sortOrder: sortOrder,
        });
        if (!isCancelled) {
          setHistoryScans(res.items || []);
          setHistoryTotal(res.total || 0);
          setHistoryTotalPages(res.total_pages || 0);
          setHistoryHasNext(res.has_next || false);
          setHistoryHasPrev(res.has_prev || false);
        }
      } catch (err) {
        if (!isCancelled) {
          console.error("Scan history fetch error:", err);
          setHistoryError(err.message);
        }
      } finally {
        if (!isCancelled) {
          setHistoryLoading(false);
        }
      }
    }

    loadScans();

    return () => {
      isCancelled = true;
    };
  }, [activeTab, historyPage, historyPageSize, filterCrop, filterStatus, sortOrder]);

  const handleLogout = () => {
    setShowLogoutConfirmModal(true);
  };

  const handleConfirmLogout = async () => {
    setShowLogoutConfirmModal(false);
    await logout();
    navigate("/login");
  };

  const getWeatherIcon = (condition) => {
    if (!condition) return "☀️";
    const c = condition.toLowerCase();
    if (c.includes("thunder") || c.includes("storm")) return "⛈️";
    if (c.includes("rain") || c.includes("drizzle") || c.includes("shower")) return "🌧️";
    if (c.includes("snow")) return "❄️";
    if (c.includes("fog") || c.includes("mist")) return "🌫️";
    if (c.includes("cloud") || c.includes("overcast")) return "⛅";
    return "☀️";
  };

  const refreshFarmWeather = async () => {
    const primaryFarmId = dashboardData?.farm?.id;
    if (!primaryFarmId) return;
    try {
      setWeatherRefreshing(true);
      const updatedWx = await fetchFarmWeather(primaryFarmId, true);
      setWeatherData(updatedWx);
    } catch (err) {
      console.error("Failed to refresh weather:", err);
    } finally {
      setWeatherRefreshing(false);
    }
  };

  const handleOpenEditProfile = () => {
    setEditName(dashboardData?.user?.display_name || userProfile?.display_name || user?.fullName || "");
    setEditPhone(dashboardData?.user?.phone_number || userProfile?.phone_number || "");
    setEditLanguage(dashboardData?.user?.preferred_language || userProfile?.preferred_language || language || "en");
    setProfileError(null);
    setProfileSuccess(null);
    setIsEditingProfile(true);
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setProfileError(null);
    setProfileSuccess(null);

    if (!editName.trim()) {
      setProfileError(t("profile.nameRequired", "Full name is required."));
      return;
    }

    try {
      setProfileSaving(true);
      const updated = await updateProfile({
        displayName: editName.trim(),
        phoneNumber: editPhone.trim(),
        preferredLanguage: editLanguage,
      });

      if (editLanguage && editLanguage !== language) {
        changeLanguage(editLanguage);
      }

      setProfileSuccess(t("profile.updateSuccess", "Profile updated successfully!"));
      setIsEditingProfile(false);
      await loadDashboard();
    } catch (err) {
      console.error("Profile update error:", err);
      setProfileError(err.message || t("profile.updateFailed", "Failed to update profile."));
    } finally {
      setProfileSaving(false);
    }
  };

  const displayName =
    dashboardData?.user?.display_name ||
    userProfile?.display_name ||
    user?.displayName ||
    "Farmer";

  const contact =
    dashboardData?.user?.phone_number ||
    dashboardData?.user?.email ||
    user?.phoneNumber ||
    user?.email ||
    "Registered Farmer";

  const farm = dashboardData?.farm;
  const stats = dashboardData?.stats || {
    total_scans: 0,
    healthy_scans: 0,
    issues_detected: 0,
    active_farms_count: 0,
    last_scan_date: null,
    most_recent_crop: null,
  };
  const activeCrops = dashboardData?.active_crops || [];
  const recentScans = dashboardData?.recent_scans || [];

  return (
    <div className="landing">
      <Navbar />
      <main className="dash-container">
        <div className="dash-inner">
          {/* 1. Welcome Message & Banner */}
          <div className="dash-banner">
            <div className="dash-banner-left">
              <div className="dash-avatar">
                {displayName.charAt(0).toUpperCase()}
              </div>
              <div>
                <h1 className="dash-greeting-title">
                  {getTimeGreeting(t)}, {displayName}!
                </h1>
                <p style={{ margin: "0.2rem 0 0.5rem 0", color: "#a9d47c", fontSize: "1.05rem", fontWeight: 500 }}>
                  {t("dashboard.subtitle", "Ready to check the health of your crops?")}
                </p>
                <div className="dash-greeting-subtitle">
                  <span>{contact}</span>
                  <span>•</span>
                  <span>{t("nav.language", "Language")}: {language.toUpperCase()}</span>
                  <span className="dash-badge-active">
                    <span style={{ fontSize: "0.6rem" }}>●</span> Verified Account
                  </span>
                </div>
              </div>
            </div>

            <div className="dash-banner-actions">
              <Link to="/farms" className="dash-cta-btn" style={{ background: "rgba(111, 160, 70, 0.2)", color: "#a9d47c", border: "1px solid rgba(111, 160, 70, 0.4)" }}>
                <span>🏡</span> {t("nav.farms", "My Farms")}
              </Link>
              <Link to="/diagnose" className="dash-cta-btn">
                <span>🍃</span> {t("nav.diagnose", "New Diagnosis")}
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                style={{
                  background: "transparent",
                  border: "1px solid rgba(220, 240, 200, 0.2)",
                  color: "rgba(243, 239, 228, 0.75)",
                  padding: "0.85rem 1.25rem",
                  borderRadius: "12px",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                  transition: "all 0.2s ease",
                }}
              >
                {t("nav.logout", "Log Out")}
              </button>
            </div>
          </div>

          {/* 2. Navigation Tabs */}
          <nav className="dash-nav" aria-label="Dashboard sections">
            <button
              type="button"
              className={`dash-nav-btn ${activeTab === "overview" ? "active" : ""}`}
              onClick={() => setActiveTab("overview")}
            >
              📊 Overview
            </button>
            <button
              type="button"
              className={`dash-nav-btn ${activeTab === "diagnoses" ? "active" : ""}`}
              onClick={() => setActiveTab("diagnoses")}
            >
              📋 {t("dashboard.recentScans", "Recent Diagnoses")} ({recentScans.length})
            </button>
            <button
              type="button"
              className={`dash-nav-btn ${activeTab === "settings" ? "active" : ""}`}
              onClick={() => setActiveTab("settings")}
            >
              ⚙️ Profile & Settings
            </button>
          </nav>

          {/* Loading Feedback */}
          {loading && !dashboardData && (
            <div style={{ textAlign: "center", padding: "3rem 0", color: "#a9d47c" }}>
              <div
                style={{
                  width: "42px",
                  height: "42px",
                  border: "4px solid rgba(169, 212, 124, 0.2)",
                  borderTop: "4px solid #a9d47c",
                  borderRadius: "50%",
                  margin: "0 auto 1rem",
                  animation: "spin 1s linear infinite",
                }}
              />
              <p>Loading your farm dashboard...</p>
              <style>{`
                @keyframes spin {
                  0% { transform: rotate(0deg); }
                  100% { transform: rotate(360deg); }
                }
              `}</style>
            </div>
          )}

          {/* Error Feedback */}
          {error && (
            <div
              style={{
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                color: "#fca5a5",
                padding: "1rem 1.25rem",
                borderRadius: "12px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "0.75rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <span>⚠️</span>
                <span>{error}</span>
              </div>
              <button
                type="button"
                onClick={() => window.location.reload()}
                style={{
                  background: "rgba(239, 68, 68, 0.25)",
                  border: "1px solid rgba(239, 68, 68, 0.5)",
                  color: "#fca5a5",
                  padding: "0.4rem 0.8rem",
                  borderRadius: "8px",
                  cursor: "pointer",
                  fontSize: "0.85rem",
                }}
              >
                Retry
              </button>
            </div>
          )}

          {/* TAB CONTENT: OVERVIEW */}
          {activeTab === "overview" && (
            <>
              {/* 3. Farm Statistics Grid */}
              <div className="dash-stats-grid">
                <div className="dash-stat-card">
                  <div className="dash-stat-icon dash-stat-icon--green">🌱</div>
                  <div>
                    <div className="dash-stat-value">{stats.total_scans}</div>
                    <div className="dash-stat-label">Total Diagnoses</div>
                  </div>
                </div>

                <div className="dash-stat-card">
                  <div className="dash-stat-icon dash-stat-icon--blue">📅</div>
                  <div>
                    <div className="dash-stat-value" style={{ fontSize: stats.last_scan_date ? "1.25rem" : "1.2rem" }}>
                      {stats.last_scan_date || "No scans yet"}
                    </div>
                    <div className="dash-stat-label">Last Diagnosis Date</div>
                  </div>
                </div>

                <div className="dash-stat-card">
                  <div className="dash-stat-icon dash-stat-icon--amber">🌾</div>
                  <div>
                    <div className="dash-stat-value" style={{ fontSize: "1.4rem" }}>
                      {stats.most_recent_crop || "—"}
                    </div>
                    <div className="dash-stat-label">Most Recent Crop</div>
                  </div>
                </div>

                <div className="dash-stat-card">
                  <div className="dash-stat-icon dash-stat-icon--emerald">🛡️</div>
                  <div>
                    <div className="dash-stat-value">
                      {stats.healthy_scans}
                      <span style={{ fontSize: "0.9rem", fontWeight: 400, color: "rgba(243, 239, 228, 0.6)", marginLeft: "0.4rem" }}>
                        / {stats.total_scans}
                      </span>
                    </div>
                    <div className="dash-stat-label">Healthy Leaf Results</div>
                  </div>
                </div>
              </div>

              {/* 3.5. Module 13: Local Agro-Weather Context Card */}
              <div className="dash-weather-card">
                <div className="dash-weather-header">
                  <div className="dash-weather-header-left">
                    <div className="dash-weather-icon-badge">
                      {weatherData
                        ? getWeatherIcon(weatherData.weather_condition)
                        : "🌦️"}
                    </div>
                    <div>
                      <h2 className="dash-weather-title">{t("dashboard.weatherContextTitle", "Local Agro-Weather Context")}</h2>
                      <div className="dash-weather-subtitle">
                        {farm
                          ? `${t("dashboard.primaryPlot", "Primary Plot")}: ${farm.name} • ${farm.district || farm.village || t("dashboard.localRegion", "Local Region")}`
                          : t("dashboard.noFarmPlotsLinked", "No farm plots linked yet")}
                      </div>
                    </div>
                  </div>

                  <div className="dash-weather-actions">
                    <span className="farm-weather-source-badge">
                      {t("common.agroWeatherBadge", "Agro-Weather")}
                    </span>
                    {farm?.has_location && (
                      <button
                        type="button"
                        className="farm-weather-refresh-btn"
                        disabled={weatherRefreshing}
                        onClick={refreshFarmWeather}
                        title={t("dashboard.refreshWeatherTitle", "Refresh latest local weather")}
                      >
                        <span
                          style={{
                            display: "inline-block",
                            transform: weatherRefreshing ? "rotate(180deg)" : "none",
                            transition: "transform 0.5s ease",
                          }}
                        >
                          🔄
                        </span>
                        {weatherRefreshing ? "Refreshing..." : "Refresh"}
                      </button>
                    )}
                    <Link
                      to="/farms"
                      className="dash-cta-btn"
                      style={{ padding: "0.35rem 0.8rem", fontSize: "0.8rem" }}
                    >
                      Farms →
                    </Link>
                  </div>
                </div>

                {farm?.has_location ? (
                  weatherData ? (
                    <>
                      <div className="dash-weather-grid">
                        <div className="dash-weather-tile">
                          <div className="dash-weather-tile-label">
                            <span>🌡️</span> Ambient Temp
                          </div>
                          <div className="dash-weather-tile-val">
                            {weatherData.temperature_c !== null
                              ? `${weatherData.temperature_c}°C`
                              : "—"}
                          </div>
                          <div className="dash-weather-tile-sub">
                            {weatherData.weather_condition || "Clear"}
                          </div>
                        </div>

                        <div className="dash-weather-tile">
                          <div className="dash-weather-tile-label">
                            <span>💧</span> Relative Humidity
                          </div>
                          <div className="dash-weather-tile-val">
                            {weatherData.humidity_pct !== null
                              ? `${weatherData.humidity_pct}%`
                              : "—"}
                          </div>
                          <div className="dash-weather-tile-sub">
                            Atmospheric moisture
                          </div>
                        </div>

                        <div className="dash-weather-tile">
                          <div className="dash-weather-tile-label">
                            <span>🌧️</span> Precipitation
                          </div>
                          <div className="dash-weather-tile-val">
                            {weatherData.rainfall_mm !== null
                              ? `${weatherData.rainfall_mm} mm`
                              : "0.0 mm"}
                          </div>
                          <div className="dash-weather-tile-sub">
                            Rainfall gauge
                          </div>
                        </div>

                        <div className="dash-weather-tile">
                          <div className="dash-weather-tile-label">
                            <span>💨</span> Wind Speed
                          </div>
                          <div className="dash-weather-tile-val">
                            {weatherData.wind_speed_kmh !== null
                              ? `${weatherData.wind_speed_kmh} km/h`
                              : "—"}
                          </div>
                          <div className="dash-weather-tile-sub">
                            Surface wind 10m
                          </div>
                        </div>
                      </div>

                      <div
                        style={{
                          marginTop: "0.85rem",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          fontSize: "0.78rem",
                          color: "rgba(243, 239, 228, 0.55)",
                        }}
                      >
                        <span>
                          Observation time:{" "}
                          {weatherData.recorded_at
                            ? new Date(weatherData.recorded_at).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            : "Recent"}
                        </span>
                        <span>
                          {weatherData.cached ? "⚡ DB Snapshot" : "🟢 Provider Live"}
                        </span>
                      </div>
                    </>
                  ) : (
                    <div
                      style={{
                        textAlign: "center",
                        padding: "1rem 0",
                        color: "rgba(243, 239, 228, 0.7)",
                        fontSize: "0.9rem",
                      }}
                    >
                      <span>⏳</span> Loading meteorological snapshot...
                    </div>
                  )
                ) : farm ? (
                  <div className="farm-weather-no-gps-box" style={{ marginTop: 0 }}>
                    <div className="farm-weather-no-gps-text">
                      📍 <strong>GPS coordinates optional but unconfigured:</strong> Add
                      latitude and longitude for "{farm.name}" to view localized
                      weather snapshots here.
                    </div>
                    <Link to="/farms" className="farm-weather-no-gps-btn">
                      Edit Farm GPS
                    </Link>
                  </div>
                ) : (
                  <div
                    style={{
                      textAlign: "center",
                      padding: "1rem 0",
                      color: "rgba(243, 239, 228, 0.6)",
                      fontSize: "0.9rem",
                    }}
                  >
                    No farms registered. Register your plot in{" "}
                    <Link to="/farms" style={{ color: "#a9d47c" }}>
                      My Farms
                    </Link>{" "}
                    to connect live agro-meteorological monitoring.
                  </div>
                )}
              </div>

              {/* 4. Recent Diagnoses Section */}
              <div className="dash-card">
                <div className="dash-card-header">
                  <h2 className="dash-card-title">
                    <span>📋</span> Recent Diagnoses
                  </h2>
                  <Link
                    to="/diagnose"
                    style={{
                      color: "#a9d47c",
                      fontSize: "0.88rem",
                      textDecoration: "underline",
                      fontWeight: 500,
                    }}
                  >
                    + New Diagnosis
                  </Link>
                </div>

                {recentScans.length > 0 ? (
                  <div style={{ overflowX: "auto" }}>
                    <table className="dash-table">
                      <thead>
                        <tr>
                          <th>Crop</th>
                          <th>Disease / Prediction</th>
                          <th>Confidence</th>
                          <th>Status</th>
                          <th>Date</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {recentScans.map((scan) => (
                          <tr key={scan.id}>
                            <td>
                              <strong>{scan.crop}</strong>
                            </td>
                            <td>
                              <span
                                className={`dash-tag ${
                                  scan.is_healthy ? "dash-tag--healthy" : "dash-tag--issue"
                                }`}
                              >
                                {scan.condition || scan.disease || "Undetermined"}
                              </span>
                            </td>
                            <td>{scan.confidence ? `${scan.confidence}%` : "—"}</td>
                            <td>
                              <span style={{ fontSize: "0.82rem", color: "rgba(243, 239, 228, 0.7)" }}>
                                {scan.status}
                              </span>
                            </td>
                            <td>
                              {scan.date || (scan.created_at ? new Date(scan.created_at).toLocaleDateString() : "Recent")}
                            </td>
                            <td>
                              <button
                                type="button"
                                onClick={() => setSelectedScanId(scan.id)}
                                style={{
                                  padding: "0.3rem 0.6rem",
                                  borderRadius: "6px",
                                  border: "1px solid rgba(169, 212, 124, 0.3)",
                                  background: "rgba(169, 212, 124, 0.1)",
                                  color: "#a9d47c",
                                  fontSize: "0.78rem",
                                  cursor: "pointer",
                                }}
                              >
                                {t("history.viewDetails", "View")}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="dash-empty-state">
                    <div className="dash-empty-icon">🍃</div>
                    <div className="dash-empty-text">
                      No recent diagnoses yet.
                    </div>
                    <Link to="/diagnose" className="dash-cta-btn" style={{ padding: "0.6rem 1.2rem", fontSize: "0.9rem" }}>
                      Start New Diagnosis
                    </Link>
                  </div>
                )}
              </div>

              {/* 5. Two-Column Grid: Profile Summary & Supported Crops */}
              <div className="dash-grid-2">
                {/* User Profile Summary Card */}
                <div className="dash-card">
                  <div className="dash-card-header">
                    <h2 className="dash-card-title">
                      <span>👤</span> Profile Summary
                    </h2>
                    <span className="dash-card-subtitle">Authenticated Account</span>
                  </div>

                  <div className="dash-info-list">
                    <div className="dash-info-item">
                      <span className="dash-info-term">Farmer Name</span>
                      <span className="dash-info-val">{displayName}</span>
                    </div>
                    <div className="dash-info-item">
                      <span className="dash-info-term">Contact Info</span>
                      <span className="dash-info-val">{contact}</span>
                    </div>
                    <div className="dash-info-item">
                      <span className="dash-info-term">{t("nav.language", "Preferred Language")}</span>
                      <div style={{ display: "flex", gap: "6px" }}>
                        {supportedLanguages.map((l) => (
                          <button
                            key={l.code}
                            type="button"
                            onClick={() => changeLanguage(l.code)}
                            style={{
                              background: language === l.code ? "#6fa046" : "rgba(255, 255, 255, 0.08)",
                              border: "1px solid rgba(255, 255, 255, 0.2)",
                              color: "#f3efe4",
                              padding: "4px 8px",
                              borderRadius: "6px",
                              fontSize: "0.82rem",
                              cursor: "pointer",
                            }}
                          >
                            {l.flag} {l.nativeName}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="dash-info-item">
                      <span className="dash-info-term">{t("dashboard.accountStatus", "Account Status")}</span>
                      <span className="dash-info-val" style={{ color: "#86efac" }}>{t("dashboard.accountVerified", "Active (Verified Farmer)")}</span>
                    </div>
                  </div>

                  <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}>
                    <button
                      type="button"
                      onClick={() => {
                        setActiveTab("profile");
                        handleOpenEditProfile();
                      }}
                      className="dash-cta-btn"
                      style={{ padding: "0.45rem 0.9rem", fontSize: "0.82rem", background: "rgba(169, 212, 124, 0.15)", color: "#a9d47c", border: "1px solid rgba(169, 212, 124, 0.3)" }}
                    >
                      ✏️ {t("profile.editProfileBtn", "Edit Profile")}
                    </button>
                  </div>

                  <div style={{ marginTop: "1.25rem", padding: "0.85rem", background: "rgba(111, 160, 70, 0.1)", border: "1px solid rgba(111, 160, 70, 0.25)", borderRadius: "10px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <strong style={{ display: "block", color: "#f3efe4", fontSize: "0.9rem" }}>
                        🏡 {t("dashboard.farmPlotsTitle", "Farm Plots")} ({stats.active_farms_count || 0})
                      </strong>
                      <span style={{ fontSize: "0.82rem", color: "rgba(243, 239, 228, 0.65)" }}>
                        {farm ? `${farm.name} (${farm.district || t("dashboard.registered", "Registered")})` : t("dashboard.noFarmPlotsLinked", "No farm plots linked yet")}
                      </span>
                    </div>
                    <Link to="/farms" className="dash-cta-btn" style={{ padding: "0.45rem 0.9rem", fontSize: "0.82rem" }}>
                      {t("dashboard.manageFarmsBtn", "Manage Farms →")}
                    </Link>
                  </div>
                </div>

                {/* Supported Crops Catalog Card */}
                <div className="dash-card">
                  <div className="dash-card-header">
                    <h2 className="dash-card-title">
                      <span>🌱</span> {t("dashboard.cropCatalogTitle", "Supported Crop Catalog")}
                    </h2>
                    <span className="dash-card-subtitle">{t("dashboard.cropCatalogSubtitle", "AI Diagnostic Engines")}</span>
                  </div>

                  <div className="dash-crops-container">
                    {activeCrops.length > 0 ? (
                      activeCrops.map((crop) => (
                        <div
                          key={crop.id}
                          className={`dash-crop-pill ${crop.is_supported ? "dash-crop-pill--active" : ""}`}
                        >
                          <span style={{ fontSize: "1.2rem" }}>
                            {crop.name === "chili" ? "🌶️" : crop.name === "potato" ? "🥔" : "🥜"}
                          </span>
                          <div>
                            <strong style={{ display: "block" }}>{crop.display_name}</strong>
                            <span
                              className={`dash-crop-pill-status ${
                                crop.is_supported
                                  ? "dash-crop-pill-status--ready"
                                  : "dash-crop-pill-status--soon"
                              }`}
                            >
                              {crop.status}
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div style={{ color: "rgba(243, 239, 228, 0.6)", fontSize: "0.9rem" }}>
                        Chili (Active), Potato (Active), Groundnut (In Progress)
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}

          {/* TAB CONTENT: DIAGNOSES (Module 16 Paginated History) */}
          {activeTab === "diagnoses" && (
            <div className="dash-card">
              <div className="dash-card-header" style={{ flexWrap: "wrap", gap: "1rem" }}>
                <div>
                  <h2 className="dash-card-title">
                    <span>📋</span> {t("history.title", "Diagnostic Scan History")}
                  </h2>
                  <p style={{ margin: "0.25rem 0 0", fontSize: "0.85rem", color: "rgba(243, 239, 228, 0.65)" }}>
                    {t("history.subtitle", "View, filter, and inspect past crop health scans.")}
                  </p>
                </div>
                <Link to="/diagnose" className="dash-cta-btn" style={{ padding: "0.55rem 1.2rem", fontSize: "0.88rem" }}>
                  + {t("dashboard.newDiagnosisBtn", "New Diagnosis")}
                </Link>
              </div>

              {/* Filter & Sorting Controls */}
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.75rem",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "1rem",
                  background: "rgba(255, 255, 255, 0.03)",
                  borderRadius: "12px",
                  margin: "1rem 0",
                  border: "1px solid rgba(255, 255, 255, 0.06)",
                }}
              >
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center" }}>
                  {/* Crop Filter */}
                  <select
                    value={filterCrop}
                    onChange={(e) => {
                      setFilterCrop(e.target.value);
                      setHistoryPage(1);
                    }}
                    style={{
                      background: "#16241b",
                      color: "#f3efe4",
                      border: "1px solid rgba(169, 212, 124, 0.3)",
                      borderRadius: "8px",
                      padding: "0.45rem 0.8rem",
                      fontSize: "0.85rem",
                      cursor: "pointer",
                    }}
                  >
                    <option value="">🌱 {t("history.allCrops", "All Crops")}</option>
                    <option value="chili">Chili (Mirchi)</option>
                    <option value="potato">Potato (Aloo)</option>
                  </select>

                  {/* Status Filter */}
                  <select
                    value={filterStatus}
                    onChange={(e) => {
                      setFilterStatus(e.target.value);
                      setHistoryPage(1);
                    }}
                    style={{
                      background: "#16241b",
                      color: "#f3efe4",
                      border: "1px solid rgba(169, 212, 124, 0.3)",
                      borderRadius: "8px",
                      padding: "0.45rem 0.8rem",
                      fontSize: "0.85rem",
                      cursor: "pointer",
                    }}
                  >
                    <option value="">📊 {t("history.allStatuses", "All Statuses")}</option>
                    <option value="success">{t("history.statusSuccess", "Confident Diagnosis")}</option>
                    <option value="low_confidence">{t("history.statusLowConfidence", "Low Confidence")}</option>
                  </select>

                  {/* Date Sort Order */}
                  <select
                    value={sortOrder}
                    onChange={(e) => {
                      setSortOrder(e.target.value);
                      setHistoryPage(1);
                    }}
                    style={{
                      background: "#16241b",
                      color: "#f3efe4",
                      border: "1px solid rgba(169, 212, 124, 0.3)",
                      borderRadius: "8px",
                      padding: "0.45rem 0.8rem",
                      fontSize: "0.85rem",
                      cursor: "pointer",
                    }}
                  >
                    <option value="desc">⬇️ {t("history.sortDesc", "Newest First")}</option>
                    <option value="asc">⬆️ {t("history.sortAsc", "Oldest First")}</option>
                  </select>

                  {(filterCrop || filterStatus || sortOrder !== "desc") && (
                    <button
                      type="button"
                      onClick={() => {
                        setFilterCrop("");
                        setFilterStatus("");
                        setSortOrder("desc");
                        setHistoryPage(1);
                      }}
                      style={{
                        background: "rgba(255, 255, 255, 0.08)",
                        border: "none",
                        color: "#fca5a5",
                        borderRadius: "8px",
                        padding: "0.45rem 0.75rem",
                        fontSize: "0.8rem",
                        cursor: "pointer",
                      }}
                    >
                      ✕ {t("history.resetFilters", "Reset Filters")}
                    </button>
                  )}
                </div>

                {/* Page Size Selector */}
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.82rem", color: "rgba(243, 239, 228, 0.7)" }}>
                  <span>{t("history.pageSize", "Per page")}:</span>
                  <select
                    value={historyPageSize}
                    onChange={(e) => {
                      setHistoryPageSize(Number(e.target.value));
                      setHistoryPage(1);
                    }}
                    style={{
                      background: "#16241b",
                      color: "#f3efe4",
                      border: "1px solid rgba(169, 212, 124, 0.3)",
                      borderRadius: "6px",
                      padding: "0.3rem 0.5rem",
                      fontSize: "0.82rem",
                      cursor: "pointer",
                    }}
                  >
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                  </select>
                </div>
              </div>

              {/* Loading State */}
              {historyLoading && (
                <div style={{ textAlign: "center", padding: "3rem 0", color: "#a9d47c" }}>
                  <div
                    style={{
                      width: "36px",
                      height: "36px",
                      border: "3px solid rgba(169, 212, 124, 0.2)",
                      borderTop: "3px solid #a9d47c",
                      borderRadius: "50%",
                      margin: "0 auto 1rem",
                      animation: "spin 1s linear infinite",
                    }}
                  />
                  <p>{t("common.loading", "Loading scan history...")}</p>
                </div>
              )}

              {/* Error State */}
              {!historyLoading && historyError && (
                <div
                  style={{
                    background: "rgba(239, 68, 68, 0.15)",
                    border: "1px solid #ef4444",
                    borderRadius: "10px",
                    padding: "1rem",
                    color: "#fca5a5",
                    margin: "1rem 0",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span>{historyError}</span>
                  <button
                    onClick={() => setHistoryPage((p) => p)}
                    style={{
                      background: "#ef4444",
                      color: "#fff",
                      border: "none",
                      borderRadius: "6px",
                      padding: "0.3rem 0.7rem",
                      fontSize: "0.8rem",
                      cursor: "pointer",
                    }}
                  >
                    {t("common.retry", "Retry")}
                  </button>
                </div>
              )}

              {/* Content: Scans List */}
              {!historyLoading && !historyError && historyScans.length > 0 && (
                <>
                  <div style={{ overflowX: "auto" }}>
                    <table className="dash-table">
                      <thead>
                        <tr>
                          <th>Crop</th>
                          <th>Diagnosis</th>
                          <th>Confidence</th>
                          <th>Status</th>
                          <th>Plot / Location</th>
                          <th>Date</th>
                          <th>Report</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {historyScans.map((s) => {
                          const isLow = s.status === "low_confidence" || (s.prediction && !s.prediction.is_confident);
                          return (
                            <tr key={s.id}>
                              <td>
                                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                                  <span>{s.crop === "chili" ? "🌶️" : "🌱"}</span>
                                  <strong>{s.crop_display_name || s.crop}</strong>
                                </div>
                              </td>
                              <td>
                                <span
                                  className={`dash-tag ${
                                    isLow
                                      ? "dash-tag--pending"
                                      : s.prediction?.is_healthy
                                      ? "dash-tag--healthy"
                                      : "dash-tag--issue"
                                  }`}
                                  style={{
                                    backgroundColor: isLow ? "rgba(234, 179, 8, 0.15)" : undefined,
                                    color: isLow ? "#fde047" : undefined,
                                    borderColor: isLow ? "rgba(234, 179, 8, 0.3)" : undefined,
                                  }}
                                >
                                  {isLow ? "Low Confidence" : s.prediction?.disease_display_name || "Diagnosed"}
                                </span>
                              </td>
                              <td>
                                {s.prediction?.confidence_percentage
                                  ? `${s.prediction.confidence_percentage}%`
                                  : "—"}
                              </td>
                              <td>
                                <span style={{ fontSize: "0.82rem", color: "rgba(243, 239, 228, 0.7)" }}>
                                  {s.status}
                                </span>
                              </td>
                              <td>
                                <span style={{ fontSize: "0.82rem", color: "rgba(243, 239, 228, 0.75)" }}>
                                  {s.farm?.name || "General Plot"}
                                </span>
                              </td>
                              <td>{s.date_formatted || s.created_at}</td>
                              <td>
                                {s.has_report ? (
                                  <span style={{ color: "#86efac", fontSize: "0.78rem" }}>
                                    ✓ Available ({s.available_report_languages?.join(", ") || "en"})
                                  </span>
                                ) : isLow ? (
                                  <span style={{ color: "rgba(243, 239, 228, 0.4)", fontSize: "0.78rem" }}>
                                    N/A (Inconclusive)
                                  </span>
                                ) : (
                                  <span style={{ color: "rgba(243, 239, 228, 0.5)", fontSize: "0.78rem" }}>
                                    Pending
                                  </span>
                                )}
                              </td>
                              <td>
                                <button
                                  type="button"
                                  onClick={() => setSelectedScanId(s.id)}
                                  style={{
                                    padding: "0.35rem 0.75rem",
                                    borderRadius: "6px",
                                    border: "1px solid rgba(169, 212, 124, 0.4)",
                                    background: "rgba(169, 212, 124, 0.12)",
                                    color: "#a9d47c",
                                    fontSize: "0.8rem",
                                    cursor: "pointer",
                                    fontWeight: 500,
                                    transition: "all 0.2s ease",
                                  }}
                                >
                                  {t("history.viewDetails", "Inspect")}
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination Navigation Bar */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginTop: "1.25rem",
                      paddingTop: "1rem",
                      borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                      flexWrap: "wrap",
                      gap: "0.75rem",
                    }}
                  >
                    <div style={{ fontSize: "0.85rem", color: "rgba(243, 239, 228, 0.7)" }}>
                      {t("history.totalScans", "Total Scans")}: <strong>{historyTotal}</strong> &bull;{" "}
                      {t("history.page", "Page")} <strong>{historyPage}</strong> {t("history.of", "of")}{" "}
                      <strong>{historyTotalPages || 1}</strong>
                    </div>

                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <button
                        type="button"
                        onClick={() => setHistoryPage((p) => Math.max(1, p - 1))}
                        disabled={!historyHasPrev || historyLoading}
                        style={{
                          padding: "0.4rem 0.85rem",
                          borderRadius: "6px",
                          border: "1px solid rgba(169, 212, 124, 0.3)",
                          background: historyHasPrev ? "rgba(169, 212, 124, 0.1)" : "rgba(255, 255, 255, 0.02)",
                          color: historyHasPrev ? "#a9d47c" : "rgba(243, 239, 228, 0.3)",
                          cursor: historyHasPrev ? "pointer" : "not-allowed",
                          fontSize: "0.82rem",
                        }}
                      >
                        ◀ {t("history.prevPage", "Previous")}
                      </button>

                      <button
                        type="button"
                        onClick={() => setHistoryPage((p) => p + 1)}
                        disabled={!historyHasNext || historyLoading}
                        style={{
                          padding: "0.4rem 0.85rem",
                          borderRadius: "6px",
                          border: "1px solid rgba(169, 212, 124, 0.3)",
                          background: historyHasNext ? "rgba(169, 212, 124, 0.1)" : "rgba(255, 255, 255, 0.02)",
                          color: historyHasNext ? "#a9d47c" : "rgba(243, 239, 228, 0.3)",
                          cursor: historyHasNext ? "pointer" : "not-allowed",
                          fontSize: "0.82rem",
                        }}
                      >
                        {t("history.nextPage", "Next")} ▶
                      </button>
                    </div>
                  </div>
                </>
              )}

              {/* Empty State */}
              {!historyLoading && !historyError && historyScans.length === 0 && (
                <div className="dash-empty-state">
                  <div className="dash-empty-icon">🍃</div>
                  <div className="dash-empty-text">
                    {filterCrop || filterStatus
                      ? t("history.noScansMatch", "No diagnostic scans match the selected filters.")
                      : t("dashboard.noScansYet", "No leaf scans recorded yet.")}
                  </div>
                  {filterCrop || filterStatus ? (
                    <button
                      type="button"
                      onClick={() => {
                        setFilterCrop("");
                        setFilterStatus("");
                        setHistoryPage(1);
                      }}
                      className="dash-cta-btn"
                      style={{ padding: "0.5rem 1rem", fontSize: "0.85rem", marginTop: "0.5rem" }}
                    >
                      {t("history.resetFilters", "Reset Filters")}
                    </button>
                  ) : (
                    <Link to="/diagnose" className="dash-cta-btn" style={{ padding: "0.6rem 1.2rem", fontSize: "0.9rem" }}>
                      {t("dashboard.newDiagnosisBtn", "Start New Diagnosis")}
                    </Link>
                  )}
                </div>
              )}
            </div>
          )}

          {/* TAB CONTENT: PROFILE & SETTINGS */}
          {activeTab === "settings" && (
            <div className="dash-card">
              <div className="dash-card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <h2 className="dash-card-title">
                    <span>⚙️</span> {t("profile.title", "Farmer Profile & Settings")}
                  </h2>
                  <span className="dash-card-subtitle">{t("profile.subtitle", "Manage your personal profile and language preferences")}</span>
                </div>
                {!isEditingProfile && (
                  <button
                    type="button"
                    onClick={handleOpenEditProfile}
                    className="dash-cta-btn"
                    style={{ padding: "0.5rem 1rem", fontSize: "0.85rem" }}
                  >
                    ✏️ {t("profile.editProfileBtn", "Edit Profile")}
                  </button>
                )}
              </div>

              {profileSuccess && (
                <div style={{ marginTop: "1rem", padding: "0.85rem", background: "rgba(34, 197, 94, 0.15)", border: "1px solid rgba(34, 197, 94, 0.3)", borderRadius: "10px", color: "#86efac", fontSize: "0.9rem" }}>
                  ✅ {profileSuccess}
                </div>
              )}

              {profileError && (
                <div style={{ marginTop: "1rem", padding: "0.85rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "10px", color: "#fca5a5", fontSize: "0.9rem" }}>
                  ⚠️ {profileError}
                </div>
              )}

              {!isEditingProfile ? (
                <div className="dash-info-list" style={{ marginTop: "1.25rem" }}>
                  <div className="dash-info-item">
                    <span className="dash-info-term">{t("profile.nameLabel", "Farmer Name")}</span>
                    <span className="dash-info-val">{displayName}</span>
                  </div>
                  <div className="dash-info-item">
                    <span className="dash-info-term">{t("profile.emailLabel", "Email Address")}</span>
                    <span className="dash-info-val">
                      {dashboardData?.user?.email || userProfile?.email || user?.email || t("profile.notLinked", "Not linked")}
                    </span>
                  </div>
                  <div className="dash-info-item">
                    <span className="dash-info-term">{t("profile.phoneLabel", "Phone Number")}</span>
                    <span className="dash-info-val">
                      {dashboardData?.user?.phone_number || userProfile?.phone_number || t("profile.notLinked", "Not linked")}
                    </span>
                  </div>
                  <div className="dash-info-item">
                    <span className="dash-info-term">{t("profile.languageLabel", "Preferred Language")}</span>
                    <span className="dash-info-val">
                      {(dashboardData?.user?.preferred_language || userProfile?.preferred_language || language || "en").toUpperCase()}
                    </span>
                  </div>
                  <div className="dash-info-item">
                    <span className="dash-info-term">{t("dashboard.accountStatus", "Account Status")}</span>
                    <span className="dash-info-val" style={{ color: "#86efac" }}>{t("dashboard.accountVerified", "Active (Verified Farmer)")}</span>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSaveProfile} style={{ marginTop: "1.25rem" }}>
                  <div className="farm-form-grid">
                    <div className="farm-field">
                      <label className="farm-label" htmlFor="edit-profile-name">
                        {t("profile.nameLabel", "Full Name")} *
                      </label>
                      <input
                        id="edit-profile-name"
                        type="text"
                        className="farm-input"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        required
                        placeholder={t("profile.namePlaceholder", "e.g. Ramesh Patel")}
                      />
                    </div>

                    <div className="farm-field">
                      <label className="farm-label" htmlFor="edit-profile-email">
                        {t("profile.emailLabel", "Email Address")} ({t("profile.readOnlyLabel", "Read-only")})
                      </label>
                      <input
                        id="edit-profile-email"
                        type="email"
                        className="farm-input"
                        value={dashboardData?.user?.email || userProfile?.email || user?.email || ""}
                        disabled
                        style={{ opacity: 0.65, cursor: "not-allowed" }}
                      />
                      <span style={{ fontSize: "0.76rem", color: "rgba(243, 239, 228, 0.55)", marginTop: "4px" }}>
                        {t("profile.emailNotice", "Email is managed by your authentication provider.")}
                      </span>
                    </div>

                    <div className="farm-field">
                      <label className="farm-label" htmlFor="edit-profile-phone">
                        {t("profile.phoneLabel", "Phone Number")} ({t("common.optional", "Optional")})
                      </label>
                      <input
                        id="edit-profile-phone"
                        type="tel"
                        className="farm-input"
                        value={editPhone}
                        onChange={(e) => setEditPhone(e.target.value)}
                        placeholder={t("profile.phonePlaceholder", "e.g. +91 9876543210 or 9876543210")}
                      />
                    </div>

                    <div className="farm-field">
                      <label className="farm-label" htmlFor="edit-profile-lang">
                        {t("profile.languageLabel", "Preferred Language")}
                      </label>
                      <select
                        id="edit-profile-lang"
                        className="farm-input"
                        value={editLanguage}
                        onChange={(e) => setEditLanguage(e.target.value)}
                        style={{ background: "#101d13", color: "#f3efe4" }}
                      >
                        {supportedLanguages.map((l) => (
                          <option key={l.code} value={l.code}>
                            {l.flag} {l.nativeName} ({l.label})
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: "1rem", marginTop: "1.5rem", justifyContent: "flex-end" }}>
                    <button
                      type="button"
                      onClick={() => setIsEditingProfile(false)}
                      className="farms-btn-secondary"
                    >
                      {t("common.cancel", "Cancel")}
                    </button>
                    <button
                      type="submit"
                      disabled={profileSaving}
                      className="farms-btn-primary"
                    >
                      {profileSaving ? t("common.saving", "Saving...") : t("profile.saveBtn", "Save Changes")}
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Module 16: Scan Inspection & Localized Advisory Modal */}
      {selectedScanId && (
        <ScanDetailModal
          scanId={selectedScanId}
          initialLang={language}
          onClose={() => setSelectedScanId(null)}
        />
      )}

      {/* Logout Confirmation Dialog */}
      <LogoutConfirmModal
        isOpen={showLogoutConfirmModal}
        onClose={() => setShowLogoutConfirmModal(false)}
        onConfirm={handleConfirmLogout}
      />

      <Footer />
    </div>
  );
}
