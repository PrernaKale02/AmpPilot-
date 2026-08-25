# AmpPilot Backend

FastAPI service behind the AmpPilot React Native app. It holds the charging-data
provider credential and normalises third-party data into the exact shape the app
already renders, so the frontend never talks to a provider directly.

**Current phase: 2 — Open Charge Map integration.** `GET /api/charging-stations`
returns real nearby stations from [Open Charge Map](https://openchargemap.org)
v3. Google Places is not used.

## Folder structure

```text
Backend/
├── app/
│   ├── main.py                  app construction, CORS, error handlers, /health
│   ├── api/routes/charging.py   GET /api/charging-stations
│   ├── core/
│   │   ├── config.py            pydantic-settings, reads .env
│   │   ├── exceptions.py        domain errors (no FastAPI imports)
│   │   └── geo.py               haversine_km()
│   ├── schemas/charging.py      the frontend contract (camelCase JSON)
│   └── services/
│       ├── open_charge_map.py   OCM HTTP client
│       └── mappers.py           OCM POI -> ChargingStation (pure)
└── tests/                       80 tests, no network access
```

## Setup

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

cp .env.example .env            # then add your OCM API key
```

Get a free key at <https://openchargemap.org/site/develop/api>.

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Swagger UI: <http://localhost:8001/docs>

## Endpoints

### `GET /health`

Liveness probe. Calls no external service and needs no API key.

```json
{ "status": "ok" }
```

### `GET /api/charging-stations`

| Param | Type | Required | Default | Validation |
|---|---|---|---|---|
| `latitude` | float | yes | — | −90 … 90 |
| `longitude` | float | yes | — | −180 … 180 |
| `radius_km` | float | no | 10 | > 0, ≤ 50 |

```bash
curl "http://localhost:8001/api/charging-stations?latitude=19.0760&longitude=72.8777&radius_km=15"
```

```json
{
  "stations": [
    {
      "id": "ocm-307102",
      "name": "Andheri West",
      "network": null,
      "address": "Four Bunglows, Mumbai, Maharashtra, 400057",
      "latitude": 19.1166,
      "longitude": 72.82927,
      "distanceKm": 6.8,
      "status": null,
      "availableConnectors": null,
      "totalConnectors": 1,
      "maxPowerKw": 120.0,
      "connectorTypes": ["CCS2"],
      "chargerType": "DC",
      "pricePerKwh": null,
      "currency": null,
      "isOpen24Hours": null,
      "hours": null,
      "lastUpdatedAt": "2025-03-10T14:49:00Z"
    }
  ],
  "origin": { "latitude": 19.076, "longitude": 72.8777 },
  "radiusKm": 15.0
}
```

Distances are computed by this backend with `haversine_km()` from the request
origin and rounded to 1 decimal — the provider's own distance field is ignored.
Results are filtered to `radius_km` and sorted nearest-first.

Errors: `422` invalid parameters · `502` provider failure · `504` provider
timeout · `503` missing API key. Zero results is a **200 with an empty
`stations` array**, not a 404.

## Nulls are deliberate

Open Charge Map is crowd-sourced and mostly sparse. Any field the provider does
not supply is returned as `null` rather than filled with a placeholder, a zero,
or a guess. `null` means "not known"; a fabricated `0` would read as "none
available", which is a different and false claim.

`status` is `null` unless OCM genuinely reports availability. OCM's
`Operational` means the site exists and works — not that a connector is free —
so it maps to `null`. **The API can never emit `"unknown"`**; that value is not
in the schema.

Typically missing from OCM: `network`, `status`, `availableConnectors`,
`pricePerKwh`, `currency`, `hours`, `isOpen24Hours`.

## Testing

```bash
pip install pytest        # dev-only, not in requirements.txt
pytest
```

All 80 tests mock HTTP with `httpx.MockTransport` and never touch the live API.

Recommended dev extras (not installed): `pytest`, `ruff`.

## Connecting from a phone

`localhost` on a phone means the phone itself, not your computer. Bind the
server with `--host 0.0.0.0`, then point the app at your machine:

| Target | `EXPO_PUBLIC_API_URL` |
|---|---|
| Android emulator | `http://10.0.2.2:8001` |
| iOS simulator | `http://localhost:8001` |
| Physical device | `http://<your-LAN-IP>:8001` |

The device must be on the same Wi-Fi, and Windows Firewall must allow inbound
port 8001. Android release builds block cleartext HTTP — production needs HTTPS.

## Git

The repository root is **not** a git repository; only `Frontend/.git` exists, so
`Backend/` is currently outside version control. `Backend/.gitignore` is in
place and lists `.env`, but **it protects nothing until `Backend/` is actually
tracked**. Initialise a repo at the root (or inside `Backend/`) before
committing. No repo was initialised automatically.

## Security

The OCM API key lives only in `Backend/.env` (gitignored) and is sent to OCM as
an `X-API-Key` **header**, never as a query parameter — httpx puts request URLs
into exception messages and logs, so a query-string key would leak there. It
never appears in an API response, an error body, or a log line.

Never put the key in the React Native app: `EXPO_PUBLIC_*` values are inlined
into the shipped bundle and are trivially extractable.

## Next step

Resolve OCM operator and reference IDs so `network` is populated — `/poi/`
returns only numeric IDs, and the 982-entry operator list needs one call to
`/v3/referencedata/` held in memory at startup.
