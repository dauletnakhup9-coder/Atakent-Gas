import json
from pathlib import Path
from app.main import app

root = Path(__file__).resolve().parents[1]
(root / "packages/shared/openapi.json").write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding="utf-8"
)
