import { useEffect, useState } from "react";

export function usePWA() {
  const [installPrompt, setInstallPrompt] = useState(() => window.__pwaPrompt || null);

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
    installPrompt.userChoice.then(() => setInstallPrompt(null));
  }

  return { canInstall: !!installPrompt, install };
}
