import type { PropsWithChildren, ReactNode } from "react";
import { NavLink } from "react-router-dom";

import type { User } from "../types/api";

type LayoutProps = PropsWithChildren<{
  user: User | null;
  headerRight?: ReactNode;
}>;

export function Layout({ children, user, headerRight }: LayoutProps) {
  return (
    <div className="shell">
      <div className="shell__bg" />
      <header className="topbar">
        <div>
          <p className="eyebrow">Recording Studio</p>
          <h1 className="topbar__title">Бронирование</h1>
        </div>
        <div className="topbar__meta">
          {headerRight}
          {user ? <span className="pill pill--soft">{user.first_name}</span> : null}
        </div>
      </header>
      <main className="content">{children}</main>
      <nav className="bottom-nav">
        <NavLink to="/" end className={({ isActive }) => `bottom-nav__link ${isActive ? "active" : ""}`.trim()}>
          Услуги
        </NavLink>
        <NavLink to="/my-bookings" className={({ isActive }) => `bottom-nav__link ${isActive ? "active" : ""}`.trim()}>
          Мои записи
        </NavLink>
        {user?.is_admin ? (
          <NavLink to="/admin" className={({ isActive }) => `bottom-nav__link ${isActive ? "active" : ""}`.trim()}>
            Админ
          </NavLink>
        ) : null}
      </nav>
    </div>
  );
}
