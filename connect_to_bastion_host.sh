#!/bin/bash
# Script để kết nối tới GKE Bastion Host và thiết lập Hybrid ML Tunnel (Task 6.5)
# --------------------------------------------------------------------------

# 1. Tự động lấy IP External của Bastion Service
BASTION_IP=$(kubectl get svc -n mlops ssh-bastion-svc -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

if [ -z "$BASTION_IP" ]; then
    echo "❌ Lỗi: Không tìm thấy IP External của ssh-bastion-svc."
    echo "Hãy đảm bảo bạn đã kết nối tới cụm GKE (gcloud container clusters get-credentials...)"
    exit 1
fi

echo "🚀 Đang chuẩn bị kết nối tới Bastion tại địa chỉ: $BASTION_IP"
echo "----------------------------------------------------------------"
echo "Các cổng được ánh xạ (Tunneling):"
echo "  - Cổng 8765 (R): Airflow (GKE) -> Máy bạn  (Để Airflow gọi về training)"
echo "  - Cổng 5000 (L): Máy bạn  -> MLflow (GKE) (Để đẩy model artifact lên cluster)"
echo "----------------------------------------------------------------"

# 2. Thực hiện kết nối SSH
# -i: Sử dụng file key bastion_ed25519
# -p 2222: Cổng SSH của container bastion
# -o StrictHostKeyChecking=no: Bỏ qua xác thực host key lần đầu
ssh -i bastion_ed25519 -p 2222 \
    -o StrictHostKeyChecking=no \
    -R 8765:localhost:8765 \
    -L 5000:mlflow-tracking-svc.mlops.svc.cluster.local:80 \
    mldev@$BASTION_IP

echo "💡 Lưu ý: Hãy giữ terminal này luôn mở. Sau đó mở một terminal mới và chạy 'python ml/scripts/trigger_server.py'."
