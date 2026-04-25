# Adding a New Resource

This guide walks through adding a new AWS resource to an existing stack, with full examples. Follow the same pattern for any service.

---

## Example 1 — SQS Queue in PlatformStack

### Step 1: Add the resource to the stack

Open `infra/stacks/platform_stack.py` and add the queue:

```python
from aws_cdk import aws_sqs as sqs, Duration

class PlatformStack(cdk.Stack):
    def __init__(self, ...) -> None:
        super().__init__(...)

        # ... existing resources ...

        # Dead-letter queue
        dlq = sqs.Queue(
            self,
            "WorkerDlq",
            queue_name=f"{env_config.name}-worker-dlq",
            retention_period=Duration.days(14),
            encryption=sqs.QueueEncryption.KMS_MANAGED,
        )

        # Main queue with DLQ
        self.worker_queue = sqs.Queue(
            self,
            "WorkerQueue",
            queue_name=f"{env_config.name}-worker-queue",
            visibility_timeout=Duration.seconds(30),
            encryption=sqs.QueueEncryption.KMS_MANAGED,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=dlq,
            ),
        )

        # Grant the global app_role permission to send messages
        self.worker_queue.grant_send_messages(app_role)

        cdk.CfnOutput(
            self,
            "WorkerQueueUrl",
            value=self.worker_queue.queue_url,
            export_name=f"{id}-WorkerQueueUrl",
        )
```

### Step 2: Write a unit test

Create or extend `tests/unit/test_platform_stack.py`:

```python
def test_worker_queue_has_dlq():
    template = _make_stacks()
    # Main queue
    template.has_resource_properties(
        "AWS::SQS::Queue",
        {
            "RedrivePolicy": cdk.assertions.Match.object_like({
                "maxReceiveCount": 3,
            })
        },
    )

def test_worker_queue_encrypted():
    template = _make_stacks()
    template.has_resource_properties(
        "AWS::SQS::Queue",
        {"SqsManagedSseEnabled": True},
    )
```

### Step 3: Verify

```bash
make test           # unit tests pass
make synth-dev      # CloudFormation template generates cleanly
make diff-dev       # review what would be created
```

---

## Example 2 — RDS Aurora Cluster (new construct)

When a resource is complex enough to reuse, extract it to a construct first.

### Step 1: Create the construct

`infra/constructs/aurora.py`:

```python
from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_kms as kms,
    RemovalPolicy,
    Duration,
)
from constructs import Construct


class EnterpriseAurora(Construct):
    """Aurora Serverless v2 cluster with encryption, automated backups, deletion protection."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.IVpc,
        kms_key: kms.IKey,
        db_name: str,
        removal_policy: RemovalPolicy = RemovalPolicy.RETAIN,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.cluster = rds.DatabaseCluster(
            self,
            "Cluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_4
            ),
            writer=rds.ClusterInstance.serverless_v2("writer"),
            readers=[
                rds.ClusterInstance.serverless_v2("reader", scale_with_writer=True)
            ],
            serverless_v2_min_capacity=0.5,
            serverless_v2_max_capacity=8,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            default_database_name=db_name,
            storage_encrypted=True,
            storage_encryption_key=kms_key,
            backup=rds.BackupProps(retention=Duration.days(7)),
            deletion_protection=removal_policy == RemovalPolicy.RETAIN,
            removal_policy=removal_policy,
        )
```

### Step 2: Use the construct in a stack

```python
# infra/stacks/platform_stack.py
from infra.constructs.aurora import EnterpriseAurora

class PlatformStack(cdk.Stack):
    def __init__(self, ..., kms_key: kms.IKey, ...) -> None:
        super().__init__(...)

        self.aurora = EnterpriseAurora(
            self,
            "AppDatabase",
            vpc=vpc,
            kms_key=kms_key,
            db_name="appdb",
            removal_policy=cdk.RemovalPolicy.DESTROY
                if env_config.removal_policy_destroy
                else cdk.RemovalPolicy.RETAIN,
        )
```

### Step 3: Pass the KMS key from NetworkingStack

Since the key lives in `NetworkingStack`, expose it and pass it down in `app.py`:

```python
# infra/stacks/networking_stack.py — already exposes:
self.kms_key = EnterpriseKmsKey(...)  # add .key property reference

# app.py
PlatformStack(
    ...,
    kms_key=networking.kms_key.key,  # pass the IKey
)
```

### Step 4: Write the construct test

`tests/unit/test_aurora_construct.py`:

```python
import aws_cdk as cdk
from aws_cdk.assertions import Template
from aws_cdk import aws_ec2 as ec2, aws_kms as kms, RemovalPolicy
from infra.constructs.aurora import EnterpriseAurora


def test_aurora_storage_encrypted():
    app = cdk.App()
    stack = cdk.Stack(app, "TestStack", env=cdk.Environment(account="123456789012", region="us-east-1"))
    vpc = ec2.Vpc(stack, "Vpc")
    key = kms.Key(stack, "Key")

    EnterpriseAurora(stack, "Aurora", vpc=vpc, kms_key=key, db_name="test")

    template = Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::RDS::DBCluster",
        {"StorageEncrypted": True},
    )
```

---

## Example 3 — Global Resource (ACM Certificate)

Resources that must live in `us-east-1` (e.g. ACM certificates for CloudFront) go in `GlobalStack`.

```python
# infra/stacks/global_stack.py
from aws_cdk import aws_certificatemanager as acm, aws_route53 as route53

class GlobalStack(cdk.Stack):
    def __init__(self, ...) -> None:
        super().__init__(...)   # already pins to us-east-1

        # Lookup an existing hosted zone (does not create one)
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name="example.com"
        )

        self.cdn_certificate = acm.Certificate(
            self,
            "CdnCertificate",
            domain_name=f"{env_config.name}.example.com",
            subject_alternative_names=[f"*.{env_config.name}.example.com"],
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        cdk.CfnOutput(
            self,
            "CdnCertArn",
            value=self.cdn_certificate.certificate_arn,
            export_name=f"{id}-CdnCertArn",
        )
```

Then pass it to whatever regional stack needs it:

```python
# app.py
CloudFrontStack(..., certificate=global_stack.cdn_certificate)
```

!!! tip "Rule of thumb"
    If the AWS Console shows the resource only in `us-east-1` regardless of where you create it — it belongs in `GlobalStack`.

---

## Checklist for Any New Resource

- [ ] Resource added to the appropriate stack (global vs regional)
- [ ] `env_config.removal_policy_destroy` respected where applicable
- [ ] Tags applied via `cdk.Tags.of(self)` in the stack constructor (already inherited)
- [ ] `CfnOutput` added for any value other stacks or operators need
- [ ] If reusable → extracted to `infra/constructs/`
- [ ] Unit test added using `aws_cdk.assertions.Template`
- [ ] `make test` passes
- [ ] `make synth-dev` produces a clean template
- [ ] `make diff-dev` reviewed before merging
