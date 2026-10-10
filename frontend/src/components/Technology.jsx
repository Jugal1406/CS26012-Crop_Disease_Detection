import { TECH } from "../content/landing";
import { LeafCloseup } from "./plant/LeafArt";
import { Icon } from "./Icons";
import { Reveal, RevealHeading } from "./Reveal";
import { useTranslation } from "../context/LanguageContext";

export default function Technology() {
  const { t, language } = useTranslation();

  return (
    <section id="technology" className="lp-section lp-tech" aria-labelledby="tech-title">
      <div className="lp-container">
        <header className="lp-section__head lp-section__head--light">
          <Reveal as="p" className="lp-eyebrow">
            {t("landing.technology.eyebrow", "Technology")}
          </Reveal>
          <RevealHeading
            key={`tech-title-${language}`}
            id="tech-title"
            text={t("landing.technology.title", "Powered by Deep Learning")}
            className="lp-h2"
          />
          <Reveal as="p" className="lp-lead" delay={200}>
            {t(
              "landing.technology.lead",
              "Crop-specific deep learning models analyze leaf images and identify visible disease patterns."
            )}
          </Reveal>
        </header>

        <Reveal className="lp-flow" delay={250}>
          <div className="lp-flow__node">
            <div className="lp-flow__thumb">
              <LeafCloseup lesions={1} title={t("landing.technology.flowLeafPhoto", "Leaf photo")} />
            </div>
            <p>{t("landing.technology.flowLeafPhoto", "Leaf photo")}</p>
          </div>
          <span className="lp-flow__link" aria-hidden="true" />
          <div className="lp-flow__node">
            <div className="lp-flow__core">
              <Icon name="net" size={34} />
            </div>
            <p>{t("landing.technology.flowModel", "Crop-specific model")}</p>
          </div>
          <span className="lp-flow__link" aria-hidden="true" />
          <div className="lp-flow__node">
            <div className="lp-flow__out">
              <span>{t("landing.technology.flowDisease", "Disease")}</span>
              <strong>{t("landing.technology.flowConfidence", "+ confidence")}</strong>
            </div>
            <p>{t("landing.technology.flowDiagnosis", "Diagnosis")}</p>
          </div>
        </Reveal>

        <ul className="lp-tech__grid">
          {TECH.map((item, i) => {
            const role = t(`landing.technology.techItems.${i}.role`, item.role);

            return (
              <Reveal as="li" key={item.name} className="lp-tech__item" delay={150 + i * 110}>
                <span className="lp-tech__icon">
                  <Icon name={item.icon} />
                </span>
                <div>
                  <h3>{item.name}</h3>
                  <p>{role}</p>
                </div>
              </Reveal>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
