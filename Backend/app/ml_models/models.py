"""Network definitions, copied unchanged from the training notebook (battery_multitask_v2, cell 5).

The backend imports this file instead of redefining the networks, so the layers
and state-dict keys always match the checkpoint. Replace it with the notebook's
own models.py when a newer notebook changes the architecture.
"""
import torch
import torch.nn as nn

def _head(i):
    return nn.Sequential(nn.Linear(i, 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1))

class BiLSTMAttention(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True,
                            bidirectional=True, dropout=0.3)
        self.attn = nn.Linear(hidden_size * 2, 1)
        self.cap_head, self.soh_head, self.fault_head = _head(hidden_size*2), _head(hidden_size*2), _head(hidden_size*2)
    def forward(self, x, return_attention=False):
        out, _ = self.lstm(x)
        w = torch.softmax(self.attn(out), dim=1)
        ctx = (out * w).sum(dim=1)
        r = (self.cap_head(ctx).squeeze(-1), self.soh_head(ctx).squeeze(-1), self.fault_head(ctx).squeeze(-1))
        return (*r, w.squeeze(-1)) if return_attention else r

class DeepLSTM(nn.Module):
    def __init__(self, input_size, hidden_size=128, num_layers=3):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.3)
        self.cap_head, self.soh_head, self.fault_head = _head(hidden_size), _head(hidden_size), _head(hidden_size)
    def forward(self, x, return_attention=False):
        _, (h, _) = self.lstm(x)
        f = h[-1]
        return self.cap_head(f).squeeze(-1), self.soh_head(f).squeeze(-1), self.fault_head(f).squeeze(-1)

class CNNLSTM(nn.Module):
    def __init__(self, input_size, cnn_channels=32, hidden_size=64, num_layers=2):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(input_size, cnn_channels, 5, padding=2), nn.BatchNorm1d(cnn_channels), nn.ReLU(),
            nn.Conv1d(cnn_channels, cnn_channels, 3, padding=1), nn.BatchNorm1d(cnn_channels), nn.ReLU())
        self.lstm = nn.LSTM(cnn_channels, hidden_size, num_layers, batch_first=True, dropout=0.3)
        self.cap_head, self.soh_head, self.fault_head = _head(hidden_size), _head(hidden_size), _head(hidden_size)
    def forward(self, x, return_attention=False):
        x = self.conv(x.permute(0, 2, 1)).permute(0, 2, 1)
        _, (h, _) = self.lstm(x)
        f = h[-1]
        return self.cap_head(f).squeeze(-1), self.soh_head(f).squeeze(-1), self.fault_head(f).squeeze(-1)

ARCHS = {"BiLSTM+Attn": BiLSTMAttention, "DeepLSTM": DeepLSTM, "CNN-LSTM": CNNLSTM}
def build_model(name, input_size):
    return ARCHS[name](input_size)