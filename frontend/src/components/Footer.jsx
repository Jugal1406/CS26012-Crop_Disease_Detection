import { Link } from "react-router-dom";
import { LogoMark } from "./Icons";
import { useTranslation } from "../context/LanguageContext";
import { useAuth } from "../context/AuthContext";

export default function Footer() {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();

  const diagnoseTarget = isAuthenticated ? "/diagnose" : "/login";

  return (
    <footer className="lp-footer">
      <div className="lp-container lp-footer__inner">
        <div className="lp-footer__brand">
          <Link to="/" className="lp-nav__brand">
            <LogoMark />
            <span>{t("common.appName", "Crop Disease Detection")}</span>
          </Link>
          <p>{t("landing.footer.tagline", "AI-powered leaf diagnosis for potato, groundnut and chili.")}</p>
        </div>

        <nav className="lp-footer__nav" aria-label="Footer">
          <ul>
            <li><Link to="/">{t("nav.home", "Home")}</Link></li>
            <li><Link to={diagnoseTarget}>{t("nav.diagnose", "Diagnose")}</Link></li>
            <li><a href="#about">{t("landing.footer.about", "About")}</a></li>
            <li><a href="#technology">{t("nav.technology", "Technology")}</a></li>
          </ul>
        </nav>
      </div>
      <div className="lp-container lp-footer__base">
        <p className="lp-footer__disclaimer">{t("landing.footer.disclaimer", "Predictions are guidance, not a substitute for advice from an agronomist.")}</p>
      </div>
    </footer>
  );
}
