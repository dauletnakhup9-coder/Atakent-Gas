from datetime import date, timedelta

import pytest

from bot.services.validators import is_valid_account_format, parse_kk_date, validate_future_date


@pytest.mark.parametrize("account", ["123456789", "1234", "0000000000"])
def test_valid_account_formats(account):
    assert is_valid_account_format(account) is True


@pytest.mark.parametrize("account", ["", "abc123", "12 34", "12-34", "123", "  "])
def test_invalid_account_formats(account):
    assert is_valid_account_format(account) is False


def test_parse_kk_date_valid():
    assert parse_kk_date("25.09.2026") == date(2026, 9, 25)


@pytest.mark.parametrize("text", ["2026-09-25", "25/09/2026", "not a date", "32.13.2026"])
def test_parse_kk_date_invalid(text):
    assert parse_kk_date(text) is None


def test_validate_future_date_rejects_past():
    ok, reason = validate_future_date(date.today() - timedelta(days=1))
    assert ok is False
    assert reason == "past"


def test_validate_future_date_rejects_too_far():
    ok, reason = validate_future_date(date.today().replace(year=date.today().year + 5))
    assert ok is False
    assert reason == "too_far"


def test_validate_future_date_accepts_valid():
    ok, reason = validate_future_date(date.today() + timedelta(days=30))
    assert ok is True
    assert reason is None
