import { createContext, useContext, useState, useCallback } from "react";

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

  const login = useCallback((token, name, email = "") => {
    localStorage.setItem("wb_token", token);
    localStorage.setItem("wb_name", name);
    localStorage.setItem("wb_email", email);
    setUser({ token, name, email, isAdmin: ADMIN_EMAILS.has(email) });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("wb_token");
    localStorage.removeItem("wb_name");
    localStorage.removeItem("wb_email");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
