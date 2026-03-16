import { useEffect } from "react";

import { getTelegramWebApp } from "../lib/telegram";

function applyTheme(): void {
  const app = getTelegramWebApp();
  const params = app?.themeParams ?? {};
  const root = document.documentElement;

  root.style.setProperty("--tg-bg", params.bg_color ?? "#faf4eb");
  root.style.setProperty("--tg-surface", params.secondary_bg_color ?? "#fffaf4");
  root.style.setProperty("--tg-text", params.text_color ?? "#1d180f");
  root.style.setProperty("--tg-hint", params.hint_color ?? "#796b5c");
  root.style.setProperty("--tg-primary", params.button_color ?? "#ec6b3b");
  root.style.setProperty("--tg-primary-text", params.button_text_color ?? "#fff8f0");
  root.style.setProperty("--tg-link", params.link_color ?? "#b64b25");
}

export function useTelegramTheme(): void {
  useEffect(() => {
    const app = getTelegramWebApp();
    applyTheme();
    app?.ready();
    app?.expand();

    const onThemeChange = (): void => applyTheme();
    app?.onEvent("themeChanged", onThemeChange);

    return () => {
      app?.offEvent("themeChanged", onThemeChange);
    };
  }, []);
}

