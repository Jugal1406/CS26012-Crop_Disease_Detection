import { useEffect } from "react";
import { useTranslation } from "../context/LanguageContext";

export default function LogoutConfirmModal({ isOpen, onClose, onConfirm }) {
  const { t } = useTranslation();

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="logout-modal-title"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
        background: "rgba(5, 10, 7, 0.82)",
        backdropFilter: "blur(6px)",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "420px",
          background: "#131e16",
          border: "1px solid rgba(220, 240, 200, 0.25)",
          borderRadius: "18px",
          padding: "2rem",
          boxShadow: "0 24px 48px rgba(0, 0, 0, 0.65)",
          color: "#f3efe4",
          animation: "modalFadeIn 0.2s ease-out",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "1rem" }}>
          <div
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "12px",
              background: "rgba(239, 68, 68, 0.15)",
              border: "1px solid rgba(239, 68, 68, 0.35)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.4rem",
              flexShrink: 0,
            }}
          >
            🚪
          </div>
          <div>
            <h3
              id="logout-modal-title"
              style={{
                margin: 0,
                fontSize: "1.2rem",
                fontWeight: 700,
                letterSpacing: "-0.01em",
                color: "#fff",
              }}
            >
              {t("auth.logoutConfirmTitle", "Confirm Log Out")}
            </h3>
            <p
              style={{
                margin: "4px 0 0",
                fontSize: "0.85rem",
                color: "rgba(243, 239, 228, 0.65)",
              }}
            >
              {t("auth.logoutConfirmSubtitle", "Ending your current farmer session")}
            </p>
          </div>
        </div>

        <p
          style={{
            fontSize: "0.95rem",
            lineHeight: 1.5,
            color: "rgba(243, 239, 228, 0.85)",
            margin: "0 0 1.75rem",
          }}
        >
          {t("auth.logoutConfirmMessage", "Are you sure you want to log out of your account?")}
        </p>

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: "10px",
          }}
        >
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: "0.65rem 1.25rem",
              borderRadius: "10px",
              border: "1px solid rgba(255, 255, 255, 0.2)",
              background: "rgba(255, 255, 255, 0.06)",
              color: "#f3efe4",
              fontSize: "0.9rem",
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
          >
            {t("common.cancel", "Cancel")}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            style={{
              padding: "0.65rem 1.35rem",
              borderRadius: "10px",
              border: "none",
              background: "#dc2626",
              color: "#ffffff",
              fontSize: "0.9rem",
              fontWeight: 600,
              cursor: "pointer",
              boxShadow: "0 4px 12px rgba(220, 38, 38, 0.4)",
              transition: "all 0.2s ease",
            }}
          >
            {t("auth.logoutConfirmBtn", "Yes, Log Out")}
          </button>
        </div>
      </div>
    </div>
  );
}
