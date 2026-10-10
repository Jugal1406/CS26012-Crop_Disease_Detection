// frontend/src/components/ProtectedRoute.jsx
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "60vh",
        gap: "1rem",
        color: "#166534"
      }}>
        <div style={{
          width: "40px",
          height: "40px",
          border: "4px solid #dcfce7",
          borderTop: "4px solid #16a34a",
          borderRadius: "50%",
          animation: "spin 1s linear infinite"
        }} />
        <p style={{ fontWeight: 500 }}>Verifying authentication...</p>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect unauthenticated user to /login and preserve destination
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
