// frontend/src/components/ScanDetailModal.jsx
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "../context/LanguageContext";
import { fetchScanDetail, fetchScanImageBlobUrl, downloadScanPdf } from "../services/scanService";

export default function ScanDetailModal({ scanId, initialLang = "en", onClose }) {
  const { t, language } = useTranslation();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [imageLoading, setImageLoading] = useState(true);
  const [currentLang, setCurrentLang] = useState(initialLang || language || "en");
  const [langSwitching, setLangSwitching] = useState(false);
  const [activeReportTab, setActiveReportTab] = useState("management");
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [pdfError, setPdfError] = useState(null);

  // Load scan details
  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchScanDetail(scanId, currentLang);
        if (isMounted) {
          setScan(data);
        }
      } catch (err) {
        if (isMounted) setError(err.message);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, [scanId]);

  // Handle language switch
  const handleLanguageChange = async (newLang) => {
    if (newLang === currentLang || langSwitching) return;
    try {
      setLangSwitching(true);
      setCurrentLang(newLang);
      const updated = await fetchScanDetail(scanId, newLang);
      setScan(updated);
    } catch (err) {
      console.error("Failed to switch advisory language:", err);
    } finally {
      setLangSwitching(false);
    }
  };

  // Handle PDF report generation & download (Module 17)
  const handleDownloadPdf = async () => {
    if (downloadingPdf) return;
    try {
      setDownloadingPdf(true);
      setPdfError(null);
      await downloadScanPdf(scanId, currentLang);
    } catch (err) {
      console.error("PDF download error:", err);
      setPdfError(err.message || t("pdf.error", "Failed to download PDF report"));
    } finally {
      setDownloadingPdf(false);
    }
  };

  // Load authenticated image blob
  useEffect(() => {
    let isMounted = true;
    let objectUrl = null;

    async function loadImage() {
      try {
        setImageLoading(true);
        objectUrl = await fetchScanImageBlobUrl(scanId);
        if (isMounted) setImageUrl(objectUrl);
      } catch (err) {
        console.warn("Could not load scan image blob:", err);
      } finally {
        if (isMounted) setImageLoading(false);
      }
    }

    loadImage();

    return () => {
      isMounted = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [scanId]);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const weather = scan?.weather;
  const prediction = scan?.prediction;
  const report = scan?.report;
  const isLowConf =
    scan?.status === "low_confidence" || (prediction && !prediction.is_confident);

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(10, 16, 13, 0.82)",
        backdropFilter: "blur(6px)",
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
        overflowY: "auto",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          background: "linear-gradient(145deg, #16241b, #0f1a13)",
          border: "1px solid rgba(169, 212, 124, 0.25)",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "880px",
          maxHeight: "92vh",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.6)",
          color: "#f3efe4",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "1.25rem 1.5rem",
            borderBottom: "1px solid rgba(169, 212, 124, 0.15)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <h2 style={{ margin: 0, fontSize: "1.25rem", color: "#a9d47c" }}>
              🔬 {t("history.scanDetails", "Scan Inspection & Report")}
            </h2>
            <p style={{ margin: "0.25rem 0 0", fontSize: "0.82rem", color: "rgba(243, 239, 228, 0.65)" }}>
              {scan?.crop_display_name || "Crop"} &bull; {scan?.date_formatted || "..."}
            </p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <button
              type="button"
              onClick={handleDownloadPdf}
              disabled={downloadingPdf || loading}
              style={{
                background: "rgba(169, 212, 124, 0.15)",
                border: "1px solid rgba(169, 212, 124, 0.35)",
                color: "#a9d47c",
                padding: "0.45rem 0.85rem",
                borderRadius: "8px",
                fontSize: "0.82rem",
                fontWeight: 600,
                cursor: downloadingPdf || loading ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
                transition: "all 0.2s ease",
              }}
              title={t("pdf.downloadBtn", "Download PDF")}
            >
              {downloadingPdf ? (
                <>⏳ {t("pdf.downloading", "Generating PDF...")}</>
              ) : (
                <>📄 {t("pdf.downloadBtn", "Download PDF")}</>
              )}
            </button>
            <button
              onClick={onClose}
              style={{
                background: "rgba(255, 255, 255, 0.08)",
                border: "none",
                color: "#f3efe4",
                borderRadius: "8px",
                width: "36px",
                height: "36px",
                cursor: "pointer",
                fontSize: "1.2rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
              title="Close (Esc)"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div style={{ padding: "1.5rem", overflowY: "auto", flex: 1 }}>
          {pdfError && (
            <div
              style={{
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid #ef4444",
                borderRadius: "8px",
                padding: "0.75rem 1rem",
                color: "#fca5a5",
                marginBottom: "1rem",
                fontSize: "0.85rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span>⚠️ {pdfError}</span>
              <button
                onClick={() => setPdfError(null)}
                style={{ background: "none", border: "none", color: "#fca5a5", cursor: "pointer", fontSize: "1rem" }}
              >
                ✕
              </button>
            </div>
          )}

          {loading && (
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
              <p>{t("common.loading", "Loading scan details...")}</p>
            </div>
          )}

          {error && (
            <div
              style={{
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid #ef4444",
                borderRadius: "10px",
                padding: "1rem",
                color: "#fca5a5",
                margin: "1rem 0",
              }}
            >
              <strong>{t("common.error", "Error")}:</strong> {error}
            </div>
          )}

          {!loading && scan && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.5rem" }}>
              {/* Left Column: Image & Diagnostic Summary */}
              <div>
                {/* Leaf Image View */}
                <div
                  style={{
                    borderRadius: "12px",
                    overflow: "hidden",
                    backgroundColor: "#0d1610",
                    border: "1px solid rgba(169, 212, 124, 0.15)",
                    aspectRatio: "4 / 3",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    position: "relative",
                  }}
                >
                  {imageLoading && (
                    <div style={{ color: "rgba(243, 239, 228, 0.5)", fontSize: "0.85rem" }}>
                      Loading leaf photo...
                    </div>
                  )}
                  {imageUrl ? (
                    <img
                      src={imageUrl}
                      alt="Crop leaf scan"
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                        display: imageLoading ? "none" : "block",
                      }}
                    />
                  ) : !imageLoading ? (
                    <div style={{ textAlign: "center", padding: "1rem", color: "rgba(243, 239, 228, 0.5)" }}>
                      <span style={{ fontSize: "2rem", display: "block", marginBottom: "0.5rem" }}>🍃</span>
                      {t("history.imageNotAvailable", "Image preview unavailable")}
                    </div>
                  ) : null}
                </div>

                {/* Primary Diagnostic Metrics */}
                <div
                  style={{
                    background: "rgba(255, 255, 255, 0.04)",
                    borderRadius: "12px",
                    padding: "1rem",
                    marginTop: "1rem",
                    border: "1px solid rgba(255, 255, 255, 0.08)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                    <span style={{ fontSize: "0.85rem", color: "rgba(243, 239, 228, 0.6)" }}>{t("history.metricStatus", "Status")}</span>
                    <span
                      style={{
                        padding: "0.25rem 0.6rem",
                        borderRadius: "20px",
                        fontSize: "0.78rem",
                        fontWeight: 600,
                        backgroundColor: isLowConf
                          ? "rgba(234, 179, 8, 0.15)"
                          : "rgba(74, 222, 128, 0.15)",
                        color: isLowConf ? "#fde047" : "#86efac",
                        border: `1px solid ${isLowConf ? "rgba(234, 179, 8, 0.3)" : "rgba(74, 222, 128, 0.3)"}`,
                      }}
                    >
                      {isLowConf
                        ? t("history.statusLowConfidence", "Low Confidence")
                        : t("history.statusSuccess", "Confident Diagnosis")}
                    </span>
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                    <span style={{ fontSize: "0.85rem", color: "rgba(243, 239, 228, 0.6)" }}>{t("history.metricCondition", "Condition")}</span>
                    <strong style={{ fontSize: "0.95rem", color: prediction?.is_healthy ? "#86efac" : "#fca5a5" }}>
                      {prediction?.disease_display_name || "Uncertain"}
                    </strong>
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                    <span style={{ fontSize: "0.85rem", color: "rgba(243, 239, 228, 0.6)" }}>{t("history.metricConfidence", "Confidence")}</span>
                    <span style={{ fontWeight: 600 }}>
                      {prediction?.confidence_percentage ? `${prediction.confidence_percentage}%` : "—"}
                    </span>
                  </div>

                  {scan.farm && (
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                      <span style={{ fontSize: "0.85rem", color: "rgba(243, 239, 228, 0.6)" }}>{t("history.farmPlot", "Farm Plot")}</span>
                      <span style={{ fontSize: "0.85rem", textAlign: "right" }}>
                        {scan.farm.name} {scan.farm.village ? `(${scan.farm.village})` : ""}
                      </span>
                    </div>
                  )}
                </div>

                {/* Weather Snapshot */}
                {weather && (
                  <div
                    style={{
                      background: "rgba(255, 255, 255, 0.04)",
                      borderRadius: "12px",
                      padding: "1rem",
                      marginTop: "1rem",
                      border: "1px solid rgba(255, 255, 255, 0.08)",
                    }}
                  >
                    <h4 style={{ margin: "0 0 0.5rem", fontSize: "0.85rem", color: "#a9d47c" }}>
                      🌤️ {t("history.weatherAtScan", "Weather at Scan Time")}
                    </h4>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", fontSize: "0.82rem" }}>
                      <div>🌡️ {weather.temperature_c ?? "—"}°C</div>
                      <div>💧 {weather.humidity_pct ?? "—"}% RH</div>
                      <div>🌧️ {weather.rainfall_mm ?? 0} mm</div>
                      <div>💨 {weather.wind_speed_kmh ?? "—"} km/h</div>
                    </div>
                    {weather.weather_condition && (
                      <div style={{ marginTop: "0.5rem", fontSize: "0.8rem", color: "rgba(243, 239, 228, 0.7)" }}>
                        {t("history.weatherConditionLabel", "Condition")}: {weather.weather_condition}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Right Column: Advisory or Low Confidence Notice */}
              <div>
                {isLowConf ? (
                  <div
                    style={{
                      background: "rgba(234, 179, 8, 0.08)",
                      border: "1px solid rgba(234, 179, 8, 0.25)",
                      borderRadius: "12px",
                      padding: "1.5rem",
                    }}
                  >
                    <h3 style={{ margin: "0 0 0.75rem", color: "#fde047", fontSize: "1.05rem" }}>
                      ⚠️ {t("diagnose.rejectionTitle", "Inconclusive Scan")}
                    </h3>
                    <p style={{ margin: "0 0 1rem", fontSize: "0.88rem", lineHeight: 1.5, color: "rgba(243, 239, 228, 0.85)" }}>
                      {scan.rejection_guidance || t("history.lowConfidenceNotice", "This scan was inconclusive due to low prediction confidence.")}
                    </p>
                    <div
                      style={{
                        background: "rgba(0, 0, 0, 0.2)",
                        borderRadius: "8px",
                        padding: "0.85rem",
                        fontSize: "0.82rem",
                        color: "rgba(243, 239, 228, 0.75)",
                        marginBottom: "1.25rem",
                      }}
                    >
                      💡 {t("history.retakeTip", "Tip: For accurate AI detection, capture clear, close-up photos of leaves in good natural lighting.")}
                    </div>
                    <Link
                      to="/diagnose"
                      style={{
                        display: "inline-block",
                        background: "#a9d47c",
                        color: "#0f1a13",
                        padding: "0.6rem 1.25rem",
                        borderRadius: "8px",
                        fontWeight: 600,
                        textDecoration: "none",
                        fontSize: "0.88rem",
                      }}
                    >
                      📸 Retake Leaf Photo
                    </Link>
                  </div>
                ) : (
                  <div>
                    {/* Multilingual Advisory Switcher */}
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        marginBottom: "1rem",
                        flexWrap: "wrap",
                        gap: "0.5rem",
                      }}
                    >
                      <span style={{ fontSize: "0.88rem", fontWeight: 600, color: "#a9d47c" }}>
                        🌾 {t("history.advisoryReport", "Agricultural Advisory")}
                      </span>
                      <div style={{ display: "flex", gap: "0.4rem" }}>
                        {[
                          { code: "en", label: "English" },
                          { code: "hi", label: "हिन्दी" },
                          { code: "gu", label: "ગુજરાતી" },
                        ].map((btn) => (
                          <button
                            key={btn.code}
                            type="button"
                            onClick={() => handleLanguageChange(btn.code)}
                            disabled={langSwitching}
                            style={{
                              padding: "0.3rem 0.65rem",
                              borderRadius: "6px",
                              fontSize: "0.78rem",
                              fontWeight: 500,
                              cursor: "pointer",
                              border: "1px solid",
                              borderColor: currentLang === btn.code ? "#a9d47c" : "rgba(255, 255, 255, 0.15)",
                              backgroundColor: currentLang === btn.code ? "rgba(169, 212, 124, 0.2)" : "transparent",
                              color: currentLang === btn.code ? "#a9d47c" : "rgba(243, 239, 228, 0.8)",
                            }}
                          >
                            {btn.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {langSwitching && (
                      <div style={{ textAlign: "center", padding: "1.5rem 0", color: "#a9d47c", fontSize: "0.85rem" }}>
                        Translating advisory report...
                      </div>
                    )}

                    {!langSwitching && report ? (
                      <div>
                        {/* Report Navigation Tabs */}
                        <div
                          style={{
                            display: "flex",
                            gap: "0.3rem",
                            borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                            paddingBottom: "0.5rem",
                            marginBottom: "1rem",
                            overflowX: "auto",
                          }}
                        >
                          {[
                            { key: "management", label: t("diagnose.tabManagement", "Management") },
                            { key: "prevention", label: t("diagnose.tabPrevention", "Prevention") },
                            { key: "symptoms", label: t("diagnose.tabSymptoms", "Symptoms") },
                            { key: "causes", label: t("diagnose.tabCauses", "Causes") },
                            { key: "warnings", label: t("diagnose.tabWarnings", "Warnings") },
                          ].map((tItem) => (
                            <button
                              key={tItem.key}
                              type="button"
                              onClick={() => setActiveReportTab(tItem.key)}
                              style={{
                                padding: "0.35rem 0.7rem",
                                borderRadius: "6px",
                                border: "none",
                                fontSize: "0.8rem",
                                cursor: "pointer",
                                background: activeReportTab === tItem.key ? "rgba(169, 212, 124, 0.2)" : "transparent",
                                color: activeReportTab === tItem.key ? "#a9d47c" : "rgba(243, 239, 228, 0.7)",
                                fontWeight: activeReportTab === tItem.key ? 600 : 400,
                              }}
                            >
                              {tItem.label}
                            </button>
                          ))}
                        </div>

                        {/* Summary overview */}
                        {report.summary && (
                          <p style={{ fontSize: "0.88rem", lineHeight: 1.5, color: "rgba(243, 239, 228, 0.9)", marginBottom: "1rem" }}>
                            {report.summary}
                          </p>
                        )}

                        {/* Active Tab Content */}
                        <div
                          style={{
                            background: "rgba(0, 0, 0, 0.2)",
                            borderRadius: "10px",
                            padding: "1rem",
                            fontSize: "0.85rem",
                            lineHeight: 1.5,
                            minHeight: "140px",
                          }}
                        >
                          {activeReportTab === "management" && (
                            <ul style={{ margin: 0, paddingLeft: "1.2rem" }}>
                              {report.management_steps && report.management_steps.length > 0 ? (
                                report.management_steps.map((step, idx) => <li key={idx} style={{ marginBottom: "0.4rem" }}>{step}</li>)
                              ) : (
                                <li>No specific immediate steps recorded.</li>
                              )}
                            </ul>
                          )}

                          {activeReportTab === "prevention" && (
                            <ul style={{ margin: 0, paddingLeft: "1.2rem" }}>
                              {report.prevention_measures && report.prevention_measures.length > 0 ? (
                                report.prevention_measures.map((p, idx) => <li key={idx} style={{ marginBottom: "0.4rem" }}>{p}</li>)
                              ) : (
                                <li>Maintain standard foliar hygiene and soil aeration.</li>
                              )}
                            </ul>
                          )}

                          {activeReportTab === "symptoms" && (
                            <ul style={{ margin: 0, paddingLeft: "1.2rem" }}>
                              {report.symptoms_observed && report.symptoms_observed.length > 0 ? (
                                report.symptoms_observed.map((sym, idx) => <li key={idx} style={{ marginBottom: "0.4rem" }}>{sym}</li>)
                              ) : (
                                <li>{report.summary || "Symptoms typical for observed condition."}</li>
                              )}
                            </ul>
                          )}

                          {activeReportTab === "causes" && (
                            <p style={{ margin: 0 }}>
                              {report.probable_causes || "Fungal spores or moisture saturation in foliar canopy."}
                            </p>
                          )}

                          {activeReportTab === "warnings" && (
                            <ul style={{ margin: 0, paddingLeft: "1.2rem", color: "#fca5a5" }}>
                              {report.warning_triggers && report.warning_triggers.length > 0 ? (
                                report.warning_triggers.map((w, idx) => <li key={idx} style={{ marginBottom: "0.4rem" }}>{w}</li>)
                              ) : (
                                <li>Monitor canopy weekly. Inspect neighboring plants if lesions spread.</li>
                              )}
                            </ul>
                          )}
                        </div>

                        {/* Statutory Disclaimer */}
                        {report.disclaimer && (
                          <div
                            style={{
                              marginTop: "1rem",
                              fontSize: "0.72rem",
                              color: "rgba(243, 239, 228, 0.45)",
                              borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                              paddingTop: "0.5rem",
                            }}
                          >
                            ℹ️ {report.disclaimer}
                          </div>
                        )}
                      </div>
                    ) : !langSwitching ? (
                      <div
                        style={{
                          background: "rgba(255, 255, 255, 0.03)",
                          borderRadius: "10px",
                          padding: "1.5rem",
                          textAlign: "center",
                          color: "rgba(243, 239, 228, 0.6)",
                          fontSize: "0.85rem",
                        }}
                      >
                        {t("history.noAdvisoryAvailable", "No agricultural advisory available for this scan.")}
                      </div>
                    ) : null}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
