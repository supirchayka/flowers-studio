import { useEffect, useRef } from "react";

import { getTelegramWebApp } from "../lib/telegram";

export function useTelegramBackButton(enabled: boolean, onClick: () => void): void {
  const callbackRef = useRef(onClick);
  callbackRef.current = onClick;

  useEffect(() => {
    const app = getTelegramWebApp();
    if (!app) {
      return;
    }

    const handler = (): void => callbackRef.current();
    if (enabled) {
      app.BackButton.show();
      app.onEvent("backButtonClicked", handler);
    } else {
      app.BackButton.hide();
    }

    return () => {
      app.offEvent("backButtonClicked", handler);
      app.BackButton.hide();
    };
  }, [enabled]);
}
