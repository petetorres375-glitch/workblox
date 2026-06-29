import { createContext, useContext, useState, useCallback } from "react";

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

  const login = useCallback((token, name, email = "", plan = "free") => {
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
    <AuthContext.Provider value={{ user, login, logout, planBlocked }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
