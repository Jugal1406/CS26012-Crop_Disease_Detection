import { LeafShape, PlantDefs, useSvgId } from "./PlantScene";

/** A single chili leaf filling the frame, optionally showing leaf-spot lesions and AI markers. */
export function LeafCloseup({ lesions = 1, markers = 0, title = "Close-up of a chili leaf", className }) {
  const uid = useSvgId();
  return (
    <svg viewBox="-6 -46 150 92" className={className} role="img" aria-label={title}>
      <PlantDefs uid={uid} />
      <g transform="rotate(-9 68 0)">
        <LeafShape uid={uid} lesions={lesions} markers={markers} petiole={12} />
      </g>
    </svg>
  );
}

const at = (x, y, angle, scale) => `translate(${x} ${y}) rotate(${angle}) scale(${scale})`;

function Chili({ uid }) {
  return (
    <g>
      <g transform={at(-10, 34, -24, 1.02)}>
        <LeafShape uid={uid} />
      </g>
      <g transform={at(18, 52, 8, 0.7)}>
        <LeafShape uid={uid} fill="back" />
      </g>
      <g transform="translate(96 4) rotate(-14) scale(1.15)">
        <path d="M0 0 Q3.5 8 2.5 16" stroke="#3c6b25" strokeWidth={2} fill="none" strokeLinecap="round" />
        <path d="M-3.8 18 C-5.5 34 -2.5 58 6 76 C8 79 10.2 78 9.4 74 C7 56 8.6 34 8 18 Z" fill={`url(#${uid}-pod-red)`} />
        <path d="M1.2 24 C1 40 3 56 7 70" stroke="#fff" strokeOpacity={0.35} strokeWidth={1.4} fill="none" strokeLinecap="round" />
        <ellipse cx={2.1} cy={18.5} rx={6.4} ry={3.6} fill="#3b6a23" />
      </g>
    </g>
  );
}

/** Potato: a compound leaf — pairs of ovate leaflets along a central rachis, with tiny leaflets between. */
function Potato({ uid }) {
  const pairs = [
    [28, 0.5],
    [66, 0.6],
    [104, 0.62],
  ];
  return (
    <g transform="translate(-6 30) rotate(-20)">
      <path d="M0 0 C40 -2 90 -6 150 -6" stroke="#3f6e2a" strokeWidth={2.6} fill="none" strokeLinecap="round" />
      {[47, 86].map((x) =>
        [-1, 1].map((s) => (
          <g key={`${x}${s}`} transform={`translate(${x} -3) rotate(${s * 70}) scale(0.2)`}>
            <LeafShape uid={uid} shape="ovate" petiole={0} shadow={false} />
          </g>
        )),
      )}
      {pairs.map(([x, k]) =>
        [-1, 1].map((s) => (
          <g key={`${x}${s}`} transform={`translate(${x} -3) rotate(${s * 58}) scale(${k})`}>
            <LeafShape uid={uid} shape="ovate" petiole={6} fill={s < 0 ? "front" : "back"} />
          </g>
        )),
      )}
      <g transform="translate(148 -6) rotate(-4) scale(0.68)">
        <LeafShape uid={uid} shape="ovate" petiole={6} />
      </g>
    </g>
  );
}

/** Groundnut: four rounded (obovate) leaflets in two opposite pairs. */
function Groundnut({ uid }) {
  return (
    <g transform="translate(4 52) rotate(-38)">
      <path d="M0 0 C30 -1 64 -2 92 -2" stroke="#3f6e2a" strokeWidth={2.4} fill="none" strokeLinecap="round" />
      {[
        [62, -1, 0.72, "back"],
        [62, 1, 0.72, "front"],
        [92, -1, 0.8, "front"],
        [92, 1, 0.8, "front"],
      ].map(([x, s, k, fill]) => (
        <g key={`${x}${s}`} transform={`translate(${x} -2) rotate(${s * 42}) scale(${k})`}>
          <LeafShape uid={uid} shape="obovate" petiole={4} fill={fill} />
        </g>
      ))}
    </g>
  );
}

const ART = { chili: Chili, potato: Potato, groundnut: Groundnut };

export function CropLeaf({ crop, title }) {
  const uid = useSvgId();
  const Art = ART[crop];
  return (
    <svg viewBox="-24 -96 210 196" role="img" aria-label={title} className="lp-cropleaf">
      <PlantDefs uid={uid} />
      <g className="lp-cropleaf__sway">
        <Art uid={uid} />
      </g>
    </svg>
  );
}
