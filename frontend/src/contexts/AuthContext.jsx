import { createContext, useContext, useState, useCallback } from "react";
import i18n from "../i18n";
import { patch } from "../api/client";

const AuthContext = createContext(null);

const ADMIN_EMAILS = new Set([
  "pete.torres.375@gmail.com",
  "pedro_torres@torrestechremote.com",
]);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const token = localStorage.getItem("wb_token");
      const name = localStorage.getItem("wb_name");
      const email = localStorage.getItem("wb_email");
      return token ? { token, name, email, isAdmin: ADMIN_EMAILS.has(email) } : null;
    } catch {
      return null;
    }
  });

  const login = useCallback((token, name, email = "", language = null) => {
    localStorage.setItem("wb_token", token);
    localStorage.setItem("wb_name", name);
    localStorage.setItem("wb_email", email);
    setUser({ token, name, email, isAdmin: ADMIN_EMAILS.has(email) });

    if (language) {
      // The profile already has an explicit saved language — it wins over
      // whatever this browser auto-detected, so a second device picks up
      // the first device's choice.
      i18n.changeLanguage(language);
    } else if (email) {
      // Backend returned null: this profile has never had a language saved.
      // Treat whatever this browser is already showing (auto-detected via
      // i18next-browser-languagedetector, or manually chosen pre-login) as
      // the real preference, and save it so it's there next time.
      patch("/api/profile/language", { language: i18n.resolvedLanguage || i18n.language }).catch(() => {});
    }
  }, []);

  const setLanguage = useCallback((lang) => {
    // i18n.changeLanguage also writes the choice back to localStorage
    // (wb_lang) via the language detector's configured cache.
    i18n.changeLanguage(lang);
    setUser((current) => {
      if (current?.email) {
        patch("/api/profile/language", { language: lang }).catch(() => {});
      }
      return current;
    });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("wb_token");
    localStorage.removeItem("wb_name");
    localStorage.removeItem("wb_email");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, setLanguage }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
