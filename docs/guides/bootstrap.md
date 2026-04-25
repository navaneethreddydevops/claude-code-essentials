# Bootstrap AWS Accounts

CDK bootstrapping deploys the `CDKToolkit` CloudFormation stack to each account. It provisions the S3 staging bucket and IAM roles that CDK needs to deploy assets and CloudFormation templates.

## When to Run

- Once per account/region **before the first deployment**
- After adding a new region to an account
- When updating the CDK bootstrap version (`cdk bootstrap --template`)

## Running the Script

```bash
export DEV_ACCOUNT_ID=111111111111
export STAGING_ACCOUNT_ID=222222222222
export PROD_ACCOUNT_ID=333333333333

make bootstrap
```

This calls `scripts/bootstrap.sh`, which bootstraps all three accounts sequentially. Staging and prod use `--trust <dev-account-id>` so the pipeline can deploy cross-account without assuming a separate role manually.

## What the Script Does

```
dev account     → bootstrapped standalone
staging account → bootstrapped with --trust dev (pipeline cross-account)
prod account    → bootstrapped with --trust dev (pipeline cross-account)
```

## Manual Bootstrap (single account)

```bash
# Bootstrap only dev
cdk bootstrap aws://111111111111/us-east-1 \
  --profile dev \
  --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess

# Bootstrap staging to trust dev for cross-account deploys
cdk bootstrap aws://222222222222/us-east-1 \
  --profile staging \
  --trust 111111111111 \
  --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess
```

## GitHub OIDC Provider

Before the CI/CD pipeline can assume `CiDeployRole` (created by `GlobalStack`), the GitHub OIDC identity provider must exist in each account. Create it once per account:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --profile dev
```

Repeat with `--profile staging` and `--profile prod`. After this, deploying `GlobalStack` via CDK will wire up the trust relationship automatically.
