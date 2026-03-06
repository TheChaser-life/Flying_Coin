# 📁 Cấu Trúc Thư Mục Dự Án (Project Structure)

```
market-forecasting/
│
├── 📁 services/
│   ├── 📁 api-gateway/                    # API Gateway
│   │   ├── nginx.conf / kong.yml
│   │   └── Dockerfile
│   │
│   ├── 📁 auth-service/                   # Auth Service
│   │   ├── 📁 app/
│   │   │   ├── api/                       # Login, Register endpoints
│   │   │   ├── core/                      # Config, Security, JWT
│   │   │   ├── models/                    # User model
│   │   │   ├── schemas/                   # Pydantic schemas
│   │   │   ├── services/                  # Auth logic
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── 📁 market-data-service/            # Market Data Service
│   │   ├── 📁 app/
│   │   │   ├── api/                       # Market data endpoints
│   │   │   ├── collectors/                # Yahoo, Binance collectors
│   │   │   ├── models/                    # MarketData, Symbol models
│   │   │   ├── services/                  # Collection & processing
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── 📁 forecast-service/               # Forecast Service
│   │   ├── 📁 app/
│   │   │   ├── api/                       # Prediction endpoints
│   │   │   ├── ml/
│   │   │   │   ├── models/                # LSTM, XGBoost, ARIMA (serving only)
│   │   │   │   ├── inference/             # Load model → prediction
│   │   │   │   └── pipelines/             # Feature engineering
│   │   │   ├── services/                  # Forecasting logic
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── 📁 sentiment-service/              # Sentiment Service
│   │   ├── 📁 app/
│   │   │   ├── api/                       # Sentiment endpoints
│   │   │   ├── collectors/                # News, Twitter collectors
│   │   │   ├── nlp/                       # FinBERT, VADER
│   │   │   ├── services/                  # Sentiment logic
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── 📁 portfolio-service/              # Portfolio Service
│   │   ├── 📁 app/
│   │   │   ├── api/                       # Portfolio endpoints
│   │   │   ├── optimizers/                # Markowitz, Risk Parity
│   │   │   ├── backtesting/               # Backtesting engine
│   │   │   ├── services/                  # Portfolio logic
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── 📁 websocket-service/              # WebSocket Service (Go)
│   │   ├── cmd/
│   │   │   └── main.go                    # Entrypoint
│   │   ├── internal/
│   │   │   ├── handler/                   # WebSocket handlers
│   │   │   ├── hub/                       # Connection hub (fan-out)
│   │   │   ├── auth/                      # JWT verification middleware
│   │   │   └── subscriber/               # Redis Pub/Sub subscriber
│   │   ├── go.mod
│   │   ├── go.sum
│   │   └── Dockerfile
│   │
│   └── 📁 notification-service/           # Notification Service (Go)
│       ├── cmd/
│       │   └── main.go                    # Entrypoint
│       ├── internal/
│       │   ├── handler/                   # API handlers
│       │   ├── provider/                  # Email, Push providers
│       │   ├── service/                   # Alert logic
│       │   └── subscriber/               # Redis subscriber
│       ├── go.mod
│       ├── go.sum
│       └── Dockerfile
│
├── 📁 frontend/                           # Frontend Dashboard
│   ├── 📁 src/
│   │   ├── components/
│   │   │   ├── charts/                    # Candlestick, Line, Pie
│   │   │   ├── dashboard/                 # Dashboard widgets
│   │   │   ├── portfolio/                 # Portfolio views
│   │   │   ├── auth/                      # Login, Register forms
│   │   │   └── common/                    # Shared components
│   │   ├── pages/                         # Route pages
│   │   ├── hooks/                         # useWebSocket, useAuth
│   │   ├── services/                      # API service layer
│   │   ├── store/                         # Zustand stores
│   │   ├── utils/
│   │   └── styles/
│   ├── package.json
│   ├── Dockerfile
│   └── next.config.js
│
├── 📁 shared/                             # Shared giữa services
│   ├── schemas/                           # Shared Pydantic schemas
│   ├── utils/                             # Common utilities
│   └── constants/                         # Shared constants
│
├── 📁 data/                               # Data storage (dev)
│   ├── raw/
│   ├── processed/
│   └── models/
│
├── 📁 ml/                                # ML Training (chạy local, ngoài K8s)
│   ├── scripts/
│   │   ├── train_arima.py                # ARIMA training → MLflow
│   │   ├── train_xgboost.py              # XGBoost GPU training → MLflow
│   │   ├── train_lstm.py                 # LSTM PyTorch CUDA → MLflow
│   │   └── run_finbert.py                # FinBERT inference → batch scores
│   ├── pipelines/
│   │   ├── preprocessing.py              # EDA, missing values, outlier, normalization
│   │   ├── dataset_builder.py            # JOIN multi-source data → training dataset
│   │   ├── feature_engineering.py        # SMA, RSI, MACD, Bollinger Bands
│   │   └── naive_baselines.py            # Naive forecast + MA benchmark
│   ├── configs/                           # Hyperparameter configs
│   └── requirements-training.txt          # PyTorch CUDA, Optuna, etc.
│
├── 📁 notebooks/                          # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_training.ipynb
│   └── 04_sentiment_analysis.ipynb
│
├── 📁 terraform/                           # Infrastructure as Code
│   ├── 📁 modules/
│   │   ├── networking/                    # VPC, Subnets, NAT, Firewall
│   │   ├── kubernetes/                    # GKE cluster, Node Pool, SA
│   │   ├── storage/                       # GCS buckets (MLflow artifacts)
│   │   └── registry/                      # Artifact Registry (Docker images)
│   ├── main.tf                            # Root module
│   ├── variables.tf                       # Input variables
│   └── terraform.tfvars                   # Giá trị biến
│
├── 📁 .github/                            # CI/CD Pipelines
│   └── 📁 workflows/
│       ├── ci.yml                         # Lint → Test → Build → Push image
│       ├── cd-dev.yml                     # Auto-deploy to dev on merge
│       ├── cd-staging.yml                 # Deploy to staging (manual approval)
│       ├── cd-production.yml              # Deploy to prod (Blue-Green/Canary)
│       └── ml-pipeline.yml                # MLOps: train → validate → register
│
├── 📁 helm-values/                        # Helm values cho từng môi trường
│   ├── postgresql-local.yaml              # Minikube: ít RAM, storage nhỏ
│   ├── postgresql-cloud.yaml              # GKE: SSD, RAM nhiều hơn
│   ├── redis-local.yaml
│   ├── redis-cloud.yaml
│   ├── rabbitmq-local.yaml
│   ├── rabbitmq-cloud.yaml
│   ├── airflow-cloud.yaml                 # Airflow Helm values cho GKE
│   └── mlflow-local.yaml
│
├── 📁 airflow/                            # Airflow DAGs
│   └── dags/
│       ├── training_dag.py                # DAG: fetch → preprocess → build dataset → features → train → validate → promote
│       └── sentiment_dag.py               # DAG: fetch news → FinBERT → sentiment score
│
├── 📁 k8s/                               # Kubernetes manifests
│   ├── 📁 base/                           # Base manifests (shared)
│   │   ├── deployments/                   # Deployment cho mỗi service
│   │   ├── services/                      # K8s Service definitions
│   │   ├── configmaps/                    # ConfigMaps
│   │   └── secrets/                       # Secrets (encrypted)
│   ├── 📁 overlays/
│   │   ├── local/                        # Minikube local (Phase 1-2)
│   │   ├── dev/                          # GKE dev (Phase 3+)
│   │   ├── staging/                      # Staging overrides
│   │   └── production/                   # Production overrides
│   ├── ingress.yaml                       # Ingress rules
│   ├── namespace.yaml                     # Namespace definition
│   └── kustomization.yaml                 # Kustomize config
│
├── 📁 scripts/                            # Utility scripts
│   ├── terraform-toggle.sh                # Bật/tắt hạ tầng cloud tiết kiệm chi phí
│   └── bootstrap.sh                       # Initial setup
│
├── 📁 docs/                               # Documentation
├── docker-compose-airflow.yml              # Airflow Docker Compose (on-demand local)
├── .gitignore
├── README.md
└── Makefile
```
