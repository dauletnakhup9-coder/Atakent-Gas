import io
from datetime import date, timedelta

import pytest
from PIL import Image

from app.services import file_service, realtime
from tests.conftest import auth_header

INTERNAL_HEADERS = {"X-Internal-Api-Key": "test-internal-key"}


def _fake_jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="blue").save(buffer, format="JPEG")
    return buffer.getvalue()


FAKE_JPEG = _fake_jpeg()


@pytest.fixture(autouse=True)
def patch_external_calls(monkeypatch):
    async def fake_download(file_id: str) -> bytes:
        return FAKE_JPEG

    async def fake_publish(event_type, payload):
        return None

    monkeypatch.setattr(file_service, "download_telegram_file", fake_download)
    monkeypatch.setattr(realtime, "publish_event", fake_publish)


def _bot_payload(**overrides):
    payload = {
        "user": {"telegram_user_id": 12345, "telegram_username": "resident", "first_name": "Aigerim"},
        "personal_account": "123456789",
        "application_type": "METER_NOT_WORKING",
        "latitude": 51.169,
        "longitude": 71.449,
        "files": [{"file_type": "METER_PHOTO", "telegram_file_id": "tg-file-1"}],
    }
    payload.update(overrides)
    return payload


def test_meter_not_working_requires_photo(client):
    payload = _bot_payload(files=[])
    resp = client.post("/api/bot/applications", json=payload, headers=INTERNAL_HEADERS)
    assert resp.status_code == 400


def test_meter_not_working_requires_location(client):
    payload = _bot_payload(latitude=None, longitude=None)
    resp = client.post("/api/bot/applications", json=payload, headers=INTERNAL_HEADERS)
    assert resp.status_code == 400


def test_meter_not_working_success(client):
    resp = client.post("/api/bot/applications", json=_bot_payload(), headers=INTERNAL_HEADERS)
    assert resp.status_code == 201
    body = resp.json()
    assert body["application_number"].startswith("REQ-")
    assert body["priority"] == "NORMAL"
    assert body["status"] == "NEW"
    assert len(body["files"]) == 1


def test_gas_leak_is_critical_and_requires_both_photos(client):
    payload = _bot_payload(
        application_type="GAS_LEAK",
        files=[{"file_type": "METER_PHOTO", "telegram_file_id": "tg-1"}],
    )
    resp = client.post("/api/bot/applications", json=payload, headers=INTERNAL_HEADERS)
    assert resp.status_code == 400

    payload["files"].append({"file_type": "GAS_LEAK_PHOTO", "telegram_file_id": "tg-2"})
    resp = client.post("/api/bot/applications", json=payload, headers=INTERNAL_HEADERS)
    assert resp.status_code == 201
    assert resp.json()["priority"] == "CRITICAL"


def test_mpi_removal_rejects_past_date(client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    payload = _bot_payload(application_type="MPI_REMOVAL", requested_date=yesterday, files=[], latitude=None, longitude=None)
    resp = client.post("/api/bot/applications", json=payload, headers=INTERNAL_HEADERS)
    assert resp.status_code == 400


def test_mpi_removal_success(client):
    future = (date.today() + timedelta(days=10)).isoformat()
    payload = _bot_payload(application_type="MPI_REMOVAL", requested_date=future, files=[], latitude=None, longitude=None)
    resp = client.post("/api/bot/applications", json=payload, headers=INTERNAL_HEADERS)
    assert resp.status_code == 201
    assert resp.json()["requested_date"] == future


def test_invalid_personal_account_format_rejected(client):
    payload = _bot_payload(personal_account="abc-not-a-number")
    resp = client.post("/api/bot/applications", json=payload, headers=INTERNAL_HEADERS)
    assert resp.status_code == 422


def test_bot_endpoint_requires_internal_key(client):
    resp = client.post("/api/bot/applications", json=_bot_payload())
    assert resp.status_code == 401


def test_admin_can_sort_applications_by_application_number(client, super_admin):
    client.post("/api/bot/applications", json=_bot_payload(personal_account="111111111"), headers=INTERNAL_HEADERS)
    client.post("/api/bot/applications", json=_bot_payload(personal_account="222222222"), headers=INTERNAL_HEADERS)
    headers = auth_header(client, "super@example.com", "password123")

    asc_resp = client.get(
        "/api/applications", params={"sort_by": "application_number", "sort_dir": "asc"}, headers=headers
    )
    desc_resp = client.get(
        "/api/applications", params={"sort_by": "application_number", "sort_dir": "desc"}, headers=headers
    )

    asc_numbers = [a["application_number"] for a in asc_resp.json()["items"]]
    desc_numbers = [a["application_number"] for a in desc_resp.json()["items"]]
    assert asc_numbers == list(reversed(desc_numbers))
    assert asc_numbers == sorted(asc_numbers)


def test_admin_can_list_created_applications(client, super_admin):
    client.post("/api/bot/applications", json=_bot_payload(), headers=INTERNAL_HEADERS)
    headers = auth_header(client, "super@example.com", "password123")
    resp = client.get("/api/applications", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["application_type"] == "METER_NOT_WORKING"


def test_status_change_creates_history_entry(client, super_admin):
    create_resp = client.post("/api/bot/applications", json=_bot_payload(), headers=INTERNAL_HEADERS)
    app_id = create_resp.json()["id"]
    headers = auth_header(client, "super@example.com", "password123")

    resp = client.patch(
        f"/api/applications/{app_id}/status",
        json={"status": "IN_PROGRESS", "comment": "Қабылданды"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"

    history_resp = client.get(f"/api/applications/{app_id}/history", headers=headers)
    history = history_resp.json()
    assert len(history) == 2
    assert history[-1]["new_status"] == "IN_PROGRESS"
    assert history[-1]["comment"] == "Қабылданды"
