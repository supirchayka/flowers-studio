import { HashRouter } from "react-router-dom";

import { AuthProvider } from "./AuthContext";
import { AppRouter } from "../routes/router";
import { useTelegramTheme } from "../shared/hooks/useTelegramTheme";

function ThemedApp() {
  useTelegramTheme();
  return <AppRouter />;
}

export function App() {
  return (
    <AuthProvider>
      <HashRouter>
        <ThemedApp />
      </HashRouter>
    </AuthProvider>
  );
}

