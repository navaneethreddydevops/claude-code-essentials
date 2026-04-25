# CI/CD Pipeline

**File:** `.github/workflows/cdk-deploy.yml`

## Pipeline Stages

```
push to main
    │
    ├── test          lint (ruff + black) + pytest
    │
    ├── synth         CDK synth for dev, staging, prod (parallel matrix)
    │
    ├── deploy-dev    OIDC → DevGlobal + DevNetworking + DevPlatform
    │
    ├── deploy-staging  OIDC → StagingGlobal + ... (requires deploy-dev success)
    │
    └── deploy-prod   OIDC → ProdGlobal + ...  (requires manual approval in GitHub Environments)
```

## Authentication

All deployments use **OIDC** — no AWS access keys are stored in GitHub secrets. The trust is established by `CiDeployRole` in each account's `GlobalStack`:

```
GitHub Actions token → STS AssumeRoleWithWebIdentity → CiDeployRole
```

The required GitHub secrets are:

| Secret | Value |
|--------|-------|
| `DEV_ACCOUNT_ID` | Dev account ID |
| `STAGING_ACCOUNT_ID` | Staging account ID |
| `PROD_ACCOUNT_ID` | Prod account ID |
| `DEV_DEPLOY_ROLE_ARN` | ARN of `CiDeployRole` in dev |
| `STAGING_DEPLOY_ROLE_ARN` | ARN of `CiDeployRole` in staging |
| `PROD_DEPLOY_ROLE_ARN` | ARN of `CiDeployRole` in prod |

The role ARNs are available as `CfnOutput` values after the first `GlobalStack` deployment, or follow the pattern:  
`arn:aws:iam::{ACCOUNT_ID}:role/{env}-ci-deploy-role`

## Manual Approval for Prod

The `deploy-prod` job references the `prod` GitHub Environment. Configure a **required reviewer** in **Settings → Environments → prod** to enforce manual approval before any production deployment.

## Running the Pipeline Locally

```bash
# Replicate what CI does
make lint
make test
make synth-dev
make synth-staging
make synth-prod
```
