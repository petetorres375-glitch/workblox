import { useEffect, useRef, useState } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "../../contexts/AuthContext";
import { post } from "../../api/client";

export default function Login({ onSwitchToSignUp }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [demoVisible, setDemoVisible] = useState(false);
  const [demoPassword, setDemoPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const keySequence = useRef("");
  const keyTimer = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === "INPUT") return;
      keySequence.current += e.key.toLowerCase();
      if (keySequence.current.length > 3) {
        keySequence.current = keySequence.current.slice(-3);
      }
      clearTimeout(keyTimer.current);
      keyTimer.current = setTimeout(() => { keySequence.current = ""; }, 1000);
      if (keySequence.current === "ttr") {
        keySequence.current = "";
        setDemoVisible((v) => !v);
        setError("");
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  async function handleEmailLogin(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await post("/api/auth/login", { email, password });
      login(data.token, data.name);
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
      login(data.token, data.name);
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
      const data = await post("/api/auth/demo", { password: demoPassword });
      login(data.token, data.name);
    } catch {
      setError("Incorrect password");
    } finally {
      setLoading(false);
      setDemoPassword("");
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <span className="brand-name" style={{ fontSize: "1.1rem" }}>
            Torres<span className="brand-accent">Tech</span> Remote
          </span>
          <span className="login-product">Workblox</span>
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
          <input
            type="password"
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

        {error && <p className="login-error">{error}</p>}

        <p className="auth-switch">
          Don't have an account?{" "}
          <button className="auth-link" onClick={onSwitchToSignUp}>
            Sign up
          </button>
        </p>

        {demoVisible && (
          <form className="demo-form" onSubmit={handleDemo}>
            <input
              type="password"
              placeholder="Demo password"
              value={demoPassword}
              onChange={(e) => setDemoPassword(e.target.value)}
              autoFocus
              disabled={loading}
            />
            <button type="submit" disabled={loading}>Enter</button>
          </form>
        )}
      </div>
    </div>
  );
}
