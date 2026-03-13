# Requirements Document: AWS Infrastructure Migration

## Introduction

This requirements document specifies the functional and non-functional requirements for migrating the Market Data Mining & Forecasting System (MDMFS) infrastructure from Google Cloud Platform (GCP) to Amazon Web Services (AWS). The migration supports a multi-cloud strategy that enables cost comparison, reduces vendor lock-in risk, and provides operational flexibility. The AWS infrastructure will maintain feature parity with the existing GCP deployment while leveraging AWS-native services for improved integration and cost optimization.

The system consists of 8 microservices (Python FastAPI + Go) deployed on Kubernetes, with supporting infrastructure for container registry, object storage, secret management, and CI/CD automation. The migration preserves the local-first development workflow (Minikube → AWS EKS) and maintains all security, scalability, and operational characteristics.

## Glossary

- **MDMFS**: Market Data Mining & Forecasting System - the application being migrated
- **Infrastructure**: The complete set of AWS resources including networking, compute, storage, and security components
- **EKS_Cluster**: Amazon Elastic Kubernetes Service cluster for running containerized workloads
- **VPC**: Virtual Private Cloud - isolated network environment in AWS
- **NAT_Gateway**: Network Address Translation gateway for outbound internet connectivity from private subnets
- **IRSA**: IAM Roles for Service Accounts - AWS mechanism for granting Kubernetes pods access to AWS services
- **ECR**: Elastic Container Registry - AWS Docker image registry
- **ESO**: External Secrets Operator - Kubernetes operator for syncing secrets from AWS Secrets Manager
- **OIDC_Provider**: OpenID Connect identity provider for federated authentication
- **Terraform**: Infrastructure-as-code tool for provisioning AWS resources
- **CI/CD_Pipeline**: Continuous Integration/Continuous Deployment automation via GitHub Actions
- **Private_Subnet**: Subnet without direct internet access, requiring NAT Gateway for outbound traffic
- **Public_Subnet**: Subnet with direct internet access via Internet Gateway
- **Service_Account**: Kubernetes identity for pods to authenticate to AWS services
- **IAM_Role**: AWS identity with specific permissions for accessing AWS resources
- **Availability_Zone**: Isolated location within an AWS region for high availability

## Requirements

### Requirement 1: Multi-Cloud Infrastructure Strategy

**User Story:** As a platform architect, I want to deploy MDMFS on AWS infrastructure, so that I can compare costs between cloud providers and reduce vendor lock-in risk.

#### Acceptance Criteria

1. THE Infrastructure SHALL provision all AWS resources required to run MDMFS with feature parity to the existing GCP deployment
2. WHEN the Infrastructure is deployed, THE Infrastructure SHALL support the same 8 microservices (auth, market, forecast, data-ingestion, notification, analytics, ml-training, api-gateway) as the GCP deployment
3. THE Infrastructure SHALL maintain the local-first development workflow where developers can test on Minikube before deploying to AWS EKS
4. THE Infrastructure SHALL use AWS-native services (EKS, ECR, S3, Secrets Manager) that provide equivalent functionality to GCP services (GKE, Artifact Registry, Cloud Storage, Secret Manager)
5. WHEN comparing infrastructure costs, THE Infrastructure SHALL provide CloudWatch metrics and cost allocation tags to enable accurate cost analysis between AWS and GCP

### Requirement 2: Network Infrastructure and Isolation

**User Story:** As a DevOps engineer, I want a secure VPC with public and private subnets across multiple availability zones, so that the EKS cluster has network isolation and high availability.

#### Acceptance Criteria

1. THE Infrastructure SHALL create a VPC with configurable CIDR block and DNS support enabled
2. THE Infrastructure SHALL create private subnets in at least 2 availability zones for EKS worker nodes
3. THE Infrastructure SHALL create public subnets in at least 2 availability zones for load balancers and NAT Gateways
4. WHEN EKS nodes are deployed, THE Infrastructure SHALL place all nodes in private subnets without public IP addresses
5. THE Infrastructure SHALL deploy a NAT_Gateway in each availability zone to provide outbound internet access for private subnets
6. THE Infrastructure SHALL configure route tables so that private subnet traffic to the internet routes through NAT_Gateways
7. THE Infrastructure SHALL create security groups that restrict traffic to only necessary ports and protocols
8. THE Infrastructure SHALL tag subnets appropriately for EKS cluster discovery (kubernetes.io/role/elb and kubernetes.io/role/internal-elb)

### Requirement 3: Kubernetes Cluster Deployment

**User Story:** As a DevOps engineer, I want an EKS cluster with managed node groups and proper IAM configuration, so that I can deploy containerized applications with auto-scaling and AWS service integration.

#### Acceptance Criteria

1. THE Infrastructure SHALL create an EKS_Cluster with a specified Kubernetes version in the configured VPC
2. THE Infrastructure SHALL enable the OIDC_Provider on the EKS_Cluster to support IRSA for pod authentication to AWS services
3. THE Infrastructure SHALL create a managed node group with configurable instance types, minimum size, desired size, and maximum size
4. WHEN the node group is created, THE Infrastructure SHALL configure auto-scaling to maintain the desired number of nodes and scale between minimum and maximum
5. THE Infrastructure SHALL create an IAM_Role for the EKS_Cluster with AmazonEKSClusterPolicy attached
6. THE Infrastructure SHALL create an IAM_Role for worker nodes with AmazonEKSWorkerNodePolicy, AmazonEKS_CNI_Policy, AmazonEC2ContainerRegistryReadOnly, and AmazonSSMManagedInstanceCore policies attached
7. THE Infrastructure SHALL create 9 Kubernetes namespaces: database, kong, auth, external-secrets, dev, staging, production, logging-monitoring, and mlops
8. THE Infrastructure SHALL enable EKS cluster logging to CloudWatch for audit, authenticator, controllerManager, and scheduler logs
9. THE Infrastructure SHALL configure kubectl access by updating the kubeconfig file with cluster credentials

### Requirement 4: Container Registry Management

**User Story:** As a developer, I want ECR repositories for each microservice with image scanning and lifecycle policies, so that I can store Docker images securely and manage storage costs.

#### Acceptance Criteria

1. THE Infrastructure SHALL create an ECR repository for each of the 8 microservices
2. WHEN an ECR repository is created, THE Infrastructure SHALL enable image scanning on push to detect vulnerabilities
3. THE Infrastructure SHALL configure image tag immutability to prevent overwriting existing image tags
4. THE Infrastructure SHALL enable AES-256 encryption for all images stored in ECR repositories
5. THE Infrastructure SHALL apply a lifecycle policy to each repository that retains only the last 10 images and expires older images
6. WHEN a Docker image is pushed to ECR, THE Infrastructure SHALL provide a repository URL in the format <account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>

### Requirement 5: Object Storage for ML Artifacts

**User Story:** As a data scientist, I want an S3 bucket for storing MLflow model artifacts with versioning and lifecycle management, so that I can track model versions and automatically clean up old artifacts.

#### Acceptance Criteria

1. THE Infrastructure SHALL create an S3 bucket with a unique name for storing MLflow model artifacts
2. THE Infrastructure SHALL enable versioning on the S3 bucket to maintain history of model artifacts
3. THE Infrastructure SHALL apply a lifecycle rule that deletes objects older than 7 days
4. THE Infrastructure SHALL apply a lifecycle rule that deletes noncurrent object versions older than 7 days
5. THE Infrastructure SHALL enable server-side encryption with AES-256 for all objects in the bucket
6. THE Infrastructure SHALL block all public access to the S3 bucket
7. THE Infrastructure SHALL configure bucket policies to allow EKS worker nodes to read and write objects

### Requirement 6: Secret Management with IRSA

**User Story:** As a security engineer, I want AWS Secrets Manager integration with Kubernetes using IRSA, so that pods can securely access secrets without storing credentials in code or environment variables.

#### Acceptance Criteria

1. THE Infrastructure SHALL create an IAM_Role for the External Secrets Operator with a trust policy that allows the EKS OIDC_Provider to assume the role
2. WHEN creating the IRSA trust policy, THE Infrastructure SHALL restrict role assumption to the specific Service_Account (eso-ksa) in the external-secrets namespace
3. THE Infrastructure SHALL attach an IAM policy to the ESO role that grants secretsmanager:GetSecretValue and secretsmanager:DescribeSecret permissions
4. THE Infrastructure SHALL create a Kubernetes Service_Account named eso-ksa in the external-secrets namespace with the annotation eks.amazonaws.com/role-arn pointing to the ESO IAM_Role
5. THE Infrastructure SHALL install the External Secrets Operator via Helm chart configured to use the eso-ksa Service_Account
6. WHEN the ESO is deployed, THE Infrastructure SHALL verify that ESO pods can successfully assume the IAM_Role and access AWS Secrets Manager

### Requirement 7: CI/CD Integration with GitHub Actions

**User Story:** As a developer, I want GitHub Actions to authenticate to AWS using OIDC without storing long-lived credentials, so that the CI/CD pipeline can build, push, and deploy applications securely.

#### Acceptance Criteria

1. THE Infrastructure SHALL create an OIDC_Provider for GitHub Actions with the URL https://token.actions.githubusercontent.com
2. THE Infrastructure SHALL create an IAM_Role for CI/CD with a trust policy that allows the GitHub OIDC_Provider to assume the role
3. WHEN creating the trust policy, THE Infrastructure SHALL restrict role assumption to the specific GitHub repository using the condition token.actions.githubusercontent.com:sub = repo:<owner>/<repo>:*
4. THE Infrastructure SHALL attach IAM policies to the CI/CD role that grant permissions for ECR authentication, image push/pull, EKS cluster description, and S3 object operations
5. WHEN GitHub Actions workflows run, THE CI/CD_Pipeline SHALL authenticate to AWS using the OIDC_Provider and assume the CI/CD IAM_Role without requiring stored AWS credentials
6. THE CI/CD_Pipeline SHALL successfully push Docker images to ECR repositories
7. THE CI/CD_Pipeline SHALL successfully deploy applications to the EKS_Cluster using kubectl

### Requirement 8: High Availability and Fault Tolerance

**User Story:** As a platform architect, I want infrastructure distributed across multiple availability zones, so that the system remains operational during single availability zone failures.

#### Acceptance Criteria

1. THE Infrastructure SHALL distribute private subnets across at least 2 availability zones
2. THE Infrastructure SHALL distribute public subnets across at least 2 availability zones
3. THE Infrastructure SHALL deploy a NAT_Gateway in each availability zone to avoid single points of failure
4. WHEN the EKS node group is created, THE Infrastructure SHALL distribute worker nodes across multiple availability zones
5. WHEN a single availability zone becomes unavailable, THE EKS_Cluster SHALL continue operating with nodes in the remaining availability zones
6. WHEN a NAT_Gateway fails, THE Infrastructure SHALL maintain outbound internet connectivity for nodes in other availability zones through their respective NAT_Gateways

### Requirement 9: Infrastructure as Code with Terraform

**User Story:** As a DevOps engineer, I want all infrastructure defined in Terraform modules, so that I can version control infrastructure changes, review them in pull requests, and apply them consistently across environments.

#### Acceptance Criteria

1. THE Infrastructure SHALL be defined using Terraform configuration files organized into reusable modules (networking, kubernetes, registry, storage, secrets, cicd)
2. WHEN running terraform plan, THE Infrastructure SHALL display all planned changes before applying them
3. WHEN running terraform apply, THE Infrastructure SHALL create all resources in the correct dependency order
4. THE Infrastructure SHALL output critical values (VPC ID, EKS cluster endpoint, ECR repository URLs, S3 bucket name, IAM role ARNs) for use in CI/CD pipelines
5. WHEN infrastructure changes are made, THE Infrastructure SHALL maintain Terraform state to track resource lifecycle
6. THE Infrastructure SHALL support destroying all resources cleanly with terraform destroy
7. THE Infrastructure SHALL use Terraform variables to make configuration values (region, instance types, node counts) customizable without code changes

### Requirement 10: Security and Compliance

**User Story:** As a security engineer, I want infrastructure that follows AWS security best practices, so that the system meets compliance requirements and minimizes security risks.

#### Acceptance Criteria

1. THE Infrastructure SHALL place all EKS worker nodes in private subnets without public IP addresses
2. THE Infrastructure SHALL encrypt all data at rest including EBS volumes, S3 objects, ECR images, and Secrets Manager secrets
3. THE Infrastructure SHALL encrypt all data in transit using TLS for API communications
4. THE Infrastructure SHALL follow the principle of least privilege for all IAM roles and policies
5. WHEN creating IAM policies with wildcard resources, THE Infrastructure SHALL limit actions to read-only operations
6. THE Infrastructure SHALL enable CloudTrail logging for all API calls to provide audit trails
7. THE Infrastructure SHALL enable VPC Flow Logs to capture network traffic for security analysis
8. THE Infrastructure SHALL configure security groups to allow only necessary inbound traffic
9. WHEN EKS cluster endpoint public access is enabled, THE Infrastructure SHALL restrict access to specific CIDR blocks
10. THE Infrastructure SHALL enable GuardDuty for threat detection and security monitoring

## Non-Functional Requirements

### Requirement 11: Cost Optimization

**User Story:** As a finance manager, I want infrastructure that optimizes costs while maintaining performance, so that we can operate efficiently within budget constraints.

#### Acceptance Criteria

1. THE Infrastructure SHALL use cost-effective instance types (t3.xlarge) that provide equivalent performance to GCP e2-standard-4 instances
2. THE Infrastructure SHALL deploy NAT_Gateways per availability zone to minimize cross-AZ data transfer costs
3. THE Infrastructure SHALL apply ECR lifecycle policies to automatically delete old images and reduce storage costs
4. THE Infrastructure SHALL apply S3 lifecycle policies to automatically delete old object versions and reduce storage costs
5. THE Infrastructure SHALL use resource tagging to enable cost allocation and tracking by environment, service, and team
6. WHERE cost optimization is prioritized, THE Infrastructure SHALL support using Spot instances for non-critical workloads with up to 70% cost savings

### Requirement 12: Performance and Scalability

**User Story:** As a platform architect, I want infrastructure that meets performance targets and scales automatically, so that the system handles varying workloads efficiently.

#### Acceptance Criteria

1. THE Infrastructure SHALL configure EKS node groups with auto-scaling between minimum and maximum node counts based on resource utilization
2. THE Infrastructure SHALL use Enhanced Networking (ENA) on EC2 instances for higher bandwidth and lower latency
3. THE Infrastructure SHALL achieve API response times under 200ms at the 95th percentile
4. THE Infrastructure SHALL achieve pod startup times under 30 seconds
5. THE Infrastructure SHALL achieve container image pull times under 60 seconds from ECR
6. THE Infrastructure SHALL achieve secret synchronization times under 10 seconds via External Secrets Operator
7. WHERE high-performance storage is required, THE Infrastructure SHALL support configuring io2 Block Express EBS volumes with appropriate IOPS

### Requirement 13: Monitoring and Observability

**User Story:** As a DevOps engineer, I want comprehensive monitoring and logging, so that I can troubleshoot issues quickly and maintain system reliability.

#### Acceptance Criteria

1. THE Infrastructure SHALL enable CloudWatch Container Insights for EKS cluster metrics
2. THE Infrastructure SHALL collect metrics for node CPU utilization, memory utilization, disk utilization, and network utilization
3. THE Infrastructure SHALL enable EKS control plane logging to CloudWatch for audit, authenticator, controllerManager, and scheduler components
4. THE Infrastructure SHALL configure CloudWatch alarms for critical resource thresholds (CPU > 80%, memory > 80%, disk > 85%)
5. WHEN infrastructure resources are created, THE Infrastructure SHALL apply consistent tags for resource identification and filtering
6. THE Infrastructure SHALL retain CloudWatch logs for at least 30 days for troubleshooting and compliance

### Requirement 14: Disaster Recovery and Backup

**User Story:** As a platform architect, I want backup and recovery capabilities, so that we can restore service quickly in case of data loss or infrastructure failure.

#### Acceptance Criteria

1. THE Infrastructure SHALL enable S3 versioning to maintain backup copies of all model artifacts
2. THE Infrastructure SHALL enable EBS snapshots for persistent volumes used by stateful applications
3. THE Infrastructure SHALL store Terraform state in a remote backend (S3 with DynamoDB locking) to prevent state corruption
4. THE Infrastructure SHALL support deploying to multiple AWS regions for disaster recovery
5. WHEN critical infrastructure components fail, THE Infrastructure SHALL provide documented recovery procedures for restoration

### Requirement 15: Migration and Compatibility

**User Story:** As a DevOps engineer, I want the AWS infrastructure to maintain compatibility with existing application code and deployment processes, so that migration requires minimal application changes.

#### Acceptance Criteria

1. THE Infrastructure SHALL support the same Kubernetes API version as the existing GKE cluster
2. THE Infrastructure SHALL create the same 9 namespaces as the GCP deployment
3. THE Infrastructure SHALL support the same container image formats and registries as the GCP deployment
4. THE Infrastructure SHALL provide equivalent secret management capabilities to GCP Secret Manager via AWS Secrets Manager and External Secrets Operator
5. THE Infrastructure SHALL support the same kubectl commands and Kubernetes manifests as the GCP deployment
6. WHEN applications are migrated from GCP to AWS, THE Infrastructure SHALL require only configuration changes (image URLs, secret references) without code modifications
