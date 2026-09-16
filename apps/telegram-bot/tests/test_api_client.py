import httpx
import pytest

from bot.services import api_client


class FakeResponse:
    def __init__(self, status_code: int, json_data: dict) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = str(json_data)

    def json(self) -> dict:
        return self._json_data


@pytest.mark.asyncio
async def test_create_application_sends_expected_payload(monkeypatch):
    captured = {}

    async def fake_request(self, method, path, headers=None, json=None, params=None, **kwargs):
        captured["method"] = method
        captured["path"] = path
        captured["headers"] = headers
        captured["json"] = json
        return FakeResponse(201, {"application_number": "REQ-20260915-00001", "id": 1})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    result = await api_client.create_application(
        telegram_user_id=555,
        telegram_username="user",
        first_name="Aigerim",
        last_name=None,
        personal_account="123456789",
        application_type="METER_NOT_WORKING",
        latitude=51.1,
        longitude=71.4,
        files=[{"file_type": "METER_PHOTO", "telegram_file_id": "tg-1"}],
    )

    assert result["application_number"] == "REQ-20260915-00001"
    assert captured["method"] == "POST"
    assert captured["path"] == "/bot/applications"
    assert captured["headers"]["X-Internal-Api-Key"] == "test-internal-key"
    assert captured["json"]["personal_account"] == "123456789"
    assert captured["json"]["user"]["telegram_user_id"] == 555
    assert captured["json"]["files"][0]["telegram_file_id"] == "tg-1"


@pytest.mark.asyncio
async def test_api_error_raises_backend_api_error(monkeypatch):
    async def fake_request(self, method, path, headers=None, json=None, params=None, **kwargs):
        return FakeResponse(400, {"detail": "Дербес шот форматы дұрыс емес"})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    with pytest.raises(api_client.BackendApiError) as exc_info:
        await api_client.get_application_by_number("REQ-BAD")

    assert exc_info.value.status_code == 400
    assert "форматы" in exc_info.value.detail
