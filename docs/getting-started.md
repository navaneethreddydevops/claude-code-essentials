# Prerequisites & Setup

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| AWS CDK CLI | latest | `npm install -g aws-cdk` |
| AWS CLI | v2 | [docs.aws.amazon.com](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) |

## Installation

```bash
# Clone the repo
git clone https://github.com/navaneethreddydevops/claude-code-essentials.git
cd claude-code-essentials

# Install all dependencies (runtime + dev)
uv sync --all-extras
```

## AWS Profile Setup

Configure named profiles in `~/.aws/config` for each account:

```ini
[profile dev]
sso_start_url = https://your-sso.awsapps.com/start
sso_region = us-east-1
sso_account_id = 111111111111
sso_role_name = AdministratorAccess
region = us-east-1

[profile staging]
sso_account_id = 222222222222
# ... same pattern

[profile prod]
sso_account_id = 333333333333
# ... same pattern
```

Then set your real account IDs in the environment (or edit `infra/config/accounts.py` directly):

```bash
export DEV_ACCOUNT_ID=111111111111
export STAGING_ACCOUNT_ID=222222222222
export PROD_ACCOUNT_ID=333333333333
```

## Bootstrap (One-Time per Account)

CDK bootstrapping deploys the CDKToolkit CloudFormation stack to each account, which provisions the S3 bucket and IAM roles needed for deployments.

```bash
make bootstrap
```

This runs `scripts/bootstrap.sh`, which bootstraps all three accounts. Staging and prod are bootstrapped with `--trust <dev-account>` so the CI/CD pipeline can deploy cross-account.

!!! warning
    Bootstrap must be run **once per account/region** before any `cdk deploy`. It is safe to re-run.

## Local Development Workflow

```bash
# Verify synth works (no AWS calls, purely local)
make synth-dev

# See what would change in dev
make diff-dev

# Deploy to dev
make deploy-dev

# Run tests
make test

# Lint & format
make lint
make format
```

## Serving the Docs Locally

```bash
make docs-serve
# Open http://127.0.0.1:8000
```
