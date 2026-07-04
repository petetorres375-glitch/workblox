import { useEffect, useState } from "react";

// GNOME requires new .desktop launchers to be marked trusted before they'll run,
// so Chrome's PWA shortcut fails silently with an "Untrusted Desktop File" warning.
const isLinux = () => /Linux/.test(navigator.userAgent) && !/Android/.test(navigator.userAgent);

export function usePWA() {
  const [installPrompt, setInstallPrompt] = useState(() => window.__pwaPrompt || null);
  const [showLinuxTrustTip, setShowLinuxTrustTip] = useState(false);
  const isInstalled = window.matchMedia("(display-mode: standalone)").matches;

  useEffect(() => {
    // Pick up any prompt that fired before React mounted
    if (window.__pwaPrompt) setInstallPrompt(window.__pwaPrompt);

    const handler = (e) => {
      e.preventDefault();
      window.__pwaPrompt = e;
      setInstallPrompt(e);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  function install() {
    if (!installPrompt) return;
    installPrompt.prompt();
    installPrompt.userChoice.then(({ outcome }) => {
      setInstallPrompt(null);
      if (outcome === "accepted" && isLinux()) setShowLinuxTrustTip(true);
    });
  }

  function dismissLinuxTrustTip() {
    setShowLinuxTrustTip(false);
  }

  return { canInstall: !!installPrompt, install, isInstalled, showLinuxTrustTip, dismissLinuxTrustTip };
}
