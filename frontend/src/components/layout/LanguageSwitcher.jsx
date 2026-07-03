import { useTranslation } from "react-i18next";
import { useAuth } from "../../contexts/AuthContext";
import { SUPPORTED_LANGUAGES } from "../../i18n";

// Native autonyms so people can find their own language without reading English.
const LANGUAGE_LABELS = {
  en: "English",
  es: "Español",
  fr: "Français",
  de: "Deutsch",
  pt: "Português",
  zh: "中文",
  ja: "日本語",
  ko: "한국어",
  ar: "العربية",
  hi: "हिन्दी",
  ru: "Русский",
  it: "Italiano",
  nl: "Nederlands",
  pl: "Polski",
  tr: "Türkçe",
  vi: "Tiếng Việt",
  th: "ไทย",
  id: "Bahasa Indonesia",
  sv: "Svenska",
  uk: "Українська",
  el: "Ελληνικά",
  he: "עברית",
  cs: "Čeština",
  ro: "Română",
};

// English names alongside the autonym, for people who don't recognize the
// native spelling — e.g. "Русский (Russian)".
const ENGLISH_NAMES = {
  es: "Spanish",
  fr: "French",
  de: "German",
  pt: "Portuguese",
  zh: "Chinese",
  ja: "Japanese",
  ko: "Korean",
  ar: "Arabic",
  hi: "Hindi",
  ru: "Russian",
  it: "Italian",
  nl: "Dutch",
  pl: "Polish",
  tr: "Turkish",
  vi: "Vietnamese",
  th: "Thai",
  id: "Indonesian",
  sv: "Swedish",
  uk: "Ukrainian",
  el: "Greek",
  he: "Hebrew",
  cs: "Czech",
  ro: "Romanian",
};

function languageLabel(lng) {
  const native = LANGUAGE_LABELS[lng] || lng.toUpperCase();
  const english = ENGLISH_NAMES[lng];
  return english ? `${native} (${english})` : native;
}

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation("common");
  const { setLanguage } = useAuth();

  return (
    <select
      aria-label={t("language")}
      className="language-switcher"
      value={i18n.resolvedLanguage || i18n.language}
      onChange={(e) => setLanguage(e.target.value)}
    >
      {SUPPORTED_LANGUAGES.map((lng) => (
        <option key={lng} value={lng}>{languageLabel(lng)}</option>
      ))}
    </select>
  );
}
