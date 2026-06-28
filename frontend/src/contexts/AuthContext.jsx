import { createContext, useContext, useState, useCallback } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const token = localStorage.getItem("wb_token");
      const name = localStorage.getItem("wb_name");
      return token ? { token, name } : null;
    } catch {
      return null;
    }
  });

  const login = useCallback((token, name) => {
    localStorage.setItem("wb_token", token);
    localStorage.setItem("wb_name", name);
    setUser({ token, name });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("wb_token");
    localStorage.removeItem("wb_name");
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
