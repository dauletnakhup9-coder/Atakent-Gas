import io
import uuid
from datetime import timedelta
from unittest.mock import AsyncMock
import httpx
import pytest
from PIL import Image
from pydantic import ValidationError
from sqlalchemy import func, select
from app.config import get_settings
from app.models import Application, ApplicationFile, ApplicationHistory, FileType, Outbox, Priority, RealtimeEvent, Role
from app.notifications import deliver_one
from app.schemas import CreateApplication, StatusUpdate, local_today, verify_personal_account
from app.services import change_status, create_application
from app.storage import normalize_image


def payload(**updates):
    result = {
        "user": {"telegram_user_id": 123456, "first_name": "Resident"},
        "idempotency_key": str(uuid.uuid4()),
        "personal_account": "12345678",
        "application_type": "MPI_REMOVAL",
        "requested_date": local_today().isoformat(),
    }
    result.update(updates)
    return result


def jpeg():
    output = io.BytesIO()
    Image.new("RGB", (40, 40), "blue").save(output, "JPEG")
    return output.getvalue()


async def test_create_idempotent_and_initial_history(db):
    data = CreateApplication(**payload())
    a = await create_application(db, data)
    again = await create_application(db, data)
    assert a.id == again.id
    assert a.application_number.startswith("REQ-")
    assert await db.scalar(select(func.count()).select_from(Application)) == 1
    assert await db.scalar(select(func.count()).select_from(ApplicationHistory)) == 1
    assert await db.scalar(select(func.count()).select_from(RealtimeEvent)) == 1


@pytest.mark.parametrize(
    "updates",
    [
        {"personal_account": "１２３４５６"},
        {"personal_account": "123abc"},
        {"requested_date": (local_today() - timedelta(days=1)).isoformat()},
        {"user": {"telegram_user_id": -1, "first_name": "x"}},
        {"application_type": "METER_NOT_WORKING", "requested_date": None},
        {"latitude": 91},
        {"longitude": -181},
    ],
)
def test_validation(updates):
    with pytest.raises(ValidationError):
        CreateApplication(**payload(**updates))


def test_account_is_only_format_verified():
    assert verify_personal_account("12345678") == {"format_valid": True, "subscriber_verified": False}


async def test_gas_requires_owned_two_photos_and_coordinates(db):
    ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    for file_id, type in zip(ids, [FileType.METER_PHOTO, FileType.GAS_LEAK_PHOTO]):
        db.add(
            ApplicationFile(
                id=file_id,
                owner_telegram_id=123456,
                file_type=type,
                telegram_file_id=file_id,
                storage_url=file_id + ".jpg",
            )
        )
    await db.commit()
    data = CreateApplication(
        **payload(
            application_type="GAS_LEAK",
            requested_date=None,
            meter_photo_id=ids[0],
            leak_photo_id=ids[1],
            latitude=0,
            longitude=0,
        )
    )
    a = await create_application(db, data)
    assert a.priority == Priority.CRITICAL
    assert a.latitude == 0 and a.longitude == 0
    for id in ids:
        assert (await db.get(ApplicationFile, id)).application_id == a.id


async def test_cannot_attach_someone_elses_photo(db):
    from fastapi import HTTPException

    file = ApplicationFile(
        owner_telegram_id=999, file_type=FileType.METER_PHOTO, telegram_file_id="x", storage_url="x.jpg"
    )
    db.add(file)
    await db.commit()
    data = CreateApplication(
        **payload(
            application_type="METER_NOT_WORKING", requested_date=None, meter_photo_id=file.id, latitude=1, longitude=2
        )
    )
    with pytest.raises(HTTPException) as exc:
        await create_application(db, data)
    assert exc.value.status_code == 422
    assert await db.scalar(select(func.count()).select_from(Application)) == 0


async def test_status_history_outbox_atomic_and_private_comment(db, admin):
    a = await create_application(db, CreateApplication(**payload()))
    await change_status(
        db, a, admin, StatusUpdate(version=1, status="IN_PROGRESS", comment="private secret", public_comment=False)
    )
    notification = await db.scalar(select(Outbox))
    assert "private secret" not in notification.text
    assert a.application_number in notification.text
    await change_status(
        db, a, admin, StatusUpdate(version=2, status="COMPLETED", comment="public note", public_comment=True)
    )
    rows = (await db.scalars(select(Outbox).order_by(Outbox.id))).all()
    assert "public note" in rows[-1].text
    assert a.completed_at is not None
    assert await db.scalar(select(func.count()).select_from(ApplicationHistory)) == 3


async def test_auth_csrf_logout(logged_in):
    client = logged_in
    assert (await client.get("/api/auth/me")).status_code == 200
    client.headers.pop("X-CSRF-Token")
    assert (await client.post("/api/auth/logout")).status_code == 403
    me = (await client.get("/api/auth/me")).json()
    client.headers["X-CSRF-Token"] = me["csrf_token"]
    assert (await client.post("/api/auth/logout")).status_code == 204
    assert (await client.get("/api/applications")).status_code == 401


async def test_bad_login_and_origin(client, admin):
    assert (await client.post("/api/auth/login", json={"email": admin.email, "password": "wrong"})).status_code == 401
    assert (
        await client.post(
            "/api/auth/login",
            headers={"Origin": "https://evil.test"},
            json={"email": admin.email, "password": "correct-password-123"},
        )
    ).status_code == 403


async def test_rbac_list_detail_update_and_export(logged_in, db, admin):
    a = await create_application(db, CreateApplication(**payload()))
    admin.role = Role.OPERATOR
    await db.commit()
    assert (await logged_in.get("/api/applications")).json()["total"] == 0
    assert (await logged_in.get(f"/api/applications/{a.id}")).status_code == 404
    assert (
        await logged_in.patch(f"/api/applications/{a.id}/assign", json={"version": 1, "assigned_to": admin.id})
    ).status_code == 403
    assert (
        await logged_in.post(
            "/api/admins",
            json={
                "name": "Other",
                "email": "other@example.com",
                "password": "long-password-123",
                "role": "SUPER_ADMIN",
            },
        )
    ).status_code == 403
    a.assigned_to = admin.id
    await db.commit()
    assert (await logged_in.get(f"/api/applications/{a.id}")).status_code == 200
    assert (await logged_in.get("/api/reports")).json()["total"] == 1
    assert (await logged_in.get("/api/reports/export?format=xlsx")).content.startswith(b"PK")


async def test_status_conflict_and_transitions(logged_in, db):
    a = await create_application(db, CreateApplication(**payload()))
    path = f"/api/applications/{a.id}/status"
    assert (await logged_in.patch(path, json={"version": 1, "status": "COMPLETED"})).status_code == 422
    assert (await logged_in.patch(path, json={"version": 1, "status": "IN_PROGRESS"})).status_code == 200
    assert (await logged_in.patch(path, json={"version": 1, "status": "COMPLETED"})).status_code == 409


async def test_photos_type_size_and_private_access(client, logged_in, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "upload_dir", tmp_path)
    headers = {"X-Bot-Key": get_settings().bot_api_key}
    data = {"telegram_user_id": "123456", "telegram_file_id": "telegram-photo", "file_type": "METER_PHOTO"}
    response = await client.post(
        "/api/internal/photos", headers=headers, data=data, files={"photo": ("x.jpg", b"not an image", "image/jpeg")}
    )
    assert response.status_code == 422
    response = await client.post(
        "/api/internal/photos",
        headers=headers,
        data=data,
        files={"photo": ("x.exe", b"evil", "application/octet-stream")},
    )
    assert response.status_code == 415
    monkeypatch.setattr(get_settings(), "max_photo_bytes", 50)
    response = await client.post(
        "/api/internal/photos", headers=headers, data=data, files={"photo": ("x.jpg", jpeg(), "image/jpeg")}
    )
    assert response.status_code == 413
    monkeypatch.setattr(get_settings(), "max_photo_bytes", 10 * 1024 * 1024)
    response = await client.post(
        "/api/internal/photos", headers=headers, data=data, files={"photo": ("x.jpg", jpeg(), "image/jpeg")}
    )
    assert response.status_code == 201, response.text
    id = response.json()["id"]
    assert (await client.get(f"/api/files/{id}")).status_code == 404  # staged is private even to admins
    created = await client.post(
        "/api/internal/applications",
        headers=headers,
        json=payload(
            application_type="METER_NOT_WORKING", requested_date=None, meter_photo_id=id, latitude=45.1, longitude=65.2
        ),
    )
    assert created.status_code == 201, created.text
    assert (await client.get(f"/api/files/{id}")).status_code == 200
    client.cookies.clear()
    assert (await client.get(f"/api/files/{id}")).status_code == 401


def test_image_normalization_strips_metadata():
    result = normalize_image(jpeg())
    with Image.open(io.BytesIO(result)) as image:
        assert image.format == "JPEG"
        assert not image.getexif()


async def test_telegram_delivery_retries_and_success(db):
    row = Outbox(telegram_user_id=123456, text="Notification")
    db.add(row)
    await db.commit()
    client = AsyncMock()
    client.post.return_value = httpx.Response(429, json={"ok": False, "parameters": {"retry_after": 30}})
    assert await deliver_one(db, client)
    assert row.attempts == 1 and row.sent_at is None
    from app.database import utcnow

    row.next_attempt_at = utcnow() - timedelta(seconds=1)
    await db.commit()
    client.post.return_value = httpx.Response(200, json={"ok": True})
    assert await deliver_one(db, client)
    assert row.sent_at is not None


async def test_service_auth(client):
    assert (await client.post("/api/internal/applications", json=payload())).status_code == 401


async def test_settings_validation_and_stats(logged_in):
    settings = (await logged_in.get("/api/settings")).json()
    assert settings["emergency_phone"] == ""
    settings["notification_texts"]["COMPLETED"] = "{number.__class__}"
    assert (await logged_in.patch("/api/settings", json=settings)).status_code == 422
    assert (await logged_in.get("/api/dashboard/stats")).json()["total"] == 0
