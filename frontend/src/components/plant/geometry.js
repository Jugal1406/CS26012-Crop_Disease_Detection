/*
 * Pure maths for the plant illustration. No React here, so it is easy to read and test.
 *
 * World coordinates (shared by every plant drawing):
 *   - the soil surface is the line y = 600
 *   - the plant grows from (300, 600) upwards (smaller y = higher)
 */

export const SOIL_Y = 600;
export const BASE_X = 300;

export const clamp = (v, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
export const lerp = (a, b, t) => a + (b - a) * t;
/** 0 before e0, 1 after e1, smooth S-curve in between */
export const smooth = (e0, e1, x) => {
  const t = clamp((x - e0) / (e1 - e0));
  return t * t * (3 - 2 * t);
};
export const easeOut = (t) => 1 - Math.pow(1 - clamp(t), 3);

/** Piecewise interpolation through [x, y] keyframes with smooth easing between them. */
export function keyframes(frames, x) {
  if (x <= frames[0][0]) return frames[0][1];
  for (let i = 1; i < frames.length; i++) {
    const [x1, y1] = frames[i];
    const [x0, y0] = frames[i - 1];
    if (x <= x1) return lerp(y0, y1, smooth(x0, x1, x));
  }
  return frames[frames.length - 1][1];
}

/** Small deterministic random generator, so decorative scatter looks the same on every render. */
export function seeded(seed) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

const f = (n) => Math.round(n * 100) / 100;

/* ------------------------------------------------------------------ leaves */

/*
 * A leaf is drawn pointing along +x, from its base (0,0) to its tip (L,0).
 * The upper edge is one cubic Bézier curve; the lower edge mirrors it.
 * c1/c2 are the control points as fractions of length L and half-width W.
 */
const SHAPES = {
  lanceolate: { L: 120, W: 30, c1: [0.12, 0.95], c2: [0.55, 0.92] }, // chili leaf
  ovate: { L: 100, W: 37, c1: [0.0, 0.9], c2: [0.55, 1.02] }, // potato leaflet
  obovate: { L: 88, W: 34, c1: [0.26, 0.42], c2: [1.02, 1.12] }, // groundnut leaflet
  cotyledon: { L: 46, W: 9, c1: [0.18, 1.1], c2: [0.75, 1.1] }, // seed leaf
};

const cache = new Map();

function cubic(p0, p1, p2, p3, t) {
  const u = 1 - t;
  return u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3;
}

export function leafGeometry(name = "lanceolate") {
  if (cache.has(name)) return cache.get(name);
  const { L, W, c1, c2 } = SHAPES[name];
  const C1 = [c1[0] * L, c1[1] * W];
  const C2 = [c2[0] * L, c2[1] * W];
  const d =
    `M0 0 C${f(C1[0])} ${f(-C1[1])} ${f(C2[0])} ${f(-C2[1])} ${L} 0 ` +
    `C${f(C2[0])} ${f(C2[1])} ${f(C1[0])} ${f(C1[1])} 0 0Z`;

  // sample the upper edge so we know the leaf's half-width at any x (used for veins)
  const samples = [];
  for (let i = 0; i <= 48; i++) {
    const t = i / 48;
    samples.push([cubic(0, C1[0], C2[0], L, t), cubic(0, C1[1], C2[1], 0, t)]);
  }
  const widthAt = (x) => {
    for (let i = 1; i < samples.length; i++) {
      const [x0, y0] = samples[i - 1];
      const [x1, y1] = samples[i];
      if ((x >= x0 && x <= x1) || (x <= x0 && x >= x1)) {
        return x1 === x0 ? y0 : lerp(y0, y1, (x - x0) / (x1 - x0));
      }
    }
    return 0;
  };

  const midrib = `M0 0 Q${f(L * 0.5)} ${f(-W * 0.06)} ${f(L * 0.96)} 0`;
  const n = name === "cotyledon" ? 0 : name === "obovate" ? 4 : 6;
  let veins = "";
  for (let i = 0; i < n; i++) {
    const x0 = L * (0.1 + (0.72 * i) / n);
    const xe = Math.min(x0 + L * 0.17, L * 0.93);
    const we = widthAt(xe) * 0.84;
    const cx = x0 + L * 0.05;
    veins += `M${f(x0)} 0 Q${f(cx)} ${f(-we * 0.55)} ${f(xe)} ${f(-we)} `;
    veins += `M${f(x0)} 0 Q${f(cx)} ${f(we * 0.55)} ${f(xe)} ${f(we)} `;
  }

  const g = { L, W, d, midrib, veins: veins.trim(), widthAt };
  cache.set(name, g);
  return g;
}

/* ------------------------------------------------------------------ stem */

/** Stem height (world units) for a growth progress p in [0, 1]. */
export const stemHeight = (p) =>
  keyframes(
    [
      [0.16, 0],
      [0.27, 72],
      [0.4, 190],
      [0.54, 360],
      [0.68, 470],
      [0.74, 482],
    ],
    p,
  );

/** Point on the (slightly S-shaped) stem at fraction t (0 = soil, 1 = tip). y is exactly SOIL_Y - H*t. */
export function stemPoint(H, t) {
  const x = cubic(BASE_X, BASE_X - 2, BASE_X + 0.03 * H, BASE_X + 0.02 * H, t);
  return [x, SOIL_Y - H * t];
}

/** Closed outline of a tapered stem (thick at the base, thin at the tip). */
export function stemOutline(H, baseWidth) {
  if (H <= 0.5) return "";
  const N = 18;
  const left = [];
  const right = [];
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    const [x, y] = stemPoint(H, t);
    const [x2, y2] = stemPoint(H, Math.min(1, t + 0.01));
    const [x1, y1] = stemPoint(H, Math.max(0, t - 0.01));
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy) || 1;
    const nx = -dy / len;
    const ny = dx / len;
    const w = (baseWidth * lerp(1, 0.32, t)) / 2;
    left.push([x + nx * w, y + ny * w]);
    right.push([x - nx * w, y - ny * w]);
  }
  const pts = [...left, ...right.reverse()];
  return "M" + pts.map(([x, y]) => `${f(x)} ${f(y)}`).join(" L") + "Z";
}

/* ------------------------------------------------------------------ the plant */

// [height on stem, side (-1 left / 1 right), resting angle, size, isBackLeaf]
const LEAVES = [
  [88, -1, -20, 0.8],
  [112, 1, -24, 0.85],
  [150, -1, -18, 1.0],
  [178, 1, -16, 1.05],
  [200, 1, -44, 0.9, true],
  [215, -1, -24, 1.05],
  [246, 1, -12, 1.15, false, true], // ← the leaf the AI inspects
  [262, -1, -52, 0.95, true],
  [280, -1, -30, 1.0],
  [300, -1, -8, 1.05, true],
  [305, 1, -34, 0.95],
  [335, -1, -38, 0.9],
  [356, 1, -6, 0.95, true],
  [360, 1, -42, 0.85],
  [385, -1, -48, 0.8],
  [408, 1, -50, 0.72],
  [430, -1, -56, 0.62],
  [448, 1, -60, 0.52],
];

// chili pods: [height, side, swing angle, colour, start progress]
const PODS = [
  [228, 1, 14, "red", 0.6],
  [268, -1, -10, "green", 0.62],
  [300, 1, 6, "red", 0.64],
  [322, -1, 16, "red", 0.655],
];

const FLOWERS = [
  [392, 1, 0.56],
  [418, -1, 0.575],
  [440, 1, 0.59],
];

// lesions on the inspected leaf, in leaf-local coordinates: [x, y, radius]
export const LESIONS = [
  [44, -8, 5.2],
  [61, 9, 4.2],
  [79, -5, 6],
  [96, 9, 3.6],
  [57, -16, 3.2],
  [89, -15, 3.4],
  [108, -2, 3.1],
];

export const TARGET = { at: 246, side: 1, angle: -12, size: 1.15, petiole: 14 };

/** World position of a point (lx, ly) given in a leaf's local coordinates. */
export function leafToWorld(attach, side, angleDeg, scale, lx, ly) {
  const a = (angleDeg * Math.PI) / 180;
  const x = lx * scale;
  const y = ly * scale;
  const rx = x * Math.cos(a) - y * Math.sin(a);
  const ry = x * Math.sin(a) + y * Math.cos(a);
  return [attach[0] + side * rx, attach[1] + ry];
}

/** World position of the inspected leaf's centre once the plant is fully grown. */
export function targetLeafCenter() {
  const H = stemHeight(1);
  const attach = stemPoint(H, TARGET.at / H);
  return leafToWorld(attach, TARGET.side, TARGET.angle, TARGET.size, TARGET.petiole + 60, 0);
}

/**
 * Everything needed to draw the plant at growth progress p (0 = seed, 1 = AI result).
 * Returns plain numbers; PlantScene.jsx turns them into SVG.
 */
export function buildPlant(p) {
  const H = stemHeight(p);
  const stemW = 2.4 + 8.6 * (H / 482);

  const seed = {
    crack: smooth(0.05, 0.09, p),
    shift: smooth(0.2, 0.32, p),
    opacity: 1 - 0.45 * smooth(0.22, 0.34, p),
  };
  const radicle = smooth(0.055, 0.13, p);
  const hook = { a: 30 * smooth(0.07, 0.17, p), opacity: 1 - smooth(0.185, 0.225, p) };

  const open = smooth(0.2, 0.29, p);
  const cotH = Math.min(H, 64);
  const cotyledons =
    H > 0.5
      ? {
          attach: stemPoint(H, cotH / H),
          angle: lerp(-84, -16, open) + 10 * smooth(0.55, 0.7, p),
          scale: lerp(0.45, 1, open),
          aged: smooth(0.55, 0.72, p),
        }
      : null;

  const leaves = LEAVES.map(([at, side, angle, size, back, target], i) => {
    if (H < at + 6) return null;
    const g = clamp((H - at - 6) / 110);
    return {
      key: i,
      attach: stemPoint(H, at / H),
      side,
      angle: lerp(-64, angle, easeOut(g)),
      scale: Math.max(0.05, size * easeOut(g)),
      youth: 1 - g,
      back: Boolean(back),
      target: Boolean(target),
    };
  }).filter(Boolean);

  const tip = stemPoint(H, 1);
  const bud = H > 70 ? { attach: tip, scale: 0.32 * smooth(70, 140, H) } : null;

  const pods = PODS.map(([at, side, swing, colour, t0], i) => {
    const g = easeOut(smooth(t0, t0 + 0.08, p));
    if (g <= 0 || H < at) return null;
    const [x, y] = stemPoint(H, at / H);
    return { key: i, x: x + side * 5, y, swing, colour, scale: g };
  }).filter(Boolean);

  const flowers = FLOWERS.map(([at, side, t0], i) => {
    const g = smooth(t0, t0 + 0.05, p);
    if (g <= 0 || H < at) return null;
    const [x, y] = stemPoint(H, at / H);
    return { key: i, x: x + side * 14, y: y + 6, scale: g };
  }).filter(Boolean);

  return {
    H,
    stemPath: stemOutline(H, stemW),
    seed,
    radicle,
    hook,
    cotyledons,
    leaves,
    bud,
    pods,
    flowers,
    lesions: smooth(0.76, 0.87, p),
    markers: smooth(0.88, 0.93, p),
    shadowRx: 22 + H * 0.3,
  };
}
