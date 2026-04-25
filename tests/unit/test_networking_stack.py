import aws_cdk as cdk
from aws_cdk.assertions import Template
from infra.stacks.networking_stack import NetworkingStack
from infra.config.accounts import ENVIRONMENTS


def _make_stack(env_name: str = "dev") -> Template:
    app = cdk.App()
    env_config = ENVIRONMENTS[env_name]
    stack = NetworkingStack(
        app,
        "TestNetworking",
        env_config=env_config,
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    return Template.from_stack(stack)


def test_vpc_created():
    template = _make_stack()
    template.resource_count_is("AWS::EC2::VPC", 1)


def test_subnets_created():
    template = _make_stack()
    # 3 AZs × 3 subnet types = 9 subnets
    template.resource_count_is("AWS::EC2::Subnet", 9)


def test_nat_gateway_created():
    template = _make_stack()
    template.resource_count_is("AWS::EC2::NatGateway", 1)


def test_kms_key_has_rotation():
    template = _make_stack("staging")
    template.has_resource_properties(
        "AWS::KMS::Key",
        {"EnableKeyRotation": True},
    )


def test_tags_applied():
    template = _make_stack()
    template.has_resource_properties(
        "AWS::EC2::VPC",
        {
            "Tags": cdk.assertions.Match.array_with([
                {"Key": "Environment", "Value": "dev"},
                {"Key": "ManagedBy", "Value": "CDK"},
            ])
        },
    )
