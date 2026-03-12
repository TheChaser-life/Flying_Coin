#!/bin/bash

set -eo pipefail

cd terraform && terraform init && terraform apply

gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID

helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add apache-airflow https://airflow.apache.org
helm repo update

helm upgrade --install postgres bitnami/postgresql -f helm_values/postgres/postgres-gcp.yaml -n database
helm upgrade --install redis bitnami/redis -f helm_values/redis/redis-gcp.yaml -n database
helm upgrade --install rabbitmq bitnami/rabbitmq -f helm_values/rabbitmq/rabbitmq-gcp.yaml -n database
helm upgrade --install airflow apache-airflow/airflow -f helm_values/airflow/airflow-gcp.yaml -n mlops

kubectl apply -k k8s/overlays/dev-gcp/

kubectl get pods -A
