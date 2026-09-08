import json, random

def fake_row(i):
    return [
        round(random.uniform(3.5, 4.2), 3),
        round(random.uniform(-40, 0), 2),
        round(random.uniform(20, 100), 1),
        round(random.uniform(3.5, 4.2), 3),
        round(random.uniform(3.5, 4.2), 3),
        round(random.uniform(15, 35), 1),
        round(random.uniform(15, 35), 1),
        i * 5.0
    ]

payload = {"readings": [fake_row(i) for i in range(128)]}

with open("sample_payload.json", "w") as f:
    json.dump(payload, f)

print("Saved to sample_payload.json")