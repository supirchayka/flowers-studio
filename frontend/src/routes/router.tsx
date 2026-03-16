import { Routes, Route, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../app/AuthContext";
import { useTelegramBackButton } from "../shared/hooks/useTelegramBackButton";
import { Layout } from "../shared/ui/Layout";
import { AdminPage } from "../pages/AdminPage";
import { BookingPage } from "../pages/BookingPage";
import { MyBookingsPage } from "../pages/MyBookingsPage";
import { ServicePage } from "../pages/ServicePage";
import { ServicesPage } from "../pages/ServicesPage";
import { SuccessPage } from "../pages/SuccessPage";

function RouterContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const { loading, error, user } = useAuth();

  useTelegramBackButton(location.pathname !== "/", () => navigate(-1));

  if (loading) {
    return (
      <Layout user={null}>
        <p className="muted">Подключаю Mini App…</p>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout user={null}>
        <p className="error-text">{error}</p>
      </Layout>
    );
  }

  return (
    <Layout user={user}>
      <Routes>
        <Route path="/" element={<ServicesPage />} />
        <Route path="/services/:serviceId" element={<ServicePage />} />
        <Route path="/book/:serviceId" element={<BookingPage />} />
        <Route path="/my-bookings" element={<MyBookingsPage />} />
        <Route path="/success" element={<SuccessPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </Layout>
  );
}

export function AppRouter() {
  return <RouterContent />;
}
