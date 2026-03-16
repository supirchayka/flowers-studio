import { useEffect, useState } from "react";

import { apiRequest } from "../../shared/api/client";
import type { AdminBooking, BlockedInterval, ScheduleRule, Service } from "../../shared/types/api";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { Field } from "../../shared/ui/Field";

type AdminPanelProps = {
  token: string;
};

const weekdayOptions = [
  { value: 0, label: "Пн" },
  { value: 1, label: "Вт" },
  { value: 2, label: "Ср" },
  { value: 3, label: "Чт" },
  { value: 4, label: "Пт" },
  { value: 5, label: "Сб" },
  { value: 6, label: "Вс" },
];

export function AdminPanel({ token }: AdminPanelProps) {
  const [dashboard, setDashboard] = useState<Record<string, number>>({});
  const [services, setServices] = useState<Service[]>([]);
  const [rules, setRules] = useState<ScheduleRule[]>([]);
  const [blocks, setBlocks] = useState<BlockedInterval[]>([]);
  const [bookings, setBookings] = useState<AdminBooking[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [serviceName, setServiceName] = useState("");
  const [serviceDescription, setServiceDescription] = useState("");
  const [serviceDuration, setServiceDuration] = useState("60");
  const [servicePrice, setServicePrice] = useState("350000");

  const [weekday, setWeekday] = useState("0");
  const [startTime, setStartTime] = useState("10:00");
  const [endTime, setEndTime] = useState("20:00");

  const [blockStart, setBlockStart] = useState("");
  const [blockEnd, setBlockEnd] = useState("");
  const [blockReason, setBlockReason] = useState("");

  const loadAll = async (): Promise<void> => {
    try {
      const [dashboardData, servicesData, rulesData, blocksData, bookingsData] = await Promise.all([
        apiRequest<Record<string, number>>("/admin/bookings/dashboard", {}, token),
        apiRequest<Service[]>("/admin/services", {}, token),
        apiRequest<ScheduleRule[]>("/admin/schedule/rules", {}, token),
        apiRequest<BlockedInterval[]>("/admin/schedule/blocked-intervals", {}, token),
        apiRequest<AdminBooking[]>("/admin/bookings", {}, token),
      ]);
      setDashboard(dashboardData);
      setServices(servicesData);
      setRules(rulesData);
      setBlocks(blocksData);
      setBookings(bookingsData);
      setError(null);
    } catch (value) {
      setError(value instanceof Error ? value.message : "Не удалось загрузить админ-данные");
    }
  };

  useEffect(() => {
    void loadAll();
  }, [token]);

  const createService = async (): Promise<void> => {
    await apiRequest(
      "/admin/services",
      {
        method: "POST",
        body: JSON.stringify({
          name: serviceName,
          description: serviceDescription,
          duration_minutes: Number(serviceDuration),
          price_minor: Number(servicePrice),
          currency: "RUB",
          is_active: true,
        }),
      },
      token,
    );
    setServiceName("");
    setServiceDescription("");
    setServiceDuration("60");
    setServicePrice("350000");
    await loadAll();
  };

  const createRule = async (): Promise<void> => {
    await apiRequest(
      "/admin/schedule/rules",
      {
        method: "POST",
        body: JSON.stringify({
          weekday: Number(weekday),
          start_time: `${startTime}:00`,
          end_time: `${endTime}:00`,
          is_active: true,
        }),
      },
      token,
    );
    await loadAll();
  };

  const createBlock = async (): Promise<void> => {
    await apiRequest(
      "/admin/schedule/blocked-intervals",
      {
        method: "POST",
        body: JSON.stringify({
          start_at: new Date(blockStart).toISOString(),
          end_at: new Date(blockEnd).toISOString(),
          reason: blockReason || null,
        }),
      },
      token,
    );
    setBlockStart("");
    setBlockEnd("");
    setBlockReason("");
    await loadAll();
  };

  const archiveService = async (serviceId: number): Promise<void> => {
    await apiRequest(`/admin/services/${serviceId}`, { method: "DELETE" }, token);
    await loadAll();
  };

  const deleteRule = async (ruleId: number): Promise<void> => {
    await apiRequest(`/admin/schedule/rules/${ruleId}`, { method: "DELETE" }, token);
    await loadAll();
  };

  const deleteBlock = async (blockId: number): Promise<void> => {
    await apiRequest(`/admin/schedule/blocked-intervals/${blockId}`, { method: "DELETE" }, token);
    await loadAll();
  };

  const updateStatus = async (bookingId: number, status: AdminBooking["status"]): Promise<void> => {
    await apiRequest(
      `/admin/bookings/${bookingId}/status`,
      {
        method: "PATCH",
        body: JSON.stringify({ status, admin_note: null }),
      },
      token,
    );
    await loadAll();
  };

  return (
    <div className="stack">
      {error ? <p className="error-text">{error}</p> : null}

      <Card>
        <div className="dashboard-grid">
          <div><span className="eyebrow">UPCOMING</span><strong>{dashboard.upcoming ?? 0}</strong></div>
          <div><span className="eyebrow">NEW</span><strong>{dashboard.new ?? 0}</strong></div>
          <div><span className="eyebrow">CONFIRMED</span><strong>{dashboard.confirmed ?? 0}</strong></div>
          <div><span className="eyebrow">CANCELLED</span><strong>{dashboard.cancelled ?? 0}</strong></div>
        </div>
      </Card>

      <Card>
        <div className="stack">
          <div className="inline-row">
            <h3>Услуги</h3>
            <span className="pill pill--soft">{services.length}</span>
          </div>
          <Field label="Название" value={serviceName} onChange={(event) => setServiceName(event.target.value)} />
          <Field label="Описание" multiline value={serviceDescription} onChange={(event) => setServiceDescription(event.target.value)} />
          <div className="split-grid">
            <Field label="Длительность, мин" type="number" value={serviceDuration} onChange={(event) => setServiceDuration(event.target.value)} />
            <Field label="Цена, копейки" type="number" value={servicePrice} onChange={(event) => setServicePrice(event.target.value)} />
          </div>
          <Button onClick={() => void createService()}>Добавить услугу</Button>
          {services.map((service) => (
            <div key={service.id} className="admin-item">
              <div>
                <strong>{service.name}</strong>
                <p className="muted">{service.duration_minutes} мин • {(service.price_minor / 100).toFixed(2)} {service.currency}</p>
              </div>
              {!service.is_archived ? <Button variant="secondary" onClick={() => void archiveService(service.id)}>Архивировать</Button> : <span className="pill pill--soft">Архив</span>}
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <div className="stack">
          <h3>Рабочие часы</h3>
          <div className="split-grid split-grid--three">
            <label className="field">
              <span>День недели</span>
              <select className="field__control" value={weekday} onChange={(event) => setWeekday(event.target.value)}>
                {weekdayOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
            <Field label="С" type="time" value={startTime} onChange={(event) => setStartTime(event.target.value)} />
            <Field label="До" type="time" value={endTime} onChange={(event) => setEndTime(event.target.value)} />
          </div>
          <Button onClick={() => void createRule()}>Добавить правило</Button>
          {rules.map((rule) => (
            <div key={rule.id} className="admin-item">
              <div>
                <strong>{weekdayOptions.find((item) => item.value === rule.weekday)?.label}</strong>
                <p className="muted">{rule.start_time.slice(0, 5)} - {rule.end_time.slice(0, 5)}</p>
              </div>
              <Button variant="secondary" onClick={() => void deleteRule(rule.id)}>Удалить</Button>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <div className="stack">
          <h3>Блокировки</h3>
          <div className="split-grid">
            <Field label="Начало" type="datetime-local" value={blockStart} onChange={(event) => setBlockStart(event.target.value)} />
            <Field label="Конец" type="datetime-local" value={blockEnd} onChange={(event) => setBlockEnd(event.target.value)} />
          </div>
          <Field label="Причина" value={blockReason} onChange={(event) => setBlockReason(event.target.value)} />
          <Button onClick={() => void createBlock()}>Добавить блокировку</Button>
          {blocks.map((block) => (
            <div key={block.id} className="admin-item">
              <div>
                <strong>{new Date(block.start_at).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" })}</strong>
                <p className="muted">
                  до {new Date(block.end_at).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" })}
                  {block.reason ? ` • ${block.reason}` : ""}
                </p>
              </div>
              <Button variant="secondary" onClick={() => void deleteBlock(block.id)}>Удалить</Button>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <div className="stack">
          <h3>Записи</h3>
          {bookings.map((booking) => (
            <div key={booking.id} className="admin-item admin-item--tall">
              <div>
                <strong>{booking.service_name_snapshot}</strong>
                <p className="muted">
                  {booking.client_name} • {booking.client_phone}
                </p>
                <p className="muted">
                  {new Date(booking.start_at).toLocaleString("ru-RU", { dateStyle: "medium", timeStyle: "short" })}
                </p>
              </div>
              <label className="field admin-status">
                <span>Статус</span>
                <select
                  className="field__control"
                  value={booking.status}
                  onChange={(event) => void updateStatus(booking.id, event.target.value as AdminBooking["status"])}
                >
                  <option value="new">new</option>
                  <option value="confirmed">confirmed</option>
                  <option value="completed">completed</option>
                  <option value="cancelled">cancelled</option>
                </select>
              </label>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

