import { Card } from "../../shared/ui/Card";
import { Button } from "../../shared/ui/Button";
import type { Booking } from "../../shared/types/api";

type BookingCardProps = {
  booking: Booking;
  onCancel?: (booking: Booking) => void;
};

export function BookingCard({ booking, onCancel }: BookingCardProps) {
  const start = new Date(booking.start_at);

  return (
    <Card>
      <div className="booking-card">
        <div className="booking-card__header">
          <div>
            <p className="eyebrow">Статус</p>
            <h3>{booking.service_name_snapshot}</h3>
          </div>
          <span className={`pill pill--status pill--status-${booking.status}`}>{booking.status}</span>
        </div>
        <p>{start.toLocaleString("ru-RU", { dateStyle: "medium", timeStyle: "short" })}</p>
        <p className="muted">{booking.client_phone}</p>
        {booking.client_comment ? <p className="muted">{booking.client_comment}</p> : null}
        {booking.can_cancel && onCancel ? (
          <Button variant="secondary" onClick={() => onCancel(booking)}>
            Отменить
          </Button>
        ) : null}
      </div>
    </Card>
  );
}

