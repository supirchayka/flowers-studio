import { Link } from "react-router-dom";

import { Card } from "../../shared/ui/Card";
import type { Service } from "../../shared/types/api";

export function ServiceCard({ service }: { service: Service }) {
  return (
    <Card>
      <div className="service-card">
        <div className="service-card__copy">
          <span className="pill">{service.duration_minutes} мин</span>
          <h3>{service.name}</h3>
          <p>{service.description}</p>
        </div>
        <div className="service-card__footer">
          <strong>{(service.price_minor / 100).toFixed(2)} {service.currency}</strong>
          <Link className="text-link" to={`/services/${service.id}`}>
            Открыть
          </Link>
        </div>
      </div>
    </Card>
  );
}

