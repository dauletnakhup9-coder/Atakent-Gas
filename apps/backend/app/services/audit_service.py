from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    *,
    admin_id: int | None,
    action: str,
    entity: str | None = None,
    entity_id: str | None = None,
    ip_address: str | None = None,
    details: str | None = None,
) -> None:
    db.add(
        AuditLog(
            admin_id=admin_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            ip_address=ip_address,
            details=details,
        )
    )
    await db.commit()
