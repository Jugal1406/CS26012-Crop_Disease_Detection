// frontend/src/context/LanguageContext.jsx
import React, { createContext, useContext, useEffect, useState } from "react";
import { en } from "../locales/en";
import { hi } from "../locales/hi";
import { gu } from "../locales/gu";
import { getAuthToken } from "../services/authService";

const dictionaries = { en, hi, gu };

export const SUPPORTED_LANGUAGES = [
  { code: "en", label: "English", nativeName: "English", flag: "🇬🇧" },
  { code: "hi", label: "Hindi", nativeName: "हिन्दी", flag: "🇮🇳" },
  { code: "gu", label: "Gujarati", nativeName: "ગુજરાતી", flag: "🌾" },
];

const BACKEND_URL = "http://localhost:8000";

const LanguageContext = createContext({
  language: "en",
  setLanguage: () => {},
  changeLanguage: () => {},
  t: (key, fallback) => fallback || key,
  supportedLanguages: SUPPORTED_LANGUAGES,
});

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    const saved = localStorage.getItem("preferred_language");
    if (saved && (saved === "en" || saved === "hi" || saved === "gu")) {
      return saved;
    }
    return "en";
  });

  const changeLanguage = async (newLang) => {
    if (!["en", "hi", "gu"].includes(newLang)) return;
    setLanguageState(newLang);
    localStorage.setItem("preferred_language", newLang);

    // Sync with PostgreSQL if user is authenticated
    try {
      const token = await getAuthToken();
      if (token) {
        await fetch(`${BACKEND_URL}/api/v1/auth/preferences`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ preferred_language: newLang }),
        });
      }
    } catch (err) {
      console.warn("Could not sync language preference with backend:", err);
    }
  };

  /**
   * Helper translation function supporting dot-notation keys:
   * e.g., t("nav.dashboard") or t("diagnose.runBtn")
   */
  const t = (path, fallback = "") => {
    const activeDict = dictionaries[language] || dictionaries.en;
    const fallbackDict = dictionaries.en;

    const resolve = (obj, p) => {
      if (!p) return undefined;
      const parts = p.split(".");
      let current = obj;
      for (const part of parts) {
        if (current && typeof current === "object" && part in current) {
          current = current[part];
        } else {
          return undefined;
        }
      }
      return current;
    };

    const val = resolve(activeDict, path);
    if (val !== undefined && typeof val === "string") return val;

    const fallbackVal = resolve(fallbackDict, path);
    if (fallbackVal !== undefined && typeof fallbackVal === "string") return fallbackVal;

    return fallback || path;
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage: changeLanguage,
        changeLanguage,
        t,
        supportedLanguages: SUPPORTED_LANGUAGES,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}

export function useTranslation() {
  return useContext(LanguageContext);
}
