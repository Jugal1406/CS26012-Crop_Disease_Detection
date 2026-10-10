// frontend/src/pages/Login.jsx
import React, { useEffect, useState, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useSignIn, useSignUp } from "@clerk/clerk-react";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "../context/LanguageContext";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import "../styles/landing.css";
import "../styles/auth.css";

// SVG Google Icon
function GoogleIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#EA4335"
        d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.8 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.4l3.7 2.9C6.5 7.4 9 5 12 5z"
      />
      <path
        fill="#4285F4"
        d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"
      />
      <path
        fill="#FBBC05"
        d="M5.6 14.7c-.2-.7-.4-1.5-.4-2.7s.2-2 .4-2.7L1.9 6.4C.7 8.8 0 10.8 0 12s.7 3.2 1.9 5.6l3.7-2.9z"
      />
      <path
        fill="#34A853"
        d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.4-6.4-5.3L1.9 16C3.7 19.8 7.5 23 12 23z"
      />
    </svg>
  );
}

export default function Login() {
  const { isAuthenticated, syncWithBackend } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  const { isLoaded: signInLoaded, signIn, setActive: setSignInActive } = useSignIn();
  const { isLoaded: signUpLoaded, signUp, setActive: setSignUpActive } = useSignUp();

  // Screen modes: "login" | "signup" | "otp" | "forgot" | "reset"
  const [mode, setMode] = useState("login");

  // Form input states
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");

  // UI status states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // OTP cooldown timer in seconds
  const [cooldown, setCooldown] = useState(0);
  const cooldownRef = useRef(null);

  // Safe destination helper (validates internal path; defaults to /dashboard)
  const getSafeDestination = () => {
    const raw = location.state?.from?.pathname;
    if (raw && typeof raw === "string" && raw.startsWith("/") && !raw.startsWith("//") && raw !== "/login") {
      return raw;
    }
    return "/dashboard";
  };

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate(getSafeDestination(), { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Cooldown countdown handler
  useEffect(() => {
    if (cooldown > 0) {
      cooldownRef.current = setTimeout(() => {
        setCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearTimeout(cooldownRef.current);
  }, [cooldown]);

  const clearMessages = () => {
    setError(null);
    setSuccessMessage(null);
  };

  const parseClerkError = (err) => {
    if (err?.errors && err.errors.length > 0) {
      const first = err.errors[0];
      return first.longMessage || first.message || t("auth.generalError", "Authentication failed.");
    }
    return err?.message || t("auth.generalError", "Authentication failed.");
  };

  // ---------------------------------------------------------------------------
  // 1. SIGN IN (Email & Password)
  // ---------------------------------------------------------------------------
  const handleSignIn = async (e) => {
    e.preventDefault();
    clearMessages();

    if (!signInLoaded) return;
    if (!email.trim() || !password) {
      setError(t("auth.generalError", "Please provide both email and password."));
      return;
    }

    try {
      setLoading(true);
      const result = await signIn.create({
        identifier: email.trim().toLowerCase(),
        password,
      });

      if (result.status === "complete") {
        await setSignInActive({ session: result.createdSessionId });
        await syncWithBackend();
        navigate(getSafeDestination(), { replace: true });
      } else {
        setError(t("auth.generalError", "Sign in incomplete. Additional verification required."));
      }
    } catch (err) {
      console.error("Sign-in error:", err);
      setError(parseClerkError(err));
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 2. SIGN UP (Email & Password + Email OTP initiation)
  // ---------------------------------------------------------------------------
  const handleSignUp = async (e) => {
    e.preventDefault();
    clearMessages();

    if (!signUpLoaded) return;

    if (!fullName.trim()) {
      setError(t("auth.nameRequired", "Full name is required."));
      return;
    }
    if (!email.trim()) {
      setError(t("auth.emailRequired", "Valid email address is required."));
      return;
    }
    if (password.length < 8) {
      setError(t("auth.passwordTooShort", "Password must be at least 8 characters long."));
      return;
    }
    if (password !== confirmPassword) {
      setError(t("auth.passwordsMismatch", "Passwords do not match."));
      return;
    }

    try {
      setLoading(true);
      // Split display name into first/last
      const nameParts = fullName.trim().split(" ");
      const firstName = nameParts[0] || fullName.trim();
      const lastName = nameParts.slice(1).join(" ") || "";

      await signUp.create({
        emailAddress: email.trim().toLowerCase(),
        password,
        firstName,
        lastName,
      });

      // Send OTP code to email
      await signUp.prepareEmailAddressVerification({
        strategy: "email_code",
      });

      setMode("otp");
      setCooldown(30);
      setSuccessMessage(t("auth.subtitleOtp", "We sent a 6-digit verification code to") + ` ${email.trim()}`);
    } catch (err) {
      console.error("Sign-up error:", err);
      setError(parseClerkError(err));
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 3. OTP VERIFICATION (Sign Up completion)
  // ---------------------------------------------------------------------------
  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    clearMessages();

    if (!signUpLoaded) return;
    if (!otp.trim()) {
      setError(t("auth.otpRequired", "Please enter the 6-digit verification code."));
      return;
    }

    try {
      setLoading(true);
      const completeSignUp = await signUp.attemptEmailAddressVerification({
        code: otp.trim(),
      });

      if (completeSignUp.status === "complete") {
        await setSignUpActive({ session: completeSignUp.createdSessionId });
        await syncWithBackend(fullName.trim());
        navigate(getSafeDestination(), { replace: true });
      } else {
        setError(t("auth.generalError", "Verification could not be completed. Please check your code."));
      }
    } catch (err) {
      console.error("OTP verification error:", err);
      setError(parseClerkError(err));
    } finally {
      setLoading(false);
    }
  };

  // Resend OTP handler
  const handleResendOtp = async () => {
    if (cooldown > 0 || !signUpLoaded) return;
    clearMessages();

    try {
      setLoading(true);
      await signUp.prepareEmailAddressVerification({ strategy: "email_code" });
      setCooldown(45);
      setSuccessMessage(t("auth.subtitleOtp", "Verification code resent to") + ` ${email.trim()}`);
    } catch (err) {
      console.error("Resend OTP error:", err);
      setError(parseClerkError(err));
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 4. FORGOT PASSWORD & RESET PASSWORD
  // ---------------------------------------------------------------------------
  const handleRequestPasswordReset = async (e) => {
    e.preventDefault();
    clearMessages();

    if (!signInLoaded) return;
    if (!email.trim()) {
      setError(t("auth.emailRequired", "Valid email address is required."));
      return;
    }

    try {
      setLoading(true);
      await signIn.create({
        strategy: "reset_password_email_code",
        identifier: email.trim().toLowerCase(),
      });
      setMode("reset");
      setSuccessMessage(t("auth.subtitleReset", "Enter the code sent to your email along with your new password."));
    } catch (err) {
      console.error("Password reset request error:", err);
      setError(parseClerkError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleCompletePasswordReset = async (e) => {
    e.preventDefault();
    clearMessages();

    if (!signInLoaded) return;
    if (!otp.trim()) {
      setError(t("auth.otpRequired", "Please enter the verification code."));
      return;
    }
    if (newPassword.length < 8) {
      setError(t("auth.passwordTooShort", "Password must be at least 8 characters long."));
      return;
    }

    try {
      setLoading(true);
      const result = await signIn.attemptFirstFactor({
        strategy: "reset_password_email_code",
        code: otp.trim(),
        password: newPassword,
      });

      if (result.status === "complete") {
        await setSignInActive({ session: result.createdSessionId });
        await syncWithBackend();
        const destination = location.state?.from?.pathname || "/dashboard";
        navigate(destination, { replace: true });
      } else {
        setMode("login");
        setSuccessMessage("Password reset successful. Please sign in with your new password.");
      }
    } catch (err) {
      console.error("Password reset completion error:", err);
      setError(parseClerkError(err));
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 5. GOOGLE OAUTH
  // ---------------------------------------------------------------------------
  const handleGoogleSignIn = async () => {
    clearMessages();
    const activeClient = mode === "signup" ? signUp : signIn;
    if (!activeClient) return;

    try {
      setLoading(true);
      await activeClient.authenticateWithRedirect({
        strategy: "oauth_google",
        redirectUrl: "/login",
        redirectUrlComplete: getSafeDestination(),
      });
    } catch (err) {
      console.error("Google sign-in error:", err);
      setError(parseClerkError(err));
      setLoading(false);
    }
  };

  return (
    <div className="landing">
      <Navbar />
      <div className="auth-page-container">
        <div className="auth-card">
          {/* Header Title & Subtitle */}
          <div className="auth-header">
            <h1 className="auth-title">
              {mode === "signup" && t("auth.titleSignup", "Create Your Account")}
              {mode === "login" && t("auth.titleLogin", "Welcome Back, Farmer")}
              {mode === "otp" && t("auth.titleOtp", "Verify Your Email")}
              {mode === "forgot" && t("auth.titleForgot", "Reset Your Password")}
              {mode === "reset" && t("auth.titleReset", "Set New Password")}
            </h1>
            <p className="auth-subtitle">
              {mode === "signup" && t("auth.subtitleSignup", "Register to track crop health, receive AI diagnostics, and manage farm records.")}
              {mode === "login" && t("auth.subtitleLogin", "Sign in with your email and password to access your personalized farm diagnostics.")}
              {mode === "otp" && `${t("auth.subtitleOtp", "We sent a 6-digit verification code to")} ${email}`}
              {mode === "forgot" && t("auth.subtitleForgot", "Enter your registered email address and we will send a password reset code.")}
              {mode === "reset" && t("auth.subtitleReset", "Enter the code sent to your email along with your new password.")}
            </p>
          </div>

          {/* Mode Switch Tabs (Sign In vs Create Account) */}
          {(mode === "login" || mode === "signup") && (
            <div className="auth-tabs">
              <button
                type="button"
                className={`auth-tab-btn ${mode === "login" ? "active" : ""}`}
                onClick={() => {
                  setMode("login");
                  clearMessages();
                }}
              >
                {t("nav.login", "Log In")}
              </button>
              <button
                type="button"
                className={`auth-tab-btn ${mode === "signup" ? "active" : ""}`}
                onClick={() => {
                  setMode("signup");
                  clearMessages();
                }}
              >
                {t("auth.registerLink", "Create Account")}
              </button>
            </div>
          )}

          {/* Error & Success Feedback Banners */}
          {error && (
            <div className="auth-alert auth-alert--error" role="alert">
              <span>⚠️</span>
              <div>{error}</div>
            </div>
          )}

          {successMessage && (
            <div className="auth-alert auth-alert--success" role="status">
              <span>✓</span>
              <div>{successMessage}</div>
            </div>
          )}

          {/* =============================================================== */}
          {/* A. SIGN IN FORM */}
          {/* =============================================================== */}
          {mode === "login" && (
            <form onSubmit={handleSignIn}>
              <div className="auth-form-group">
                <label className="auth-label" htmlFor="login-email">
                  {t("auth.emailLabel", "Email Address")}
                </label>
                <input
                  id="login-email"
                  type="email"
                  className="auth-input"
                  placeholder={t("auth.emailPlaceholder", "farmer@example.com")}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>

              <div className="auth-form-group">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <label className="auth-label" htmlFor="login-password">
                    {t("auth.passwordLabel", "Password")}
                  </label>
                  <button
                    type="button"
                    className="auth-text-btn"
                    onClick={() => {
                      setMode("forgot");
                      clearMessages();
                    }}
                  >
                    {t("auth.forgotPasswordLink", "Forgot password?")}
                  </button>
                </div>
                <input
                  id="login-password"
                  type="password"
                  className="auth-input"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>

              <button type="submit" className="auth-submit-btn" disabled={loading || !signInLoaded}>
                {loading ? t("auth.signingIn", "Signing in...") : t("auth.signInBtn", "Sign In")}
              </button>

              <div className="auth-divider">{t("common.or", "OR")}</div>

              <button
                type="button"
                className="auth-google-btn"
                onClick={handleGoogleSignIn}
                disabled={loading}
              >
                <GoogleIcon />
                {t("auth.googleSignIn", "Continue with Google")}
              </button>

              <div className="auth-mode-switch">
                <span>{t("auth.noAccount", "Don't have an account?")}</span>
                <button
                  type="button"
                  className="auth-mode-link"
                  onClick={() => {
                    setMode("signup");
                    clearMessages();
                  }}
                >
                  {t("auth.registerLink", "Create an account")}
                </button>
              </div>
            </form>
          )}

          {/* =============================================================== */}
          {/* B. SIGN UP FORM */}
          {/* =============================================================== */}
          {mode === "signup" && (
            <form onSubmit={handleSignUp}>
              <div className="auth-form-group">
                <label className="auth-label" htmlFor="signup-name">
                  {t("auth.fullNameLabel", "Full Name")}
                </label>
                <input
                  id="signup-name"
                  type="text"
                  className="auth-input"
                  placeholder={t("auth.fullNamePlaceholder", "e.g. Ramesh Patel")}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoComplete="name"
                  required
                />
              </div>

              <div className="auth-form-group">
                <label className="auth-label" htmlFor="signup-email">
                  {t("auth.emailLabel", "Email Address")}
                </label>
                <input
                  id="signup-email"
                  type="email"
                  className="auth-input"
                  placeholder={t("auth.emailPlaceholder", "farmer@example.com")}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>

              <div className="auth-form-group">
                <label className="auth-label" htmlFor="signup-password">
                  {t("auth.passwordLabel", "Password")}
                </label>
                <input
                  id="signup-password"
                  type="password"
                  className="auth-input"
                  placeholder={t("auth.passwordPlaceholder", "Enter password (min. 8 characters)")}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
              </div>

              <div className="auth-form-group">
                <label className="auth-label" htmlFor="signup-confirm-password">
                  {t("auth.confirmPasswordLabel", "Confirm Password")}
                </label>
                <input
                  id="signup-confirm-password"
                  type="password"
                  className="auth-input"
                  placeholder={t("auth.confirmPasswordPlaceholder", "Re-enter your password")}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
              </div>

              <button type="submit" className="auth-submit-btn" disabled={loading || !signUpLoaded}>
                {loading ? t("auth.creatingAccount", "Creating account...") : t("auth.signUpBtn", "Create Account")}
              </button>

              <div className="auth-divider">{t("common.or", "OR")}</div>

              <button
                type="button"
                className="auth-google-btn"
                onClick={handleGoogleSignIn}
                disabled={loading}
              >
                <GoogleIcon />
                {t("auth.googleSignIn", "Continue with Google")}
              </button>

              <div className="auth-mode-switch">
                <span>{t("auth.haveAccount", "Already have an account?")}</span>
                <button
                  type="button"
                  className="auth-mode-link"
                  onClick={() => {
                    setMode("login");
                    clearMessages();
                  }}
                >
                  {t("auth.loginLink", "Sign in here")}
                </button>
              </div>
            </form>
          )}

          {/* =============================================================== */}
          {/* C. EMAIL OTP VERIFICATION FORM */}
          {/* =============================================================== */}
          {mode === "otp" && (
            <form onSubmit={handleVerifyOtp}>
              <div className="auth-form-group">
                <label className="auth-label" htmlFor="otp-input">
                  {t("auth.otpLabel", "6-Digit Verification Code")}
                </label>
                <input
                  id="otp-input"
                  type="text"
                  maxLength={6}
                  className="auth-input"
                  placeholder="123456"
                  style={{ letterSpacing: "6px", textAlign: "center", fontSize: "1.4rem" }}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                  autoFocus
                  required
                />
              </div>

              <button type="submit" className="auth-submit-btn" disabled={loading || otp.length < 6}>
                {loading ? t("auth.verifying", "Verifying...") : t("auth.verifyOtpBtn", "Verify & Complete Registration")}
              </button>

              <div className="auth-resend-row">
                <span>
                  {cooldown > 0
                    ? `${t("auth.resendCooldown", "Resend code in")} ${cooldown}s`
                    : t("auth.resendOtp", "Didn't receive code?")}
                </span>
                <button
                  type="button"
                  className="auth-text-btn"
                  onClick={handleResendOtp}
                  disabled={cooldown > 0 || loading}
                >
                  {t("auth.resendOtp", "Resend Code")}
                </button>
              </div>

              <div className="auth-mode-switch" style={{ marginTop: "2rem" }}>
                <button
                  type="button"
                  className="auth-mode-link"
                  onClick={() => {
                    setMode("signup");
                    clearMessages();
                  }}
                >
                  ← {t("common.back", "Back to registration")}
                </button>
              </div>
            </form>
          )}

          {/* =============================================================== */}
          {/* D. FORGOT PASSWORD (REQUEST CODE) */}
          {/* =============================================================== */}
          {mode === "forgot" && (
            <form onSubmit={handleRequestPasswordReset}>
              <div className="auth-form-group">
                <label className="auth-label" htmlFor="forgot-email">
                  {t("auth.emailLabel", "Email Address")}
                </label>
                <input
                  id="forgot-email"
                  type="email"
                  className="auth-input"
                  placeholder={t("auth.emailPlaceholder", "farmer@example.com")}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>

              <button type="submit" className="auth-submit-btn" disabled={loading || !signInLoaded}>
                {loading ? t("auth.sendingCode", "Sending code...") : t("auth.sendResetCodeBtn", "Send Password Reset Code")}
              </button>

              <div className="auth-mode-switch">
                <button
                  type="button"
                  className="auth-mode-link"
                  onClick={() => {
                    setMode("login");
                    clearMessages();
                  }}
                >
                  ← {t("auth.backToLogin", "Back to Sign In")}
                </button>
              </div>
            </form>
          )}

          {/* =============================================================== */}
          {/* E. RESET PASSWORD (SUBMIT CODE & NEW PASSWORD) */}
          {/* =============================================================== */}
          {mode === "reset" && (
            <form onSubmit={handleCompletePasswordReset}>
              <div className="auth-form-group">
                <label className="auth-label" htmlFor="reset-code">
                  {t("auth.otpLabel", "6-Digit Verification Code")}
                </label>
                <input
                  id="reset-code"
                  type="text"
                  maxLength={6}
                  className="auth-input"
                  placeholder="123456"
                  style={{ letterSpacing: "6px", textAlign: "center", fontSize: "1.4rem" }}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                  autoFocus
                  required
                />
              </div>

              <div className="auth-form-group">
                <label className="auth-label" htmlFor="reset-new-password">
                  {t("auth.newPasswordLabel", "New Password")}
                </label>
                <input
                  id="reset-new-password"
                  type="password"
                  className="auth-input"
                  placeholder={t("auth.newPasswordPlaceholder", "Enter new secure password (min. 8 characters)")}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  minLength={8}
                  required
                />
              </div>

              <button type="submit" className="auth-submit-btn" disabled={loading || !signInLoaded}>
                {loading ? t("auth.verifying", "Updating...") : t("auth.submitNewPasswordBtn", "Update Password & Sign In")}
              </button>

              <div className="auth-mode-switch">
                <button
                  type="button"
                  className="auth-mode-link"
                  onClick={() => {
                    setMode("login");
                    clearMessages();
                  }}
                >
                  ← {t("auth.backToLogin", "Back to Sign In")}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
      <Footer />
    </div>
  );
}