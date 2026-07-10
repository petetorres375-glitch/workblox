import { createContext, useContext, useState, useCallback, useRef } from "react";
import i18n from "../i18n";
import { patch } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const token = localStorage.getItem("wbb_token");
      const name = localStorage.getItem("wbb_name");
      const email = localStorage.getItem("wbb_email");
      const hasBusiness = localStorage.getItem("wbb_has_business");
      return (token && hasBusiness === "true") ? { token, name, email } : null;
    } catch {
      return null;
    }
  });
  const [accessBlocked, setAccessBlocked] = useState(false);
  // Tracks whether the user explicitly picked a language this session (e.g.
  // via the pre-login Welcome screen) — if so, that choice must win over
  // whatever was previously saved on the account, rather than login()
  // silently reverting it.
  const manualLanguage = useRef(false);

  const login = useCallback((token, name, email = "", hasBusiness = false, language = null) => {
    if (!hasBusiness) {
      setAccessBlocked(true);
      return;
    }
    localStorage.setItem("wbb_token", token);
    localStorage.setItem("wbb_name", name);
    localStorage.setItem("wbb_email", email);
    localStorage.setItem("wbb_has_business", "true");
    setUser({ token, name, email });
    setAccessBlocked(false);

    if (language && !manualLanguage.current) {
      // The profile already has an explicit saved language — it wins over
      // whatever this browser auto-detected, so a second device picks up
      // the first device's choice. Skipped if the user just manually chose
      // a language this session (e.g. on the Welcome screen) — that choice
      // is more recent than whatever's saved and shouldn't be discarded.
      i18n.changeLanguage(language);
    } else if (email) {
      // Either the profile has never had a language saved, or the user just
      // manually picked one this session — either way, push whatever this
      // browser is currently showing up to the profile so it sticks.
      patch("/api/profile/language", { language: i18n.resolvedLanguage || i18n.language }).catch(() => {});
    }
  }, []);

  const setLanguage = useCallback((lang) => {
    manualLanguage.current = true;
    // i18n.changeLanguage also writes the choice back to localStorage
    // (wbb_lang) via the language detector's configured cache.
    i18n.changeLanguage(lang);
    setUser((current) => {
      if (current?.email) {
        patch("/api/profile/language", { language: lang }).catch(() => {});
      }
      return current;
    });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("wbb_token");
    localStorage.removeItem("wbb_name");
    localStorage.removeItem("wbb_email");
    localStorage.removeItem("wbb_has_business");
    setUser(null);
    setAccessBlocked(false);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, accessBlocked, setLanguage }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
