import asyncio
import json
from pathlib import Path

from app.database import Session
from app.models import SecuritySeverity
from app.services import register_security_event


EVE_JSON_PATH = Path("/var/log/suricata/eve.json")


def map_suricata_severity(value: int | None) -> SecuritySeverity:
    if value == 1:
        return SecuritySeverity.CRITICAL
    if value == 2:
        return SecuritySeverity.HIGH
    if value == 3:
        return SecuritySeverity.WARNING
    return SecuritySeverity.INFO


async def save_suricata_event(event: dict) -> None:
    if event.get("event_type") != "alert":
        return

    alert = event.get("alert") or {}

    async with Session() as db:
        await register_security_event(
            db,
            source="suricata",
            severity=map_suricata_severity(alert.get("severity")),
            signature=alert.get("signature"),
            src_ip=event.get("src_ip"),
            src_country=None,
            dst_port=event.get("dest_port"),
            action=alert.get("action"),
            raw=event,
        )


async def process_line(line: str) -> None:
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return

    await save_suricata_event(event)


async def follow_eve_json() -> None:
    while not EVE_JSON_PATH.exists():
        await asyncio.sleep(5)

    with EVE_JSON_PATH.open("r", encoding="utf-8") as file:
        file.seek(0, 2)

        while True:
            line = file.readline()

            if not line:
                await asyncio.sleep(0.5)
                continue

            await process_line(line)


async def main() -> None:
    await follow_eve_json()


if __name__ == "__main__":
    asyncio.run(main())