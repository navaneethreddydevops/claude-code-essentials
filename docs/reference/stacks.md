# Stack Inventory

## GlobalStack

**File:** `infra/stacks/global_stack.py`  
**Region:** Always `us-east-1`  
**Stack name pattern:** `{Env}Global` (e.g. `DevGlobal`, `ProdGlobal`)

| Resource | Logical ID | Notes |
|----------|-----------|-------|
| IAM Role | `AppRole` | Lambda execution role; passed to PlatformStack |
| IAM Role | `CiDeployRole` | GitHub Actions OIDC role; `AdministratorAccess` scoped per env |
| OIDC Provider (ref) | `GitHubOidcProvider` | References existing provider — does not create it |

**Outputs:** `{id}-AppRoleArn`, `{id}-DeployRoleArn`

---

## NetworkingStack

**File:** `infra/stacks/networking_stack.py`  
**Region:** Account's primary region  
**Stack name pattern:** `{Env}Networking`

| Resource | Logical ID | Notes |
|----------|-----------|-------|
| VPC | `EnterpriseVpc/Vpc` | `/16` CIDR, 3 AZs, 3 subnet tiers |
| KMS Key | `NetworkingKey/Key` | CMK with rotation, alias `{env}/networking` |
| Flow Logs | `EnterpriseVpc/FlowLog` | Disabled in dev |

**Outputs:** `{id}-VpcId`, `{id}-KmsKeyArn`

---

## PlatformStack

**File:** `infra/stacks/platform_stack.py`  
**Region:** Account's primary region  
**Stack name pattern:** `{Env}Platform`

| Resource | Logical ID | Notes |
|----------|-----------|-------|
| S3 Bucket | `ArtifactsBucket` | Encrypted, versioned, access logs, SSL enforced |

**Outputs:** `{id}-ArtifactsBucket`

**Receives:** `vpc` from NetworkingStack, `app_role` from GlobalStack
