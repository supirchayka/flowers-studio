import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { BookingFlow } from "../features/booking/BookingFlow";
import { useAuth } from "../app/AuthContext";
import { apiRequest } from "../shared/api/client";
import type { Service } from "../shared/types/api";

export function BookingPage() {
  const { token } = useAuth();
  const params = useParams();
  const [service, setService] = useState<Service | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.serviceId) {
      return;
    }

    void apiRequest<Service>(`/services/${params.serviceId}`)
      .then(setService)
      .catch((value: Error) => setError(value.message));
  }, [params.serviceId]);

  if (!token) {
    return <p className="error-text">Нет активной авторизации</p>;
  }

  if (error) {
    return <p className="error-text">{error}</p>;
  }

  if (!service) {
    return <p className="muted">Готовлю поток бронирования…</p>;
  }

  return <BookingFlow service={service} token={token} />;
}

