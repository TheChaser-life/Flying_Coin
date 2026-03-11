"""Test MLflow connection to Minikube tracking server."""
import os
import subprocess
import sys

def _print(msg: str) -> None:
    print(msg, flush=True)

def get_mlflow_url():
    """Get MLflow URL. Prefer env var; minikube service --url blocks on Windows Docker driver."""
    # 1. Env var (user runs tunnel in another terminal first)
    url = os.environ.get("MLFLOW_TRACKING_URI", "").strip()
    if url and (url.startswith("http://") or url.startswith("https://")):
        return url
    # 2. Try subprocess with short timeout (minikube may print URL then block)
    _print("Getting MLflow URL from minikube (timeout 5s)...")
    try:
        result = subprocess.run(
            "minikube service mlflow-tracking-svc -n mlops --url",
            capture_output=True,
            text=True,
            timeout=5,
            shell=True,
        )
        out = (result.stdout or "").strip()
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("http://") or line.startswith("https://"):
                return line
    except subprocess.TimeoutExpired as e:
        # May have URL in output before timeout (tunnel blocks)
        out = (e.output or "").strip() if hasattr(e, "output") else ""
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("http://") or line.startswith("https://"):
                return line
    except (FileNotFoundError, OSError):
        pass
    return None

def main():
    url = get_mlflow_url()
    if not url:
        _print("ERROR: Could not get MLflow URL.")
        _print("")
        _print("On Windows (Docker driver), run in ANOTHER terminal and keep it open:")
        _print("  minikube service mlflow-tracking-svc -n mlops --url")
        _print("")
        _print("Then copy the URL (e.g. http://127.0.0.1:60905) and run:")
        _print('  $env:MLFLOW_TRACKING_URI = "http://127.0.0.1:60905"')
        _print("  python ml/scripts/test_mlflow_connection.py")
        return 1
    _print(f"MLFLOW_TRACKING_URI={url}")
    os.environ["MLFLOW_TRACKING_URI"] = url

    import mlflow

    _print("Connecting to MLflow...")
    mlflow.set_tracking_uri(url)
    mlflow.set_experiment("connection_test")
    with mlflow.start_run(run_name="test_run"):
        mlflow.log_param("test_param", 1)
        mlflow.log_metric("test_metric", 0.5)
    _print("OK: MLflow connection successful")
    return 0

if __name__ == "__main__":
    sys.exit(main())
