import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from "react";

import { apiRequest, ApiError } from "../shared/api/client";
import { clearStoredToken, getStoredToken, setStoredToken } from "../shared/lib/auth";
import { getTelegramWebApp } from "../shared/lib/telegram";
import type { SessionResponse, User } from "../shared/types/api";

type AuthState = {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

async function exchangeSession(): Promise<SessionResponse> {
  const app = getTelegramWebApp();
  if (app?.initData) {
    return apiRequest<SessionResponse>("/auth/session", {
      method: "POST",
      body: JSON.stringify({ init_data: app.initData })
    });
  }

  if (import.meta.env.VITE_DEV_LOGIN === "true") {
    return apiRequest<SessionResponse>("/auth/dev-session", {
      method: "POST",
      body: JSON.stringify({
        telegram_id: Number(import.meta.env.VITE_DEV_TELEGRAM_ID ?? "5000"),
        first_name: import.meta.env.VITE_DEV_FIRST_NAME ?? "Alex",
        last_name: import.meta.env.VITE_DEV_LAST_NAME ?? "Studio",
        username: import.meta.env.VITE_DEV_USERNAME ?? "studio_admin",
        language_code: "ru"
      })
    });
  }

  throw new Error("Не удалось получить Telegram initData и dev-login выключен");
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshUser = async (): Promise<void> => {
    const currentToken = getStoredToken();
    if (!currentToken) {
      setUser(null);
      setToken(null);
      return;
    }

    const me = await apiRequest<User>("/auth/me", {}, currentToken);
    setUser(me);
    setToken(currentToken);
  };

  useEffect(() => {
    let mounted = true;

    const bootstrap = async (): Promise<void> => {
      try {
        setLoading(true);
        const existingToken = getStoredToken();
        if (existingToken) {
          const me = await apiRequest<User>("/auth/me", {}, existingToken);
          if (!mounted) {
            return;
          }
          setUser(me);
          setToken(existingToken);
          setError(null);
          return;
        }

        const session = await exchangeSession();
        if (!mounted) {
          return;
        }
        setStoredToken(session.access_token);
        setUser(session.user);
        setToken(session.access_token);
        setError(null);
      } catch (errorValue) {
        if (!mounted) {
          return;
        }
        clearStoredToken();
        setUser(null);
        setToken(null);
        if (errorValue instanceof ApiError || errorValue instanceof Error) {
          setError(errorValue.message);
        } else {
          setError("Не удалось авторизоваться");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    void bootstrap();
    return () => {
      mounted = false;
    };
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      token,
      loading,
      error,
      refreshUser,
    }),
    [error, loading, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}

