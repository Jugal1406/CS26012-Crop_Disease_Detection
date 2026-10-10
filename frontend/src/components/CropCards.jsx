import { Link } from "react-router-dom";
import { CROPS, MEDIA, PLANNED_CROPS } from "../content/landing";
import { CropLeaf } from "./plant/LeafArt";
import { Icon } from "./Icons";
import { Reveal, RevealHeading } from "./Reveal";
import { useTranslation } from "../context/LanguageContext";
import { useAuth } from "../context/AuthContext";

export default function CropCards() {
  const { t, language } = useTranslation();
  const { isAuthenticated } = useAuth();

  const plannedCrops = t("landing.crops.plannedList") || PLANNED_CROPS;
  const plannedCropsText = Array.isArray(plannedCrops) ? plannedCrops.join(" · ") : PLANNED_CROPS.join(" · ");

  const diagnoseTarget = isAuthenticated ? "/diagnose" : "/login";

  return (
    <section id="crops" className="lp-section lp-crops" aria-labelledby="crops-title">
      <div className="lp-container">
        <header className="lp-section__head">
          <Reveal as="p" className="lp-eyebrow">
            {t("landing.crops.eyebrow", "Supported crops")}
          </Reveal>
          <RevealHeading
            key={`crops-title-${language}`}
            id="crops-title"
            text={t("landing.crops.title", "Built for Real Crops")}
            className="lp-h2"
          />
          <Reveal as="p" className="lp-lead" delay={200}>
            {t(
              "landing.crops.lead",
              "Each crop gets its own model, trained on photographs taken in real Indian fields, not on lab images with plain backgrounds."
            )}
          </Reveal>
        </header>

        <ul className="lp-crops__grid">
          {CROPS.map((c, i) => {
            const cropDisplayName = t(`landing.crops.cropNames.${c.id}`, c.name);
            const cropOrigin = t(`landing.crops.origins.${c.id}`, c.origin);

            return (
              <Reveal as="li" key={c.id} delay={120 + i * 140}>
                <article className="lp-crop">
                  <div className="lp-crop__visual">
                    {MEDIA.crops[c.id] ? (
                      <img src={MEDIA.crops[c.id]} alt={`${cropDisplayName} leaf`} loading="lazy" className="lp-crop__photo" />
                    ) : (
                      <CropLeaf crop={c.leaf} title={`Illustration of a ${cropDisplayName.toLowerCase()} leaf`} />
                    )}
                    <span className="lp-crop__scan" aria-hidden="true" />
                  </div>
                  <div className="lp-crop__body">
                    <h3 className="lp-crop__name">{cropDisplayName}</h3>
                    <p className="lp-crop__latin">{c.latin}</p>
                    <dl className="lp-crop__meta">
                      <div>
                        <dt>{t("landing.crops.trainingData", "Training data")}</dt>
                        <dd>{cropOrigin}</dd>
                      </div>
                      <div>
                        <dt>{t("landing.crops.leafClasses", "Leaf classes")}</dt>
                        <dd>{c.classes}</dd>
                      </div>
                    </dl>
                    <Link to={diagnoseTarget} className="lp-crop__link">
                      {t("landing.crops.diagnoseAction", "Diagnose")} {cropDisplayName} <Icon name="arrow" size={16} />
                    </Link>
                  </div>
                </article>
              </Reveal>
            );
          })}
        </ul>

        <Reveal as="p" className="lp-crops__next" delay={300}>
          <span>{t("landing.crops.plannedNext", "Planned next:")}</span> {plannedCropsText}
        </Reveal>
      </div>
    </section>
  );
}
