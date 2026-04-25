# Multi-Region Deployments

The project supports deploying to multiple regions within the same account by adding region-specific entries to `ACCOUNTS` in `accounts.py` and instantiating additional stacks in `app.py`.

## Adding a Second Region

### Step 1: Add a region config entry

`infra/config/accounts.py`:

```python
ACCOUNTS = {
    "dev": AccountConfig(
        account_id=os.getenv("DEV_ACCOUNT_ID", "111111111111"),
        region="us-east-1",
    ),
    "dev-us-west-2": AccountConfig(     # second region, same account
        account_id=os.getenv("DEV_ACCOUNT_ID", "111111111111"),
        region="us-west-2",
    ),
}

ENVIRONMENTS = {
    "dev": EnvironmentConfig(name="dev", account=ACCOUNTS["dev"], vpc_cidr="10.0.0.0/16", ...),
    "dev-us-west-2": EnvironmentConfig(
        name="dev",
        account=ACCOUNTS["dev-us-west-2"],
        vpc_cidr="10.3.0.0/16",   # non-overlapping CIDR
        ...
    ),
}
```

### Step 2: Bootstrap the new region

```bash
cdk bootstrap aws://111111111111/us-west-2 --profile dev \
  --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess
```

### Step 3: Instantiate regional stacks in `app.py`

```python
for env_key in ["dev", "dev-us-west-2"]:
    cfg = ENVIRONMENTS[env_key]
    regional = cdk.Environment(account=cfg.account.account_id, region=cfg.account.region)
    label = f"Dev{cfg.account.region.replace('-', '').title()}"

    net = NetworkingStack(app, f"{label}Networking", env_config=cfg, env=regional)
    PlatformStack(
        app, f"{label}Platform",
        env_config=cfg, vpc=net.vpc, app_role=global_stack.app_role,
        env=regional,
    )
```

!!! note
    `GlobalStack` is still instantiated **once per account** (not per region). IAM is global — you never need two `GlobalStack`s in the same account.

## VPC Peering Across Regions

If workloads in different regions need to communicate, add a peering resource in a dedicated stack after both VPCs exist:

```python
# infra/stacks/peering_stack.py
from aws_cdk import aws_ec2 as ec2

class PeeringStack(cdk.Stack):
    def __init__(self, scope, id, vpc_a: ec2.IVpc, vpc_b: ec2.IVpc, ...) -> None:
        super().__init__(...)
        ec2.CfnVPCPeeringConnection(
            self, "Peer",
            vpc_id=vpc_a.vpc_id,
            peer_vpc_id=vpc_b.vpc_id,
            peer_region="us-west-2",
        )
```
