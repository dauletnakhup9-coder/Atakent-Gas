# packages/shared

Reserved for code genuinely shared across apps (e.g. a generated OpenAPI TypeScript client for
`apps/admin-web`, or a JSON schema both the bot and the dashboard validate against).

Currently the three apps intentionally stay decoupled and only share a contract, not code:
the backend's OpenAPI schema at `/api/openapi.json` is the source of truth for request/response
shapes, mirrored by hand in `apps/admin-web/lib/types.ts` and the Pydantic models the bot's
`api_client.py` sends/receives. If that duplication becomes painful, generate a typed client
into this package with a tool such as `openapi-typescript` and import it from `admin-web`.
