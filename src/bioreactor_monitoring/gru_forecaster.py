"""Standalone GRU penicillin forecaster for IndPenSim.

This is a self-contained modelling component. It does not depend on the
dashboard, monitoring, golden-batch logic, or control simulation. It forecasts
the dense simulated penicillin trajectory ``p_true_g_l`` (Mode 1) as the primary
benchmark, optionally against sparse offline assays (Mode 2, see the script).

Architecture notes:

- ``tanh`` is the GRU candidate activation; PyTorch exposes it internally and
  does not take a candidate-activation argument, so none is added here.
- ``dropout`` is applied by PyTorch between recurrent layers only when
  ``num_layers > 1``. A single-layer GRU therefore gets no inter-layer dropout
  unless an explicit output dropout argument is added; this model only adds an
  output layer, so dropout as configured applies between layers.
- Adamax optimiser, MSE loss, gradient clipping, and early stopping on a
  grouped validation split are used for a paper-inspired setup.
- All sequence windows are built batch-locally (see ``sequence.build_windows``),
  so no window crosses a batch boundary and no time-ordering leak occurs.

All hyperparameters are project-selected defaults until the 2026 paper methods
are verified. They are not claimed as published values.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn


class GRUForecaster(nn.Module):
    """A configurable GRU regressor with a linear output head.

    Input shape ``(batch, lookback, n_features)``; output is one scalar
    penicillin value per sample (direct horizon forecast after the window).
    """

    def __init__(self, n_features: int, hidden_size: int = 64,
                 num_layers: int = 1, dropout: float = 0.0):
        super().__init__()
        self.gru = nn.GRU(n_features, hidden_size, num_layers=num_layers,
                          batch_first=True, dropout=dropout)
        self.head = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.gru(x)
        return self.head(out[:, -1, :]).squeeze(-1)


def _arrays_to_tensor(x: np.ndarray) -> torch.Tensor:
    return torch.as_tensor(x, dtype=torch.float32)


def train_forecaster(X_train: np.ndarray, y_train: np.ndarray,
                     X_val: np.ndarray, y_val: np.ndarray,
                     hidden_size: int = 64, num_layers: int = 1,
                     dropout: float = 0.0, batch_size: int = 64,
                     epochs: int = 50, lr: float = 1e-3,
                     weight_decay: float = 1e-5,
                     grad_clip: float = 1.0, patience: int = 8,
                     seed: int = 0, device: str | None = None) -> tuple[nn.Module, dict]:
    """Train with Adamax and early stopping on validation loss.

    Returns ``(model, history)`` where ``history`` holds per-epoch train/val
    loss and the best validation epoch. The model is the best-validation
    checkpoint (weights restored). Loops over the CPU unless a CUDA device is
    explicitly requested and available.
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(seed)
    np.random.seed(seed)
    if device.startswith("cuda"):
        torch.cuda.manual_seed_all(seed)

    n_features = X_train.shape[2]
    model = GRUForecaster(n_features, hidden_size=hidden_size,
                          num_layers=num_layers, dropout=dropout).to(device)
    optimizer = torch.optim.Adamax(model.parameters(), lr=lr,
                                   weight_decay=weight_decay)
    loss_fn = nn.MSELoss()

    Xt = torch.as_tensor(X_train, dtype=torch.float32)
    yt = torch.as_tensor(y_train, dtype=torch.float32)
    Xv = torch.as_tensor(X_val, dtype=torch.float32)
    yv = torch.as_tensor(y_val, dtype=torch.float32)

    n = len(Xt)
    best_val = float("inf")
    best_state = None
    best_epoch = -1
    early = 0
    history: dict[str, list] = {"train_loss": [], "val_loss": [], "epoch": []}

    for epoch in range(epochs):
        model.train()
        order = torch.randperm(n)
        running = 0.0
        count = 0
        for i in range(0, n, batch_size):
            idx = order[i:i + batch_size]
            xb = Xt[idx].to(device)
            yb = yt[idx].to(device)
            optimizer.zero_grad()
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()
            running += float(loss.item()) * len(idx)
            count += len(idx)
        train_l = running / count

        model.eval()
        with torch.no_grad():
            val_l = float(loss_fn(model(Xv.to(device)), yv.to(device)).item())

        history["epoch"].append(epoch)
        history["train_loss"].append(train_l)
        history["val_loss"].append(val_l)

        if val_l < best_val - 1e-8:
            best_val = val_l
            best_epoch = epoch
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            early = 0
        else:
            early += 1
            if early >= patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    return model, {"best_epoch": best_epoch, "best_val_loss": best_val,
                   "history": history}


def predict(model: nn.Module, X: np.ndarray, device: str | None = None) -> np.ndarray:
    """Forecast on windows ``X`` of shape ``(samples, lookback, n_features)``."""
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    model.eval()
    Xt = torch.as_tensor(X, dtype=torch.float32).to(device)
    with torch.no_grad():
        out = model(Xt)
    return out.detach().cpu().numpy()