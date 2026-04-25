# Adding a New Construct

Constructs are reusable building blocks. Create one when a pattern appears in more than one stack, or when a resource group is complex enough to deserve its own unit tests.

## Step 1: Create the construct file

`infra/constructs/lambda_function.py`:

```python
from aws_cdk import (
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
    aws_kms as kms,
    Duration,
    RemovalPolicy,
)
from constructs import Construct


class EnterpriseLambda(Construct):
    """
    Lambda function with opinionated enterprise defaults:
    - CloudWatch log group with 3-month retention
    - X-Ray tracing enabled
    - Reserved concurrency configurable
    - Dead-letter queue wired if provided
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        code: lambda_.Code,
        handler: str,
        runtime: lambda_.Runtime = lambda_.Runtime.PYTHON_3_12,
        environment: dict | None = None,
        reserved_concurrent_executions: int | None = None,
        timeout: Duration = Duration.seconds(30),
        role: iam.IRole | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        log_group = logs.LogGroup(
            self,
            "LogGroup",
            retention=logs.RetentionDays.THREE_MONTHS,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.function = lambda_.Function(
            self,
            "Function",
            code=code,
            handler=handler,
            runtime=runtime,
            environment=environment or {},
            timeout=timeout,
            tracing=lambda_.Tracing.ACTIVE,
            reserved_concurrent_executions=reserved_concurrent_executions,
            role=role,
            log_group=log_group,
        )
```

## Step 2: Use it in a stack

```python
# infra/stacks/platform_stack.py
from aws_cdk import aws_lambda as lambda_
from infra.constructs.lambda_function import EnterpriseLambda


class PlatformStack(cdk.Stack):
    def __init__(self, ...) -> None:
        super().__init__(...)

        self.processor = EnterpriseLambda(
            self,
            "Processor",
            code=lambda_.Code.from_asset("src/processor"),
            handler="index.handler",
            environment={
                "QUEUE_URL": self.worker_queue.queue_url,
                "ENV": env_config.name,
            },
            role=app_role,
        )
```

## Step 3: Unit test the construct in isolation

`tests/unit/test_lambda_construct.py`:

```python
import aws_cdk as cdk
from aws_cdk import aws_lambda as lambda_
from aws_cdk.assertions import Template
from infra.constructs.lambda_function import EnterpriseLambda


def _make_template() -> Template:
    app = cdk.App()
    stack = cdk.Stack(app, "Test")
    EnterpriseLambda(
        stack,
        "TestFn",
        code=lambda_.Code.from_inline("def handler(e, c): pass"),
        handler="index.handler",
    )
    return Template.from_stack(stack)


def test_tracing_active():
    _make_template().has_resource_properties(
        "AWS::Lambda::Function",
        {"TracingConfig": {"Mode": "Active"}},
    )


def test_log_group_retention():
    _make_template().has_resource_properties(
        "AWS::Logs::LogGroup",
        {"RetentionInDays": 90},
    )
```

## Construct Design Rules

- **Expose outputs as attributes** (`self.function`, `self.queue`, etc.) — callers should never reach into the construct's internal construct tree.
- **Accept `IRole`, `IVpc`, `IKey`** (interfaces) rather than concrete classes — keeps tests lightweight.
- **Never import from stacks** — constructs sit below stacks in the hierarchy; importing upward creates circular dependencies.
- **Props over kwargs** for more than 3 optional parameters — define a dataclass or `@dataclass` props object for clarity.
