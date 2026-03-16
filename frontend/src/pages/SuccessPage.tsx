import { useLocation, useNavigate } from "react-router-dom";

import type { Booking } from "../shared/types/api";
import { Button } from "../shared/ui/Button";
import { Card } from "../shared/ui/Card";

export function SuccessPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const booking = location.state as Booking | undefined;

  return (
    <Card>
      <div className="success-screen">
        <p className="eyebrow">Успех</p>
        <h2>Запись создана</h2>
        <p>
          {booking
            ? `${booking.service_name_snapshot} • ${new Date(booking.start_at).toLocaleString("ru-RU", {
                dateStyle: "medium",
                timeStyle: "short"
              })}`
            : "Мы сохранили бронирование и отправили подтверждение."}
        </p>
        <Button fullWidth onClick={() => navigate("/my-bookings")}>
          Открыть мои записи
        </Button>
      </div>
    </Card>
  );
}
