# Adding a New Stack

Add a stack when you need a new CloudFormation stack boundary — for example, to isolate a team's resources, model a separate deployment lifecycle, or group resources that are destroyed together.

## Step 1: Create the stack file

`infra/stacks/data_stack.py`:

```python
import aws_cdk as cdk
from aws_cdk import aws_s3 as s3, aws_ec2 as ec2
from constructs import Construct
from infra.config.accounts import EnvironmentConfig


class DataStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,           # receive dependencies as params, not imports
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        cdk.Tags.of(self).add("Stack", "data")
        for key, value in env_config.tags.items():
            cdk.Tags.of(self).add(key, value)

        removal_policy = (
            cdk.RemovalPolicy.DESTROY
            if env_config.removal_policy_destroy
            else cdk.RemovalPolicy.RETAIN
        )

        self.data_bucket = s3.Bucket(
            self,
            "DataLake",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            removal_policy=removal_policy,
            auto_delete_objects=env_config.removal_policy_destroy,
        )

        cdk.CfnOutput(
            self,
            "DataBucketName",
            value=self.data_bucket.bucket_name,
            export_name=f"{id}-DataBucket",
        )
```

## Step 2: Register it in `app.py`

```python
from infra.stacks.data_stack import DataStack

# After networking is defined:
data = DataStack(
    app,
    f"{prefix}Data",
    env_config=env_config,
    vpc=networking.vpc,
    env=regional_env,
    description=f"Data layer – {env_name}",
)
```

CDK infers the deployment order from the `vpc` parameter dependency on `networking`.

## Step 3: Add a unit test

`tests/unit/test_data_stack.py`:

```python
import aws_cdk as cdk
from aws_cdk.assertions import Template
from infra.stacks.networking_stack import NetworkingStack
from infra.stacks.data_stack import DataStack
from infra.config.accounts import ENVIRONMENTS


def _make_stack(env_name: str = "dev") -> Template:
    app = cdk.App()
    env_config = ENVIRONMENTS[env_name]
    env = cdk.Environment(account="123456789012", region="us-east-1")
    networking = NetworkingStack(app, "Net", env_config=env_config, env=env)
    data = DataStack(app, "Data", env_config=env_config, vpc=networking.vpc, env=env)
    return Template.from_stack(data)


def test_bucket_versioned():
    _make_stack().has_resource_properties(
        "AWS::S3::Bucket",
        {"VersioningConfiguration": {"Status": "Enabled"}},
    )


def test_bucket_blocks_public():
    _make_stack().has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            }
        },
    )
```

## Step 4: Deploy a single stack

```bash
# Synth and review
CDK_ENV=dev uv run cdk synth DevData --profile dev

# Diff
CDK_ENV=dev uv run cdk diff DevData --profile dev

# Deploy only this stack
CDK_ENV=dev uv run cdk deploy DevData --profile dev
```

## Deciding: Stack vs Construct

| Use a **Stack** when… | Use a **Construct** when… |
|---|---|
| Resources have a different lifecycle (deployed/destroyed separately) | Resources always travel together |
| A team owns the boundary independently | The pattern is reused across multiple stacks |
| You need a separate CloudFormation change set | It's a logical grouping within one stack |
| Resources in a genuinely different region | Same region and account as the parent |
