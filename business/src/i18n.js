import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

// English is bundled eagerly — it's the fallback language, so it must always
// be available synchronously with zero network round-trip, regardless of
// what the detected/selected language turns out to be.
const englishModules = import.meta.glob("./locales/en/*.json", { eager: true });
const englishResources = {};
for (const path in englishModules) {
  const match = path.match(/\.\/locales\/en\/([^/]+)\.json$/);
  if (!match) continue;
  englishResources[match[1]] = englishModules[path].default;
}

// Every other language is code-split into its own chunk by Vite and only
// fetched when actually needed — keeps the initial bundle from shipping all
// 24 languages' worth of translation JSON to every visitor.
const lazyModules = import.meta.glob("./locales/*/*.json");

const availableLangs = new Set(["en"]);
const availableNamespaces = new Set(Object.keys(englishResources));
for (const path in lazyModules) {
  const match = path.match(/\.\/locales\/([^/]+)\/([^/]+)\.json$/);
  if (!match) continue;
  availableLangs.add(match[1]);
  availableNamespaces.add(match[2]);
}

export const SUPPORTED_LANGUAGES = [...availableLangs].sort();
const NAMESPACES = [...availableNamespaces].sort();
const RTL_LANGUAGES = new Set(["ar", "he", "fa", "ur"]);

const lazyBackend = {
  type: "backend",
  init() {},
  read(language, namespace, callback) {
    if (language === "en") {
      callback(null, englishResources[namespace] || {});
      return;
    }
    const importer = lazyModules[`./locales/${language}/${namespace}.json`];
    if (!importer) {
      callback(null, {});
      return;
    }
    importer()
      .then((mod) => callback(null, mod.default))
      .catch((err) => callback(err, null));
  },
};

function applyDirection(lng) {
  document.documentElement.lang = lng;
  document.documentElement.dir = RTL_LANGUAGES.has(lng) ? "rtl" : "ltr";
}

export const initPromise = i18n
  .use(lazyBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en: englishResources }, // preloaded — backend only fires for other languages
    partialBundledLanguages: true,
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
  })
  .then(() => {
    applyDirection(i18n.resolvedLanguage || i18n.language);
  });

i18n.on("languageChanged", applyDirection);

export default i18n;
