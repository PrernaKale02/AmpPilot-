"""Measures the voice assistant per language: recognition, answer correctness, response time."""
import csv, difflib, statistics, time, unicodedata
from pathlib import Path
import httpx

HERE = Path(__file__).parent
URL = "http://localhost:8001/api/assistant/voice"
LAT, LON = 19.186, 72.99

def norm(t):
    t = unicodedata.normalize("NFC", t.lower())
    return "".join(c for c in t if c.isalnum() or c.isspace()).split()

def similar(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()

# start a fresh simulation so battery questions have live data
httpx.post("http://localhost:8001/api/simulation/start",
           json={"durationMinutes": 15, "speedMultiplier": 1, "telemetryIntervalSeconds": 1}, timeout=10)
time.sleep(1.5)
httpx.get("http://localhost:8001/api/simulation/status", timeout=10)

rows = list(csv.DictReader(open(HERE / "queries.csv", encoding="utf-8")))
results = []
for r in rows:
    audio = (HERE / r["file"]).read_bytes()
    start = time.perf_counter()
    resp = httpx.post(URL, files={"audio": (r["file"], audio, "audio/mp4")},
                      data={"latitude": LAT, "longitude": LON}, timeout=90)
    secs = time.perf_counter() - start
    body = resp.json() if resp.status_code == 200 else {}
    transcript = body.get("transcript", "")
    reply = body.get("reply", "")
    action = body.get("action")
    recognised = similar(transcript, r["expected"]) >= 0.8
    if r["intent"] == "stations":
        correct = resp.status_code == 200 and action == "show_stations"
    else:
        correct = resp.status_code == 200 and action is None and (any(ch.isdigit() for ch in reply) or any(w in reply.lower() for w in ["percent", "%", "प्रतिशत", "टक्के"]))
    results.append({**r, "status": resp.status_code, "transcript": transcript, "reply": reply,
                    "action": action, "recognised": recognised, "correct": correct,
                    "seconds": round(secs, 2)})
    time.sleep(12)  # stay under free-tier per-minute limits
    print(f'{r["file"]}: {resp.status_code} | heard "{transcript}" | correct={correct} | {secs:.1f}s')

with open(HERE / "voice_eval_results.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    w.writeheader()
    w.writerows(results)

print("\nLanguage | Test queries | Speech recognised (%) | Answer correct (%) | Response time (s)")
for lang in ["English", "Hindi", "Marathi"]:
    g = [x for x in results if x["lang"] == lang]
    if g:
        rec = 100 * sum(x["recognised"] for x in g) / len(g)
        ok = 100 * sum(x["correct"] for x in g) / len(g)
        avg = statistics.mean(x["seconds"] for x in g)
        print(f"{lang} | {len(g)} | {rec:.0f} | {ok:.0f} | {avg:.1f}")
