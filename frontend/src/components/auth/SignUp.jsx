import { useState } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "../../contexts/AuthContext";
import { post } from "../../api/client";
import PasswordInput from "../ui/PasswordInput";

export default function SignUp({ onSwitchToLogin }) {
  const { login } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  async function handleSignUp(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await post("/api/auth/register", { name, email, password });
      setSuccessMsg(data.message);
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

  if (successMsg) {
    return (
      <div className="login-page">
        <div className="login-card">
          <div className="login-brand">
            <span className="brand-name" style={{ fontSize: "1.1rem" }}>
              Torres<span className="brand-accent">Tech</span> Remote
            </span>
            <span className="login-product">Workblox</span>
          </div>
          <div className="pending-state">
            <div className="pending-icon">✓</div>
            <h2 className="pending-title">Account created</h2>
            <p className="pending-msg">{successMsg}</p>
            <button className="auth-link" onClick={onSwitchToLogin}>
              Back to sign in
            </button>
          </div>
        </div>
      </div>
    );
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
        <p className="login-tagline">Create your account</p>

        <div className="login-google">
          <GoogleLogin
            onSuccess={(res) => handleGoogle(res.credential)}
            onError={() => setError("Google sign-in failed")}
            text="signup_with"
            shape="rectangular"
            size="large"
            width="280"
          />
        </div>

        <div className="auth-divider"><span>or</span></div>

        <form className="auth-form" onSubmit={handleSignUp}>
          <input
            type="text"
            placeholder="Full name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            disabled={loading}
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
          />
          <PasswordInput
            placeholder="Password (min 8 characters)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
          />
          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        {error && <p className="login-error">{error}</p>}

        <p className="auth-switch">
          Already have an account?{" "}
          <button className="auth-link" onClick={onSwitchToLogin}>
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
