import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "../../contexts/AuthContext";
import { post } from "../../api/client";
import PasswordInput from "../ui/PasswordInput";

export default function Login({ onSwitchToSignUp, onBack }) {
  const { t } = useTranslation("auth");
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [demoVisible, setDemoVisible] = useState(false);
  const [demoPassword, setDemoPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);

  const keySequence = useRef("");
  const keyTimer = useRef(null);
  const demoInputRef = useRef(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("verified") === "true") {
      setInfo(t("emailVerifiedInfo"));
      window.history.replaceState({}, "", window.location.pathname);
    } else if (params.get("verified") === "false") {
      setError(t("verificationInvalid"));
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [t]);

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
        setDemoPassword("");
        setDemoVisible((v) => !v);
        setError("");
        setTimeout(() => demoInputRef.current?.focus(), 50);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  async function handleEmailLogin(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setInfo("");
    try {
      const data = await post("/api/auth/login", { email, password });
      login(data.token, data.name, data.email, data.language);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogle(credential) {
    setLoading(true);
    setError("");
    setInfo("");
    try {
      const data = await post("/api/auth/google", { credential });
      login(data.token, data.name, data.email, data.language);
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
      setError(t("incorrectPassword"));
    } finally {
      setLoading(false);
      setDemoPassword("");
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        {onBack && (
          <button type="button" className="auth-back" onClick={onBack}>
            ‹ {t("common:back")}
          </button>
        )}
        <div className="login-brand">
          <span className="brand-name" style={{ fontSize: "1.1rem" }}>
            Torres<span className="brand-accent">Tech</span> Remote
          </span>
          <span className="login-product">Workblox</span>
        </div>
        <p className="login-tagline">{t("signInTagline")}</p>

        <div className="login-google">
          <GoogleLogin
            onSuccess={(res) => handleGoogle(res.credential)}
            onError={() => setError(t("googleError"))}
            text="signin_with"
            shape="rectangular"
            size="large"
            width="280"
          />
        </div>

        <div className="auth-divider"><span>{t("or")}</span></div>

        <form className="auth-form" onSubmit={handleEmailLogin}>
          <input
            type="email"
            placeholder={t("emailPlaceholder")}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
          />
          <PasswordInput
            placeholder={t("passwordPlaceholder")}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
          />
          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? t("signingIn") : t("signIn")}
          </button>
        </form>

        {info && <p className="login-info">{info}</p>}
        {error && <p className="login-error">{error}</p>}

        <p className="auth-switch">
          {t("noAccount")}{" "}
          <button className="auth-link" onClick={onSwitchToSignUp}>
            {t("signUp")}
          </button>
        </p>

        {demoVisible && (
          <form className="demo-form" onSubmit={handleDemo}>
            <input
              ref={demoInputRef}
              type="password"
              placeholder={t("demoPasswordPlaceholder")}
              value={demoPassword}
              onChange={(e) => setDemoPassword(e.target.value)}
              disabled={loading}
            />
            <button type="submit" disabled={loading}>{t("enter")}</button>
          </form>
        )}
      </div>
    </div>
  );
}
