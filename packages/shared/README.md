# API contract

The backend Pydantic schemas are the source of truth. `openapi.json` is generated from the implemented API. TypeScript view types live in `apps/admin-web/src/types/index.ts`. Bot speaks JSON through the internal API; it does not import backend code or access PostgreSQL.

Regenerate the OpenAPI contract from the repository root:

```sh
PYTHONPATH=apps/backend python scripts/export_openapi.py
```

Requires backend environment variables. This script never connects to a database.
