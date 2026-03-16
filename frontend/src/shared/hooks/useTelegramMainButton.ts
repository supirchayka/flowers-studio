import { useEffect, useRef } from "react";

import { getTelegramWebApp } from "../lib/telegram";

type MainButtonOptions = {
  text: string;
  visible: boolean;
  loading?: boolean;
  onClick?: () => void;
};

export function useTelegramMainButton({ text, visible, loading = false, onClick }: MainButtonOptions): void {
  const callbackRef = useRef(onClick);
  callbackRef.current = onClick;

  useEffect(() => {
    const app = getTelegramWebApp();
    if (!app) {
      return;
    }

    const handler = (): void => {
      callbackRef.current?.();
    };

    app.MainButton.setParams({ text, is_visible: visible, is_active: !loading });
    if (visible) {
      app.MainButton.show();
    } else {
      app.MainButton.hide();
    }

    if (loading) {
      app.MainButton.showProgress();
    } else {
      app.MainButton.hideProgress();
    }

    app.onEvent("mainButtonClicked", handler);
    return () => {
      app.offEvent("mainButtonClicked", handler);
      app.MainButton.hideProgress();
      app.MainButton.hide();
    };
  }, [loading, text, visible]);
}

