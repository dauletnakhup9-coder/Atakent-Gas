"""Field technicians (seal installers) and their seal-installation reports.

A technician is staff, not a resident: access is granted by a SUPER_ADMIN who
registers the technician's Telegram ID in the admin panel. The bot shows a
technician-only menu to that Telegram ID instead of the resident flow.
"""
import csv
import io
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from pydantic import Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.auth import bot_auth, rate_limit, super_admin
from app.database import get_db
from app.models import Admin, ApplicationFile, FileType
from app.schemas import StrictModel
from app.services import audit
from app.storage import storage_path
from app.subscribers import safe_cell
from app.technician_models import SealInstallation, Technician

router = APIRouter(prefix="/api/technicians", tags=["technicians"])
internal = APIRouter(prefix="/api/internal/technicians", dependencies=[Depends(bot_auth)])
DB = Annotated[AsyncSession, Depends(get_db)]
Super = Annotated[Admin, Depends(super_admin)]


class TechnicianInput(StrictModel):
    telegram_user_id: int = Field(gt=0, le=2**52)
    full_name: str = Field(min_length=2, max_length=200)


class TechnicianUpdate(StrictModel):
    full_name: str = Field(min_length=2, max_length=200)
    active: bool
    version: int = Field(ge=1)


class SealInstallationInput(StrictModel):
    telegram_user_id: int = Field(gt=0, le=2**52)
    idempotency_key: UUID
    account_number: str = Field(pattern=r"^[0-9]{6,20}$")
    meter_number: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9-]+$")
    reading_value: Decimal = Field(ge=0, le=99999999999, max_digits=14, decimal_places=3)
    seal_number: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9-]+$")
    photo_id: UUID
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    @field_validator("meter_number", "seal_number")
    @classmethod
    def upper(cls, value):
        return value.upper()


def technician_dict(row):
    return {"id": row.id, "telegram_user_id": row.telegram_user_id, "full_name": row.full_name,
            "active": row.active, "version": row.version, "created_at": row.created_at.isoformat()}


def seal_dict(row):
    return {"id": row.id, "technician_id": row.technician_id, "account_number": row.account_number,
            "meter_number": row.meter_number, "reading_value": str(row.reading_value), "seal_number": row.seal_number,
            "latitude": row.latitude, "longitude": row.longitude, "created_at": row.created_at.isoformat()}


@router.get("")
async def list_technicians(db: DB, admin: Super):
    rows = (await db.scalars(select(Technician).order_by(Technician.id.desc()))).all()
    return {"items": [technician_dict(r) for r in rows]}


@router.post("", status_code=201)
async def create_technician(data: TechnicianInput, db: DB, admin: Super):
    row = Technician(telegram_user_id=data.telegram_user_id, full_name=data.full_name, created_by=admin.id)
    db.add(row)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "Бұл Telegram ID тіркелген") from exc
    audit(db, admin.id, "technician_create", row.id)
    await db.commit()
    return technician_dict(row)


@router.put("/{technician_id}")
async def update_technician(technician_id: int, data: TechnicianUpdate, db: DB, admin: Super):
    row = await db.scalar(select(Technician).where(Technician.id == technician_id).with_for_update())
    if row is None:
        raise HTTPException(404, "Техник табылмады")
    if row.version != data.version:
        raise HTTPException(409, "Деректер өзгерген. Бетті жаңартыңыз.")
    row.full_name, row.active = data.full_name, data.active
    row.version += 1
    audit(db, admin.id, "technician_update", row.id)
    await db.commit()
    return technician_dict(row)


@router.get("/seal-installations")
async def list_seal_installations(db: DB, admin: Super, page: int = Query(1, ge=1)):
    query = select(SealInstallation, Technician.full_name).join(Technician)
    total = await db.scalar(select(func.count()).select_from(SealInstallation))
    rows = (await db.execute(query.order_by(SealInstallation.created_at.desc())
        .offset((page - 1) * 25).limit(25))).all()
    return {"items": [{**seal_dict(row), "technician_name": name} for row, name in rows], "total": total}


@router.get("/seal-installations/{seal_id}/photo")
async def seal_installation_photo(seal_id: UUID, db: DB, admin: Super):
    row = await db.scalar(select(SealInstallation).where(SealInstallation.id == str(seal_id)))
    if row is None:
        raise HTTPException(404, "Жазба табылмады")
    file = await db.get(ApplicationFile, row.photo_id)
    path = storage_path(file.storage_url) if file else None
    if path is None or not path.is_file():
        raise HTTPException(404, "Фото табылмады")
    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


def make_seal_export(rows, fmt):
    header = ["Күні", "Техник", "Дербес шот", "Есептегіш нөмірі", "Пломба нөмірі", "Көрсеткіш", "Координаттар"]
    if fmt == "csv":
        data = [[
            row.created_at.strftime("%d.%m.%Y %H:%M"), safe_cell(name), safe_cell(row.account_number),
            safe_cell(row.meter_number), safe_cell(row.seal_number), str(row.reading_value),
            f"https://www.google.com/maps?q={row.latitude},{row.longitude}",
        ] for row, name in rows]
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(header)
        writer.writerows(data)
        return buffer.getvalue().encode("utf-8-sig")
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("Пломбалар")
    sheet.append(header)
    for row, name in rows:
        coordinates = WriteOnlyCell(sheet, value=f"{row.latitude}, {row.longitude}")
        coordinates.hyperlink = f"https://www.google.com/maps?q={row.latitude},{row.longitude}"
        sheet.append([
            row.created_at.strftime("%d.%m.%Y %H:%M"), safe_cell(name), safe_cell(row.account_number),
            safe_cell(row.meter_number), safe_cell(row.seal_number), str(row.reading_value), coordinates,
        ])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


@router.get("/seal-installations/export")
async def export_seal_installations(db: DB, admin: Super, format: Literal["csv", "xlsx"] = "csv"):
    await rate_limit(f"seal-export:{admin.id}", 10, 300)
    rows = (await db.execute(select(SealInstallation, Technician.full_name).join(Technician)
        .order_by(SealInstallation.created_at.desc()))).all()
    result = await run_in_threadpool(make_seal_export, rows, format)
    audit(db, admin.id, "seal_installation_export", format)
    await db.commit()
    media = ("text/csv; charset=utf-8" if format == "csv"
             else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    return Response(result, media_type=media,
                    headers={"Content-Disposition": f'attachment; filename="plomba.{format}"'})


@internal.get("/{telegram_user_id}")
async def technician_status(telegram_user_id: int, db: DB):
    await rate_limit(f"technician-lookup:{telegram_user_id}", 30, 60)
    row = await db.scalar(select(Technician).where(
        Technician.telegram_user_id == telegram_user_id, Technician.active.is_(True)))
    return {"active": row is not None, "full_name": row.full_name if row else None}


@internal.post("/seal-installations", status_code=201)
async def submit_seal_installation(data: SealInstallationInput, db: DB):
    await rate_limit(f"seal-installation:{data.telegram_user_id}", 20, 3600)
    technician = await db.scalar(select(Technician).where(
        Technician.telegram_user_id == data.telegram_user_id, Technician.active.is_(True)))
    if technician is None:
        raise HTTPException(403, "Техник ретінде тіркелмегенсіз")
    existing = await db.scalar(select(SealInstallation).where(
        SealInstallation.telegram_user_id == data.telegram_user_id,
        SealInstallation.idempotency_key == str(data.idempotency_key),
    ))
    if existing:
        return seal_dict(existing)
    photo = await db.scalar(select(ApplicationFile).where(ApplicationFile.id == str(data.photo_id)).with_for_update())
    if photo is None or photo.owner_telegram_id != data.telegram_user_id or photo.application_id is not None \
            or photo.file_type != FileType.SEAL_PHOTO:
        raise HTTPException(422, "Фото табылмады немесе рұқсат жоқ. Қайта жіберіңіз.")
    already_used = await db.scalar(select(SealInstallation.id).where(SealInstallation.photo_id == str(data.photo_id)))
    if already_used:
        raise HTTPException(422, "Бұл фото бұрын пайдаланылған. Қайта түсіріп жіберіңіз.")
    row = SealInstallation(
        technician_id=technician.id, telegram_user_id=data.telegram_user_id,
        idempotency_key=str(data.idempotency_key), account_number=data.account_number,
        meter_number=data.meter_number, reading_value=data.reading_value, seal_number=data.seal_number,
        photo_id=str(data.photo_id), latitude=data.latitude, longitude=data.longitude,
    )
    db.add(row)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "Бұл сұраныс бұрын қолданылған.") from exc
    audit(db, None, "seal_installation_submit", row.id)
    await db.commit()
    return seal_dict(row)
