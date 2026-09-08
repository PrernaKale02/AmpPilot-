"""Battery health model: loads the trained network once at import time
and exposes a single predict() function.

Normalization constants below come from training the multi-task
BiLSTM+Attention model (final_model_no_mfg) on all 3 EVBattery
manufacturer datasets combined. If the model is retrained, re-run the
training notebook's Step 3 and update these values:
    print("SENSOR_MEAN =", mean.tolist())
    print("SENSOR_STD =", std.tolist())
    print("CAPACITY_MEAN =", capacity_mean)
    print("CAPACITY_STD =", capacity_std)
    print("SOH_MEAN =", soh_mean)
    print("SOH_STD =", soh_std)
"""

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

_MODEL_PATH = Path(__file__).resolve().parent.parent / "ml_models" / "final_model_no_mfg.pt"

# Normalization constants from the trained model (final_model_no_mfg, all 3 manufacturers).
_SENSOR_MEAN = np.array(
    [3.94499135017395, -9.583528518676758, 70.92549896240234, 3.952288866043091,
     3.902657985687256, 29.018632888793945, 25.83769989013672, 634.0243530273438],
    dtype=np.float32,
)
_SENSOR_STD = np.array(
    [0.2569948434829712, 7.840857028961182, 25.75346565246582, 0.2583308815956116,
     0.25116822123527527, 8.011555671691895, 8.574789047241211, 369.41412353515625],
    dtype=np.float32,
)
_CAPACITY_MEAN = 41.01803
_CAPACITY_STD = 1.9790907
_SOH_MEAN = 95.37797
_SOH_STD = 3.4451575


class _MultiTaskBiLSTMAttention(nn.Module):
    def __init__(self, input_size: int = 8, hidden_size: int = 64, num_layers: int = 2) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layers,
            batch_first=True, bidirectional=True, dropout=0.3,
        )
        self.attn = nn.Linear(hidden_size * 2, 1)
        self.capacity_head = nn.Sequential(
            nn.Linear(hidden_size * 2, 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1)
        )
        self.soh_head = nn.Sequential(
            nn.Linear(hidden_size * 2, 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1)
        )
        self.fault_head = nn.Sequential(
            nn.Linear(hidden_size * 2, 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1)
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        out, _ = self.lstm(x)
        attn_weights = torch.softmax(self.attn(out), dim=1)
        context = (out * attn_weights).sum(dim=1)
        capacity = self.capacity_head(context).squeeze(-1)
        soh = self.soh_head(context).squeeze(-1)
        fault_logit = self.fault_head(context).squeeze(-1)
        return capacity, soh, fault_logit


_model = _MultiTaskBiLSTMAttention(input_size=8)
_model.load_state_dict(torch.load(_MODEL_PATH, map_location="cpu"))
_model.eval()


def predict(readings: list[list[float]]) -> dict:
    """Runs one charging session through the model."""
    arr = np.asarray(readings, dtype=np.float32)
    arr_norm = (arr - _SENSOR_MEAN) / _SENSOR_STD
    x = torch.tensor(arr_norm[None, :, :], dtype=torch.float32)

    with torch.no_grad():
        cap_pred, soh_pred, fault_logit = _model(x)

    capacity = cap_pred.item() * _CAPACITY_STD + _CAPACITY_MEAN
    soh = soh_pred.item() * _SOH_STD + _SOH_MEAN
    fault_prob = torch.sigmoid(fault_logit).item()

    return {
        "capacity": round(capacity, 2),
        "soh_percent": round(soh, 2),
        "fault_probability": round(fault_prob, 3),
        "is_faulty": fault_prob > 0.5,
    }