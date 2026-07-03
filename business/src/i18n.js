import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

// Auto-discover every locale file under src/locales/<lang>/<namespace>.json —
// adding a new language later just means adding the files, no code changes here.
const modules = import.meta.glob("./locales/*/*.json", { eager: true });
const resources = {};
for (const path in modules) {
  const match = path.match(/\.\/locales\/([^/]+)\/([^/]+)\.json$/);
  if (!match) continue;
  const [, lng, ns] = match;
  resources[lng] = resources[lng] || {};
  resources[lng][ns] = modules[path].default;
}

export const SUPPORTED_LANGUAGES = Object.keys(resources).sort();
const NAMESPACES = Object.keys(resources.en || {});
const RTL_LANGUAGES = new Set(["ar", "he", "fa", "ur"]);

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: "en",
    supportedLngs: SUPPORTED_LANGUAGES,
    nonExplicitSupportedLngs: true, // "es-MX", "pt-BR", etc. resolve down to their base language
    ns: NAMESPACES,
    defaultNS: "common",
    detection: {
      // Only ever check localStorage then the browser's own language — no
      // querystring/cookie detection needed for this app. Once a language is
      // picked (auto or manual), it's cached back into localStorage so
      // detection effectively only runs once per browser.
      order: ["localStorage", "navigator"],
      caches: ["localStorage"],
      lookupLocalStorage: "wbb_lang",
    },
    interpolation: { escapeValue: false },
  });

function applyDirection(lng) {
  document.documentElement.lang = lng;
  document.documentElement.dir = RTL_LANGUAGES.has(lng) ? "rtl" : "ltr";
}

applyDirection(i18n.resolvedLanguage || i18n.language);
i18n.on("languageChanged", applyDirection);

export default i18n;
