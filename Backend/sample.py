import numpy as np
import json

X = np.load("X.npy")   # adjust path if it's not in the current folder
print("X shape:", X.shape)

sample = X[100]  # pick any index, e.g. session #100
payload = {"readings": sample.tolist()}

# save it to a file so you can easily copy-paste
with open("test_payload.json", "w") as f:
    json.dump(payload, f)

print(json.dumps(payload)[:300], "...")  # preview