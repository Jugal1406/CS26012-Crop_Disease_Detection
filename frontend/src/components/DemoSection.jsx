import { useRef } from "react";
import { DEMO_RESULT, MEDIA, REPORT_ITEMS } from "../content/landing";
import { useInView } from "../hooks/useInView";
import { LeafCloseup } from "./plant/LeafArt";
import { Icon } from "./Icons";
import { Reveal } from "./Reveal";
import { useTranslation } from "../context/LanguageContext";

export default function DemoSection() {
  const { t, language } = useTranslation();
  const ref = useRef(null);
  const live = useInView(ref, { threshold: 0.35 });

  const sampleCrop = t("landing.crops.cropNames.chili", DEMO_RESULT.crop);
  const sampleDisease = t("landing.demo.sampleDisease", DEMO_RESULT.disease);

  return (
    <section className="lp-section lp-demo" aria-labelledby="demo-title">
      <div className="lp-container">
        <header className="lp-section__head lp-section__head--light">
          <Reveal as="p" className="lp-eyebrow">
            {t("landing.demo.eyebrow", "The diagnosis")}
          </Reveal>
          <h2 id="demo-title" className="lp-h2 lp-demo__title">
            <Reveal key={`see-${language}`} as="span" delay={0}>
              {t("landing.demo.see", "See.")}
            </Reveal>{" "}
            <Reveal key={`detect-${language}`} as="span" delay={180}>
              {t("landing.demo.detect", "Detect.")}
            </Reveal>{" "}
            <Reveal key={`act-${language}`} as="span" delay={360}>
              {t("landing.demo.act", "Act.")}
            </Reveal>
          </h2>
        </header>

        <div ref={ref} className={`lp-demo__grid ${live ? "is-live" : ""}`}>
          <figure className="lp-demo__leaf">
            {MEDIA.demoLeaf ? (
              <img src={MEDIA.demoLeaf} alt={`${sampleCrop} leaf`} loading="lazy" />
            ) : (
              <LeafCloseup lesions={1} markers={live ? 1 : 0} title={`${sampleCrop} leaf`} />
            )}
            <span className="lp-demo__line" aria-hidden="true" />
            <span className="lp-demo__corners" aria-hidden="true" />
            <figcaption>
              <span className="lp-step-tag">{t("landing.demo.seeStep", "See")}</span> {t("landing.demo.seeCaption", "A photo of one leaf")}
            </figcaption>
          </figure>

          <div className="lp-demo__side">
            <article className="lp-demo__card lp-glass" aria-label="Example diagnosis result">
              <p className="lp-step-tag">{t("landing.demo.detectStep", "Detect")}</p>
              <dl className="lp-demo__rows">
                <div>
                  <dt>{t("landing.demo.cropLabel", "Crop")}</dt>
                  <dd>{sampleCrop}</dd>
                </div>
                <div>
                  <dt>{t("landing.demo.predictionLabel", "Prediction")}</dt>
                  <dd className="lp-demo__disease">{sampleDisease}</dd>
                </div>
                <div>
                  <dt>{t("landing.demo.confidenceLabel", "Confidence")}</dt>
                  <dd>{DEMO_RESULT.confidence}%</dd>
                </div>
              </dl>
              <div className="lp-meter lp-meter--done lp-demo__meter">
                <span style={{ transform: `scaleX(${live ? DEMO_RESULT.confidence / 100 : 0})` }} />
              </div>
              <p className="lp-result__note">{t("landing.demo.exampleNote", "Illustrative example, not a live prediction")}</p>
            </article>

            <div className="lp-demo__act">
              <p className="lp-step-tag">{t("landing.demo.actStep", "Act")}</p>
              <ul>
                {REPORT_ITEMS.map((item, i) => {
                  const translatedItem = t(`landing.demo.reports.${i}`, item);
                  return (
                    <li key={item} style={{ "--i": i }}>
                      <Icon name="check" size={16} /> {translatedItem}
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
