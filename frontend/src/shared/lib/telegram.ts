export type TelegramThemeParams = {
  bg_color?: string;
  secondary_bg_color?: string;
  text_color?: string;
  hint_color?: string;
  button_color?: string;
  button_text_color?: string;
  link_color?: string;
};

type EventName = "themeChanged" | "mainButtonClicked" | "backButtonClicked";

export type TelegramWebApp = {
  initData: string;
  themeParams: TelegramThemeParams;
  ready: () => void;
  expand: () => void;
  enableClosingConfirmation: () => void;
  disableClosingConfirmation: () => void;
  showPopup?: (params: { title?: string; message: string; buttons: Array<{ id: string; type?: string; text: string }> }, callback: (buttonId: string) => void) => void;
  onEvent: (event: EventName, cb: () => void) => void;
  offEvent: (event: EventName, cb: () => void) => void;
  MainButton: {
    setParams: (params: Record<string, unknown>) => void;
    show: () => void;
    hide: () => void;
    showProgress: () => void;
    hideProgress: () => void;
  };
  BackButton: {
    show: () => void;
    hide: () => void;
  };
};

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}

export function getTelegramWebApp(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null;
}

export async function confirmTelegram(message: string): Promise<boolean> {
  const app = getTelegramWebApp();
  if (app?.showPopup) {
    return new Promise((resolve) => {
      app.showPopup?.(
        {
          title: "Подтверждение",
          message,
          buttons: [
            { id: "confirm", text: "Да", type: "default" },
            { id: "cancel", text: "Нет", type: "destructive" }
          ]
        },
        (buttonId) => resolve(buttonId === "confirm"),
      );
    });
  }

  return window.confirm(message);
}

