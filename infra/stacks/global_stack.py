"""
Global stack — always deployed to us-east-1 regardless of the account's primary region.

Put here:
  - IAM roles & policies (IAM is global but the API lives in us-east-1)
  - Route53 hosted zones
  - ACM certificates used by CloudFront (must be us-east-1)
  - WAF WebACLs attached to CloudFront (must be us-east-1)
"""

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from constructs import Construct

from infra.config.accounts import EnvironmentConfig

GLOBAL_REGION = "us-east-1"


class GlobalStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        env_config: EnvironmentConfig,
        **kwargs,
    ) -> None:
        # Force us-east-1 regardless of the env's primary region
        global_env = cdk.Environment(
            account=env_config.account.account_id,
            region=GLOBAL_REGION,
        )
        super().__init__(scope, id, env=global_env, **kwargs)

        cdk.Tags.of(self).add("Stack", "global")
        cdk.Tags.of(self).add("Region", "global")
        for key, value in env_config.tags.items():
            cdk.Tags.of(self).add(key, value)

        # ── IAM: application execution role ──────────────────────────────
        self.app_role = iam.Role(
            self,
            "AppRole",
            role_name=f"{env_config.name}-app-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
            description=f"Application execution role – {env_config.name}",
        )

        # ── IAM: CI/CD deploy role (assumed by GitHub Actions via OIDC) ──
        github_provider = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
            self,
            "GitHubOidcProvider",
            open_id_connect_provider_arn=f"arn:aws:iam::{env_config.account.account_id}:oidc-provider/token.actions.githubusercontent.com",
        )

        self.deploy_role = iam.Role(
            self,
            "CiDeployRole",
            role_name=f"{env_config.name}-ci-deploy-role",
            assumed_by=iam.WebIdentityPrincipal(
                github_provider.open_id_connect_provider_arn,
                conditions={
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": "repo:*:ref:refs/heads/main"
                    }
                },
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
            ],
            description=f"GitHub Actions OIDC deploy role – {env_config.name}",
        )

        cdk.CfnOutput(
            self, "AppRoleArn", value=self.app_role.role_arn, export_name=f"{id}-AppRoleArn"
        )
        cdk.CfnOutput(
            self,
            "DeployRoleArn",
            value=self.deploy_role.role_arn,
            export_name=f"{id}-DeployRoleArn",
        )
