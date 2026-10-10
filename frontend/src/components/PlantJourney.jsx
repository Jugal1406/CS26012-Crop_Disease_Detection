import { useRef } from "react";
import { LIFECYCLE } from "../content/landing";
import { useInView } from "../hooks/useInView";
import { PlantStill } from "./plant/PlantScene";
import { LeafCloseup } from "./plant/LeafArt";
import { Reveal, RevealHeading } from "./Reveal";
import { useTranslation } from "../context/LanguageContext";

export default function PlantJourney() {
  const { t, language } = useTranslation();
  const listRef = useRef(null);
  const grown = useInView(listRef, { threshold: 0.2 });

  return (
    <section id="about" className="lp-section lp-journey" aria-labelledby="journey-title">
      <div className="lp-container">
        <header className="lp-section__head">
          <Reveal as="p" className="lp-eyebrow">
            {t("landing.journey.eyebrow", "The plant journey")}
          </Reveal>
          <RevealHeading
            key={`journey-title-${language}`}
            id="journey-title"
            text={t("landing.journey.title", "From Seed to Harvest")}
            className="lp-h2"
          />
          <Reveal as="p" className="lp-lead" delay={200}>
            {t(
              "landing.journey.lead",
              "Healthy crops begin with healthy plants. Every stage of growth leaves clues on the leaf, and catching them early is what protects the harvest."
            )}
          </Reveal>
        </header>

        <ol ref={listRef} className={`lp-timeline ${grown ? "is-grown" : ""}`}>
          {LIFECYCLE.map((s, i) => {
            const stageName = t(`landing.journey.stages.${i}.name`, s.name);
            const stageText = t(`landing.journey.stages.${i}.text`, s.text);

            return (
              <Reveal as="li" key={s.name} className="lp-timeline__item" delay={150 + i * 140} style={{ "--i": i }}>
                <div className="lp-timeline__frame">
                  {s.leaf ? (
                    <div className="lp-timeline__leaf">
                      <LeafCloseup lesions={1} markers={1} title={`${stageName} - ${stageText}`} />
                      <span className="lp-timeline__scan" aria-hidden="true" />
                    </div>
                  ) : (
                    <PlantStill progress={s.progress} view={s.view} title={`${stageName} stage`} />
                  )}
                </div>
                <span className="lp-timeline__node" aria-hidden="true" />
                <p className="lp-timeline__num">{String(i + 1).padStart(2, "0")}</p>
                <h3 className="lp-timeline__name">{stageName}</h3>
                <p className="lp-timeline__text">{stageText}</p>
              </Reveal>
            );
          })}
        </ol>
      </div>
    </section>
  );
}
