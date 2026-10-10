import { useRef } from "react";
import { STEPS } from "../content/landing";
import { useInView } from "../hooks/useInView";
import { Icon } from "./Icons";
import { Reveal, RevealHeading } from "./Reveal";
import { useTranslation } from "../context/LanguageContext";

// node height on the desktop vine as a fraction of its 160px box (matches the path below)
const NODE_Y = [0.375, 0.6875, 0.375, 0.6875, 0.375];
const H_PATH =
  "M0 90 C50 90 60 60 100 60 S200 110 300 110 S420 60 500 60 S620 110 700 110 S820 60 900 60 S980 90 1000 90";
const V_PATH = "M30 0 C10 100 50 100 30 200 S10 300 30 400 S50 500 30 600 S10 700 30 800 S50 900 30 1000";

function SproutLeaf({ flip }) {
  return (
    <svg viewBox="0 0 40 24" className={`lp-vine__leaf ${flip ? "is-flip" : ""}`} aria-hidden="true">
      <path d="M2 20C8 6 20 2 38 4 30 18 18 23 2 20Z" fill="#6f9e45" />
      <path d="M2 20C14 14 24 9 34 6" stroke="#d6e8b4" strokeWidth="1" fill="none" opacity=".7" />
    </svg>
  );
}

export default function HowItWorks() {
  const { t, language } = useTranslation();
  const vineRef = useRef(null);
  const drawn = useInView(vineRef, { threshold: 0.3 });

  return (
    <section id="how-it-works" className="lp-section lp-how" aria-labelledby="how-title">
      <div className="lp-container">
        <header className="lp-section__head">
          <Reveal as="p" className="lp-eyebrow">
            {t("landing.howItWorks.eyebrow", "How it works")}
          </Reveal>
          <RevealHeading
            key={`how-title-${language}`}
            id="how-title"
            text={t("landing.howItWorks.title", "One Image. Intelligent Diagnosis.")}
            className="lp-h2"
          />
          <Reveal as="p" className="lp-lead" delay={200}>
            {t("landing.howItWorks.lead", "No equipment, no lab. A clear photo of one leaf is all the app needs.")}
          </Reveal>
        </header>

        <div ref={vineRef} className={`lp-vine ${drawn ? "is-drawn" : ""}`}>
          {/* desktop: a vine running left to right */}
          <svg className="lp-vine__path lp-vine__path--h" viewBox="0 0 1000 160" preserveAspectRatio="none" aria-hidden="true">
            <path d={H_PATH} pathLength="1" />
          </svg>
          {/* mobile: the same vine running top to bottom */}
          <svg className="lp-vine__path lp-vine__path--v" viewBox="0 0 60 1000" preserveAspectRatio="none" aria-hidden="true">
            <path d={V_PATH} pathLength="1" />
          </svg>

          <ol className="lp-steps">
            {STEPS.map((s, i) => {
              const stepTitle = t(`landing.howItWorks.steps.${i}.title`, s.title);
              const stepText = t(`landing.howItWorks.steps.${i}.text`, s.text);
              const stepLabel = t("landing.howItWorks.step", "Step");

              return (
                <li key={s.title} className="lp-step" style={{ "--yf": NODE_Y[i], "--i": i }}>
                  <span className="lp-step__node">
                    <Icon name={s.icon} size={26} />
                    <SproutLeaf flip={i % 2 === 1} />
                  </span>
                  <div className="lp-step__text">
                    <p className="lp-step__num">
                      {stepLabel} {i + 1}
                    </p>
                    <h3 className="lp-step__title">{stepTitle}</h3>
                    <p className="lp-step__body">{stepText}</p>
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
      </div>
    </section>
  );
}
