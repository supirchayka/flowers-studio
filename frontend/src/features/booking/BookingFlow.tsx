import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiRequest } from "../../shared/api/client";
import { getTelegramWebApp } from "../../shared/lib/telegram";
import { useTelegramMainButton } from "../../shared/hooks/useTelegramMainButton";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { Field } from "../../shared/ui/Field";
import type { Availability, Booking, Service, Slot } from "../../shared/types/api";

type BookingFlowProps = {
  service: Service;
  token: string;
};

type Step = "date" | "time" | "contacts" | "confirm";

function buildDateOptions(): string[] {
  return Array.from({ length: 14 }, (_, index) => {
    const day = new Date();
    day.setDate(day.getDate() + index);
    const year = day.getFullYear();
    const month = `${day.getMonth() + 1}`.padStart(2, "0");
    const date = `${day.getDate()}`.padStart(2, "0");
    return `${year}-${month}-${date}`;
  });
}

export function BookingFlow({ service, token }: BookingFlowProps) {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("date");
  const [selectedDate, setSelectedDate] = useState<string>(buildDateOptions()[0]);
  const [availability, setAvailability] = useState<Availability | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [comment, setComment] = useState("");
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoadingSlots(true);
    setError(null);
    setSelectedSlot(null);

    void apiRequest<Availability>(`/services/${service.id}/availability?day=${selectedDate}`)
      .then(setAvailability)
      .catch((value: Error) => setError(value.message))
      .finally(() => setLoadingSlots(false));
  }, [selectedDate, service.id]);

  useEffect(() => {
    const app = getTelegramWebApp();
    if (step === "date") {
      app?.disableClosingConfirmation();
      return;
    }

    app?.enableClosingConfirmation();
    return () => app?.disableClosingConfirmation();
  }, [step]);

  const mainAction = useMemo(() => {
    if (step === "date") {
      return { visible: true, text: "Ко времени", onClick: () => setStep("time"), disabled: false };
    }
    if (step === "time") {
      return { visible: true, text: "К контактам", onClick: () => selectedSlot && setStep("contacts"), disabled: !selectedSlot };
    }
    if (step === "contacts") {
      return { visible: true, text: "Проверить запись", onClick: () => setStep("confirm"), disabled: !name || !phone };
    }
    return {
      visible: true,
      text: submitting ? "Бронируем…" : "Подтвердить запись",
      onClick: () => void submitBooking(),
      disabled: submitting,
    };
  }, [name, phone, selectedSlot, step, submitting]);

  useTelegramMainButton({
    text: mainAction.text,
    visible: mainAction.visible,
    loading: submitting,
    onClick: mainAction.disabled ? undefined : mainAction.onClick,
  });

  const submitBooking = async (): Promise<void> => {
    if (!selectedSlot) {
      setStep("time");
      return;
    }

    try {
      setSubmitting(true);
      const booking = await apiRequest<Booking>(
        "/bookings",
        {
          method: "POST",
          body: JSON.stringify({
            service_id: service.id,
            start_at: selectedSlot.start_at,
            client_name: name,
            client_phone: phone,
            client_comment: comment || null,
            client_request_id: crypto.randomUUID()
          })
        },
        token,
      );
      navigate("/success", { state: booking });
    } catch (value) {
      setError(value instanceof Error ? value.message : "Не удалось создать запись");
    } finally {
      setSubmitting(false);
    }
  };

  const summary = (
    <Card>
      <div className="summary">
        <p className="eyebrow">Сводка</p>
        <h3>{service.name}</h3>
        <p>{selectedDate || "Дата не выбрана"}</p>
        <p>{selectedSlot ? `${selectedSlot.label} • ${service.duration_minutes} мин` : "Время не выбрано"}</p>
      </div>
    </Card>
  );

  return (
    <div className="stack">
      {summary}
      {error ? <p className="error-text">{error}</p> : null}

      <Card>
        <div className="stepper">
          <span className={step === "date" ? "pill" : "pill pill--soft"}>1. Дата</span>
          <span className={step === "time" ? "pill" : "pill pill--soft"}>2. Время</span>
          <span className={step === "contacts" ? "pill" : "pill pill--soft"}>3. Контакты</span>
          <span className={step === "confirm" ? "pill" : "pill pill--soft"}>4. Подтверждение</span>
        </div>
      </Card>

      {step === "date" ? (
        <Card>
          <div className="choice-grid">
            {buildDateOptions().map((day) => (
              <button
                key={day}
                className={`choice-chip ${day === selectedDate ? "choice-chip--active" : ""}`}
                onClick={() => setSelectedDate(day)}
                type="button"
              >
                {new Date(day).toLocaleDateString("ru-RU", { day: "numeric", month: "short", weekday: "short" })}
              </button>
            ))}
          </div>
          <Button fullWidth onClick={() => setStep("time")}>
            Ко времени
          </Button>
        </Card>
      ) : null}

      {step === "time" ? (
        <Card>
          <div className="stack">
            <div className="inline-row">
              <h3>Выберите слот</h3>
              <Button variant="ghost" onClick={() => setStep("date")}>Сменить дату</Button>
            </div>
            {loadingSlots ? <p className="muted">Считаю слоты…</p> : null}
            {!loadingSlots && availability?.slots.length === 0 ? <p className="muted">Свободных слотов нет.</p> : null}
            <div className="choice-grid">
              {availability?.slots.map((slot) => (
                <button
                  key={slot.start_at}
                  className={`choice-chip ${slot.start_at === selectedSlot?.start_at ? "choice-chip--active" : ""}`}
                  onClick={() => setSelectedSlot(slot)}
                  type="button"
                >
                  {slot.label}
                </button>
              ))}
            </div>
            <Button fullWidth disabled={!selectedSlot} onClick={() => setStep("contacts")}>
              К контактам
            </Button>
          </div>
        </Card>
      ) : null}

      {step === "contacts" ? (
        <Card>
          <div className="stack">
            <Field label="Имя" value={name} onChange={(event) => setName(event.target.value)} placeholder="Как к вам обращаться" />
            <Field label="Телефон" value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="+7 999 123-45-67" />
            <Field
              label="Комментарий"
              multiline
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              placeholder="Например: нужен вокальный микрофон и MIDI-клавиатура"
            />
            <Button fullWidth disabled={!name || !phone} onClick={() => setStep("confirm")}>
              Проверить запись
            </Button>
          </div>
        </Card>
      ) : null}

      {step === "confirm" ? (
        <Card>
          <div className="stack">
            <h3>Проверьте данные</h3>
            <dl className="details-grid">
              <div>
                <dt>Услуга</dt>
                <dd>{service.name}</dd>
              </div>
              <div>
                <dt>Дата</dt>
                <dd>{selectedDate}</dd>
              </div>
              <div>
                <dt>Время</dt>
                <dd>{selectedSlot?.label}</dd>
              </div>
              <div>
                <dt>Контакт</dt>
                <dd>{name}, {phone}</dd>
              </div>
            </dl>
            {comment ? <p className="muted">{comment}</p> : null}
            <Button fullWidth onClick={() => void submitBooking()} disabled={submitting}>
              {submitting ? "Бронируем…" : "Подтвердить запись"}
            </Button>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
