import uuid

from app.config import get_settings
from app.models import ApplicationFile, FileType, Role
from app.technician_models import Technician


def bot_headers():
    return {"X-Bot-Key": get_settings().bot_api_key}


async def register(client, telegram_user_id=555000111, full_name="Test technician"):
    response = await client.post("/api/technicians", json={
        "telegram_user_id": telegram_user_id, "full_name": full_name,
    })
    assert response.status_code == 201, response.text
    return response.json()


async def upload_seal_photo(db, telegram_user_id, content_hash=None):
    photo = ApplicationFile(owner_telegram_id=telegram_user_id, telegram_file_id="tg-" + str(uuid.uuid4()),
                            file_type=FileType.SEAL_PHOTO, storage_url=f"{uuid.uuid4()}.jpg", content_hash=content_hash)
    db.add(photo)
    await db.commit()
    return str(photo.id)


def seal_payload(**changes):
    return {
        "telegram_user_id": 555000111, "idempotency_key": str(uuid.uuid4()), "account_number": "00123456",
        "meter_number": "M-000123", "reading_value": "120.500", "seal_number": "S-000999",
        "latitude": 44.84, "longitude": 65.48, **changes,
    }


async def test_technician_registry_requires_super_admin(client, logged_in, admin, db):
    row = await register(logged_in)
    assert row["telegram_user_id"] == 555000111 and row["active"] is True
    duplicate = await logged_in.post("/api/technicians", json={"telegram_user_id": 555000111, "full_name": "Other"})
    assert duplicate.status_code == 409
    listed = await logged_in.get("/api/technicians")
    assert listed.status_code == 200 and listed.json()["items"][0]["telegram_user_id"] == 555000111
    admin.role = Role.OPERATOR
    await db.commit()
    assert (await client.get("/api/technicians")).status_code == 403


async def test_update_technician_deactivates_and_checks_version(logged_in):
    row = await register(logged_in, telegram_user_id=555000222)
    stale = await logged_in.put(f"/api/technicians/{row['id']}", json={
        "full_name": row["full_name"], "active": False, "version": 99,
    })
    assert stale.status_code == 409
    updated = await logged_in.put(f"/api/technicians/{row['id']}", json={
        "full_name": "Renamed technician", "active": False, "version": row["version"],
    })
    assert updated.status_code == 200
    assert updated.json()["active"] is False and updated.json()["full_name"] == "Renamed technician"


async def test_technician_status_endpoint_reflects_active_flag(logged_in):
    row = await register(logged_in, telegram_user_id=555000333)
    active = await logged_in.get(f"/api/internal/technicians/{row['telegram_user_id']}", headers=bot_headers())
    assert active.status_code == 200 and active.json() == {"active": True, "full_name": "Test technician"}
    unknown = await logged_in.get("/api/internal/technicians/1", headers=bot_headers())
    assert unknown.json() == {"active": False, "full_name": None}
    await logged_in.put(f"/api/technicians/{row['id']}", json={
        "full_name": row["full_name"], "active": False, "version": row["version"],
    })
    inactive = await logged_in.get(f"/api/internal/technicians/{row['telegram_user_id']}", headers=bot_headers())
    assert inactive.json()["active"] is False


async def test_submit_seal_installation_rejects_unregistered_technician(logged_in, db):
    photo_id = await upload_seal_photo(db, 555000111)
    response = await logged_in.post("/api/internal/technicians/seal-installations", headers=bot_headers(),
        json=seal_payload(photo_id=photo_id))
    assert response.status_code == 403


async def test_submit_seal_installation_success_and_idempotent(logged_in, db):
    await register(logged_in)
    photo_id = await upload_seal_photo(db, 555000111)
    payload = seal_payload(photo_id=photo_id)
    first = await logged_in.post("/api/internal/technicians/seal-installations", headers=bot_headers(), json=payload)
    assert first.status_code == 201, first.text
    assert first.json()["account_number"] == "00123456" and first.json()["seal_number"] == "S-000999"
    repeat = await logged_in.post("/api/internal/technicians/seal-installations", headers=bot_headers(), json=payload)
    assert repeat.status_code == 201 and repeat.json()["id"] == first.json()["id"]
    listed = await logged_in.get("/api/technicians/seal-installations")
    assert listed.status_code == 200 and listed.json()["total"] == 1
    assert listed.json()["items"][0]["technician_name"] == "Test technician"


async def test_submit_seal_installation_rejects_photo_from_another_owner(logged_in, db):
    await register(logged_in)
    photo_id = await upload_seal_photo(db, 999999999)
    response = await logged_in.post("/api/internal/technicians/seal-installations", headers=bot_headers(),
        json=seal_payload(photo_id=photo_id))
    assert response.status_code == 422


async def test_submit_seal_installation_rejects_wrong_file_type(logged_in, db):
    await register(logged_in)
    photo = ApplicationFile(owner_telegram_id=555000111, telegram_file_id="tg-x",
                            file_type=FileType.METER_READING_PHOTO, storage_url=f"{uuid.uuid4()}.jpg")
    db.add(photo)
    await db.commit()
    response = await logged_in.post("/api/internal/technicians/seal-installations", headers=bot_headers(),
        json=seal_payload(photo_id=str(photo.id)))
    assert response.status_code == 422


async def test_submit_seal_installation_rejects_reused_photo(logged_in, db):
    await register(logged_in)
    photo_id = await upload_seal_photo(db, 555000111)
    first = await logged_in.post("/api/internal/technicians/seal-installations", headers=bot_headers(),
        json=seal_payload(photo_id=photo_id))
    assert first.status_code == 201
    second = await logged_in.post("/api/internal/technicians/seal-installations", headers=bot_headers(),
        json=seal_payload(photo_id=photo_id, idempotency_key=str(uuid.uuid4())))
    assert second.status_code == 422


async def test_seal_installations_export_formats(logged_in, db):
    await register(logged_in)
    photo_id = await upload_seal_photo(db, 555000111)
    await logged_in.post("/api/internal/technicians/seal-installations", headers=bot_headers(),
        json=seal_payload(photo_id=photo_id))
    csv_export = await logged_in.get("/api/technicians/seal-installations/export?format=csv")
    assert csv_export.status_code == 200 and csv_export.headers["content-type"].startswith("text/csv")
    xlsx_export = await logged_in.get("/api/technicians/seal-installations/export?format=xlsx")
    assert xlsx_export.status_code == 200 and "spreadsheetml" in xlsx_export.headers["content-type"]
