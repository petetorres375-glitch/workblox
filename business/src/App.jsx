import { useState } from "react";
import { useAuth } from "./contexts/AuthContext";
import Login from "./components/auth/Login";
import Footer from "./components/layout/Footer";
import Header from "./components/layout/Header";
import AdCopyWriter from "./components/tools/AdCopyWriter";
import Contacts from "./components/tools/Contacts";
import BatchATSAnalyzer from "./components/tools/BatchATSAnalyzer";
import BusinessEmailDrafter from "./components/tools/BusinessEmailDrafter";
import ContractAnalyzer from "./components/tools/ContractAnalyzer";
import CustomerResponseDrafter from "./components/tools/CustomerResponseDrafter";
import HiringManager from "./components/tools/HiringManager";
import JobDescWriter from "./components/tools/JobDescWriter";
import MeetingNotesCleaner from "./components/tools/MeetingNotesCleaner";
import PolicyGenerator from "./components/tools/PolicyGenerator";
import ProposalGenerator from "./components/tools/ProposalGenerator";
import ReviewRequestEmail from "./components/tools/ReviewRequestEmail";
import SOPGenerator from "./components/tools/SOPGenerator";
import SocialMediaGenerator from "./components/tools/SocialMediaGenerator";

const TOOLS = {
  hiring: HiringManager,
  "batch-ats": BatchATSAnalyzer,
  "job-desc": JobDescWriter,
  proposal: ProposalGenerator,
  contract: ContractAnalyzer,
  customer: CustomerResponseDrafter,
  review: ReviewRequestEmail,
  social: SocialMediaGenerator,
  "ad-copy": AdCopyWriter,
  policy: PolicyGenerator,
  sop: SOPGenerator,
  meeting: MeetingNotesCleaner,
  email: BusinessEmailDrafter,
  contacts: Contacts,
};

export default function App() {
  const { user, logout, planBlocked } = useAuth();
  const [active, setActive] = useState("hiring");
  const Tool = TOOLS[active] || HiringManager;

  if (!user) {
    if (planBlocked) {
      return (
        <div className="login-page">
          <div className="login-card">
            <div className="login-brand">
              <span className="brand-name" style={{ fontSize: "1.1rem" }}>
                Torres<span className="brand-accent">Tech</span> Remote
              </span>
              <span className="login-product">Workblox Business</span>
            </div>
            <p className="login-error" style={{ marginTop: "1.5rem" }}>
              Business subscription required.
            </p>
            <p className="page-subtitle" style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
              Contact{" "}
              <a href="mailto:pedro_torres@torrestechremote.com" style={{ color: "var(--orange)", fontWeight: 600 }}>
                Torres Tech Remote
              </a>{" "}
              to upgrade your account.
            </p>
            <button className="auth-link" onClick={logout} style={{ marginTop: "1.25rem" }}>
              Sign out
            </button>
          </div>
        </div>
      );
    }
    return <Login />;
  }

  return (
    <>
      <Header active={active} onSelect={setActive} />
      <main>
        <Tool />
      </main>
      <Footer />
    </>
  );
}
