import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Icon, LogoMark } from "./Icons";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "../context/LanguageContext";
import LogoutConfirmModal from "./LogoutConfirmModal";

export default function Navbar() {
  const { isAuthenticated, logout } = useAuth();
  const { t, language, changeLanguage, supportedLanguages } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();

  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);

  const isLandingPage = location.pathname === "/";

  // Landing page specific anchor links
  const landingTabs = [
    { href: "#how-it-works", label: t("nav.howItWorks", "How it works") },
    { href: "#crops", label: t("nav.crops", "Crops") },
    { href: "#technology", label: t("nav.technology", "Technology") },
  ];

  // Post-login application links (available after login only)
  const appTabs = [
    { to: "/dashboard", label: t("nav.dashboard", "Dashboard") },
    { to: "/farms", label: t("nav.farms", "My Farms") },
    { to: "/history", label: t("nav.history", "History") },
  ];

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const close = () => setOpen(false);

  const handleOpenLogout = () => {
    close();
    setShowLogoutModal(true);
  };

  const handleConfirmLogout = async () => {
    setShowLogoutModal(false);
    await logout();
    navigate("/login");
  };

  const diagnoseDestination = isAuthenticated ? "/diagnose" : "/login";

  return (
    <>
      <header className={`lp-nav ${scrolled ? "is-scrolled" : ""} ${open ? "is-open" : ""}`}>
        <nav className="lp-nav__inner" aria-label="Main">
          <Link to="/" className="lp-nav__brand" onClick={close}>
            <LogoMark />
            <span>{t("common.appName", "Crop Disease Detection")}</span>
          </Link>

          <button
            type="button"
            className="lp-nav__toggle"
            aria-expanded={open}
            aria-controls="lp-nav-menu"
            onClick={() => setOpen((o) => !o)}
          >
            <Icon name={open ? "close" : "menu"} />
            <span className="lp-sr">{open ? t("nav.closeMenu", "Close menu") : t("nav.openMenu", "Open menu")}</span>
          </button>

          <div id="lp-nav-menu" className="lp-nav__menu">
            <ul className="lp-nav__links">
              {isLandingPage ? (
                /* LANDING PAGE ONLY: Keep How it works, Crops, and Technology */
                <>
                  {landingTabs.map((l) => (
                    <li key={l.href}>
                      <a href={l.href} onClick={close}>
                        {l.label}
                      </a>
                    </li>
                  ))}

                  {isAuthenticated ? (
                    <>
                      <li>
                        <Link to="/dashboard" onClick={close}>
                          {t("nav.dashboard", "Dashboard")}
                        </Link>
                      </li>
                      <li>
                        <button
                          type="button"
                          onClick={handleOpenLogout}
                          style={{
                            background: "none",
                            border: "none",
                            color: "rgba(243, 239, 228, 0.72)",
                            font: "inherit",
                            cursor: "pointer",
                            padding: 0,
                          }}
                        >
                          {t("nav.logout", "Log out")}
                        </button>
                      </li>
                    </>
                  ) : (
                    <li>
                      <Link to="/login" onClick={close}>
                        {t("nav.login", "Log In")}
                      </Link>
                    </li>
                  )}
                </>
              ) : (
                /* OTHER PAGES: Available after login only (Dashboard, My Farms, History), NEVER the 3 landing tabs */
                <>
                  {isAuthenticated ? (
                    <>
                      {appTabs.map((l) => (
                        <li key={l.to}>
                          <Link to={l.to} onClick={close}>
                            {l.label}
                          </Link>
                        </li>
                      ))}
                      <li>
                        <button
                          type="button"
                          onClick={handleOpenLogout}
                          style={{
                            background: "none",
                            border: "none",
                            color: "rgba(243, 239, 228, 0.72)",
                            font: "inherit",
                            cursor: "pointer",
                            padding: 0,
                          }}
                        >
                          {t("nav.logout", "Log out")}
                        </button>
                      </li>
                    </>
                  ) : (
                    <>
                      <li>
                        <Link to="/" onClick={close}>
                          {t("nav.home", "Home")}
                        </Link>
                      </li>
                      <li>
                        <Link to="/login" onClick={close}>
                          {t("nav.login", "Log In")}
                        </Link>
                      </li>
                    </>
                  )}
                </>
              )}
            </ul>

            {/* Language Switcher Dropdown */}
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <select
                value={language}
                onChange={(e) => changeLanguage(e.target.value)}
                style={{
                  background: "rgba(255, 255, 255, 0.08)",
                  border: "1px solid rgba(255, 255, 255, 0.2)",
                  color: "#f3efe4",
                  padding: "6px 10px",
                  borderRadius: "8px",
                  fontSize: "0.85rem",
                  fontWeight: "500",
                  cursor: "pointer",
                  outline: "none",
                }}
                aria-label={t("nav.language", "Language")}
              >
                {supportedLanguages.map((l) => (
                  <option key={l.code} value={l.code} style={{ background: "#18221b", color: "#f3efe4" }}>
                    {l.flag} {l.nativeName}
                  </option>
                ))}
              </select>

              <Link
                to={diagnoseDestination}
                className="lp-btn lp-btn--primary lp-btn--sm"
                onClick={close}
              >
                {t("nav.diagnose", "Diagnose Leaf")}
              </Link>
            </div>
          </div>
        </nav>
      </header>

      {/* Confirmation Dialog for Logout */}
      <LogoutConfirmModal
        isOpen={showLogoutModal}
        onClose={() => setShowLogoutModal(false)}
        onConfirm={handleConfirmLogout}
      />
    </>
  );
}
