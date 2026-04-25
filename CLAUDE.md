# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Package Management

This project uses **uv**. All commands should be run through `uv run` or via the Makefile targets.

```bash
uv sync --all-extras   # install all deps including dev
uv run pytest          # run tests
uv run cdk synth       # synth without Makefile
```

## Common Commands

```bash
make install           # uv sync --all-extras
make test              # pytest with coverage
make lint              # ruff + black --check
make format            # ruff --fix + black
make synth-dev         # CDK_ENV=dev cdk synth
make deploy-dev        # CDK_ENV=dev cdk deploy --all --profile dev
make diff-prod         # CDK_ENV=prod cdk diff --all --profile prod
make bootstrap         # one-time CDK bootstrap for all three accounts
```

Run a single test file:
```bash
uv run pytest tests/unit/test_global_stack.py -v
```

## Architecture

### Multi-Account Model

The `CDK_ENV` environment variable selects which account to target (`dev`, `staging`, `prod`). Account IDs, regions, and AWS CLI profiles are defined in `infra/config/accounts.py` and can be overridden with env vars (`DEV_ACCOUNT_ID`, `STAGING_ACCOUNT_ID`, `PROD_ACCOUNT_ID`, etc.).

### Global vs Regional Split

Every environment deploys **three stacks**:

| Stack | Region | Purpose |
|---|---|---|
| `{Env}Global` | always `us-east-1` | IAM, Route53, ACM-for-CloudFront, WAF-for-CloudFront |
| `{Env}Networking` | env's primary region | VPC, KMS CMK, flow logs |
| `{Env}Platform` | env's primary region | Application resources (S3, compute, etc.) |

`GlobalStack` **sets its own `env=us-east-1` internally** — never pass `env=` when constructing it from `app.py`. This prevents accidentally deploying IAM/ACM resources to the wrong region.

Cross-stack wiring: `GlobalStack` exposes `app_role` and `deploy_role` as attributes; `PlatformStack` receives `app_role` as a constructor parameter. `NetworkingStack` exposes `vpc` for `PlatformStack` to consume.

### Construct vs Stack Layering

Reusable infrastructure patterns live in `infra/constructs/` and are composed inside stacks:
- `EnterpriseVpc` — 3-tier VPC (public/private/isolated) across 3 AZs with optional flow logs
- `EnterpriseKmsKey` — CMK with rotation enabled and deny-root policy

New reusable patterns should go in `infra/constructs/`, not inline in stacks.

### EnvironmentConfig Controls Behaviour

`EnvironmentConfig` (in `accounts.py`) drives environment-specific behaviour that stacks read at synth time:
- `removal_policy_destroy=True` — only set for `dev`; enables `DESTROY` + `auto_delete_objects`
- `enable_flow_logs` / `enable_cloudtrail` — disabled in dev to reduce cost
- `vpc_cidr` — non-overlapping CIDRs across envs (`10.0`, `10.1`, `10.2`)

### CI/CD Pipeline

`.github/workflows/cdk-deploy.yml` runs: lint → test → synth (all 3 envs in parallel) → deploy-dev → deploy-staging → deploy-prod. Prod deployment requires a manual approval gate configured in GitHub Environments. All deployments use OIDC (`role-to-assume`) — no long-lived AWS keys. The OIDC trust is established via `CiDeployRole` in `GlobalStack`.

### First-Time Setup

Before first deployment, bootstrap CDK in all accounts:
```bash
export DEV_ACCOUNT_ID=... STAGING_ACCOUNT_ID=... PROD_ACCOUNT_ID=...
make bootstrap
```
Staging and prod bootstrap with `--trust <dev-account>` so the dev account's pipeline role can deploy cross-account.
