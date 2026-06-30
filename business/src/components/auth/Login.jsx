import { useState, useEffect, useRef } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "../../contexts/AuthContext";
import { post } from "../../api/client";
import PasswordInput from "../ui/PasswordInput";

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [demoVisible, setDemoVisible] = useState(false);
  const [demoPassword, setDemoPassword] = useState("");
  const keySequence = useRef("");
  const demoInputRef = useRef(null);

  useEffect(() => {
    function handler(e) {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
      keySequence.current = (keySequence.current + e.key).slice(-3);
      if (keySequence.current === "ttr") {
        setDemoVisible(true);
        setTimeout(() => demoInputRef.current?.focus(), 50);
      }
    }
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  async function handleEmailLogin(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await post("/api/auth/login", { email, password });
      login(data.token, data.name, data.email, data.plan);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogle(credential) {
    setLoading(true);
    setError("");
    try {
      const data = await post("/api/auth/google", { credential });
      login(data.token, data.name, data.email, data.plan);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDemo(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await post("/api/auth/demo", { password: demoPassword, plan: "business" });
      login(data.token, data.name, null, data.plan);
    } catch (err) {
      setError("Invalid demo password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <span className="brand-name" style={{ fontSize: "1.1rem" }}>
            Torres<span className="brand-accent">Tech</span> Remote
          </span>
          <span className="login-product">Workblox Business</span>
        </div>
        <p className="login-tagline">Sign in to your account</p>

        <div className="login-google">
          <GoogleLogin
            onSuccess={(res) => handleGoogle(res.credential)}
            onError={() => setError("Google sign-in failed")}
            text="signin_with"
            shape="rectangular"
            size="large"
            width="280"
          />
        </div>

        <div className="auth-divider"><span>or</span></div>

        <form className="auth-form" onSubmit={handleEmailLogin}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
          />
          <PasswordInput
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
          />
          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        {demoVisible && (
          <form className="demo-form" onSubmit={handleDemo} style={{ marginTop: "1rem" }}>
            <input
              ref={demoInputRef}
              type="password"
              placeholder="Demo password"
              value={demoPassword}
              onChange={(e) => setDemoPassword(e.target.value)}
              maxLength={4}
              required
              disabled={loading}
              style={{ padding: "0.6rem 0.8rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", width: "100%", outline: "none" }}
            />
            <button type="submit" className="submit-btn" disabled={loading} style={{ marginTop: "0.5rem" }}>
              {loading ? "…" : "Enter Demo"}
            </button>
          </form>
        )}

        {error && <p className="login-error">{error}</p>}
      </div>
    </div>
  );
}
