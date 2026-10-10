// frontend/src/pages/Diagnose.jsx
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "../context/LanguageContext";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import { fetchFarms } from "../services/farmService";
import { diagnoseLeaf, fetchScanReport } from "../services/diagnosisService";
import "../styles/landing.css";
import "../styles/diagnose.css";

export default function Diagnose() {
  const { user } = useAuth();
  const { t, language: appLanguage, supportedLanguages } = useTranslation();

  const [crop, setCrop] = useState("chili");
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [farms, setFarms] = useState([]);
  const [selectedFarmId, setSelectedFarmId] = useState("");
  const [language, setLanguage] = useState(appLanguage || "en");

  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [switchingLang, setSwitchingLang] = useState(false);

  // Sync default advisory language with global language selection
  useEffect(() => {
    if (appLanguage) {
      setLanguage(appLanguage);
    }
  }, [appLanguage]);

  // Load user's farms to enable localized context
  useEffect(() => {
    async function loadUserFarms() {
      if (!user) return;
      try {
        const farmList = await fetchFarms();
        setFarms(farmList);
        if (farmList.length > 0) {
          setSelectedFarmId(farmList[0].id);
        }
      } catch (err) {
        console.log("Farms could not be loaded for selector:", err.message);
      }
    }
    loadUserFarms();
  }, [user]);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  };

  const handleDiagnose = async () => {
    if (!crop || !imageFile) {
      setError(t("diagnose.dropzoneHint", "Please select a crop and upload a leaf photo."));
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setLoadingStep(t("diagnose.step1", "1. Analyzing leaf pathology..."));

      setTimeout(() => {
        setLoadingStep(t("diagnose.step2", "2. Linking localized weather & farm context..."));
      }, 700);

      setTimeout(() => {
        setLoadingStep(t("diagnose.step3", "3. Generating agronomic advisory report..."));
      }, 1500);

      const data = await diagnoseLeaf({
        crop,
        imageFile,
        farmId: selectedFarmId || null,
        language,
      });

      setResult(data);
    } catch (err) {
      console.error("Diagnosis error:", err);
      setError(err.message || "Failed to process leaf diagnosis.");
    } finally {
      setLoading(false);
      setLoadingStep("");
    }
  };

  const handleSwitchReportLanguage = async (targetLang) => {
    if (!result?.scan_id || switchingLang || result.report?.language_code === targetLang) return;
    try {
      setSwitchingLang(true);
      const updatedReport = await fetchScanReport(result.scan_id, targetLang);
      setResult((prev) => ({
        ...prev,
        report: updatedReport,
      }));
    } catch (err) {
      console.error("Failed to switch report language:", err);
    } finally {
      setSwitchingLang(false);
    }
  };

  return (
    <div className="landing">
      <Navbar />
      <main className="diag-container">
        <div className="diag-inner">
          {/* Header Banner */}
          <div className="diag-banner">
            <div className="diag-banner-left">
              <div className="diag-avatar">🔬</div>
              <div>
                <h1 className="diag-title">{t("diagnose.title", "Plant Disease Diagnosis & Advisory")}</h1>
                <p className="diag-subtitle">
                  {t(
                    "diagnose.subtitle",
                    "AI foliar pathology with localized agro-weather & intelligent agronomic advisory."
                  )}
                </p>
              </div>
            </div>
            <div>
              <Link to="/dashboard" className="farms-btn-secondary">
                ← {t("nav.dashboard", "Dashboard")}
              </Link>
            </div>
          </div>

          {/* Form Controls */}
          <div className="diag-card">
            <div className="diag-grid-controls">
              {/* Crop Selector */}
              <div className="diag-field">
                <label className="diag-label">{t("diagnose.targetCrop", "Target Crop")}</label>
                <select
                  value={crop}
                  onChange={(e) => {
                    setCrop(e.target.value);
                    setResult(null);
                  }}
                  className="diag-select"
                >
                  <option value="chili">🌶️ Chili Pepper ({t("diagnose.statusConfident", "Active")})</option>
                  <option value="potato" disabled>🥔 Potato</option>
                  <option value="groundnut" disabled>🥜 Groundnut</option>
                </select>
              </div>

              {/* Farm Plot Selector */}
              <div className="diag-field">
                <label className="diag-label">{t("diagnose.selectFarm", "Farm Plot Context")}</label>
                <select
                  value={selectedFarmId}
                  onChange={(e) => setSelectedFarmId(e.target.value)}
                  className="diag-select"
                >
                  {farms.length > 0 ? (
                    farms.map((f) => (
                      <option key={f.id} value={f.id}>
                        🏡 {f.name} ({f.district || f.village || "Registered"})
                      </option>
                    ))
                  ) : (
                    <option value="">{t("diagnose.noFarmGeneric", "No farm registered (Generic context)")}</option>
                  )}
                </select>
              </div>

              {/* Language Selector */}
              <div className="diag-field">
                <label className="diag-label">{t("diagnose.advisoryLang", "Advisory Language")}</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="diag-select"
                >
                  {supportedLanguages.map((l) => (
                    <option key={l.code} value={l.code}>
                      {l.flag} {l.nativeName} ({l.label})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Dropzone Upload */}
            <label className="diag-dropzone">
              <span className="diag-dropzone-icon">📷</span>
              <div className="diag-dropzone-text">
                {imageFile ? imageFile.name : t("diagnose.dropzoneTitle", "Click or drag leaf photo here to analyze")}
              </div>
              <div className="diag-dropzone-hint">
                {t(
                  "diagnose.dropzoneHint",
                  "Accepted formats: JPEG, PNG, WEBP (Max 10 MB). Focus closely on the affected leaf area."
                )}
              </div>
              <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                style={{ display: "none" }}
              />
            </label>

            {/* Image Preview */}
            {imagePreview && (
              <div className="diag-preview-box">
                <img src={imagePreview} alt="Leaf Preview" className="diag-preview-img" />
                <div>
                  <div style={{ fontWeight: 600, color: "#f3efe4" }}>
                    {t("diagnose.changeImage", "Ready for Analysis")}
                  </div>
                  <div style={{ fontSize: "0.85rem", color: "rgba(243, 239, 228, 0.65)" }}>
                    Selected: {imageFile?.name} ({(imageFile?.size / 1024).toFixed(1)} KB)
                  </div>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div
                style={{
                  marginTop: "1.25rem",
                  background: "rgba(239, 68, 68, 0.15)",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  color: "#fca5a5",
                  padding: "0.85rem 1.25rem",
                  borderRadius: "10px",
                }}
              >
                ⚠️ {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="button"
              onClick={handleDiagnose}
              disabled={!crop || !imageFile || loading}
              className="diag-submit-btn"
            >
              {loading ? (
                <span>⏳ {loadingStep || t("common.loading", "Analyzing Leaf...")}</span>
              ) : (
                <span>🔍 {t("diagnose.runBtn", "Analyze Leaf Disease")}</span>
              )}
            </button>
          </div>

          {/* DIAGNOSTIC RESULTS */}
          {result && (
            <div>
              {/* Branch 1: Low Confidence Rejection */}
              {result.status === "low_confidence" && (
                <div className="diag-rejection-card">
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                    <span style={{ fontSize: "2rem" }}>⚠️</span>
                    <div>
                      <h3 style={{ margin: 0, color: "#fde68a", fontSize: "1.2rem" }}>
                        {t("diagnose.rejectionTitle", "Diagnosis Inconclusive (Low Confidence)")}
                      </h3>
                      <div style={{ fontSize: "0.85rem", color: "rgba(253, 230, 138, 0.8)" }}>
                        {t("diagnose.confidence", "Model Confidence")}: {(result.confidence * 100).toFixed(1)}% (Threshold: {(result.threshold * 100).toFixed(0)}%)
                      </div>
                    </div>
                  </div>
                  <p style={{ margin: 0, color: "#f3efe4", lineHeight: 1.5 }}>
                    {result.message}
                  </p>
                  <div style={{ fontSize: "0.88rem", color: "rgba(243, 239, 228, 0.7)" }}>
                    {t(
                      "diagnose.rejectionAdvice",
                      "To protect your crop, the model avoids false positives. Please take a well-lit, steady photograph centered on the leaf symptoms and retry."
                    )}
                  </div>
                </div>
              )}

              {/* Branch 2: High Confidence + Structured LLM Advisory */}
              {result.status === "success" && result.report && (
                <div className="diag-report-card">
                  {/* Header */}
                  <div className="diag-report-header">
                    <div>
                      <div className="diag-badge-confident">
                        <span>✅</span> {t("diagnose.statusConfident", "Confident Diagnosis")} ({(result.confidence * 100).toFixed(1)}%)
                      </div>
                      <h2 className="diag-disease-headline">
                        {result.report.disease_name || result.disease_display_name}
                      </h2>
                      <div style={{ color: "rgba(243, 239, 228, 0.7)", fontSize: "0.9rem" }}>
                        {t("diagnose.targetCrop", "Crop")}: <strong>{result.crop.toUpperCase()}</strong> • {t("diagnose.diseaseIdentified", "Identified Condition")}:{" "}
                        <strong>{result.disease}</strong>
                      </div>
                    </div>

                    <div style={{ textAlign: "right", display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "8px" }}>
                      <span className="farm-weather-source-badge">
                        {t("diagnose.aiAdvisoryBadge", "AI Advisory")} ({result.report.language_code?.toUpperCase() || "EN"})
                      </span>

                      {/* Dynamic In-Place Language Switcher for Report */}
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span style={{ fontSize: "0.8rem", color: "rgba(243, 239, 228, 0.7)" }}>
                          {t("diagnose.switchLanguage", "Language:")}
                        </span>
                        {supportedLanguages.map((l) => (
                          <button
                            key={l.code}
                            type="button"
                            onClick={() => handleSwitchReportLanguage(l.code)}
                            disabled={switchingLang || result.report.language_code === l.code}
                            style={{
                              background: result.report.language_code === l.code ? "#6fa046" : "rgba(255, 255, 255, 0.08)",
                              border: "1px solid rgba(255, 255, 255, 0.2)",
                              color: "#f3efe4",
                              padding: "4px 8px",
                              borderRadius: "6px",
                              fontSize: "0.75rem",
                              cursor: result.report.language_code === l.code ? "default" : "pointer",
                              opacity: switchingLang ? 0.6 : 1,
                            }}
                          >
                            {l.flag} {l.nativeName}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {switchingLang && (
                    <div style={{ padding: "0.5rem 1rem", background: "rgba(111, 160, 70, 0.15)", borderRadius: "8px", color: "#a9d47c", fontSize: "0.85rem", marginBottom: "1rem" }}>
                      ⏳ {t("diagnose.translatingLang", "Generating advisory in selected language...")}
                    </div>
                  )}

                  {/* Localized Farm & Weather Context Banner */}
                  {(result.farm || result.weather) && (
                    <div className="diag-context-strip">
                      <div>
                        🏡 <strong>{t("dashboard.statActiveFarms", "Farm Plot")}:</strong> {result.farm ? `${result.farm.name} (${result.farm.location_text})` : "General Regional Context"}
                      </div>
                      {result.weather && result.weather.temperature_c !== null && (
                        <div>
                          🌦️ <strong>{t("diagnose.weatherSummary", "Weather Snapshot")}:</strong> {result.weather.temperature_c}°C • {result.weather.humidity_pct}% {t("dashboard.weatherHumidity", "Humidity")} • {result.weather.weather_condition}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Actionable Summary */}
                  <div className="diag-summary-box">
                    <strong style={{ color: "#a9d47c", display: "block", marginBottom: "0.25rem" }}>
                      {t("diagnose.tabAdvisory", "Agronomic Summary")}
                    </strong>
                    {result.report.summary}
                  </div>

                  {/* 2-Column: Symptoms & Contributing Causes */}
                  <div className="diag-section-grid">
                    <div className="diag-list-card">
                      <h3 className="diag-list-title">
                        <span>🔍</span> {t("diagnose.tabSymptoms", "Observed Symptoms")}
                      </h3>
                      <ul className="diag-list">
                        {result.report.symptoms?.map((s, idx) => (
                          <li key={idx} className="diag-list-item">
                            <span className="diag-list-bullet">•</span>
                            <span>{s}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="diag-list-card">
                      <h3 className="diag-list-title">
                        <span>🌡️</span> {t("diagnose.tabCauses", "Contributing Environmental Causes")}
                      </h3>
                      <ul className="diag-list">
                        {result.report.possible_causes?.map((c, idx) => (
                          <li key={idx} className="diag-list-item">
                            <span className="diag-list-bullet">•</span>
                            <span>{c}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Local Agricultural Context */}
                  {result.report.local_context && (
                    <div style={{ background: "rgba(111, 160, 70, 0.1)", border: "1px solid rgba(111, 160, 70, 0.25)", padding: "1rem 1.25rem", borderRadius: "12px" }}>
                      <strong style={{ color: "#a9d47c", display: "block", marginBottom: "0.25rem" }}>
                        🌾 {t("farms.district", "Regional & Micro-Climate Context")}
                      </strong>
                      <span style={{ fontSize: "0.92rem", color: "#f3efe4" }}>
                        {result.report.local_context}
                      </span>
                    </div>
                  )}

                  {/* 2-Column: Management & Prevention */}
                  <div className="diag-section-grid">
                    <div className="diag-list-card">
                      <h3 className="diag-list-title">
                        <span>🌱</span> {t("diagnose.tabManagement", "Immediate Management Steps")}
                      </h3>
                      <ul className="diag-list">
                        {result.report.management_steps?.map((step, idx) => (
                          <li key={idx} className="diag-list-item">
                            <span style={{ color: "#86efac", fontWeight: 700 }}>{idx + 1}.</span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="diag-list-card">
                      <h3 className="diag-list-title">
                        <span>🛡️</span> {t("diagnose.tabPrevention", "Prevention & Cultural Hygiene")}
                      </h3>
                      <ul className="diag-list">
                        {result.report.prevention_steps?.map((prev, idx) => (
                          <li key={idx} className="diag-list-item">
                            <span className="diag-list-bullet">✓</span>
                            <span>{prev}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Warning Signs & Escalation */}
                  {result.report.warning_signs?.length > 0 && (
                    <div className="diag-list-card" style={{ borderColor: "rgba(245, 158, 11, 0.3)" }}>
                      <h3 className="diag-list-title" style={{ color: "#fde68a" }}>
                        <span>⚠️</span> {t("diagnose.tabWarnings", "Warning Signs Requiring Prompt Escalation")}
                      </h3>
                      <ul className="diag-list">
                        {result.report.warning_signs.map((sign, idx) => (
                          <li key={idx} className="diag-list-item">
                            <span style={{ color: "#f59e0b" }}>!</span>
                            <span>{sign}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Disclaimer */}
                  <div className="diag-disclaimer-box">
                    <strong>⚖️ {t("diagnose.disclaimerTitle", "Agricultural Extension Disclaimer")}:</strong> {result.report.disclaimer}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}