import { useAuth } from "../app/AuthContext";
import { AdminPanel } from "../features/admin/AdminPanel";

export function AdminPage() {
  const { token, user } = useAuth();

  if (!user?.is_admin) {
    return <p className="error-text">Админ-доступ недоступен.</p>;
  }

  if (!token) {
    return <p className="error-text">Нет активной авторизации.</p>;
  }

  return <AdminPanel token={token} />;
}

