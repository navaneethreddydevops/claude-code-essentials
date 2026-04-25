import aws_cdk as cdk
from aws_cdk.assertions import Template
from infra.stacks.global_stack import GlobalStack
from infra.config.accounts import ENVIRONMENTS


def _make_stack(env_name: str = "dev") -> Template:
    app = cdk.App()
    stack = GlobalStack(app, "TestGlobal", env_config=ENVIRONMENTS[env_name])
    return Template.from_stack(stack)


def test_global_stack_region_is_us_east_1():
    app = cdk.App()
    stack = GlobalStack(app, "TestGlobal", env_config=ENVIRONMENTS["dev"])
    assert stack.region == "us-east-1"


def test_app_role_created():
    template = _make_stack()
    template.has_resource_properties(
        "AWS::IAM::Role",
        {"AssumedRolePolicyDocument": cdk.assertions.Match.object_like({
            "Statement": cdk.assertions.Match.array_with([
                cdk.assertions.Match.object_like({
                    "Principal": {"Service": "lambda.amazonaws.com"}
                })
            ])
        })},
    )


def test_deploy_role_created():
    template = _make_stack()
    # OIDC web identity role for GitHub Actions
    template.has_resource_properties(
        "AWS::IAM::Role",
        {"AssumedRolePolicyDocument": cdk.assertions.Match.object_like({
            "Statement": cdk.assertions.Match.array_with([
                cdk.assertions.Match.object_like({
                    "Principal": {"Federated": cdk.assertions.Match.any_value()}
                })
            ])
        })},
    )


def test_tags_applied():
    template = _make_stack()
    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "Tags": cdk.assertions.Match.array_with([
                {"Key": "Environment", "Value": "dev"},
            ])
        },
    )
