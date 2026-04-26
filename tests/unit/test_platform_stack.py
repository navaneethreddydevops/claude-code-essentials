import aws_cdk as cdk
from aws_cdk.assertions import Template

from infra.config.accounts import ENVIRONMENTS
from infra.stacks.global_stack import GlobalStack
from infra.stacks.networking_stack import NetworkingStack
from infra.stacks.platform_stack import PlatformStack


def _make_stacks(env_name: str = "dev"):
    app = cdk.App()
    env_config = ENVIRONMENTS[env_name]
    regional_env = cdk.Environment(account="123456789012", region="us-east-1")

    global_stack = GlobalStack(app, "TestGlobal", env_config=env_config)
    networking = NetworkingStack(app, "TestNetworking", env_config=env_config, env=regional_env)
    platform = PlatformStack(
        app,
        "TestPlatform",
        env_config=env_config,
        vpc=networking.vpc,
        app_role=global_stack.app_role,
        env=regional_env,
    )
    return Template.from_stack(platform)


def test_s3_bucket_encrypted():
    template = _make_stacks()
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {"BucketEncryption": cdk.assertions.Match.object_like({})},
    )


def test_s3_bucket_blocks_public_access():
    template = _make_stacks()
    template.has_resource_properties(
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


def test_s3_bucket_versioned():
    template = _make_stacks()
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {"VersioningConfiguration": {"Status": "Enabled"}},
    )
