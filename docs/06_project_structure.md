# 📁 Cấu Trúc Thư Mục Dự Án (Project Structure)

```
market-forecasting/
│
├── 📁 services/
│   ├── 📁 api-gateway/                    # API Gateway (Kong/Nginx)
│   │   └── Dockerfile
│   │
│   ├── 📁 auth-service/                   # Auth Service
│   │   ├── 📁 app/
│   │   │   ├── api/                       # Login, Register endpoints
│   │   │   ├── core/                      # Config, Security, JWT
│   │   │   └── main.py
│   │   └── Dockerfile
│   │
│   ├── 📁 collectors/                     # Data Collectors (Yahoo, Binance, News, RSS)
│   │   ├── 📁 app/
│   │   │   ├── base_collector.py
│   │   │   ├── main.py
│   │   │   └── ... collectors
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── 📁 market-data-service/            # Market Data Service (API)
│   │   ├── 📁 app/
│   │   │   ├── api/                       # Market data endpoints
│   │   │   ├── models/                    # MarketData, Symbol models
│   │   │   └── main.py
│   │   └── Dockerfile
│   │
│   ├── 📁 forecast-service/               # Forecast Service
│   │   ├── 📁 app/
│   │   │   ├── api/                       # Prediction endpoints
│   │   │   └── main.py
│   │   └── Dockerfile
│   │
│   ├── 📁 sentiment-service/              # Sentiment Service
│   │   ├── 📁 app/
│   │   │   ├── api/                       # Sentiment endpoints
│   │   │   ├── services/                  # FinBERT inference, News consumer
│   │   │   └── main.py
│   │   └── Dockerfile
│   │
│   └── 📁 mlops/                          # MLOps Infrastructure
│       └── 📁 mlflow/                     # MLflow tracking server
│
├── 📁 shared/                             # Shared giữa services
│   ├── 📁 database/                       # SQLAlchemy models & Alembic migrations
│   │   └── 📁 alembic/
│   ├── 📁 schemas/                        # Shared Pydantic schemas
│   ├── 📁 utils/                          # Common utilities
│   └── 📁 constants/                      # Shared constants
│
├── 📁 ml/                                 # ML Training & Pipelines (Airflow-based)
│   ├── 📁 dags/                           # Airflow DAGs
│   ├── 📁 pipelines/                      # Preprocessing, Feature engineering
│   ├── 📁 configs/                        # Hyperparameter configs
│   └── 📁 scripts/                        # Training scripts
│
├── 📁 terraform/                          # Infrastructure as Code (GCP)
│   ├── 📁 modules/                        # Networking, K8s, Storage, Registry
│   ├── main.tf
│   └── variables.tf
│
├── 📁 helm_values/                        # Helm values (postgres, redis, rabbitmq, kong)
│   ├── 📁 postgres/
│   ├── 📁 rabbitmq/
│   └── ...
│
├── 📁 k8s/                                # Kubernetes manifests (Kustomize)
│   ├── 📁 base/                           # Base configurations per service
│   │   ├── 📁 forecast-service/
│   │   ├── 📁 sentiment-service/
│   │   └── ...
│   └── 📁 overlays/
│       ├── 📁 local/                      # Minikube local
│       └── 📁 gcp/                        # GCP/GKE
│
├── 📁 scripts/                            # Utility scripts
├── 📁 docs/                               # Documentation
├── 📁 diary/                              # Development logs
├── alembic.ini                            # Alembic configuration
├── .env                                   # Environment variables
├── .gitignore
├── README.md
└── Makefile
```
