from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest


@pytest.mark.asyncio
async def test_booking_flow_supports_create_cancel_and_admin_status_updates(
    client,
    admin_headers,
    user_headers,
    second_user_headers,
):
    tz = ZoneInfo("Europe/Moscow")
    target_day = (datetime.now(tz=tz) + timedelta(days=2)).date()

    service_response = await client.post(
        "/api/v1/admin/services",
        headers=admin_headers,
        json={
            "name": "Запись вокала",
            "description": "Часовая сессия с инженером и базовой подготовкой проекта.",
            "duration_minutes": 60,
            "price_minor": 450000,
            "currency": "RUB",
            "is_active": True,
        },
    )
    assert service_response.status_code == 201
    service_id = service_response.json()["id"]

    rule_response = await client.post(
        "/api/v1/admin/schedule/rules",
        headers=admin_headers,
        json={
            "weekday": target_day.weekday(),
            "start_time": "10:00:00",
            "end_time": "18:00:00",
            "is_active": True,
        },
    )
    assert rule_response.status_code == 201

    blocked_response = await client.post(
        "/api/v1/admin/schedule/blocked-intervals",
        headers=admin_headers,
        json={
            "start_at": datetime.combine(target_day, datetime.min.time(), tzinfo=tz).replace(hour=12).isoformat(),
            "end_at": datetime.combine(target_day, datetime.min.time(), tzinfo=tz).replace(hour=13).isoformat(),
            "reason": "Техпауза",
        },
    )
    assert blocked_response.status_code == 201

    availability_response = await client.get(f"/api/v1/services/{service_id}/availability?day={target_day.isoformat()}")
    assert availability_response.status_code == 200
    slots = availability_response.json()["slots"]
    labels = [slot["label"] for slot in slots]
    assert "12:00" not in labels
    assert labels[0] == "10:00"

    first_slot = slots[0]["start_at"]
    create_response = await client.post(
        "/api/v1/bookings",
        headers=user_headers,
        json={
            "service_id": service_id,
            "start_at": first_slot,
            "client_name": "Илья",
            "client_phone": "+79990000000",
            "client_comment": "Нужен вокальный микрофон",
            "client_request_id": "flow-1",
        },
    )
    assert create_response.status_code == 200
    booking_id = create_response.json()["id"]
    assert create_response.json()["status"] == "new"

    conflict_response = await client.post(
        "/api/v1/bookings",
        headers=second_user_headers,
        json={
            "service_id": service_id,
            "start_at": first_slot,
            "client_name": "Павел",
            "client_phone": "+79991111111",
            "client_comment": None,
            "client_request_id": "flow-2",
        },
    )
    assert conflict_response.status_code == 409

    my_bookings_response = await client.get("/api/v1/bookings/me", headers=user_headers)
    assert my_bookings_response.status_code == 200
    assert len(my_bookings_response.json()) == 1

    cancel_response = await client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=user_headers)
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    restored_response = await client.post(
        "/api/v1/bookings",
        headers=second_user_headers,
        json={
            "service_id": service_id,
            "start_at": first_slot,
            "client_name": "Павел",
            "client_phone": "+79991111111",
            "client_comment": None,
            "client_request_id": "flow-3",
        },
    )
    assert restored_response.status_code == 200
    restored_id = restored_response.json()["id"]

    admin_bookings_response = await client.get("/api/v1/admin/bookings", headers=admin_headers)
    assert admin_bookings_response.status_code == 200
    assert len(admin_bookings_response.json()) == 2

    status_response = await client.patch(
        f"/api/v1/admin/bookings/{restored_id}/status",
        headers=admin_headers,
        json={"status": "confirmed", "admin_note": "Оплачено на месте"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "confirmed"
    assert status_response.json()["admin_note"] == "Оплачено на месте"

