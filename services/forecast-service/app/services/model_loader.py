"""
Forecast Model Loader — Task 6.6
--------------------------------
Load model từ MLflow artifacts → inference (CPU).
Hỗ trợ: ARIMA, XGBoost, LSTM.
"""

from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path

import mlflow
import numpy as np

logger = logging.getLogger(__name__)


class ForecastModelLoader:
    """Load và cache model từ MLflow."""

    def __init__(self, tracking_uri: str | None = None):
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        self._cache: dict[str, dict] = {}

    def _get_artifact_path(self, run_id: str, artifact_path: str = "model") -> Path:
        """Download artifacts và trả về đường dẫn local."""
        local = mlflow.artifacts.download_artifacts(artifact_uri=f"runs:/{run_id}/{artifact_path}")
        return Path(local)

    def load_arima(self, run_id: str) -> object:
        """Load ARIMA model (pickle). Cần import statsmodels trước khi unpickle."""
        import statsmodels.tsa.arima.model  # noqa: F401 - required for pickle.load

        cache_key = f"arima_{run_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]["model"]

        art_path = self._get_artifact_path(run_id)
        pkl_files = list(art_path.glob("*.pkl"))
        if not pkl_files:
            raise FileNotFoundError(f"Không tìm thấy arima_model.pkl trong {art_path}")
        with open(pkl_files[0], "rb") as f:
            model = pickle.load(f)
        self._cache[cache_key] = {"model": model}
        return model

    def load_xgboost(self, run_id: str) -> tuple[object, list[str]]:
        """Load XGBoost model (json) + feature_cols."""
        import xgboost as xgb

        cache_key = f"xgboost_{run_id}"
        if cache_key in self._cache:
            c = self._cache[cache_key]
            return c["model"], c["feature_cols"]

        art_path = self._get_artifact_path(run_id)
        model_file = art_path / "xgboost_model.json"
        meta_file = art_path / "feature_cols.pkl"
        if not model_file.exists():
            raise FileNotFoundError(f"Không tìm thấy xgboost_model.json trong {art_path}")

        model = xgb.Booster()
        model.load_model(str(model_file))
        feature_cols = []
        if meta_file.exists():
            with open(meta_file, "rb") as f:
                feature_cols = pickle.load(f)
        self._cache[cache_key] = {"model": model, "feature_cols": feature_cols}
        return model, feature_cols

    def load_lstm(self, run_id: str) -> tuple[object, list[str], int]:
        """Load LSTM model (state_dict) + feature_cols + seq_len."""
        import torch

        cache_key = f"lstm_{run_id}"
        if cache_key in self._cache:
            c = self._cache[cache_key]
            return c["model"], c["feature_cols"], c["seq_len"]

        art_path = self._get_artifact_path(run_id)
        meta_file = art_path / "lstm_meta.pkl"
        state_file = art_path / "lstm_state.pt"
        if not state_file.exists():
            raise FileNotFoundError(f"Không tìm thấy lstm_state.pt trong {art_path}")

        with open(meta_file, "rb") as f:
            meta = pickle.load(f)
        feature_cols = meta.get("feature_cols", ["close"])
        params = meta.get("params", {})
        seq_len = params.get("seq_len", 21)

        # Recreate model architecture
        from app.services.lstm_model import LSTMModel

        n_features = len(feature_cols)
        hidden = params.get("hidden_size", 64)
        layers = params.get("num_layers", 2)
        model = LSTMModel(n_features, hidden, layers)
        model.load_state_dict(torch.load(state_file, map_location="cpu", weights_only=True))
        model.eval()

        self._cache[cache_key] = {"model": model, "feature_cols": feature_cols, "seq_len": seq_len}
        return model, feature_cols, seq_len

    def predict_arima(self, run_id: str, horizon: int) -> list[float]:
        """ARIMA: forecast horizon bước (model đã có history)."""
        model = self.load_arima(run_id)
        pred = model.forecast(steps=horizon)
        return pred.tolist() if hasattr(pred, "tolist") else list(pred)

    def predict_xgboost(self, run_id: str, features: list[list[float]], horizon: int) -> list[float]:
        """XGBoost: autoregressive — predict 1 step, dùng pred làm input cho step tiếp."""
        import xgboost as xgb

        model, feature_cols = self.load_xgboost(run_id)
        if not features or len(features[0]) != len(feature_cols):
            raise ValueError(f"Cần 1 row với {len(feature_cols)} features. Nhận: {len(features) or 0} rows")

        predictions = []
        current = np.array(features[0], dtype=np.float32).reshape(1, -1)
        for _ in range(horizon):
            d = xgb.DMatrix(current)
            pred = float(model.predict(d)[0])
            predictions.append(pred)
            # Autoregressive: cột 0 là close (đã thêm trong train_xgboost)
            if current.shape[1] >= 1:
                current[0, 0] = pred
        return predictions

    def predict_lstm(self, run_id: str, features: list[list[float]], horizon: int) -> list[float]:
        """LSTM: autoregressive forecast."""
        import torch

        model, feature_cols, seq_len = self.load_lstm(run_id)
        if not features or len(features) < seq_len:
            raise ValueError(f"Cần ít nhất {seq_len} rows. Nhận: {len(features) or 0}")

        n_features = len(feature_cols)
        if len(features[0]) != n_features:
            raise ValueError(f"Mỗi row cần {n_features} features. Nhận: {len(features[0])}")

        seq = np.array(features[-seq_len:], dtype=np.float32)
        predictions = []

        with torch.no_grad():
            for _ in range(horizon):
                x = torch.from_numpy(seq).unsqueeze(0)
                pred = model(x).item()
                predictions.append(pred)
                # Roll: bỏ row đầu, thêm [pred, ...] (giả sử cột 0 là close)
                new_row = seq[-1].copy()
                new_row[0] = pred  # Cột 0 là close
                seq = np.roll(seq, -1, axis=0)
                seq[-1] = new_row

        return predictions
