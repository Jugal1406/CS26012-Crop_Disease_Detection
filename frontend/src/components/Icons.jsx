/*
 * Small line icons drawn for this page (24×24 grid, 1.6 stroke, inherit the text colour).
 */
const base = {
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
  focusable: false,
};

const PATHS = {
  crop: (
    <>
      <path d="M12 21v-8" />
      <path d="M12 13c0-4 2.5-6.5 7-7 0 4.5-2.5 7-7 7Z" />
      <path d="M12 15.5C12 12 9.8 10 6 9.5c0 3.8 2.2 6 6 6Z" />
      <path d="M8 21h8" />
    </>
  ),
  upload: (
    <>
      <rect x="3.5" y="4.5" width="17" height="15" rx="3" />
      <path d="m3.5 16 4.5-4.5 3.5 3.5 2.5-2.5 6.5 5.5" />
      <path d="M16 3v6M13.5 5.5 16 3l2.5 2.5" />
    </>
  ),
  scan: (
    <>
      <path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16" />
      <path d="M8 15c0-4.5 2.6-7 8-7 0 5.2-2.6 8-8 7Z" />
      <path d="M8 15l4-3.6" />
    </>
  ),
  tag: (
    <>
      <path d="M3.5 12.2V5a1.5 1.5 0 0 1 1.5-1.5h7.2l8.3 8.3a1.5 1.5 0 0 1 0 2.1l-7 7a1.5 1.5 0 0 1-2.1 0Z" />
      <circle cx="8" cy="8" r="1.6" />
    </>
  ),
  report: (
    <>
      <path d="M6 3.5h8.5L19 8v11a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 5 19V5a1.5 1.5 0 0 1 1-1.5Z" />
      <path d="M14 3.5V8h5" />
      <path d="M8.5 16.5v-2M12 16.5v-4.5M15.5 16.5v-3" />
    </>
  ),
  layers: (
    <>
      <path d="m12 3.5 8.5 4.5-8.5 4.5L3.5 8Z" />
      <path d="m3.5 12 8.5 4.5 8.5-4.5" />
      <path d="m3.5 16 8.5 4.5 8.5-4.5" />
    </>
  ),
  net: (
    <>
      <circle cx="5" cy="7" r="1.7" />
      <circle cx="5" cy="17" r="1.7" />
      <circle cx="12" cy="5" r="1.7" />
      <circle cx="12" cy="12" r="1.7" />
      <circle cx="12" cy="19" r="1.7" />
      <circle cx="19" cy="12" r="1.7" />
      <path d="m6.6 7.6 3.8 3.6M6.6 6.4l3.8-1M6.6 16.4l3.8-3.6M6.6 17.6l3.8 1M13.6 5.8l3.9 5.2M13.7 12h3.6M13.6 18.2l3.9-5.2" />
    </>
  ),
  bolt: <path d="M13 3 5 13.5h6L10 21l8-10.5h-6Z" />,
  window: (
    <>
      <rect x="3" y="4.5" width="18" height="15" rx="2.5" />
      <path d="M3 9h18" />
      <circle cx="6" cy="6.8" r=".4" fill="currentColor" />
      <circle cx="8.2" cy="6.8" r=".4" fill="currentColor" />
    </>
  ),
  arrow: (
    <>
      <path d="M5 12h14" />
      <path d="m13 6 6 6-6 6" />
    </>
  ),
  down: (
    <>
      <path d="M12 5v14" />
      <path d="m6 13 6 6 6-6" />
    </>
  ),
  github: (
    <path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21" />
  ),
  menu: (
    <>
      <path d="M4 7h16M4 12h16M4 17h10" />
    </>
  ),
  close: (
    <>
      <path d="M6 6l12 12M18 6 6 18" />
    </>
  ),
  check: <path d="m5 12.5 4.5 4.5L19 7.5" />,
};

export function Icon({ name, size = 24, className, ...rest }) {
  return (
    <svg {...base} width={size} height={size} className={className} {...rest}>
      {PATHS[name]}
    </svg>
  );
}

/** Brand mark: a leaf inside scan brackets. */
export function LogoMark({ size = 30 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <path
        d="M4 10V6.5A2.5 2.5 0 0 1 6.5 4H10M22 4h3.5A2.5 2.5 0 0 1 28 6.5V10M28 22v3.5a2.5 2.5 0 0 1-2.5 2.5H22M10 28H6.5A2.5 2.5 0 0 1 4 25.5V22"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        opacity=".7"
      />
      <path d="M9.5 21.5C9.5 14 13.6 10 22.5 9.5c0 8.6-4.2 12.7-13 12Z" fill="#7fb14e" />
      <path d="M9.5 21.5c3-3.4 6.2-6.3 10-8.6" stroke="#e8f2d2" strokeWidth="1.3" strokeLinecap="round" fill="none" />
    </svg>
  );
}
