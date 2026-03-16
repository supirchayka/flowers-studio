import { useEffect, useState } from "react";

import { apiRequest } from "../shared/api/client";
import type { Service } from "../shared/types/api";
import { ServiceCard } from "../features/services/ServiceCard";

export function ServicesPage() {
  const [services, setServices] = useState<Service[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void apiRequest<Service[]>("/services")
      .then(setServices)
      .catch((value: Error) => setError(value.message));
  }, []);

  return (
    <div className="stack">
      <section className="hero">
        <p className="eyebrow">Mini App MVP</p>
        <h2>Выберите услугу и забронируйте слот без переписки</h2>
        <p>
          Учитываем расписание студии, блокировки и уже созданные записи. Финальная проверка
          доступности всё равно идёт на сервере внутри транзакции.
        </p>
      </section>
      {error ? <p className="error-text">{error}</p> : null}
      {services.length === 0 && !error ? <p className="muted">Услуги пока не настроены.</p> : null}
      {services.map((service) => (
        <ServiceCard key={service.id} service={service} />
      ))}
    </div>
  );
}

