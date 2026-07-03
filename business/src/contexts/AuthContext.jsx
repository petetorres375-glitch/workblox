import { createContext, useContext, useState, useCallback } from "react";
import i18n from "../i18n";
import { patch } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const token = localStorage.getItem("wbb_token");
      const name = localStorage.getItem("wbb_name");
      const email = localStorage.getItem("wbb_email");
      const plan = localStorage.getItem("wbb_plan");
      return (token && plan === "business") ? { token, name, email, plan } : null;
    } catch {
      return null;
    }
  });
  const [planBlocked, setPlanBlocked] = useState(false);

  const login = useCallback((token, name, email = "", plan = "free", language = null) => {
    if (plan !== "business") {
      setPlanBlocked(true);
      return;
    }
    localStorage.setItem("wbb_token", token);
    localStorage.setItem("wbb_name", name);
    localStorage.setItem("wbb_email", email);
    localStorage.setItem("wbb_plan", plan);
    setUser({ token, name, email, plan });
    setPlanBlocked(false);

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
      patch("/api/profile/language", { language: i18n.language }).catch(() => {});
    }
  }, []);

  const setLanguage = useCallback((lang) => {
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
    localStorage.removeItem("wbb_plan");
    setUser(null);
    setPlanBlocked(false);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, planBlocked, setLanguage }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
