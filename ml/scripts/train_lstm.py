#!/usr/bin/env python3
"""
LSTM Model — Task 6.5
---------------------
Training script (PyTorch CUDA, RTX 4060) → log MLflow → so sánh với baselines.
~5-15 phút tùy data size.

Usage:
  python ml/scripts/train_lstm.py -d ml/outputs/datasets -s all
  python ml/scripts/train_lstm.py -d ml/outputs/datasets -s AAPL --seq-len 21 --epochs 50
"""

from __future__ import annotations

import argparse
import logging
import pickle
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from ml.pipelines.feature_engineering import get_feature_columns
from ml.pipelines.naive_baselines import BaselineMetrics, compute_metrics, evaluate_baselines

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_dataset_from_dir(data_dir: str | Path, symbol: str = "all") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load train/val/test từ thư mục dataset builder output."""
    data_dir = Path(data_dir)
    suffix = f"_{symbol}" if symbol != "all" else "_all"

    for ext in [".parquet", ".csv"]:
        train_path = data_dir / f"training_dataset{suffix}_train{ext}"
        val_path = data_dir / f"training_dataset{suffix}_val{ext}"
        test_path = data_dir / f"training_dataset{suffix}_test{ext}"
        if train_path.exists() and val_path.exists() and test_path.exists():
            if ext == ".parquet":
                train = pd.read_parquet(train_path)
                val = pd.read_parquet(val_path)
                test = pd.read_parquet(test_path)
            else:
                train = pd.read_csv(train_path)
                val = pd.read_csv(val_path)
                test = pd.read_csv(test_path)
            return train, val, test

    raise FileNotFoundError(f"Không tìm thấy dataset trong {data_dir} (suffix={suffix})")


def create_sequences(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "close",
    seq_len: int = 21,
) -> tuple[np.ndarray, np.ndarray]:
    """
    X: [n_samples, seq_len, n_features]
    y: [n_samples] next close
    """
    df = df.copy()
    cols = [c for c in feature_cols if c in df.columns] or [target_col]
    data = df[cols].values.astype(np.float32)
    target = df[target_col].values.astype(np.float32)

    X, y = [], []
    for i in range(seq_len, len(data)):
        X.append(data[i - seq_len:i])
        y.append(target[i])
    return np.array(X), np.array(y)


class LSTMModel(nn.Module):
    """LSTM for time series regression."""

    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :]).squeeze(-1)


def run_lstm_and_evaluate(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    feature_cols: list[str],
    seq_len: int = 21,
    hidden_size: int = 64,
    num_layers: int = 2,
    epochs: int = 50,
    batch_size: int = 32,
    lr: float = 0.001,
    use_cuda: bool = True,
) -> tuple[BaselineMetrics, object]:
    """Fit LSTM, forecast test, return metrics và model state."""
    from torch.utils.data import DataLoader, TensorDataset

    X_train, y_train = create_sequences(train, feature_cols, seq_len=seq_len)
    _, _ = create_sequences(val, feature_cols, seq_len=seq_len)  # validation not used in training loop
    X_test, y_test = create_sequences(test, feature_cols, seq_len=seq_len)

    device = torch.device("cuda" if use_cuda and torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    n_features = X_train.shape[2]
    model = LSTMModel(n_features, hidden_size, num_layers).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)

    train_ds = TensorDataset(
        torch.from_numpy(X_train),
        torch.from_numpy(y_train),
    )
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)

    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            pred = model(batch_x)
            loss = criterion(pred, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch + 1) % 10 == 0:
            logger.info("Epoch %d/%d loss=%.6f", epoch + 1, epochs, total_loss / len(train_loader))

    model.eval()
    with torch.no_grad():
        x_test_t = torch.from_numpy(X_test).to(device)
        pred = model(x_test_t).cpu().numpy()

    metrics = compute_metrics(y_test, pred)
    return metrics, model


def log_lstm_to_mlflow(
    metrics: BaselineMetrics,
    symbol: str,
    feature_cols: list[str],
    params: dict,
    experiment_name: str = "forecast_models",
    model=None,
) -> None:
    """Log LSTM run lên MLflow."""
    import mlflow
    import torch

    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=f"lstm_{symbol}"):
        mlflow.log_params({
            "model": "LSTM",
            "symbol": symbol,
            "n_features": len(feature_cols),
            **params,
        })
        mlflow.log_metrics({
            "rmse": metrics.rmse,
            "mae": metrics.mae,
            "directional_accuracy": metrics.directional_accuracy,
            "mape": metrics.mape,
        })
        mlflow.set_tag("baseline", "false")
        if model is not None:
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    pkl_path = Path(tmpdir) / "lstm_meta.pkl"
                    with open(pkl_path, "wb") as f:
                        pickle.dump({"feature_cols": feature_cols, "params": params}, f)
                    mlflow.log_artifact(str(pkl_path), "model")
                    state_path = Path(tmpdir) / "lstm_state.pt"
                    torch.save(model.state_dict(), state_path)
                    mlflow.log_artifact(str(state_path), "model")
            except Exception as e:
                logger.warning("Could not log model artifact: %s", e)
        logger.info("LSTM: RMSE=%.4f MAE=%.4f DA=%.1f%%", metrics.rmse, metrics.mae, metrics.directional_accuracy)


def compare_with_naive(metrics: BaselineMetrics, naive_metrics: dict) -> None:
    """In so sánh LSTM vs naive baselines."""
    logger.info("--- So sánh với Naive Baselines ---")
    for name, m in naive_metrics.items():
        rmse_ok = "✓" if metrics.rmse < m.rmse else "✗"
        da_ok = "✓" if metrics.directional_accuracy > m.directional_accuracy else "✗"
        logger.info("  %s: LSTM RMSE %s (%.4f vs %.4f), DA %s (%.1f%% vs %.1f%%)",
                    name, rmse_ok, metrics.rmse, m.rmse, da_ok,
                    metrics.directional_accuracy, m.directional_accuracy)


def main() -> int:
    parser = argparse.ArgumentParser(description="LSTM Model (PyTorch CUDA)")
    parser.add_argument("-d", "--data-dir", help="Thư mục dataset (train/val/test)")
    parser.add_argument("-s", "--symbol", default="all")
    parser.add_argument("--seq-len", type=int, default=21, help="Lookback window")
    parser.add_argument("--hidden-size", type=int, default=64)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--no-cuda", action="store_true", help="Dùng CPU thay vì GPU")
    parser.add_argument("--no-mlflow", action="store_true")
    parser.add_argument("--no-model-artifact", action="store_true")
    parser.add_argument("--experiment", default="forecast_models")
    parser.add_argument("--no-compare", action="store_true")
    args = parser.parse_args()

    if not args.data_dir:
        logger.error("Cần -d/--data-dir (ví dụ: ml/outputs/datasets)")
        return 1

    train, val, test = load_dataset_from_dir(args.data_dir, args.symbol)

    if "close" not in train.columns:
        logger.error("Dataset thiếu cột 'close'")
        return 1

    feature_cols = get_feature_columns(train)
    if not feature_cols:
        feature_cols = ["close"]
    if "close" not in feature_cols:
        feature_cols = ["close"] + feature_cols
    logger.info("Features: %s", feature_cols[:10] if len(feature_cols) > 10 else feature_cols)

    metrics, model = run_lstm_and_evaluate(
        train, val, test,
        feature_cols=feature_cols,
        seq_len=args.seq_len,
        hidden_size=args.hidden_size,
        num_layers=args.num_layers,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        use_cuda=not args.no_cuda,
    )

    logger.info("LSTM: RMSE=%.4f MAE=%.4f DA=%.1f%% MAPE=%.2f%%",
                metrics.rmse, metrics.mae, metrics.directional_accuracy, metrics.mape)

    if not args.no_compare:
        naive_metrics = evaluate_baselines(train, val, test)
        compare_with_naive(metrics, naive_metrics)

    if not args.no_mlflow:
        try:
            model_to_log = None if args.no_model_artifact else model
            log_lstm_to_mlflow(
                metrics, args.symbol, feature_cols,
                params={
                    "seq_len": args.seq_len,
                    "hidden_size": args.hidden_size,
                    "num_layers": args.num_layers,
                    "epochs": args.epochs,
                },
                experiment_name=args.experiment,
                model=model_to_log,
            )
        except Exception as e:
            logger.warning("MLflow log failed: %s", e)

    return 0


if __name__ == "__main__":
    sys.exit(main())
