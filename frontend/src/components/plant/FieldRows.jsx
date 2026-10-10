import { memo, useId, useMemo } from "react";
import { seeded } from "./geometry";

/*
 * Rows of crop plants seen from a distance, drawn as a few big SVG paths (one per row and
 * colour) so the page stays light even with hundreds of plants. Purely decorative.
 */

const ellipse = (cx, cy, rx, ry) =>
  `M${(cx - rx).toFixed(1)} ${cy.toFixed(1)}a${rx.toFixed(1)} ${ry.toFixed(1)} 0 1 0 ${(2 * rx).toFixed(1)} 0a${rx.toFixed(1)} ${ry.toFixed(1)} 0 1 0 ${(-2 * rx).toFixed(1)} 0`;

function buildRows(rows, width, seed) {
  const r = seeded(seed);
  return rows.map((row) => {
    let body = "";
    let highlights = "";
    const step = width / row.count;
    for (let i = -1; i <= row.count + 1; i++) {
      const x = i * step + (r() - 0.5) * step * 0.5;
      const h = row.height * (0.75 + r() * 0.5);
      const blobs = 7 + Math.floor(r() * 4);
      for (let b = 0; b < blobs; b++) {
        const t = b / (blobs - 1);
        const cx = x + (r() - 0.5) * row.height * 0.9;
        const cy = row.y - h * (0.18 + t * 0.7);
        const rx = row.height * (0.24 + r() * 0.2) * (1 - t * 0.4);
        const ry = rx * (0.42 + r() * 0.2);
        body += ellipse(cx, cy, rx, ry);
        if (t > 0.45 && r() > 0.55) highlights += ellipse(cx + rx * 0.2, cy - ry * 0.4, rx * 0.42, ry * 0.32);
      }
    }
    return { ...row, body, highlights };
  });
}

const VARIANTS = {
  // hero: distant field on the horizon
  far: {
    width: 1600,
    height: 300,
    rows: [
      { y: 286, height: 34, count: 46, color: "#294a33", light: "#6d8f5c", furrow: "#33402c" },
      { y: 298, height: 46, count: 36, color: "#22422b", light: "#7a9c5d", furrow: "#2f3524" },
    ],
  },
  mid: {
    width: 1600,
    height: 300,
    rows: [{ y: 300, height: 92, count: 15, color: "#1b3a22", light: "#88ad5f", furrow: "#2a2a1c" }],
  },
  // final call-to-action: a field stretching away in perspective
  cta: {
    width: 1600,
    height: 900,
    rows: [
      { y: 520, height: 16, count: 70, color: "#3d5a35", light: "#c6b46e", furrow: "#4c4a33" },
      { y: 548, height: 22, count: 56, color: "#365530", light: "#cdb66d", furrow: "#46412c" },
      { y: 585, height: 30, count: 44, color: "#2f4e2a", light: "#d2b66a", furrow: "#3e3826" },
      { y: 635, height: 44, count: 32, color: "#284625", light: "#d8b867", furrow: "#352e1f" },
      { y: 705, height: 64, count: 22, color: "#213e20", light: "#dcb862", furrow: "#2c2519" },
      { y: 800, height: 92, count: 15, color: "#1a341b", light: "#ddb45c", furrow: "#231d14" },
      { y: 930, height: 140, count: 9, color: "#132a15", light: "#d4a752", furrow: "#1a150f" },
    ],
  },
};

export const FieldRows = memo(function FieldRows({ variant = "far", className, seed = 11 }) {
  const cfg = VARIANTS[variant];
  const rows = useMemo(() => buildRows(cfg.rows, cfg.width, seed), [cfg, seed]);
  const uid = "f" + useId().replace(/[^a-zA-Z0-9_-]/g, "");
  return (
    <svg
      className={className}
      viewBox={`0 0 ${cfg.width} ${cfg.height}`}
      preserveAspectRatio="xMidYMax slice"
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        {rows.map((row, i) => (
          // each row is lit from above: sunlit tops fading into shadowed undersides
          <linearGradient key={i} id={`${uid}-${i}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={row.light} stopOpacity="0.55" />
            <stop offset="0.28" stopColor={row.color} />
            <stop offset="1" stopColor="#0b160c" />
          </linearGradient>
        ))}
      </defs>
      {rows.map((row, i) => (
        <g key={i}>
          <rect x={0} y={row.y - row.height * 0.08} width={cfg.width} height={row.height * 0.3} fill={row.furrow} opacity={0.65} />
          <path d={row.body} fill={`url(#${uid}-${i})`} />
          <path d={row.highlights} fill={row.light} opacity={0.12} />
        </g>
      ))}
    </svg>
  );
});
