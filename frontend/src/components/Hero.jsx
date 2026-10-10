import { useRef } from "react";
import { Link } from "react-router-dom";
import { useScrollProgress } from "../hooks/useScrollProgress";
import { useElementSize } from "../hooks/useElementSize";
import { DEMO_RESULT, HERO_STAGES, MEDIA } from "../content/landing";
import { BASE_X, SOIL_Y, TARGET, easeOut, keyframes, lerp, smooth, targetLeafCenter } from "./plant/geometry";
import { Ground, Plant, PlantDefs, useSvgId } from "./plant/PlantScene";
import { FieldRows } from "./plant/FieldRows";
import { SplitWords } from "./Reveal";
import { Icon } from "./Icons";
import { useTranslation } from "../context/LanguageContext";
import { useAuth } from "../context/AuthContext";

const SEED = [BASE_X - 2, 597];
const LEAF = targetLeafCenter();
const LEAF_LEN = (TARGET.petiole + 120) * TARGET.size; // whole leaf incl. stalk, world units
const BLADE_LEN = 120 * TARGET.size; // just the blade — what the scan frame wraps
const BLADE_WIDTH = 30 * 2 * 0.7 * TARGET.size;

/**
 * The "camera": decides which part of the plant's world is on screen for scroll progress p.
 *   seed close-up  → zooms out while the plant grows → rest → pushes in on one leaf.
 * Returns the SVG viewBox plus a few screen positions the HTML overlays need.
 */
function camera(p, w, h) {
  const desktop = w >= 900;
  const k0 = (desktop ? Math.min(h * 0.7, w * 0.42) : Math.min(h * 0.5, w * 0.95)) / 540; // px per world unit at rest
  const base = desktop ? [w * 0.66, h * 0.82] : [w * 0.5, h * 0.86];
  const seedStart = desktop ? [w * 0.66, h * 0.6] : [w * 0.5, h * 0.7];

  const z = smooth(0.705, 0.835, p); // leaf zoom
  let A;
  let P;
  let k;
  if (z <= 0) {
    const g = smooth(0.05, 0.56, p); // zoom out from the seed
    k = k0 * Math.pow(3.2, 1 - g);
    A = SEED;
    P = [lerp(seedStart[0], base[0], g), lerp(seedStart[1], base[1] - 3 * k0, g)];
  } else {
    const rest = [base[0] + (LEAF[0] - BASE_X) * k0, base[1] + (LEAF[1] - SOIL_Y) * k0];
    const T = desktop ? [w * 0.36, h * 0.5] : [w * 0.5, h * 0.36];
    const kT = (desktop ? Math.min(w * 0.48, h * 0.75) : w * 0.86) / LEAF_LEN;
    k = k0 * Math.pow(kT / k0, z) * (1 + 0.05 * smooth(0.83, 1, p));
    A = LEAF;
    P = [lerp(rest[0], T[0], z), lerp(rest[1], T[1], z)];
  }
  return {
    desktop,
    viewBox: [A[0] - P[0] / k, A[1] - P[1] / k, w / k, h / k].map((n) => n.toFixed(2)).join(" "),
    horizon: P[1] + (SOIL_Y - A[1]) * k,
    zoom: k / k0,
    leaf: { x: P[0], y: P[1], w: BLADE_LEN * k * 1.08, h: BLADE_WIDTH * k * 1.45 },
  };
}

export default function Hero() {
  const { t, language } = useTranslation();
  const { isAuthenticated } = useAuth();
  const sectionRef = useRef(null);
  const frameRef = useRef(null);
  const uid = useSvgId();
  const p = useScrollProgress(sectionRef);
  const { width: w, height: h } = useElementSize(frameRef);
  const cam = camera(p, w, h);

  const translatedStages = HERO_STAGES.map((s, idx) => ({
    ...s,
    name: t(`landing.hero.stages.${idx}.name`, s.name),
    line: t(`landing.hero.stages.${idx}.line`, s.line),
  }));

  const stageIndex = HERO_STAGES.reduce((acc, s, i) => (p >= s.from ? i : acc), 0);
  const stage = translatedStages[stageIndex] || translatedStages[0];

  // fades and lighting
  const intro = 1 - smooth(0.045, 0.11, p); // headline block
  const caption = smooth(0.1, 0.14, p) * (1 - smooth(0.82, 0.85, p));
  const scan = smooth(0.83, 0.86, p);
  const analyzing = smooth(0.84, 0.905, p);
  const detected = p >= 0.905;
  const confidence = Math.round(DEMO_RESULT.confidence * easeOut(smooth(0.905, 0.965, p)));
  const dawn = smooth(0.04, 0.5, p);
  const shade = keyframes([[0, 0.5], [0.3, 0.32], [0.55, 0.1], [0.72, 0.1], [0.84, 0.46], [1, 0.52]], p);
  const fieldGrow = lerp(0.25, 1, smooth(0.08, 0.62, p));
  const fieldScale = Math.pow(cam.zoom, 0.08);

  const diagnoseTarget = isAuthenticated ? "/diagnose" : "/login";

  const sampleCropName = t("landing.crops.cropNames.chili", DEMO_RESULT.crop);
  const sampleDiseaseName = t("landing.demo.sampleDisease", DEMO_RESULT.disease);

  return (
    <section ref={sectionRef} className="lp-hero" aria-labelledby="hero-title">
      <div ref={frameRef} className="lp-hero__frame">
        {/* --- background: sky, sun, distant field --- */}
        <div className="lp-hero__sky" aria-hidden="true">
          {MEDIA.heroBackdrop && <img className="lp-hero__photo" src={MEDIA.heroBackdrop} alt="" />}
          <div className="lp-hero__sun" style={{ opacity: 0.35 + 0.65 * dawn }} />
          <div className="lp-hero__beams" style={{ opacity: 0.25 + 0.75 * dawn }} />
        </div>
        {!MEDIA.heroBackdrop && (
          <>
            <div
              className="lp-hero__field lp-hero__field--far"
              style={{ transform: `translateY(${(cam.horizon - h * 0.4).toFixed(1)}px) scale(${fieldScale}, ${(fieldScale * fieldGrow).toFixed(3)})` }}
            >
              <FieldRows variant="far" className="lp-fill" />
            </div>
            <div
              className="lp-hero__field lp-hero__field--mid"
              style={{
                transform: `translateY(${(cam.horizon - h * 0.4 + 2).toFixed(1)}px) scale(${fieldScale}, ${(fieldScale * fieldGrow * 0.9).toFixed(3)})`,
                opacity: smooth(0.3, 0.6, p),
              }}
            >
              <FieldRows variant="mid" seed={5} className="lp-fill" />
            </div>
          </>
        )}
        <div className="lp-hero__shade" style={{ opacity: shade }} aria-hidden="true" />

        {/* --- the plant and its soil (one SVG, the camera is its viewBox) --- */}
        <svg className="lp-hero__scene" viewBox={cam.viewBox} preserveAspectRatio="none" aria-hidden="true" focusable="false">
          <PlantDefs uid={uid} />
          <Ground uid={uid} />
          <Plant uid={uid} progress={p} sway={p > 0.3 && p < 0.7} />
        </svg>

        <div className="lp-hero__dust" aria-hidden="true">
          {Array.from({ length: 14 }, (_, i) => (
            <span
              key={i}
              style={{
                left: `${(i * 37) % 97}%`,
                top: `${((i * 53) % 70) + 10}%`,
                animationDelay: `${-(i * 1.9).toFixed(1)}s`,
                animationDuration: `${12 + ((i * 7) % 9)}s`,
              }}
            />
          ))}
        </div>
        <div className="lp-hero__vignette" aria-hidden="true" />
        <div className="lp-hero__scrim" style={{ opacity: intro }} aria-hidden="true" />

        {/* --- AI scan frame around the inspected leaf --- */}
        {scan > 0 && (
          <div
            className={`lp-scanbox ${detected ? "is-locked" : ""}`}
            aria-hidden="true"
            style={{
              opacity: scan,
              width: cam.leaf.w,
              height: cam.leaf.h,
              transform: `translate(${(cam.leaf.x - cam.leaf.w / 2).toFixed(1)}px, ${(cam.leaf.y - cam.leaf.h / 2).toFixed(1)}px) rotate(${TARGET.angle}deg)`,
            }}
          >
            <i className="lp-scanbox__c lp-scanbox__c--tl" />
            <i className="lp-scanbox__c lp-scanbox__c--tr" />
            <i className="lp-scanbox__c lp-scanbox__c--bl" />
            <i className="lp-scanbox__c lp-scanbox__c--br" />
            {!detected && <i className="lp-scanbox__line" />}
            <span className="lp-scanbox__tag">
              {detected ? t("landing.hero.lesionsLocated", "Lesions located") : t("landing.hero.scanningLeaf", "Scanning leaf")}
            </span>
          </div>
        )}

        {/* --- result card --- */}
        {scan > 0 && (
          <div className="lp-hero__result lp-glass" style={{ opacity: scan }} aria-hidden="true">
            <div className="lp-result__head">
              <span className="lp-result__eyebrow">{t("landing.hero.leafAnalysis", "Leaf analysis")}</span>
              <span className="lp-chip">{sampleCropName}</span>
            </div>
            {!detected ? (
              <div className="lp-result__body" key="analyzing">
                <p className="lp-result__status">
                  <span className="lp-pulse" /> {t("landing.hero.analyzingLeaf", "Analyzing Leaf…")}
                </p>
                <div className="lp-meter">
                  <span style={{ transform: `scaleX(${analyzing.toFixed(3)})` }} />
                </div>
                <ul className="lp-result__checks">
                  <li className={analyzing > 0.2 ? "is-done" : ""}>{t("landing.hero.checkQuality", "Image quality checked")}</li>
                  <li className={analyzing > 0.5 ? "is-done" : ""}>{t("landing.hero.checkRegion", "Leaf region found")}</li>
                  <li className={analyzing > 0.85 ? "is-done" : ""}>{t("landing.hero.checkModel", "Chili model running")}</li>
                </ul>
              </div>
            ) : (
              <div className="lp-result__body lp-result__body--done" key="done">
                <p className="lp-result__alert">{t("landing.hero.diseaseDetected", "Disease Detected")}</p>
                <p className="lp-result__name">{sampleDiseaseName}</p>
                <div className="lp-result__conf">
                  <span className="lp-result__num">{confidence}%</span>
                  <span className="lp-result__label">{t("landing.hero.confidence", "Confidence")}</span>
                </div>
                <div className="lp-meter lp-meter--done">
                  <span style={{ transform: `scaleX(${(confidence / 100).toFixed(3)})` }} />
                </div>
              </div>
            )}
            <p className="lp-result__note">{t("landing.hero.previewNote", "Illustrative preview")}</p>
          </div>
        )}

        {/* --- headline --- */}
        <div className="lp-hero__content" style={{ opacity: intro, transform: `translateY(${(-36 * (1 - intro)).toFixed(1)}px)` }} inert={intro < 0.15 ? true : undefined}>
          <p className="lp-eyebrow lp-hero__eyebrow">
            <span className="lp-dot" /> {t("landing.hero.eyebrow", "AI crop health for farms and gardens")}
          </p>
          <h1 id="hero-title" className="lp-hero__title" aria-label={`${t("landing.hero.titleLine1", "Protect Every Leaf.")} ${t("landing.hero.titleLine2", "Grow a Healthier Future.")}`}>
            <SplitWords key={`title1-${language}`} as="span" text={t("landing.hero.titleLine1", "Protect Every Leaf.")} className="lp-hero__line" start={150} step={90} />
            <SplitWords key={`title2-${language}`} as="span" text={t("landing.hero.titleLine2", "Grow a Healthier Future.")} className="lp-hero__line lp-hero__line--accent" start={480} step={90} />
          </h1>
          <p className="lp-hero__sub">{t("landing.hero.subtitle", "AI-powered crop disease detection from a simple leaf image.")}</p>
          <div className="lp-hero__ctas">
            <Link to={diagnoseTarget} className="lp-btn lp-btn--primary">
              {t("landing.hero.startDiagnosis", "Start Diagnosis")} <Icon name="arrow" size={18} />
            </Link>
            <a href="#how-it-works" className="lp-btn lp-btn--ghost">
              {t("landing.hero.exploreHow", "Explore How It Works")}
            </a>
          </div>
        </div>

        {/* --- stage caption + progress rail --- */}
        <div className="lp-hero__caption" style={{ opacity: caption }} aria-hidden="true">
          <p className="lp-hero__caption-num">
            {t("landing.hero.stage", "Stage")} {String(stageIndex + 1).padStart(2, "0")} <span>/ {String(HERO_STAGES.length).padStart(2, "0")}</span>
          </p>
          <p key={stage.name} className="lp-hero__caption-title">
            {stage.name}
          </p>
          <p key={`${stage.name}-l`} className="lp-hero__caption-line">
            {stage.line}
          </p>
        </div>

        <ol className="lp-rail" aria-hidden="true" style={{ "--p": p, opacity: caption }}>
          {translatedStages.map((s, i) => (
            <li key={HERO_STAGES[i].name} className={i === stageIndex ? "is-active" : i < stageIndex ? "is-past" : ""}>
              <span className="lp-rail__dot" />
              <span className="lp-rail__label">{s.name}</span>
            </li>
          ))}
        </ol>

        <div className="lp-hero__hint" style={{ opacity: 1 - smooth(0.005, 0.04, p) }} aria-hidden="true">
          <span className="lp-hero__hint-line" />
          {t("landing.hero.scrollHint", "Scroll to grow")}
        </div>
        <a href="#about" className="lp-hero__skip" style={{ opacity: 1 - smooth(0.8, 0.84, p) }} inert={p > 0.84 ? true : undefined}>
          {t("landing.hero.skipJourney", "Skip the journey")} <Icon name="down" size={14} />
        </a>

        <p className="lp-sr">
          {t("landing.hero.previewAlt", "Animated illustration: as you scroll, a chili seed sprouts, grows into a mature fruiting plant, and the view zooms into one leaf where an AI scan highlights leaf-spot lesions.")}
        </p>
      </div>
    </section>
  );
}
