import { useEffect, useState } from "react";

// GNOME requires new .desktop launchers to be marked trusted before they'll run,
// so Chrome's PWA shortcut fails silently with an "Untrusted Desktop File" warning.
const isLinux = () => /Linux/.test(navigator.userAgent) && !/Android/.test(navigator.userAgent);

// iOS never fires beforeinstallprompt, so canInstall is permanently false there
// and the install button always falls through to the how-to modal. That modal
// has to show Safari's Share-sheet steps rather than Chrome's menu, so the UI
// needs to know which platform it's talking to.
const isIOS = () =>
  /iPad|iPhone|iPod/.test(navigator.userAgent) ||
  // iPadOS 13+ reports itself as a Mac; the touch points are what give it away.
  (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

export function usePWA() {
  const [installPrompt, setInstallPrompt] = useState(() => window.__pwaPrompt || null);
  const [showLinuxTrustTip, setShowLinuxTrustTip] = useState(false);
  // Older iOS versions only expose navigator.standalone, not the media query,
  // so a home-screen launch there would otherwise still show "Install".
  const isInstalled =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

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

  return { canInstall: !!installPrompt, install, isInstalled, isIOS: isIOS(), showLinuxTrustTip, dismissLinuxTrustTip };
}
