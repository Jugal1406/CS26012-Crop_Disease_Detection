// frontend/src/pages/Farms.jsx
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "../context/LanguageContext";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import {
  fetchFarms,
  createFarm,
  updateFarm,
  deleteFarm,
} from "../services/farmService";
import { fetchFarmWeather } from "../services/weatherService";
import "../styles/landing.css";
import "../styles/farms.css";

export default function Farms() {
  const { user, userProfile } = useAuth();
  const { t } = useTranslation();

  const [farms, setFarms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Weather state per farm (Module 13)
  const [farmWeather, setFarmWeather] = useState({});

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editingFarmId, setEditingFarmId] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    village: "",
    district: "",
    state: "",
    area_hectares: "",
    latitude: "",
    longitude: "",
  });

  // Geolocation helper state
  const [geoLoading, setGeoLoading] = useState(false);
  const [geoNotice, setGeoNotice] = useState(null);

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

  const loadWeatherForFarm = async (farmId, forceRefresh = false) => {
    setFarmWeather((prev) => ({
      ...prev,
      [farmId]: { ...prev[farmId], loading: true, error: null },
    }));
    try {
      const data = await fetchFarmWeather(farmId, forceRefresh);
      setFarmWeather((prev) => ({
        ...prev,
        [farmId]: { data, loading: false, error: null },
      }));
    } catch (err) {
      console.error(`Error loading weather for farm ${farmId}:`, err);
      setFarmWeather((prev) => ({
        ...prev,
        [farmId]: {
          data: null,
          loading: false,
          error: err.message || "Failed to load weather.",
        },
      }));
    }
  };

  // Load farms on mount
  const loadFarms = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchFarms();
      setFarms(data);

      // Auto-load weather for farms with GPS coordinates
      data.forEach((f) => {
        if (f.has_location) {
          loadWeatherForFarm(f.id, false);
        }
      });
    } catch (err) {
      console.error("Error loading farms:", err);
      setError(err.message || "Failed to load farm profiles.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFarms();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleOpenAddForm = () => {
    setEditingFarmId(null);
    setFormData({
      name: "",
      village: "",
      district: "",
      state: "",
      area_hectares: "",
      latitude: "",
      longitude: "",
    });
    setGeoNotice(null);
    setError(null);
    setSuccessMsg(null);
    setShowForm(true);
  };

  const handleOpenEditForm = (farm) => {
    setEditingFarmId(farm.id);
    setFormData({
      name: farm.name || "",
      village: farm.village || "",
      district: farm.district || "",
      state: farm.state || "",
      area_hectares: farm.area_hectares !== null ? farm.area_hectares.toString() : "",
      latitude: farm.latitude !== null ? farm.latitude.toString() : "",
      longitude: farm.longitude !== null ? farm.longitude.toString() : "",
    });
    setGeoNotice(null);
    setError(null);
    setSuccessMsg(null);
    setShowForm(true);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingFarmId(null);
    setGeoNotice(null);
  };

  // Browser Geolocation API Handler (One-time, on demand)
  const handleGetCurrentLocation = () => {
    if (!navigator.geolocation) {
      setGeoNotice("Geolocation is not supported by your browser. You can enter coordinates manually.");
      return;
    }

    setGeoLoading(true);
    setGeoNotice(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude.toFixed(6);
        const lon = position.coords.longitude.toFixed(6);
        setFormData((prev) => ({
          ...prev,
          latitude: lat,
          longitude: lon,
        }));
        setGeoNotice("📍 GPS coordinates captured successfully! You can adjust them before saving.");
        setGeoLoading(false);
      },
      (geoError) => {
        setGeoLoading(false);
        console.warn("Geolocation warning:", geoError);
        if (geoError.code === geoError.PERMISSION_DENIED) {
          setGeoNotice("Location permission was not granted. You can enter coordinates manually or leave them blank.");
        } else if (geoError.code === geoError.POSITION_UNAVAILABLE) {
          setGeoNotice("Location information is currently unavailable. You can enter coordinates manually or leave them blank.");
        } else if (geoError.code === geoError.TIMEOUT) {
          setGeoNotice("Location request timed out. You can enter coordinates manually or leave them blank.");
        } else {
          setGeoNotice("Unable to retrieve location. You can enter coordinates manually or leave them blank.");
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  };

  const handleClearLocation = () => {
    setFormData((prev) => ({
      ...prev,
      latitude: "",
      longitude: "",
    }));
    setGeoNotice("GPS coordinates cleared.");
  };

  // Submit Form (Create or Update)
  const handleSubmitForm = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    // Frontend pre-validation
    if (!formData.name.trim()) {
      setError("Farm name is required.");
      return;
    }
    if (!formData.village.trim()) {
      setError("Village is required.");
      return;
    }
    if (!formData.district.trim()) {
      setError("District is required.");
      return;
    }
    if (!formData.state.trim()) {
      setError("State is required.");
      return;
    }

    const payload = {
      name: formData.name.trim(),
      village: formData.village.trim(),
      district: formData.district.trim(),
      state: formData.state.trim(),
    };

    if (formData.area_hectares.trim()) {
      const area = parseFloat(formData.area_hectares);
      if (isNaN(area) || area <= 0) {
        setError("Area must be a positive number greater than 0.");
        return;
      }
      payload.area_hectares = area;
    } else {
      payload.area_hectares = null;
    }

    if (formData.latitude.trim()) {
      const lat = parseFloat(formData.latitude);
      if (isNaN(lat) || lat < -90 || lat > 90) {
        setError("Latitude must be between -90.0 and 90.0.");
        return;
      }
      payload.latitude = lat;
    } else {
      payload.latitude = null;
    }

    if (formData.longitude.trim()) {
      const lon = parseFloat(formData.longitude);
      if (isNaN(lon) || lon < -180 || lon > 180) {
        setError("Longitude must be between -180.0 and 180.0.");
        return;
      }
      payload.longitude = lon;
    } else {
      payload.longitude = null;
    }

    try {
      setLoading(true);
      if (editingFarmId) {
        await updateFarm(editingFarmId, payload);
        setSuccessMsg(`Farm "${payload.name}" updated successfully!`);
      } else {
        await createFarm(payload);
        setSuccessMsg(`Farm "${payload.name}" registered successfully!`);
      }
      setShowForm(false);
      setEditingFarmId(null);
      await loadFarms();
    } catch (err) {
      console.error("Form submit error:", err);
      setError(err.message || "Failed to save farm.");
    } finally {
      setLoading(false);
    }
  };

  // Deactivate farm
  const handleDeactivate = async (farmId, farmName) => {
    if (!window.confirm(`Are you sure you want to remove farm "${farmName}"?`)) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await deleteFarm(farmId);
      setSuccessMsg(`Farm "${farmName}" deactivated successfully.`);
      await loadFarms();
    } catch (err) {
      console.error("Deactivate error:", err);
      setError(err.message || "Failed to deactivate farm.");
    } finally {
      setLoading(false);
    }
  };

  const displayName = userProfile?.display_name || user?.displayName || "Farmer";

  return (
    <div className="landing">
      <Navbar />
      <main className="farms-container">
        <div className="farms-inner">
          {/* Header Banner */}
          <div className="farms-banner">
            <div className="farms-banner-left">
              <div className="farms-avatar">🏡</div>
              <div>
                <h1 className="farms-title">{t("farms.title", "My Farm Profiles")}</h1>
                <p className="farms-subtitle">
                  {t("farms.subtitle", "Manage your agricultural plots, GPS coordinates, and micro-climate locations.")}
                </p>
              </div>
            </div>

            <div className="farms-banner-actions">
              <Link to="/dashboard" className="farms-btn-secondary">
                ← {t("nav.dashboard", "Dashboard")}
              </Link>
              {!showForm && (
                <button
                  type="button"
                  onClick={handleOpenAddForm}
                  className="farms-btn-primary"
                >
                  <span>+</span> {t("farms.addFarmBtn", "Register New Farm")}
                </button>
              )}
            </div>
          </div>

          {/* Feedback messages */}
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
                gap: "0.75rem",
              }}
            >
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div
              style={{
                background: "rgba(34, 197, 94, 0.15)",
                border: "1px solid rgba(34, 197, 94, 0.3)",
                color: "#86efac",
                padding: "1rem 1.25rem",
                borderRadius: "12px",
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
              }}
            >
              <span>✅</span>
              <span>{successMsg}</span>
            </div>
          )}

          {/* Farm Add / Edit Form Card */}
          {showForm && (
            <div className="farm-form-card">
              <h2 className="farm-form-title">
                <span>{editingFarmId ? "✏️" : "🌱"}</span>
                {editingFarmId ? t("farms.form.editTitle", "Edit Farm Profile") : t("farms.form.addTitle", "Register New Farm")}
              </h2>

              <form onSubmit={handleSubmitForm}>
                <div className="farm-form-grid">
                  <div className="farm-field">
                    <label className="farm-label" htmlFor="farm-name">
                      {t("farms.form.nameLabel", "Farm Name")} *
                    </label>
                    <input
                      id="farm-name"
                      name="name"
                      type="text"
                      className="farm-input"
                      placeholder={t("farms.form.namePlaceholder", "e.g. North Orchard, Green Valley Farm")}
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  <div className="farm-field">
                    <label className="farm-label" htmlFor="farm-village">
                      {t("farms.form.villageLabel", "Village / Town")} *
                    </label>
                    <input
                      id="farm-village"
                      name="village"
                      type="text"
                      className="farm-input"
                      placeholder={t("farms.form.villagePlaceholder", "e.g. Petlad, Mogri")}
                      value={formData.village}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  <div className="farm-field">
                    <label className="farm-label" htmlFor="farm-district">
                      {t("farms.form.districtLabel", "District")} *
                    </label>
                    <input
                      id="farm-district"
                      name="district"
                      type="text"
                      className="farm-input"
                      placeholder={t("farms.form.districtPlaceholder", "e.g. Anand")}
                      value={formData.district}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  <div className="farm-field">
                    <label className="farm-label" htmlFor="farm-state">
                      {t("farms.form.stateLabel", "State")} *
                    </label>
                    <input
                      id="farm-state"
                      name="state"
                      type="text"
                      className="farm-input"
                      placeholder={t("farms.form.statePlaceholder", "e.g. Gujarat")}
                      value={formData.state}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  <div className="farm-field">
                    <label className="farm-label" htmlFor="farm-area">
                      {t("farms.form.areaLabel", "Total Area (Hectares)")} <span style={{ opacity: 0.6 }}>({t("common.optional", "Optional")})</span>
                    </label>
                    <input
                      id="farm-area"
                      name="area_hectares"
                      type="number"
                      step="0.01"
                      min="0.01"
                      className="farm-input"
                      placeholder={t("farms.form.areaPlaceholder", "e.g. 2.5")}
                      value={formData.area_hectares}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>

                {/* Geolocation Section */}
                <div className="farm-geo-box">
                  <div className="farm-geo-header">
                    <div>
                      <strong style={{ color: "#f3efe4", fontSize: "0.95rem" }}>
                        {t("farms.form.gpsHeading", "GPS Coordinates")} <span style={{ opacity: 0.6, fontWeight: 400 }}>({t("common.optional", "Optional")})</span>
                      </strong>
                      <p style={{ margin: "0.2rem 0 0 0", color: "rgba(243, 239, 228, 0.65)", fontSize: "0.82rem" }}>
                        {t("farms.form.gpsDesc", "Used for localized meteorological advisory. GPS is never shared with third parties.")}
                      </p>
                    </div>

                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <button
                        type="button"
                        onClick={handleGetCurrentLocation}
                        disabled={geoLoading}
                        className="farm-geo-btn"
                      >
                        {geoLoading ? t("farms.form.locating", "Locating...") : `📍 ${t("farms.form.useMyLocation", "Use my current location")}`}
                      </button>

                      {(formData.latitude || formData.longitude) && (
                        <button
                          type="button"
                          onClick={handleClearLocation}
                          style={{
                            background: "transparent",
                            border: "1px solid rgba(220, 240, 200, 0.2)",
                            color: "rgba(243, 239, 228, 0.7)",
                            borderRadius: "8px",
                            padding: "0.4rem 0.8rem",
                            cursor: "pointer",
                            fontSize: "0.82rem",
                          }}
                        >
                          {t("farms.form.clearGps", "Clear GPS")}
                        </button>
                      )}
                    </div>
                  </div>

                  {geoNotice && (
                    <div style={{ color: "#a9d47c", fontSize: "0.85rem", marginBottom: "0.75rem" }}>
                      {geoNotice}
                    </div>
                  )}

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                    <div className="farm-field">
                      <label className="farm-label" htmlFor="farm-lat">
                        {t("farms.form.latitudeLabel", "Latitude (-90.0 to 90.0)")}
                      </label>
                      <input
                        id="farm-lat"
                        name="latitude"
                        type="number"
                        step="0.000001"
                        min="-90"
                        max="90"
                        className="farm-input"
                        placeholder="e.g. 22.4731"
                        value={formData.latitude}
                        onChange={handleInputChange}
                      />
                    </div>

                    <div className="farm-field">
                      <label className="farm-label" htmlFor="farm-lon">
                        {t("farms.form.longitudeLabel", "Longitude (-180.0 to 180.0)")}
                      </label>
                      <input
                        id="farm-lon"
                        name="longitude"
                        type="number"
                        step="0.000001"
                        min="-180"
                        max="180"
                        className="farm-input"
                        placeholder="e.g. 72.8028"
                        value={formData.longitude}
                        onChange={handleInputChange}
                      />
                    </div>
                  </div>
                </div>

                {/* Form Buttons */}
                <div style={{ display: "flex", gap: "1rem", marginTop: "1.75rem", justifyContent: "flex-end" }}>
                  <button
                    type="button"
                    onClick={handleCancelForm}
                    className="farms-btn-secondary"
                  >
                    {t("common.cancel", "Cancel")}
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="farms-btn-primary"
                  >
                    {loading ? t("common.saving", "Saving...") : editingFarmId ? t("farms.form.updateBtn", "Update Farm") : t("farms.form.saveBtn", "Save Farm")}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Farm Listing Grid */}
          {!showForm && (
            <>
              {loading && farms.length === 0 ? (
                <div style={{ textAlign: "center", padding: "3rem 0", color: "#a9d47c" }}>
                  <p>Loading farm profiles...</p>
                </div>
              ) : farms.length > 0 ? (
                <div className="farms-grid">
                  {farms.map((farm) => (
                    <div key={farm.id} className="farm-card">
                      <div className="farm-card-header">
                        <div>
                          <h3 className="farm-card-name">{farm.name}</h3>
                          <span style={{ fontSize: "0.82rem", color: "rgba(243, 239, 228, 0.6)" }}>
                            {farm.location_text}
                          </span>
                        </div>
                        {farm.has_location ? (
                          <span className="farm-badge farm-badge--gps">
                            📍 GPS Linked
                          </span>
                        ) : (
                          <span className="farm-badge farm-badge--no-gps">
                            📍 GPS Optional
                          </span>
                        )}
                      </div>

                      <div className="farm-card-body">
                        <div className="farm-card-row">
                          <span className="farm-card-term">Village / Town</span>
                          <span className="farm-card-val">{farm.village || "—"}</span>
                        </div>
                        <div className="farm-card-row">
                          <span className="farm-card-term">District & State</span>
                          <span className="farm-card-val">
                            {farm.district}, {farm.state}
                          </span>
                        </div>
                        <div className="farm-card-row">
                          <span className="farm-card-term">Land Area</span>
                          <span className="farm-card-val">
                            {farm.area_hectares ? `${farm.area_hectares} hectares` : "Not specified"}
                          </span>
                        </div>
                        {farm.has_location && (
                          <div className="farm-card-row">
                            <span className="farm-card-term">GPS Coordinates</span>
                            <span className="farm-card-val" style={{ fontSize: "0.82rem" }}>
                              {farm.latitude?.toFixed(4)}, {farm.longitude?.toFixed(4)}
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Module 13: Local Agro-Weather Section */}
                      {farm.has_location ? (
                        <div className="farm-weather-card">
                          <div className="farm-weather-header">
                            <div className="farm-weather-title">
                              <span>🌦️</span> {t("farms.weather.title", "Local Agro-Weather")}
                              <span className="farm-weather-source-badge">
                                {t("common.agroWeatherBadge", "Agro-Weather")}
                              </span>
                            </div>
                            <button
                              type="button"
                              className="farm-weather-refresh-btn"
                              disabled={farmWeather[farm.id]?.loading}
                              onClick={() => loadWeatherForFarm(farm.id, true)}
                              title={t("farms.weather.refreshTitle", "Fetch latest local weather")}
                            >
                              <span
                                style={{
                                  display: "inline-block",
                                  transform: farmWeather[farm.id]?.loading
                                    ? "rotate(180deg)"
                                    : "none",
                                  transition: "transform 0.5s ease",
                                }}
                              >
                                🔄
                              </span>
                              {farmWeather[farm.id]?.loading ? "Updating..." : "Refresh"}
                            </button>
                          </div>

                          {farmWeather[farm.id]?.loading && !farmWeather[farm.id]?.data ? (
                            <div className="farm-weather-loading">
                              <span>⏳</span> Fetching live weather snapshot...
                            </div>
                          ) : farmWeather[farm.id]?.error ? (
                            <div
                              style={{
                                color: "#fca5a5",
                                fontSize: "0.82rem",
                                padding: "0.5rem 0",
                              }}
                            >
                              ⚠️ {farmWeather[farm.id]?.error}
                            </div>
                          ) : farmWeather[farm.id]?.data ? (
                            <>
                              <div className="farm-weather-condition-banner">
                                <div className="farm-weather-condition-left">
                                  <span className="farm-weather-icon">
                                    {getWeatherIcon(
                                      farmWeather[farm.id]?.data?.weather_condition
                                    )}
                                  </span>
                                  <div>
                                    <div className="farm-weather-cond-text">
                                      {farmWeather[farm.id]?.data?.weather_condition ||
                                        "Clear"}
                                    </div>
                                    <div className="farm-weather-cache-tag">
                                      {farmWeather[farm.id]?.data?.cached
                                        ? "⚡ Cached snapshot (fresh)"
                                        : "🟢 Live observation"}
                                    </div>
                                  </div>
                                </div>
                                <div
                                  style={{
                                    fontSize: "1.4rem",
                                    fontWeight: 700,
                                    color: "#a9d47c",
                                  }}
                                >
                                  {farmWeather[farm.id]?.data?.temperature_c !== null
                                    ? `${farmWeather[farm.id]?.data?.temperature_c}°C`
                                    : "—"}
                                </div>
                              </div>

                              <div className="farm-weather-metrics-grid">
                                <div className="farm-weather-metric-tile">
                                  <div className="farm-weather-metric-label">
                                    💧 Humidity
                                  </div>
                                  <div className="farm-weather-metric-val">
                                    {farmWeather[farm.id]?.data?.humidity_pct !== null
                                      ? `${farmWeather[farm.id]?.data?.humidity_pct}%`
                                      : "—"}
                                  </div>
                                </div>
                                <div className="farm-weather-metric-tile">
                                  <div className="farm-weather-metric-label">
                                    🌧️ Rain
                                  </div>
                                  <div className="farm-weather-metric-val">
                                    {farmWeather[farm.id]?.data?.rainfall_mm !== null
                                      ? `${farmWeather[farm.id]?.data?.rainfall_mm} mm`
                                      : "0.0 mm"}
                                  </div>
                                </div>
                                <div className="farm-weather-metric-tile">
                                  <div className="farm-weather-metric-label">
                                    💨 Wind
                                  </div>
                                  <div className="farm-weather-metric-val">
                                    {farmWeather[farm.id]?.data?.wind_speed_kmh !== null
                                      ? `${farmWeather[farm.id]?.data?.wind_speed_kmh} km/h`
                                      : "—"}
                                  </div>
                                </div>
                                <div className="farm-weather-metric-tile">
                                  <div className="farm-weather-metric-label">
                                    🌡️ Temp
                                  </div>
                                  <div className="farm-weather-metric-val">
                                    {farmWeather[farm.id]?.data?.temperature_c !== null
                                      ? `${farmWeather[farm.id]?.data?.temperature_c}°C`
                                      : "—"}
                                  </div>
                                </div>
                              </div>
                            </>
                          ) : (
                            <div className="farm-weather-loading">
                              Click Refresh to load weather
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="farm-weather-no-gps-box">
                          <div className="farm-weather-no-gps-text">
                            📍 <strong>GPS not configured:</strong> Add coordinates to activate
                            weather integration.
                          </div>
                          <button
                            type="button"
                            className="farm-weather-no-gps-btn"
                            onClick={() => handleOpenEditForm(farm)}
                          >
                            + Add GPS
                          </button>
                        </div>
                      )}

                      <div className="farm-card-actions">
                        <button
                          type="button"
                          onClick={() => handleOpenEditForm(farm)}
                          className="farm-action-btn farm-action-btn--edit"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeactivate(farm.id, farm.name)}
                          className="farm-action-btn farm-action-btn--deactivate"
                        >
                          🗑️ Deactivate
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="farms-empty-state">
                  <div className="farms-empty-icon">🌾</div>
                  <h2 className="farms-empty-title">No Farm Profiles Registered Yet</h2>
                  <p className="farms-empty-desc">
                    Register your agricultural plots to track disease detections, link localized weather, and organize crop diagnoses.
                  </p>
                  <button
                    type="button"
                    onClick={handleOpenAddForm}
                    className="farms-btn-primary"
                    style={{ marginTop: "0.5rem" }}
                  >
                    <span>+</span> Register Your First Farm
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
