export type BookingStatus = "new" | "confirmed" | "cancelled" | "completed";

export type User = {
  id: number;
  telegram_id: number;
  first_name: string;
  last_name: string | null;
  username: string | null;
  is_admin: boolean;
};

export type SessionResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type Service = {
  id: number;
  name: string;
  slug: string;
  description: string;
  duration_minutes: number;
  price_minor: number;
  currency: string;
  is_active: boolean;
  is_archived: boolean;
};

export type Slot = {
  start_at: string;
  end_at: string;
  label: string;
};

export type Availability = {
  date: string;
  slots: Slot[];
};

export type Booking = {
  id: number;
  status: BookingStatus;
  client_name: string;
  client_phone: string;
  client_comment: string | null;
  start_at: string;
  end_at: string;
  service_name_snapshot: string;
  service_price_snapshot: number;
  service_currency_snapshot: string;
  admin_note: string | null;
  cancelled_at: string | null;
  can_cancel: boolean;
};

export type AdminBooking = Booking & {
  service: Service;
  user: User;
};

export type ScheduleRule = {
  id: number;
  weekday: number;
  start_time: string;
  end_time: string;
  is_active: boolean;
};

export type BlockedInterval = {
  id: number;
  start_at: string;
  end_at: string;
  reason: string | null;
};
