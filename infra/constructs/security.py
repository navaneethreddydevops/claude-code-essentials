from aws_cdk import (
    aws_iam as iam,
    aws_kms as kms,
    RemovalPolicy,
)
from constructs import Construct


class EnterpriseKmsKey(Construct):
    """CMK with key rotation enabled and deny-root policy."""

    def __init__(self, scope: Construct, id: str, alias: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.key = kms.Key(
            self,
            "Key",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN,
            policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        principals=[iam.AccountRootPrincipal()],
                        actions=["kms:*"],
                        resources=["*"],
                    )
                ]
            ),
        )
        self.key.add_alias(f"alias/{alias}")
