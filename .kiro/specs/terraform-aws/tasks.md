# Implementation Plan: AWS Infrastructure Migration

## Overview

This implementation plan breaks down the AWS infrastructure migration into discrete Terraform coding tasks. The infrastructure will be built using HCL (Terraform) following a modular approach with 6 core modules: networking, kubernetes, registry, storage, secrets, and cicd. Each task builds incrementally, with checkpoints to ensure stability before proceeding.

## Tasks

- [ ] 1. Set up project structure and provider configuration
  - Create terraform-aws/ directory parallel to existing terraform/ directory
  - Create main.tf, variables.tf, outputs.tf, and terraform.tfvars files
  - Configure AWS provider with region and required version constraints
  - Create modules/ directory with subdirectories for each module
  - Set up remote state backend configuration (S3 + DynamoDB)
  - _Requirements: 9.1, 9.5_

- [ ] 2. Implement networking module
  - [ ] 2.1 Create VPC and subnet resources
    - Write modules/networking/main.tf with VPC resource
    - Create public and private subnets across multiple availability zones
    - Configure subnet tags for EKS cluster discovery
    - _Requirements: 2.1, 2.2, 2.3, 2.8_
  
  - [ ] 2.2 Implement Internet Gateway and NAT Gateway resources
    - Create Internet Gateway and attach to VPC
    - Create Elastic IPs for NAT Gateways
    - Deploy NAT Gateway in each public subnet (one per AZ)
    - _Requirements: 2.5, 8.3_
  
  - [ ] 2.3 Configure route tables
    - Create public route table with route to Internet Gateway
    - Create private route tables with routes to NAT Gateways
    - Associate route tables with appropriate subnets
    - _Requirements: 2.6_
  
  - [ ] 2.4 Create security groups
    - Create security group for EKS cluster control plane
    - Configure ingress rules for necessary ports (443 for API)
    - Configure egress rules for outbound traffic
    - _Requirements: 2.7, 10.8_
  
  - [ ]* 2.5 Write validation tests for networking module
    - Test VPC CIDR configuration
    - Test subnet distribution across AZs
    - Test NAT Gateway deployment
    - Test route table configuration

- [ ] 3. Checkpoint - Validate networking infrastructure
  - Run terraform plan to verify networking module configuration
  - Ensure all tests pass, ask the user if questions arise

- [ ] 4. Implement Kubernetes (EKS) module
  - [ ] 4.1 Create IAM roles for EKS cluster and nodes
    - Create IAM role for EKS cluster with trust policy
    - Attach AmazonEKSClusterPolicy to cluster role
    - Create IAM role for worker nodes with EC2 trust policy
    - Attach required policies (AmazonEKSWorkerNodePolicy, AmazonEKS_CNI_Policy, AmazonEC2ContainerRegistryReadOnly, AmazonSSMManagedInstanceCore)
    - _Requirements: 3.5, 3.6_
  
  - [ ] 4.2 Create EKS cluster resource
    - Write modules/kubernetes/main.tf with EKS cluster resource
    - Configure VPC settings with subnet IDs from networking module
    - Enable private and public endpoint access
    - Configure cluster version and logging
    - _Requirements: 3.1, 3.8_
  
  - [ ] 4.3 Enable OIDC provider for IRSA
    - Create OIDC identity provider for the EKS cluster
    - Extract OIDC provider URL and ARN for use in IAM trust policies
    - _Requirements: 3.2_
  
  - [ ] 4.4 Create managed node group
    - Create EKS managed node group with configurable instance types
    - Configure auto-scaling (min, desired, max sizes)
    - Set disk size and capacity type (ON_DEMAND or SPOT)
    - Associate with private subnets
    - _Requirements: 3.3, 3.4_
  
  - [ ] 4.5 Create Kubernetes namespaces
    - Use Kubernetes provider to create 9 namespaces
    - Namespaces: database, kong, auth, external-secrets, dev, staging, production, logging-monitoring, mlops
    - _Requirements: 3.7_
  
  - [ ] 4.6 Configure kubectl access
    - Add data source for EKS cluster authentication
    - Configure Kubernetes and Helm providers with cluster credentials
    - _Requirements: 3.9_
  
  - [ ]* 4.7 Write validation tests for Kubernetes module
    - Test EKS cluster creation
    - Test OIDC provider configuration
    - Test node group scaling configuration
    - Test namespace creation

- [ ] 5. Checkpoint - Validate EKS cluster
  - Run terraform plan to verify Kubernetes module configuration
  - Ensure all tests pass, ask the user if questions arise

- [ ] 6. Implement secrets module (IRSA for ESO)
  - [ ] 6.1 Create IAM role for External Secrets Operator
    - Create IAM role with IRSA trust policy
    - Configure trust policy to allow OIDC provider with specific service account
    - Restrict to external-secrets namespace and eso-ksa service account
    - _Requirements: 6.1, 6.2_
  
  - [ ] 6.2 Attach Secrets Manager permissions
    - Create IAM policy with secretsmanager:GetSecretValue and secretsmanager:DescribeSecret
    - Attach policy to ESO IAM role
    - _Requirements: 6.3_
  
  - [ ] 6.3 Create Kubernetes service account with IRSA annotation
    - Create service account named eso-ksa in external-secrets namespace
    - Add annotation eks.amazonaws.com/role-arn with ESO role ARN
    - _Requirements: 6.4_
  
  - [ ]* 6.4 Write validation tests for secrets module
    - Test IAM role trust policy format
    - Test Secrets Manager permissions
    - Test service account annotation

- [ ] 7. Implement External Secrets Operator deployment
  - [ ] 7.1 Deploy ESO via Helm chart
    - Add Helm release resource for external-secrets chart
    - Configure to use existing service account (eso-ksa)
    - Enable CRD installation
    - Set appropriate timeout and wait conditions
    - _Requirements: 6.5_
  
  - [ ]* 7.2 Write integration test for ESO
    - **Property 4: Secret Synchronization**
    - **Validates: Requirements 6.6**
    - Test creating AWS secret and ExternalSecret resource
    - Verify Kubernetes secret is created with correct data

- [ ] 8. Checkpoint - Validate secrets infrastructure
  - Run terraform plan to verify secrets module and ESO deployment
  - Ensure all tests pass, ask the user if questions arise

- [ ] 9. Implement registry (ECR) module
  - [ ] 9.1 Create ECR repositories
    - Create ECR repository resources for each of 8 microservices
    - Services: auth-service, market-service, forecast-service, data-ingestion-service, notification-service, analytics-service, ml-training-service, api-gateway
    - _Requirements: 4.1_
  
  - [ ] 9.2 Configure repository settings
    - Enable image tag immutability
    - Enable image scanning on push
    - Configure AES-256 encryption
    - _Requirements: 4.2, 4.3, 4.4_
  
  - [ ] 9.3 Apply lifecycle policies
    - Create lifecycle policy to retain last 10 images
    - Configure policy to expire older images
    - _Requirements: 4.5_
  
  - [ ]* 9.4 Write validation tests for registry module
    - **Property 5: Image Immutability**
    - **Validates: Requirements 4.2, 4.3, 4.4**
    - Test repository configuration
    - Test lifecycle policy application
    - **Property 10: ECR Repository URL Format**
    - **Validates: Requirements 4.6**
    - Test repository URL format

- [ ] 10. Implement storage (S3) module
  - [ ] 10.1 Create S3 bucket for MLflow artifacts
    - Create S3 bucket with unique name
    - Configure bucket ownership controls
    - _Requirements: 5.1_
  
  - [ ] 10.2 Configure bucket versioning and lifecycle
    - Enable versioning on the bucket
    - Create lifecycle rule to delete objects older than 7 days
    - Create lifecycle rule to delete noncurrent versions older than 7 days
    - _Requirements: 5.2, 5.3, 5.4_
  
  - [ ] 10.3 Configure bucket encryption and access control
    - Enable server-side encryption with AES-256
    - Configure public access block settings (block all public access)
    - _Requirements: 5.5, 5.6_
  
  - [ ] 10.4 Create bucket policy for EKS node access
    - Create bucket policy allowing EKS node role to read/write objects
    - Restrict access to specific IAM role
    - _Requirements: 5.7_
  
  - [ ]* 10.5 Write validation tests for storage module
    - **Property 8: Storage Lifecycle Management**
    - **Validates: Requirements 5.2, 5.3, 5.4**
    - Test versioning configuration
    - Test lifecycle rules
    - **Property 11: S3 Encryption and Access Control**
    - **Validates: Requirements 5.5, 5.6**
    - Test encryption settings
    - Test public access block

- [ ] 11. Checkpoint - Validate registry and storage
  - Run terraform plan to verify registry and storage modules
  - Ensure all tests pass, ask the user if questions arise

- [ ] 12. Implement CI/CD module (GitHub OIDC)
  - [ ] 12.1 Create OIDC provider for GitHub Actions
    - Create OIDC identity provider with GitHub URL
    - Configure client ID list with sts.amazonaws.com
    - Set thumbprint list for GitHub OIDC
    - _Requirements: 7.1_
  
  - [ ] 12.2 Create IAM role for GitHub Actions
    - Create IAM role with trust policy for GitHub OIDC provider
    - Configure trust policy to restrict to specific GitHub repository
    - Use StringLike condition for repo:<owner>/<repo>:* pattern
    - _Requirements: 7.2, 7.3_
  
  - [ ] 12.3 Attach permissions for CI/CD operations
    - Create and attach ECR policy (GetAuthorizationToken, PutImage, etc.)
    - Create and attach EKS policy (DescribeCluster, ListClusters)
    - Create and attach S3 policy (PutObject, GetObject, ListBucket)
    - _Requirements: 7.4_
  
  - [ ]* 12.4 Write validation tests for CI/CD module
    - **Property 12: GitHub OIDC Trust Policy Restriction**
    - **Validates: Requirements 7.3**
    - Test OIDC provider configuration
    - Test IAM role trust policy
    - Test permission policies

- [ ] 13. Implement root module integration
  - [ ] 13.1 Wire all modules together in main.tf
    - Call networking module with appropriate variables
    - Call kubernetes module with networking outputs
    - Call secrets module with kubernetes outputs
    - Call registry module with project configuration
    - Call storage module with project configuration
    - Call cicd module with project configuration
    - _Requirements: 9.3_
  
  - [ ] 13.2 Define input variables
    - Create variables.tf with all configurable parameters
    - Define variables: region, project_name, vpc_cidr, availability_zones, cluster_version, node_instance_types, node sizes, github_repo
    - Set appropriate types, descriptions, and default values
    - _Requirements: 9.7_
  
  - [ ] 13.3 Define outputs
    - Create outputs.tf with critical values for CI/CD
    - Output: vpc_id, cluster_endpoint, cluster_name, ecr_repository_urls, s3_bucket_name, cicd_role_arn
    - _Requirements: 9.4_
  
  - [ ] 13.4 Create terraform.tfvars template
    - Create example configuration file with all variables
    - Document expected values and formats
    - Include comments for guidance

- [ ] 14. Implement module-level variables and outputs
  - [ ] 14.1 Create variables.tf for each module
    - Define input variables for networking module
    - Define input variables for kubernetes module
    - Define input variables for secrets module
    - Define input variables for registry module
    - Define input variables for storage module
    - Define input variables for cicd module
  
  - [ ] 14.2 Create outputs.tf for each module
    - Define outputs for networking module (vpc_id, subnet_ids, security_group_id)
    - Define outputs for kubernetes module (cluster_endpoint, cluster_name, oidc_provider_arn)
    - Define outputs for secrets module (eso_role_arn)
    - Define outputs for registry module (repository_urls)
    - Define outputs for storage module (bucket_name, bucket_arn)
    - Define outputs for cicd module (cicd_role_arn)

- [ ] 15. Checkpoint - Validate complete infrastructure
  - Run terraform init to initialize all modules
  - Run terraform validate to check syntax
  - Run terraform plan to preview all changes
  - Ensure all tests pass, ask the user if questions arise

- [ ] 16. Add resource tagging for cost allocation
  - [ ] 16.1 Implement tagging strategy
    - Add common tags to all AWS resources
    - Tags: Project, Environment, ManagedBy, CostCenter
    - Use locals block for consistent tag application
    - _Requirements: 1.5, 11.5, 13.5_
  
  - [ ]* 16.2 Write validation test for resource tagging
    - **Property 15: Resource Tagging for Cost Allocation**
    - **Validates: Requirements 1.5, 11.5, 13.5**
    - Test all resources have required tags

- [ ] 17. Implement security hardening
  - [ ] 17.1 Configure encryption at rest
    - Verify EBS encryption is enabled for node volumes
    - Verify S3 encryption is configured
    - Verify ECR encryption is configured
    - Verify Secrets Manager encryption is configured
    - _Requirements: 10.2_
  
  - [ ] 17.2 Implement network security controls
    - Verify all nodes are in private subnets
    - Verify security group rules follow least privilege
    - Configure cluster endpoint access restrictions
    - _Requirements: 10.1, 10.8, 10.9_
  
  - [ ]* 17.3 Write security validation tests
    - **Property 1: Network Isolation**
    - **Validates: Requirements 2.4, 2.6, 10.1**
    - Test nodes are in private subnets without public IPs
    - **Property 6: Least Privilege IAM**
    - **Validates: Requirements 10.4, 10.5**
    - Test IAM policies follow least privilege
    - **Property 7: Cluster Endpoint Security**
    - **Validates: Requirements 10.9**
    - Test cluster endpoint access configuration
    - **Property 13: Data Encryption at Rest**
    - **Validates: Requirements 10.2**
    - Test encryption is enabled on all storage resources
    - **Property 14: Security Group Ingress Restrictions**
    - **Validates: Requirements 10.8**
    - Test security groups don't allow unrestricted access

- [ ] 18. Implement high availability validation
  - [ ]* 18.1 Write high availability tests
    - **Property 2: High Availability**
    - **Validates: Requirements 2.2, 2.3, 2.5, 8.1, 8.2, 8.3, 8.4**
    - Test resources are distributed across multiple AZs
    - Test NAT Gateways are deployed per AZ
    - Test node group spans multiple AZs

- [ ] 19. Implement IRSA validation
  - [ ]* 19.1 Write IRSA authentication tests
    - **Property 3: IRSA Authentication**
    - **Validates: Requirements 6.1, 6.2, 6.4**
    - Test service account annotations
    - Test IAM role trust policies
    - Test OIDC provider configuration

- [ ] 20. Create documentation
  - [ ] 20.1 Create README.md for terraform-aws directory
    - Document prerequisites (Terraform, AWS CLI, kubectl)
    - Document deployment steps (init, plan, apply)
    - Document variable configuration
    - Document output values and their usage
    - _Requirements: 9.1_
  
  - [ ] 20.2 Document module interfaces
    - Create README.md for each module
    - Document input variables, outputs, and usage examples
    - Document dependencies between modules
  
  - [ ] 20.3 Create deployment guide
    - Document step-by-step deployment process
    - Document kubectl configuration steps
    - Document verification steps
    - Document troubleshooting common issues

- [ ] 21. Final checkpoint - Complete infrastructure validation
  - Run full terraform plan to verify all modules
  - Review all outputs are correctly defined
  - Verify documentation is complete
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and reduce risk
- Property tests validate universal correctness properties from the design
- All Terraform code should follow HCL best practices and formatting standards
- Use `terraform fmt` to format code consistently
- Use `terraform validate` to check syntax before committing
- Module structure mirrors the existing GCP terraform/ directory for consistency
