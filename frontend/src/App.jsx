import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ClerkProvider } from "@clerk/clerk-react";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Diagnose from "./pages/Diagnose";
import Dashboard from "./pages/Dashboard";
import Farms from "./pages/Farms";
import ScrollToTop from "./components/ScrollToTop";
import ProtectedRoute from "./components/ProtectedRoute";
import ErrorBoundary from "./components/ErrorBoundary";
import { AuthProvider } from "./context/AuthContext";
import { LanguageProvider } from "./context/LanguageContext";

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

if (!CLERK_PUBLISHABLE_KEY) {
  console.warn("Missing VITE_CLERK_PUBLISHABLE_KEY environment variable.");
}

function App() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <LanguageProvider>
        <AuthProvider>
          <BrowserRouter>
            <ScrollToTop />
            <ErrorBoundary>
              <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/history"
                element={
                  <ProtectedRoute>
                    <Dashboard defaultTab="diagnoses" />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/farms"
                element={
                  <ProtectedRoute>
                    <Farms />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/diagnose"
                element={
                  <ProtectedRoute>
                    <Diagnose />
                  </ProtectedRoute>
                }
              />
            </Routes>
            </ErrorBoundary>
          </BrowserRouter>
        </AuthProvider>
      </LanguageProvider>
    </ClerkProvider>
  );
}

export default App;
