import { useEffect, useState } from "react";

/*
 * Soil grain texture, drawn once on a small canvas and reused as an image pattern.
 * (Much cheaper than an SVG turbulence filter, which would be recomputed while the camera zooms.)
 */
let cached = null;

function makeNoise() {
  if (cached) return cached;
  if (typeof document === "undefined") return null;
  const size = 128;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  const img = ctx.createImageData(size, size);
  let s = 1234567;
  const rand = () => ((s = (Math.imul(s, 1103515245) + 12345) >>> 0) / 4294967296);
  for (let i = 0; i < size * size; i++) {
    const v = rand();
    const o = i * 4;
    if (v < 0.12) {
      // light grain (sunlit sand/silt)
      img.data[o] = 196; img.data[o + 1] = 160; img.data[o + 2] = 118; img.data[o + 3] = 40 + rand() * 70;
    } else if (v < 0.42) {
      // dark grain (organic matter)
      img.data[o] = 18; img.data[o + 1] = 11; img.data[o + 2] = 6; img.data[o + 3] = 60 + rand() * 90;
    } else {
      img.data[o + 3] = 0;
    }
  }
  ctx.putImageData(img, 0, 0);
  cached = canvas.toDataURL("image/png");
  return cached;
}

export function useNoiseTexture() {
  const [url, setUrl] = useState(cached);
  useEffect(() => {
    if (!url) setUrl(makeNoise());
  }, [url]);
  return url;
}
