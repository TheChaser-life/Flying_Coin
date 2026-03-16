# Persistence Strategy: Saving UI Configs after Terraform Destroy

When you run `terraform destroy`, the GKE cluster and its resources (including PVCs) are typically deleted. To save your hard work on dashboards and views, we will use a "GitOps" (Configuration as Code) approach.

## Proposed Strategy

### 1. Grafana: Dashboards as Code
Instead of saving dashboards in the Grafana database (which gets wiped), we will:
*   Export dashboards as JSON files.
*   Store these JSON files in your project directory (e.g., `k8s/dashboards/`).
*   Configure the **Grafana Sidecar** to automatically load any ConfigMap with the label `grafana_dashboard=1`.

### 2. Kibana: Saved Objects Export
Kibana doesn't have a reliable automatic "sidecar" for Data Views and Dashboards like Grafana does.
*   **Manual Export:** Use the **Stack Management > Saved Objects > Export** feature to get an `.ndjson` file.
*   **Version Control:** Commit this `.ndjson` file to your Git repository.
*   **Recovery:** After a new `terraform apply`, simply import this file back into Kibana.

### 3. Data Retention (Elasticsearch Logs)
If you want to keep millions of logs through a `terraform destroy`, you must:
*   Set the **ReclaimPolicy** of your StorageClass (or specific PVs) to `Retain`.
*   **Warning:** This means GCE Persistent Disks will **NOT** be deleted. You will have to manually delete them later or "re-bind" them to the new cluster (which is complex).
*   **Recommendation:** For a dev project, it's usually better to just re-collect logs and only save the *UI configurations* (Dashboards/Alerts).

## Implementation Steps

### Grafana Sidecar Setup
I will update `grafana-gcp.yaml` to enable the dashboard sidecar.

```yaml
sidecar:
  dashboards:
    enabled: true
    label: grafana_dashboard
    searchNamespace: ALL
```

### Next Steps
1.  Would you like me to enable the Grafana sidecar now?
2.  Do you have any existing Dashboards in Grafana or Kibana that you need to export before your next `destroy`?
