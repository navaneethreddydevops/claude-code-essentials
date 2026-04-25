# Global vs Regional Resources

## Why the Split Exists

Certain AWS services are **global** — their APIs live exclusively in `us-east-1` regardless of where your workload runs. Deploying them in a regional stack either silently pins them to `us-east-1` anyway (IAM) or outright fails (ACM certificates for CloudFront).

`GlobalStack` makes this explicit: it **hardcodes `region=us-east-1`** inside its constructor so it is impossible to deploy these resources to the wrong region.

## What Goes Where

### GlobalStack (`us-east-1` only)

| Resource | Why global |
|----------|-----------|
| IAM roles, policies, users | IAM API is `us-east-1`; roles apply account-wide |
| ACM certificates for CloudFront | CloudFront only reads certs from `us-east-1` |
| WAF WebACLs for CloudFront | Same constraint as ACM |
| Route53 hosted zones | DNS is global |
| GitHub OIDC identity provider | IAM — same as above |

### NetworkingStack (primary region)

| Resource | Notes |
|----------|-------|
| VPC, subnets, route tables | Regional |
| NAT gateways | Regional |
| VPC flow logs | Regional |
| KMS CMK | Regional — create one per region if multi-region |

### PlatformStack (primary region)

| Resource | Notes |
|----------|-------|
| S3 buckets | Regional by default (unless replication configured) |
| Lambda functions | Regional |
| ECS clusters | Regional |
| SQS / SNS | Regional |
| RDS / Aurora | Regional |

## Cross-Stack Reference Pattern

Regional stacks receive the global `app_role` as a constructor parameter:

```python
# app.py
global_stack = GlobalStack(app, "ProdGlobal", env_config=prod_config)

PlatformStack(
    app, "ProdPlatform",
    app_role=global_stack.app_role,   # IAM role from us-east-1
    vpc=networking.vpc,               # VPC from primary region
    env=regional_env,                 # deploys to primary region
)
```

CDK tracks this as a cross-stack dependency. CloudFormation will deploy `GlobalStack` before `PlatformStack` automatically.

## Adding a New Global Resource

Open `infra/stacks/global_stack.py` and add the resource inside `__init__`. Expose it as a `self.<name>` attribute, then pass it to whichever regional stack needs it via `app.py`.

```python
# infra/stacks/global_stack.py
self.cdn_cert = acm.Certificate(self, "CdnCert", ...)

# app.py
CloudFrontStack(..., certificate=global_stack.cdn_cert)
```
