"""Checks every battery endpoint of a RUNNING backend and prints PASS / FAIL.

    python check_endpoints.py                       # http://localhost:8001
    python check_endpoints.py http://192.168.1.5:8001

Standard library only. Run it from the Backend folder (it reads the demo JSON
files in app/ml_models/demo/ to build real requests).

Add --skip-sim to leave the simulation out. The simulation check starts a replay
at 30x speed (about 45 seconds) and then stops it, so it resets any simulation
that is currently running. Everything else changes nothing.
"""

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
SKIP_SIM = "--skip-sim" in sys.argv
BASE = (ARGS[0] if ARGS else "http://localhost:8001").rstrip("/")
DEMO_DIR = Path(__file__).resolve().parent / "app" / "ml_models" / "demo"
results = []


def call(method, path, body=None, timeout=60):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as err:
        try:
            return err.code, json.loads(err.read() or b"null")
        except json.JSONDecodeError:
            return err.code, None
    except OSError as err:
        return None, str(err)


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ->  {detail}" if detail else ""))


def code_of(body):
    detail = body.get("detail") if isinstance(body, dict) else None
    return detail.get("code") if isinstance(detail, dict) else None


# ---- server up ---------------------------------------------------------------
status, body = call("GET", "/health")
check("server is reachable (GET /health)", status == 200, f"{status} {body}")
if status != 200:
    print("\nCannot reach the backend. Start it first, or fix the address.")
    sys.exit(1)

# ---- model ---------------------------------------------------------------------
status, info = call("GET", "/battery/model-info")
loaded = status == 200 and info.get("loaded") is True
check("model loaded (GET /battery/model-info)", loaded,
      f"model={info.get('model_name')}, per_dataset={info.get('per_dataset_normalisation')}, "
      f"detail={info.get('detail')}" if isinstance(info, dict) else str(info))
if not loaded:
    print("      -> model endpoints below will answer 503 until final_model.pt is in app/ml_models/\n"
          "         and MODEL_WEIGHTS_FILE=final_model.pt is set in .env, then restart.")

status, sessions = call("GET", "/battery/demo-sessions")
ids = [s["id"] for s in sessions] if status == 200 else []
check("demo sessions listed", status == 200 and "sample_session" in ids, f"{len(ids)} sessions: {ids}")

# ---- predictions on every demo session --------------------------------------------
print()
for sid in ids:
    status, out = call("GET", f"/battery/demo-sessions/{sid}")
    if status == 200:
        label = {0: "healthy", 1: "faulty", None: "unlabelled"}[out["true_label"]]
        check(f"predict {sid}", 0 <= out["soh_percent"] <= 100 and 0 <= out["fault_probability"] <= 1,
              f"label={label}, SoH={out['soh_percent']}, capacity={out['capacity']}, "
              f"fault risk={out['fault_probability']}, scaling={out['normalisation']}")
    else:
        check(f"predict {sid}", False, f"HTTP {status} {code_of(out) or out}")
print()

# ---- POST predict / explain with a real file ----------------------------------------
payload_file = DEMO_DIR / "faulty_3_515.json"
if not payload_file.exists():
    candidates = sorted(DEMO_DIR.glob("*.json"))
    payload_file = candidates[0] if candidates else None
if payload_file:
    payload = json.loads(payload_file.read_text(encoding="utf-8"))
    status, out = call("POST", "/battery/predict", payload)
    check(f"POST /battery/predict ({payload_file.name})", status == 200,
          f"HTTP {status}" + (f", SoH={out['soh_percent']}" if status == 200 else f" {code_of(out)}"))
    status, out = call("POST", "/battery/explain", payload)
    ok = status == 200 and len(out["channel_sensitivity"]) == 8
    check(f"POST /battery/explain ({payload_file.name})", ok,
          (f"top attention rows={out['top_attention_rows']}, most sensitive="
           f"{max(out['channel_sensitivity'], key=out['channel_sensitivity'].get)}") if ok
          else f"HTTP {status} {code_of(out)}")
else:
    check("POST /battery/predict", False, "no demo files in app/ml_models/demo/")

# ---- input validation (works even without the model) -------------------------------------
row = [4.1, -6.4, 92.2, 4.11, 4.09, 12.0, 10.0, 0.0]
check("rejects 127 rows (422)", call("POST", "/battery/predict", {"readings": [row] * 127})[0] == 422)
check("rejects 7 columns (422)", call("POST", "/battery/predict", {"readings": [row[:7]] * 128})[0] == 422)
check("rejects dataset 4 (422)", call("POST", "/battery/predict", {"readings": [row] * 128, "dataset": 4})[0] == 422)
status, out = call("GET", "/battery/demo-sessions/does_not_exist")
check("unknown demo session is 404", status == 404 and code_of(out) == "DEMO_SESSION_NOT_FOUND", f"HTTP {status}")

# ---- remaining useful life (does not need the model) ---------------------------------------
status, out = call("GET", "/battery/rul/1_105")
check("GET /battery/rul/1_105 (precomputed)", status == 200 and out["source"] == "precomputed",
      f"RUL={out.get('estimated_rul_km')} km, capped={out.get('capped')}" if status == 200 else f"HTTP {status}")
status, out = call("GET", "/battery/rul/9_999")
check("unknown car RUL is 404", status == 404 and code_of(out) == "RUL_NOT_FOUND", f"HTTP {status}")
history = [{"mileage_km": 10_000 * i, "soh_percent": 100 - 0.1 * 10 * i} for i in range(10)]
status, out = call("POST", "/battery/rul", {"history": history})
check("POST /battery/rul (fit)", status == 200 and abs(out["estimated_rul_km"] - 110_000) < 5,
      f"RUL={out.get('estimated_rul_km')} km (expected about 110000)" if status == 200 else f"HTTP {status}")
check("RUL rejects 4 points (422)", call("POST", "/battery/rul", {"history": history[:4]})[0] == 422)

# ---- simulation replay (recorded session + explanation) ------------------------------------
if not SKIP_SIM:
    print()
    replay_id = "faulty_3_515" if "faulty_3_515" in ids else (ids[1] if len(ids) > 1 else "sample_session")
    start = {"durationMinutes": 1, "speedMultiplier": 30, "telemetryIntervalSeconds": 1.0, "sessionId": replay_id}
    status, out = call("POST", "/api/simulation/start", start)
    check(f"simulation replay starts ({replay_id})", status == 200 and out.get("replay") is not None,
          f"HTTP {status}, total {out['replay']['totalSimulatedSeconds']:.0f} s of recorded data" if status == 200 else f"HTTP {status} {code_of(out)}")
    if status == 200:
        first = out["latestTelemetry"]
        deadline = time.time() + 90
        while time.time() < deadline and out["status"] != "completed":
            time.sleep(3)
            status, out = call("GET", "/api/simulation/status")
        done = out.get("status") == "completed"
        check("simulation replay completes", done, f"progress={out['replay']['progress']:.0%}" if done else "timed out")
        if done:
            last = out["latestTelemetry"]
            recorded_path = DEMO_DIR / f"{replay_id}.json"
            if not recorded_path.exists():
                recorded_path = DEMO_DIR.parent / f"{replay_id}.json"
            final_row = json.loads(recorded_path.read_text(encoding="utf-8"))["readings"][-1]
            matches = (abs(last["voltageV"] - final_row[0]) < 0.002
                       and abs(last["stateOfChargePercent"] - final_row[2]) < 0.02)
            check("replay ends on the recorded session's last row (cell voltage, real SOC)", matches,
                  f"replay: {last['voltageV']} V, SOC {last['stateOfChargePercent']} | file: "
                  f"{final_row[0]:.3f} V, SOC {final_row[2]:.2f}")
            analysis = out.get("analysis") or {}
            ok = analysis.get("available") is True and len(analysis.get("reasons", [])) >= 1
            check("model assessment and explanation after the replay", ok,
                  (f"{analysis['headline']} (risk {analysis['faultProbability']:.2f}), reason: {analysis['reasons'][0]}")
                  if ok else f"{analysis.get('headline')} - {analysis.get('note')}")
    status, out = call("POST", "/api/simulation/start", {**start, "sessionId": "no_such_session"})
    check("replay of an unknown session is 404", status == 404 and code_of(out) == "DEMO_SESSION_NOT_FOUND", f"HTTP {status}")
    call("POST", "/api/simulation/stop")

print(f"\n{sum(results)} of {len(results)} checks passed.")
sys.exit(0 if all(results) else 1)