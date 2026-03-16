import { useEffect, useState } from "react";

import { useAuth } from "../app/AuthContext";
import { BookingCard } from "../features/my-bookings/BookingCard";
import { apiRequest } from "../shared/api/client";
import { confirmTelegram } from "../shared/lib/telegram";
import type { Booking } from "../shared/types/api";

export function MyBookingsPage() {
  const { token } = useAuth();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = async (): Promise<void> => {
    if (!token) {
      return;
    }

    try {
      const response = await apiRequest<Booking[]>("/bookings/me", {}, token);
      setBookings(response);
      setError(null);
    } catch (value) {
      setError(value instanceof Error ? value.message : "Не удалось загрузить записи");
    }
  };

  useEffect(() => {
    void load();
  }, [token]);

  const handleCancel = async (booking: Booking): Promise<void> => {
    if (!token) {
      return;
    }

    const confirmed = await confirmTelegram("Отменить эту запись?");
    if (!confirmed) {
      return;
    }

    try {
      await apiRequest(`/bookings/${booking.id}/cancel`, { method: "POST" }, token);
      await load();
    } catch (value) {
      setError(value instanceof Error ? value.message : "Не удалось отменить запись");
    }
  };

  return (
    <div className="stack">
      <section className="hero hero--compact">
        <p className="eyebrow">My bookings</p>
        <h2>Ваши записи и быстрые отмены до начала сессии</h2>
      </section>
      {error ? <p className="error-text">{error}</p> : null}
      {bookings.length === 0 ? <p className="muted">Записей пока нет.</p> : null}
      {bookings.map((booking) => (
        <BookingCard key={booking.id} booking={booking} onCancel={(item) => void handleCancel(item)} />
      ))}
    </div>
  );
}

