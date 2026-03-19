# Script PowerShell để kết nối tới GKE Bastion Host và thiết lập Hybrid ML Tunnel
# --------------------------------------------------------------------------

# 1. Tự động lấy IP External của Bastion Service (Cần cài đặt Google Cloud SDK / kubectl)
try {
    $BASTION_IP = kubectl get svc -n mlops ssh-bastion-svc -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
} catch {
    Write-Error "❌ Lỗi: Lệnh 'kubectl' không khả dụng hoặc chưa được cấu hình."
    exit 1
}

if (-not $BASTION_IP) {
    Write-Host "❌ Lỗi: Không tìm thấy IP External của ssh-bastion-svc." -ForegroundColor Red
    Write-Host "Hãy đảm bảo bạn đã kết nối tới cụm GKE (gcloud container clusters get-credentials ...)" -ForegroundColor Yellow
    exit 1
}
$USER_NAME = "mldev"
$SSH_KEY = "bastion_ed25519"
$SSH_PORT = "2222"

Write-Host "Connect to bastion host at: $BASTION_IP" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------"
Write-Host "Tunneling ports:"
Write-Host "  - Port 8765 (R): Airflow (GKE) -> Local Computer  (for training)"
Write-Host "  - Port 5000 (L): Local Computer -> MLflow (GKE) (for pushing model artifact to cluster)"
Write-Host "----------------------------------------------------------------"

# 2. Thực hiện kết nối SSH qua PowerShell
# -o StrictHostKeyChecking=no: Bỏ qua xác thực host key lần đầu
# -R/L: Thiết lập tunnel
ssh -i $SSH_KEY -p $SSH_PORT `
    -o "StrictHostKeyChecking=no" `
    -R 0.0.0.0:8765:127.0.0.1:8765 `
    -L 127.0.0.1:5000:mlflow-tracking-svc.mlops.svc.cluster.local:80 `
    "$USER_NAME@$BASTION_IP"

Write-Host "💡 Note: Keep this terminal open. Then open a new terminal and run 'python ml/scripts/trigger_server.py'." -ForegroundColor Yellow
