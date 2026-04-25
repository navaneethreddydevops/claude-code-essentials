#!/usr/bin/env bash
# Bootstrap CDK in all accounts. Run once per account/region before first deploy.
# Usage: ./scripts/bootstrap.sh
set -euo pipefail

DEV_ACCOUNT=${DEV_ACCOUNT_ID:-111111111111}
STAGING_ACCOUNT=${STAGING_ACCOUNT_ID:-222222222222}
PROD_ACCOUNT=${PROD_ACCOUNT_ID:-333333333333}
REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo "Bootstrapping dev ($DEV_ACCOUNT)..."
cdk bootstrap "aws://${DEV_ACCOUNT}/${REGION}" --profile dev \
  --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess

echo "Bootstrapping staging ($STAGING_ACCOUNT)..."
cdk bootstrap "aws://${STAGING_ACCOUNT}/${REGION}" --profile staging \
  --trust "${DEV_ACCOUNT}" \
  --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess

echo "Bootstrapping prod ($PROD_ACCOUNT)..."
cdk bootstrap "aws://${PROD_ACCOUNT}/${REGION}" --profile prod \
  --trust "${DEV_ACCOUNT}" \
  --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess

echo "Done. All accounts bootstrapped."
