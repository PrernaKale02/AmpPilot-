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
└── tests/                       no network access; no torch or model weights needed
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

| Param       | Type  | Required | Default | Validation |
| ----------- | ----- | -------- | ------- | ---------- |
| `latitude`  | float | yes      | —       | −90 … 90   |
| `longitude` | float | yes      | —       | −180 … 180 |
| `radius_km` | float | no       | 10      | > 0, ≤ 50  |

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

## Battery health model

| Endpoint                          | Purpose                                                                                                                                                                                                                                                               |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `POST /battery/predict`           | Body `{"readings": [[8 numbers] x 128], "dataset": 1\|2\|3 (optional), "include_attention": false}`. Returns `capacity`, `soh_percent`, `fault_probability` (experimental risk score, no yes/no), `model_name`, `normalisation` (+ attention weights when requested). |
| `POST /battery/explain`           | Same body. Returns the fault score, per-sensor `channel_sensitivity` and the 5 `top_attention_rows`, for that one session.                                                                                                                                            |
| `POST /battery/rul`               | Body `{"history": [{"mileage_km", "soh_percent"} x >=5]}`. Straight-line State-of-Health trend to the 80% threshold. Not from the neural network.                                                                                                                     |
| `GET /battery/rul/{car_id}`       | The notebook's precomputed estimate for a car (`1_105`, from `rul_estimates.csv`). 404 when the car has none.                                                                                                                                                         |
| `GET /battery/demo-sessions`      | Demo sessions: the bundled sample plus the healthy/faulty cars in `app/ml_models/demo/*.json` (made by `make_demo_sessions_colab.py`).                                                                                                                                |
| `GET /battery/demo-sessions/{id}` | Predicts one demo session. `true_label` in the response is the dataset's label, not a model output.                                                                                                                                                                   |
| `GET /battery/demo`               | Shortcut for the bundled sample session.                                                                                                                                                                                                                              |
| `GET /battery/model-info`         | Which model is deployed and whether it loaded. Never errors.                                                                                                                                                                                                          |

The model weights (`app/ml_models/*.pt`) are **not in git**. Without them the API
still starts; the model endpoints answer `503 MODEL_UNAVAILABLE`. To deploy a
newly trained model see `app/ml_models/README.md`.

- `fault_probability` is experimental: fault labels are vehicle-level and
  single-session fault detection is weak, so the API never returns a yes/no.
- `rul` values above `RUL_CAP_KM` (default 500,000 km) are cut to the cap and
  flagged `"capped": true`.
- Send real sensor sessions only. The charging and simulation endpoints produce
  data the model was not trained on; do not feed their readings to `/battery/*`.

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

All tests mock HTTP with `httpx.MockTransport` (or replace the ML model) and never touch the live API or need the model weights.

Recommended dev extras (not installed): `pytest`, `ruff`.

## Connecting from a phone

`localhost` on a phone means the phone itself, not your computer. Bind the
server with `--host 0.0.0.0`, then point the app at your machine:

| Target           | `EXPO_PUBLIC_API_URL`       |
| ---------------- | --------------------------- |
| Android emulator | `http://10.0.2.2:8001`      |
| iOS simulator    | `http://localhost:8001`     |
| Physical device  | `http://<your-LAN-IP>:8001` |

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
