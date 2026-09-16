import io
from datetime import date, timedelta

import pytest
from PIL import Image

from app.config import get_settings
from app.services.file_service import FileValidationError, validate_image_bytes
from app.services.validators import validate_requested_date, verify_personal_account


def _make_image_bytes(fmt: str) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buffer, format=fmt)
    return buffer.getvalue()


def test_valid_jpeg_bytes_pass():
    assert validate_image_bytes(_make_image_bytes("JPEG")) == "image/jpeg"


def test_valid_png_bytes_pass():
    assert validate_image_bytes(_make_image_bytes("PNG")) == "image/png"


def test_corrupted_jpeg_header_rejected():
    data = b"\xff\xd8\xff" + b"0" * 100
    with pytest.raises(FileValidationError):
        validate_image_bytes(data)


def test_non_image_bytes_rejected():
    data = b"%PDF-1.4 not an image" + b"0" * 100
    with pytest.raises(FileValidationError):
        validate_image_bytes(data)


def test_empty_file_rejected():
    with pytest.raises(FileValidationError):
        validate_image_bytes(b"")


def test_oversized_file_rejected():
    settings = get_settings()
    data = b"\xff\xd8\xff" + b"0" * (settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
    with pytest.raises(FileValidationError):
        validate_image_bytes(data)


@pytest.mark.parametrize("account", ["123456789", "1234", "0000000000"])
def test_verify_personal_account_valid(account):
    assert verify_personal_account(account) is True


@pytest.mark.parametrize("account", ["", "abc123", "12 34", "12-34", "123"])
def test_verify_personal_account_invalid(account):
    assert verify_personal_account(account) is False


def test_requested_date_rejects_past():
    ok, err = validate_requested_date(date.today() - timedelta(days=1))
    assert ok is False
    assert err


def test_requested_date_accepts_future():
    ok, err = validate_requested_date(date.today() + timedelta(days=5))
    assert ok is True
    assert err is None
