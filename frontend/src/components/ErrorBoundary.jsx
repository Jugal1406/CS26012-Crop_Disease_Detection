// frontend/src/components/ErrorBoundary.jsx
import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an unhandled component error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "#0d1b10",
            color: "#f3efe4",
            padding: "2rem",
            textAlign: "center",
            fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          }}
        >
          <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🌱</div>
          <h2 style={{ fontSize: "1.6rem", marginBottom: "0.75rem", color: "#a9d47c", fontWeight: 600 }}>
            Something went wrong loading this view
          </h2>
          <p
            style={{
              maxWidth: "520px",
              color: "rgba(243, 239, 228, 0.75)",
              marginBottom: "1.5rem",
              lineHeight: 1.5,
              fontSize: "0.95rem",
            }}
          >
            {this.state.error?.message || "An unexpected error occurred while rendering the interface."}
          </p>
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", justifyContent: "center" }}>
            <button
              type="button"
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              style={{
                background: "#2e7d32",
                color: "#ffffff",
                border: "none",
                padding: "0.75rem 1.5rem",
                borderRadius: "10px",
                cursor: "pointer",
                fontWeight: 600,
                fontSize: "0.95rem",
                boxShadow: "0 4px 12px rgba(46, 125, 50, 0.3)",
              }}
            >
              🔄 Reload Application
            </button>
            <a
              href="/"
              style={{
                background: "rgba(255, 255, 255, 0.05)",
                color: "#a9d47c",
                border: "1px solid rgba(169, 212, 124, 0.3)",
                padding: "0.75rem 1.5rem",
                borderRadius: "10px",
                textDecoration: "none",
                fontWeight: 600,
                fontSize: "0.95rem",
                display: "inline-flex",
                alignItems: "center",
              }}
            >
              🏡 Return to Home
            </a>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
