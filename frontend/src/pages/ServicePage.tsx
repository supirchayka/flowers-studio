import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { apiRequest } from "../shared/api/client";
import { useTelegramMainButton } from "../shared/hooks/useTelegramMainButton";
import type { Service } from "../shared/types/api";
import { Card } from "../shared/ui/Card";
import { Button } from "../shared/ui/Button";

export function ServicePage() {
  const navigate = useNavigate();
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

  const action = useMemo(() => {
    if (!service) {
      return null;
    }

    return () => navigate(`/book/${service.id}`);
  }, [navigate, service]);

  useTelegramMainButton({
    text: "Выбрать дату",
    visible: Boolean(service),
    onClick: action ?? undefined,
  });

  if (error) {
    return <p className="error-text">{error}</p>;
  }

  if (!service) {
    return <p className="muted">Загружаю услугу…</p>;
  }

  return (
    <Card>
      <div className="service-detail">
        <span className="pill">{service.duration_minutes} мин</span>
        <h2>{service.name}</h2>
        <p>{service.description}</p>
        <dl className="details-grid">
          <div>
            <dt>Стоимость</dt>
            <dd>{(service.price_minor / 100).toFixed(2)} {service.currency}</dd>
          </div>
          <div>
            <dt>Доступность</dt>
            <dd>{service.is_active ? "Активна" : "Скрыта"}</dd>
          </div>
        </dl>
        <Button onClick={() => navigate(`/book/${service.id}`)} fullWidth>
          Выбрать дату
        </Button>
      </div>
    </Card>
  );
}
