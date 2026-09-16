import re
from datetime import date

ACCOUNT_PATTERN = re.compile(r"^\d{4,64}$")


def verify_personal_account(account_number: str) -> bool:
    """Validates a resident's personal/lицевой account number.

    Stage 1 (current): format-only validation. Stage 2 (future): plug in the
    organization's subscriber database/API here to confirm the account actually
    exists before accepting the application.
    """
    if not account_number:
        return False
    return bool(ACCOUNT_PATTERN.match(account_number.strip()))


def validate_requested_date(value: date, *, today: date | None = None) -> tuple[bool, str | None]:
    today = today or date.today()
    if value < today:
        return False, "Күні өткен уақытта болмауы керек"
    max_future = today.replace(year=today.year + 2)
    if value > max_future:
        return False, "Күн тым алыс мерзімге белгіленген"
    return True, None
