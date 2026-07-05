import { useTranslation } from "react-i18next";
import LanguageSwitcher from "../layout/LanguageSwitcher";

export default function Welcome({ onEnter }) {
  const { t } = useTranslation(["common", "auth"]);

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <span className="brand-name" style={{ fontSize: "1.1rem" }}>
            Torres<span className="brand-accent">Tech</span> Remote
          </span>
          <span className="login-product">Workblox Business</span>
        </div>
        <h1 className="welcome-title">{t("common:welcomeTitle")}</h1>
        <p className="page-subtitle">{t("common:welcomeTagline")}</p>

        <div className="welcome-language">
          <LanguageSwitcher />
        </div>

        <button type="button" className="submit-btn" onClick={onEnter}>
          {t("auth:signIn")}
        </button>
      </div>
    </div>
  );
}
