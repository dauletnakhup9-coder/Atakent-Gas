import io
import uuid
from pathlib import Path

import httpx
from PIL import Image, UnidentifiedImageError

from app.config import get_settings

settings = get_settings()

EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class FileValidationError(Exception):
    pass


def _detect_mime(data: bytes) -> str | None:
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image_bytes(data: bytes) -> str:
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(data) == 0:
        raise FileValidationError("Файл бос болмауы керек")
    if len(data) > max_bytes:
        raise FileValidationError(f"Файл өлшемі {settings.MAX_UPLOAD_SIZE_MB}MB аспауы керек")

    mime = _detect_mime(data)
    if mime is None or mime not in settings.allowed_mime_list:
        raise FileValidationError("Тек сурет файлдары қабылданады (JPEG/PNG/WEBP)")

    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise FileValidationError("Файл жарамды сурет емес") from exc

    return mime


async def download_telegram_file(telegram_file_id: str) -> bytes:
    async with httpx.AsyncClient(timeout=30) as client:
        info_resp = await client.get(
            f"{settings.TELEGRAM_API_BASE}/bot{settings.BOT_TOKEN}/getFile",
            params={"file_id": telegram_file_id},
        )
        info_resp.raise_for_status()
        file_path = info_resp.json()["result"]["file_path"]

        file_resp = await client.get(
            f"{settings.TELEGRAM_API_BASE}/file/bot{settings.BOT_TOKEN}/{file_path}"
        )
        file_resp.raise_for_status()
        return file_resp.content


def save_application_file(application_number: str, data: bytes, mime: str) -> str:
    ext = EXT_BY_MIME.get(mime, ".bin")
    directory = Path(settings.UPLOAD_DIR) / "applications" / application_number
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = directory / filename
    file_path.write_bytes(data)
    return f"/uploads/applications/{application_number}/{filename}"


async def fetch_validate_and_store_telegram_photo(application_number: str, telegram_file_id: str) -> str:
    data = await download_telegram_file(telegram_file_id)
    mime = validate_image_bytes(data)
    return save_application_file(application_number, data, mime)
