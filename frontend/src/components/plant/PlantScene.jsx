import { memo, useId, useMemo } from "react";
import {
  BASE_X,
  LESIONS,
  SOIL_Y,
  buildPlant,
  leafGeometry,
  seeded,
} from "./geometry";
import { useNoiseTexture } from "./noise";

/** React's useId() can contain characters that break url(#id) references, so clean it. */
export function useSvgId() {
  return "p" + useId().replace(/[^a-zA-Z0-9_-]/g, "");
}

/* ------------------------------------------------------------------ gradients */

export function PlantDefs({ uid }) {
  const noise = useNoiseTexture();
  const stop = (offset, color, opacity = 1) => (
    <stop offset={offset} stopColor={color} stopOpacity={opacity} />
  );
  const leafGrad = (name, a, b, c, d) => (
    <linearGradient id={`${uid}-${name}`} x1="0" y1="0" x2="0" y2="1">
      {stop(0, a)}
      {stop(0.44, b)}
      {stop(0.54, c)}
      {stop(1, d)}
    </linearGradient>
  );
  return (
    <defs>
      {leafGrad("front", "#3a6e27", "#5a9838", "#69a742", "#2b5a1c")}
      {leafGrad("back", "#21441a", "#36662a", "#3f722e", "#1b3714")}
      {leafGrad("young", "#78ad4c", "#a3cf6b", "#afd677", "#62973a")}
      {leafGrad("cotyledon", "#7aa94a", "#a6cd6c", "#b2d47a", "#5f8f37")}
      {leafGrad("aged", "#9a9a43", "#c2bd63", "#cbc46c", "#86843a")}
      <radialGradient id={`${uid}-sheen`} cx="0.62" cy="0.28" r="0.6">
        {stop(0, "#fffbe6", 0.24)}
        {stop(0.55, "#fffbe6", 0.04)}
        {stop(1, "#fffbe6", 0)}
      </radialGradient>
      <linearGradient id={`${uid}-stem`} x1="0" y1="0" x2="1" y2="0">
        {stop(0, "#284f1b")}
        {stop(0.55, "#5f943b")}
        {stop(0.78, "#4b7e2f")}
        {stop(1, "#26491a")}
      </linearGradient>
      <linearGradient id={`${uid}-soil`} gradientUnits="userSpaceOnUse" x1="0" y1={SOIL_Y - 4} x2="0" y2={SOIL_Y + 520}>
        {stop(0, "#6b4c33")}
        {stop(0.05, "#4a3221")}
        {stop(0.35, "#2b1b11")}
        {stop(1, "#120b07")}
      </linearGradient>
      <radialGradient id={`${uid}-damp`}>
        {stop(0, "#140c07", 0.55)}
        {stop(1, "#140c07", 0)}
      </radialGradient>
      <radialGradient id={`${uid}-shadow`}>
        {stop(0, "#000", 0.55)}
        {stop(1, "#000", 0)}
      </radialGradient>
      <radialGradient id={`${uid}-pebble`} cx="0.35" cy="0.3" r="0.8">
        {stop(0, "#8a7f6c")}
        {stop(0.6, "#575043")}
        {stop(1, "#2b251e")}
      </radialGradient>
      <radialGradient id={`${uid}-clod`} cx="0.4" cy="0.3" r="0.8">
        {stop(0, "#7a573a")}
        {stop(1, "#2a1a10")}
      </radialGradient>
      <radialGradient id={`${uid}-seed`} cx="0.38" cy="0.32" r="0.75">
        {stop(0, "#f6e7b8")}
        {stop(0.55, "#dcbc74")}
        {stop(1, "#9d7836")}
      </radialGradient>
      <linearGradient id={`${uid}-pod-red`} x1="0" y1="0" x2="1" y2="0">
        {stop(0, "#6f140f")}
        {stop(0.4, "#c0301f")}
        {stop(0.58, "#e65a40")}
        {stop(1, "#8c1b13")}
      </linearGradient>
      <linearGradient id={`${uid}-pod-green`} x1="0" y1="0" x2="1" y2="0">
        {stop(0, "#2a5617")}
        {stop(0.42, "#5a9434")}
        {stop(0.6, "#7cb24b")}
        {stop(1, "#30621b")}
      </linearGradient>
      <radialGradient id={`${uid}-halo`}>
        {stop(0, "#d2bc4c", 0.5)}
        {stop(0.55, "#c9b24a", 0.22)}
        {stop(1, "#cdb546", 0)}
      </radialGradient>
      {noise && (
        <pattern id={`${uid}-noise`} patternUnits="userSpaceOnUse" width="64" height="64">
          <image href={noise} width="64" height="64" />
        </pattern>
      )}
    </defs>
  );
}

/* ------------------------------------------------------------------ leaf */

/**
 * One leaf at the origin, pointing along +x. Wrap it in a <g transform> to place it.
 * `youth` (0..1) tints it lighter like a freshly unfolded leaf.
 */
export function LeafShape({
  uid,
  shape = "lanceolate",
  fill = "front",
  petiole = 14,
  youth = 0,
  lesions = 0,
  markers = 0,
  shadow = true,
}) {
  const g = leafGeometry(shape);
  return (
    <g>
      {petiole > 0 && (
        <path
          d={`M0 0 Q${petiole * 0.5} 1.2 ${petiole} 0`}
          stroke="#3f6e2a"
          strokeWidth={2.2}
          strokeLinecap="round"
          fill="none"
        />
      )}
      <g transform={`translate(${petiole} 0)`}>
        {shadow && <path d={g.d} transform="translate(2.5 3.5)" fill="#000" opacity={0.16} />}
        <path d={g.d} fill={`url(#${uid}-${fill})`} stroke="#23471a" strokeOpacity={0.55} strokeWidth={0.7} />
        {youth > 0.02 && <path d={g.d} fill={`url(#${uid}-young)`} opacity={youth * 0.85} />}
        <path d={g.d} fill={`url(#${uid}-sheen)`} />
        <path d={g.veins} stroke="#d6ecaa" strokeOpacity={0.16} strokeWidth={0.7} fill="none" strokeLinecap="round" />
        <path d={g.midrib} stroke="#d9efb0" strokeOpacity={0.38} strokeWidth={1.2} fill="none" strokeLinecap="round" />
        {lesions > 0 && <Lesions uid={uid} opacity={lesions} markers={markers} />}
      </g>
    </g>
  );
}

/**
 * Frog-eye leaf spots, the look of Cercospora leaf spot: a pale grey-tan centre, a thin dark
 * brown margin and a faint yellow halo. Slightly irregular so they don't read as perfect targets.
 */
export function Lesions({ uid, opacity = 1, markers = 0 }) {
  return (
    <g>
      <g opacity={opacity}>
        {LESIONS.map(([x, y, r], i) => {
          const rot = (i * 47) % 180;
          const k = 0.82 + ((i * 13) % 5) * 0.06;
          return (
            <g key={i} transform={`translate(${x} ${y}) rotate(${rot})`}>
              <ellipse rx={r * 1.9} ry={r * 1.6} fill={`url(#${uid}-halo)`} />
              <ellipse rx={r} ry={r * k} fill="#5e3a1f" opacity={0.92} />
              <ellipse rx={r * 0.8} ry={r * k * 0.78} fill="#8c6a48" />
              <ellipse cx={r * 0.06} rx={r * 0.55} ry={r * k * 0.5} fill="#cfc2a4" />
              <circle cx={-r * 0.25} cy={r * 0.1} r={r * 0.12} fill="#6e4a2a" opacity={0.6} />
            </g>
          );
        })}
      </g>
      {LESIONS.map(([x, y, r], i) => {
        const on = Math.max(0, Math.min(1, markers * LESIONS.length - i));
        if (on <= 0) return null;
        return (
          <circle
            key={`m${i}`}
            cx={x}
            cy={y}
            r={r * (2.5 - on * 0.4)}
            fill="none"
            stroke="#d7f5d8"
            strokeWidth={1.1}
            vectorEffect="non-scaling-stroke"
            strokeDasharray="3 2"
            opacity={on * 0.85}
          />
        );
      })}
    </g>
  );
}

const placeLeaf = ([x, y], side, angle, scale) =>
  `translate(${x.toFixed(2)} ${y.toFixed(2)}) scale(${side} 1) rotate(${angle.toFixed(2)}) scale(${scale.toFixed(3)})`;

/* ------------------------------------------------------------------ pieces */

function Pod({ uid, x, y, swing, colour, scale }) {
  return (
    <g transform={`translate(${x} ${y}) rotate(${swing}) scale(${scale})`}>
      <path d="M0 0 Q3.5 8 2.5 16" stroke="#3c6b25" strokeWidth={2} fill="none" strokeLinecap="round" />
      <path
        d="M-3.8 18 C-5.5 34 -2.5 58 6 76 C8 79 10.2 78 9.4 74 C7 56 8.6 34 8 18 Z"
        fill={`url(#${uid}-pod-${colour})`}
      />
      <path d="M1.2 24 C1 40 3 56 7 70" stroke="#fff" strokeOpacity={0.35} strokeWidth={1.4} fill="none" strokeLinecap="round" />
      <ellipse cx={2.1} cy={18.5} rx={6.4} ry={3.6} fill="#3b6a23" />
    </g>
  );
}

function Flower({ x, y, scale }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`} opacity={0.95}>
      {[0, 72, 144, 216, 288].map((a) => (
        <ellipse key={a} cx={0} cy={-4.4} rx={2.6} ry={4.6} fill="#f6f2e4" transform={`rotate(${a})`} />
      ))}
      <circle r={2.2} fill="#d8b33d" />
    </g>
  );
}

function Seed({ uid, seed, radicle, hook }) {
  const { crack, shift, opacity } = seed;
  const sx = BASE_X - 4 + shift * 20;
  const rot = -18 + shift * 34;
  return (
    <g>
      {radicle > 0 && (
        <path
          d="M292 600 C287 605 284 610 281 618"
          stroke="#efe6cd"
          strokeWidth={2.2}
          fill="none"
          strokeLinecap="round"
          pathLength={1}
          strokeDasharray={`${radicle} 1`}
          opacity={0.9 * (1 - seed.shift)}
        />
      )}
      {hook.a > 0.5 && hook.opacity > 0 && (
        <path
          d={`M304 603 C303.5 ${603 - hook.a} 316 ${603 - hook.a * 1.15} 318.5 ${603 - hook.a * 0.55}`}
          stroke="#b7d27c"
          strokeWidth={3.6}
          fill="none"
          strokeLinecap="round"
          opacity={hook.opacity}
        />
      )}
      <g transform={`translate(${sx} 596) rotate(${rot})`} opacity={opacity}>
        <path d="M-11 0 C-11 -7 -4 -9.5 2 -8.5 C9 -7.5 12 -2 11 2 C10 7 3 9 -3 8 C-8 7 -11 4 -11 0 Z" fill={`url(#${uid}-seed)`} />
        <path d="M-6 -2 C-2 -5 4 -5 7 -2" stroke="#fff6dc" strokeOpacity={0.55} strokeWidth={1.2} fill="none" strokeLinecap="round" />
        {crack > 0 && (
          <path d="M-9 1 C-5 2 -1 0 3 2 C6 3 8 2 10 1" stroke="#6b4c22" strokeWidth={1} fill="none" opacity={crack} />
        )}
      </g>
    </g>
  );
}

/* ------------------------------------------------------------------ ground */

/** Soil surface, texture, pebbles and crumbs. Static, so it is memoised. */
export const Ground = memo(function Ground({ uid, x0 = -4000, x1 = 4600, depth = 3000 }) {
  const { edge, bits } = useMemo(() => {
    const r = seeded(7);
    let d = `M${x0} ${SOIL_Y + 2}`;
    for (let x = x0; x <= x1; x += 24) d += ` L${x} ${(SOIL_Y + (r() - 0.5) * 3).toFixed(1)}`;
    d += ` L${x1} ${SOIL_Y + depth} L${x0} ${SOIL_Y + depth}Z`;

    const items = [];
    for (let i = 0; i < 150; i++) {
      const x = BASE_X + (r() - 0.5) * 760;
      const y = SOIL_Y + Math.pow(r(), 1.6) * 200 - 2;
      const near = Math.abs(x - BASE_X) < 90;
      const size = (r() * (near ? 3 : 4.6) + 0.9) * (1 + (y - SOIL_Y) / 220);
      const kind = r() < 0.32 ? "pebble" : r() < 0.7 ? "clod" : "crumb";
      items.push({ x, y, size, kind, rot: (r() - 0.5) * 50, flat: 0.45 + r() * 0.25 });
    }
    items.sort((a, b) => a.y - b.y);
    return { edge: d, bits: items };
  }, [x0, x1, depth]);

  return (
    <g>
      <path d={edge} fill={`url(#${uid}-soil)`} />
      <rect x={x0} y={SOIL_Y - 4} width={x1 - x0} height={depth} fill={`url(#${uid}-noise)`} opacity={0.75} />
      <ellipse cx={BASE_X} cy={SOIL_Y + 14} rx={120} ry={26} fill={`url(#${uid}-damp)`} />
      {bits.map((b, i) =>
        b.kind === "crumb" ? (
          <circle key={i} cx={b.x} cy={b.y} r={b.size * 0.35} fill="#7d5a3c" opacity={0.7} />
        ) : (
          <g key={i} transform={`translate(${b.x.toFixed(1)} ${b.y.toFixed(1)}) rotate(${b.rot.toFixed(0)})`}>
            <ellipse cx={1} cy={b.size * 0.35} rx={b.size * 1.05} ry={b.size * b.flat * 0.6} fill="#000" opacity={0.35} />
            <ellipse rx={b.size} ry={b.size * b.flat} fill={`url(#${uid}-${b.kind})`} />
          </g>
        ),
      )}
      {[
        [210, 607, 34, -8],
        [372, 611, 26, 12],
        [168, 622, 40, 4],
        [430, 628, 30, -14],
      ].map(([x, y, len, a], i) => (
        <path
          key={`s${i}`}
          d={`M${x} ${y} l${len} ${a * 0.2}`}
          stroke="#c8ae7a"
          strokeOpacity={0.55}
          strokeWidth={1.4}
          strokeLinecap="round"
        />
      ))}
    </g>
  );
});

/* ------------------------------------------------------------------ plant */

/** The whole plant at growth progress p. */
export function Plant({ uid, progress, sway = false }) {
  const m = buildPlant(progress);
  const back = m.leaves.filter((l) => l.back);
  const front = m.leaves.filter((l) => !l.back);
  return (
    <g>
      <ellipse cx={BASE_X + 4} cy={SOIL_Y + 3} rx={m.shadowRx} ry={7 + m.H * 0.012} fill={`url(#${uid}-shadow)`} />
      <Seed uid={uid} seed={m.seed} radicle={m.radicle} hook={m.hook} />
      <path
        d="M246 607 C262 597 281 593 300 595 C321 593 340 598 356 607 C330 611 270 611 246 607Z"
        fill={`url(#${uid}-soil)`}
      />
      <path
        d="M246 607 C262 597 281 593 300 595 C321 593 340 598 356 607 C330 611 270 611 246 607Z"
        fill={`url(#${uid}-noise)`}
        opacity={0.7}
      />

      <g className={sway ? "lp-sway" : undefined}>
        {back.map((l) => (
          <g key={l.key} transform={placeLeaf(l.attach, l.side, l.angle, l.scale)}>
            <LeafShape uid={uid} fill="back" youth={l.youth * 0.6} shadow={false} />
          </g>
        ))}

        {m.stemPath && <path d={m.stemPath} fill={`url(#${uid}-stem)`} />}

        {m.cotyledons &&
          [-1, 1].map((side) => (
            <g key={side} transform={placeLeaf(m.cotyledons.attach, side, m.cotyledons.angle, m.cotyledons.scale)}>
              <LeafShape uid={uid} shape="cotyledon" fill={m.cotyledons.aged > 0.5 ? "aged" : "cotyledon"} petiole={3} shadow={false} />
            </g>
          ))}

        {front.map((l) => (
          <g key={l.key} transform={placeLeaf(l.attach, l.side, l.angle, l.scale)}>
            <LeafShape
              uid={uid}
              youth={l.youth}
              lesions={l.target ? m.lesions : 0}
              markers={l.target ? m.markers : 0}
            />
          </g>
        ))}

        {m.bud &&
          [-1, 1].map((side) => (
            <g key={`b${side}`} transform={placeLeaf(m.bud.attach, side, -68, m.bud.scale)}>
              <LeafShape uid={uid} fill="young" petiole={4} shadow={false} />
            </g>
          ))}

        {m.flowers.map((fl) => (
          <Flower key={fl.key} {...fl} />
        ))}
        {m.pods.map((pod) => (
          <Pod key={pod.key} uid={uid} {...pod} />
        ))}
      </g>
    </g>
  );
}

/**
 * A self-contained framed picture of the plant at one stage (used for the timeline cards).
 * `view` = [x, y, width, height] in world units.
 */
export function PlantStill({ progress, view, title }) {
  const uid = useSvgId();
  return (
    <svg viewBox={view.join(" ")} role="img" aria-label={title} className="lp-still">
      <PlantDefs uid={uid} />
      <linearGradient id={`${uid}-sky`} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#13261a" />
        <stop offset="0.7" stopColor="#3d5a3a" />
        <stop offset="1" stopColor="#8f8a62" />
      </linearGradient>
      <rect x={view[0]} y={view[1]} width={view[2]} height={view[3]} fill={`url(#${uid}-sky)`} />
      <Ground uid={uid} x0={view[0] - 20} x1={view[0] + view[2] + 20} depth={view[3] + 40} />
      <Plant uid={uid} progress={progress} />
    </svg>
  );
}
