import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/** When the route changes (e.g. Home → Diagnose), start the new page at the top. */
export default function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}
