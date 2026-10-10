import { useRef } from "react";
import { Link } from "react-router-dom";
import { MEDIA } from "../content/landing";
import { useScrollProgress } from "../hooks/useScrollProgress";
import { FieldRows } from "./plant/FieldRows";
import { Icon } from "./Icons";
import { Reveal, RevealHeading } from "./Reveal";
import { useTranslation } from "../context/LanguageContext";
import { useAuth } from "../context/AuthContext";

export default function FinalCTA() {
  const { t, language } = useTranslation();
  const { isAuthenticated } = useAuth();
  const ref = useRef(null);
  const p = useScrollProgress(ref, { smoothing: 0.2, mode: "pass" });

  const diagnoseTarget = isAuthenticated ? "/diagnose" : "/login";

  return (
    <section ref={ref} className="lp-cta" aria-labelledby="cta-title">
      <div className="lp-cta__bg" aria-hidden="true">
        {MEDIA.finalBackdrop ? (
          <img src={MEDIA.finalBackdrop} alt="" loading="lazy" className="lp-cta__photo" />
        ) : (
          <>
            <div className="lp-cta__sky" />
            <div className="lp-cta__sun" style={{ transform: `translateY(${(40 - p * 80).toFixed(1)}px)` }} />
            <div className="lp-cta__field" style={{ transform: `translateY(${(30 - p * 30).toFixed(1)}px)` }}>
              <FieldRows variant="cta" seed={3} className="lp-fill" />
            </div>
          </>
        )}
        <div className="lp-cta__overlay" />
      </div>

      <div className="lp-container lp-cta__content">
        <RevealHeading
          key={`cta-title-${language}`}
          id="cta-title"
          text={t("landing.cta.title", "Give Your Crops a Healthier Tomorrow.")}
          className="lp-h2 lp-cta__title"
        />
        <Reveal as="p" className="lp-lead" delay={250}>
          {t("landing.cta.lead", "Photograph a leaf, get a diagnosis in moments, and act before a disease spreads.")}
        </Reveal>
        <Reveal delay={400}>
          <Link to={diagnoseTarget} className="lp-btn lp-btn--primary lp-btn--lg">
            {t("landing.cta.button", "Start Diagnosis")} <Icon name="arrow" size={18} />
          </Link>
        </Reveal>
      </div>
    </section>
  );
}
