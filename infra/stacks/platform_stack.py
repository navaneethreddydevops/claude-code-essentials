"""
Platform stack — regional resources (compute, storage, etc.).
Receives cross-stack references from GlobalStack (IAM) and NetworkingStack (VPC).
"""
import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2, aws_s3 as s3, aws_iam as iam
from constructs import Construct
from infra.config.accounts import EnvironmentConfig


class PlatformStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,
        app_role: iam.IRole,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        cdk.Tags.of(self).add("Stack", "platform")
        for key, value in env_config.tags.items():
            cdk.Tags.of(self).add(key, value)

        removal_policy = (
            cdk.RemovalPolicy.DESTROY
            if env_config.removal_policy_destroy
            else cdk.RemovalPolicy.RETAIN
        )

        # Encrypted S3 bucket — enterprise baseline
        self.artifacts_bucket = s3.Bucket(
            self,
            "ArtifactsBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            removal_policy=removal_policy,
            auto_delete_objects=env_config.removal_policy_destroy,
            server_access_logs_prefix="access-logs/",
        )

        # Grant the globally-defined app role access to the regional bucket
        self.artifacts_bucket.grant_read_write(app_role)

        cdk.CfnOutput(
            self,
            "ArtifactsBucketName",
            value=self.artifacts_bucket.bucket_name,
            export_name=f"{id}-ArtifactsBucket",
        )
