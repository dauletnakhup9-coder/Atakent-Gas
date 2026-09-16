import re
from datetime import date, datetime

ACCOUNT_PATTERN = re.compile(r"^\d{4,64}$")


def is_valid_account_format(account: str) -> bool:
    return bool(ACCOUNT_PATTERN.match(account.strip()))


def parse_kk_date(text: str) -> date | None:
    try:
        return datetime.strptime(text.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


def validate_future_date(value: date) -> tuple[bool, str | None]:
    today = date.today()
    if value < today:
        return False, "past"
    if value > today.replace(year=today.year + 2):
        return False, "too_far"
    return True, None
