from pydantic import BaseModel


class DashboardStats(BaseModel):
    total: int
    new: int
    in_progress: int
    completed: int
    rejected: int
    critical: int
    type_distribution: dict[str, int]
    daily_counts: list[dict]


class SettingItem(BaseModel):
    key: str
    value: str


class SettingsUpdate(BaseModel):
    values: dict[str, str]
