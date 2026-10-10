import { useEffect, useRef, useState } from "react";
import { usePrefersReducedMotion } from "./usePrefersReducedMotion";

/**
 * How far the user has scrolled through `ref`'s element, from 0 to 1.
 *   mode "sticky" (default): 0 when its top reaches the top of the screen,
 *                            1 when its bottom reaches the bottom (for tall sticky sections).
 *   mode "pass":             0 when its top enters at the bottom of the screen,
 *                            1 when its bottom leaves at the top (for parallax on normal sections).
 * The value glides towards the real scroll position, which makes scrubbing feel smooth.
 */
export function useScrollProgress(ref, { smoothing = 0.14, mode = "sticky" } = {}) {
  const reduced = usePrefersReducedMotion();
  const [progress, setProgress] = useState(0);
  const current = useRef(0);

  useEffect(() => {
    let frame = 0;

    const target = () => {
      const el = ref.current;
      if (!el) return 0;
      const rect = el.getBoundingClientRect();
      if (mode === "pass") {
        const span = rect.height + window.innerHeight;
        return Math.min(1, Math.max(0, (window.innerHeight - rect.top) / span));
      }
      const total = rect.height - window.innerHeight;
      if (total <= 0) return 0;
      return Math.min(1, Math.max(0, -rect.top / total));
    };

    const tick = () => {
      const t = target();
      const diff = t - current.current;
      if (reduced || Math.abs(diff) < 0.0004) {
        current.current = t;
        setProgress(t);
        frame = 0;
        return;
      }
      current.current += diff * smoothing;
      setProgress(current.current);
      frame = requestAnimationFrame(tick);
    };

    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(tick);
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [ref, smoothing, mode, reduced]);

  return progress;
}
