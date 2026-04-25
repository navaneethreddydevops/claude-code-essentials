# Environment Configuration

All environment-specific values live in `infra/config/accounts.py`. Edit this file to change account IDs, regions, CIDRs, or feature flags.

## EnvironmentConfig Fields

| Field | Type | Dev | Staging | Prod | Description |
|-------|------|-----|---------|------|-------------|
| `name` | `str` | `"dev"` | `"staging"` | `"prod"` | Used in resource names |
| `vpc_cidr` | `str` | `10.0.0.0/16` | `10.1.0.0/16` | `10.2.0.0/16` | Must not overlap across envs |
| `enable_flow_logs` | `bool` | `False` | `True` | `True` | VPC flow logs to CloudWatch |
| `enable_cloudtrail` | `bool` | `False` | `True` | `True` | Account-level CloudTrail |
| `removal_policy_destroy` | `bool` | `True` | `False` | `False` | `DESTROY` + `auto_delete_objects` on S3/RDS |
| `tags` | `dict` | `{...}` | `{...}` | `{...}` | Applied to all resources in all stacks |

## Overriding via Environment Variables

Account IDs and regions can be injected at runtime without editing the file — useful in CI/CD:

| Env Var | Default | Used by |
|---------|---------|---------|
| `DEV_ACCOUNT_ID` | `111111111111` | dev stacks |
| `DEV_REGION` | `us-east-1` | dev stacks |
| `DEV_PROFILE` | `dev` | bootstrap script |
| `STAGING_ACCOUNT_ID` | `222222222222` | staging stacks |
| `STAGING_REGION` | `us-east-1` | staging stacks |
| `PROD_ACCOUNT_ID` | `333333333333` | prod stacks |
| `PROD_REGION` | `us-east-1` | prod stacks |

## Adding a New Environment

1. Add an `AccountConfig` entry to `ACCOUNTS`
2. Add an `EnvironmentConfig` entry to `ENVIRONMENTS`
3. Set `CDK_ENV=<new-env>` when running `cdk deploy`
4. Bootstrap the new account/region with `scripts/bootstrap.sh` (or manually)

```python
# infra/config/accounts.py
ACCOUNTS["sandbox"] = AccountConfig(
    account_id=os.getenv("SANDBOX_ACCOUNT_ID", "444444444444"),
    region="us-east-1",
    profile="sandbox",
)

ENVIRONMENTS["sandbox"] = EnvironmentConfig(
    name="sandbox",
    account=ACCOUNTS["sandbox"],
    vpc_cidr="10.4.0.0/16",
    removal_policy_destroy=True,
    enable_flow_logs=False,
    tags={"Environment": "sandbox", "ManagedBy": "CDK", "CostCenter": "engineering"},
)
```
