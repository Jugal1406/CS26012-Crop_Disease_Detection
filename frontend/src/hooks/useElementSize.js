import { useEffect, useState } from "react";

/** Width/height of an element, kept up to date when it resizes (e.g. phone rotation). */
export function useElementSize(ref, fallback = { width: 1440, height: 900 }) {
  const [size, setSize] = useState(fallback);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const update = () => {
      const r = el.getBoundingClientRect();
      if (r.width && r.height) {
        setSize((s) =>
          Math.abs(s.width - r.width) < 1 && Math.abs(s.height - r.height) < 1
            ? s
            : { width: r.width, height: r.height },
        );
      }
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref]);
  return size;
}
