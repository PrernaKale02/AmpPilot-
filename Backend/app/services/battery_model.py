"""Battery health model: loads the trained network once at import time
and exposes a single predict() function.

IMPORTANT: The normalization constants below are PLACEHOLDERS and will
give numerically wrong (though not erroring) predictions until replaced
with the real values printed from the training notebook's Step 3:
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

# ==================== PLACEHOLDER — REPLACE AFTER RE-RUNNING TRAINING ====================
_SENSOR_MEAN = np.array([3.9, -25.0, 68.0, 3.9, 3.85, 20.0, 16.0, 635.0], dtype=np.float32)
_SENSOR_STD = np.array([0.15, 30.0, 15.0, 0.15, 0.15, 8.0, 7.0, 370.0], dtype=np.float32)
_CAPACITY_MEAN = 40.0
_CAPACITY_STD = 5.0
_SOH_MEAN = 85.0
_SOH_STD = 10.0
# ===========================================================================================


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