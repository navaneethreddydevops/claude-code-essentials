import aws_cdk as cdk
from constructs import Construct
from infra.constructs.vpc import EnterpriseVpc
from infra.constructs.security import EnterpriseKmsKey
from infra.config.accounts import EnvironmentConfig


class NetworkingStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        env_config: EnvironmentConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        cdk.Tags.of(self).add("Stack", "networking")
        for key, value in env_config.tags.items():
            cdk.Tags.of(self).add(key, value)

        self.enterprise_vpc = EnterpriseVpc(
            self,
            "EnterpriseVpc",
            cidr=env_config.vpc_cidr,
            enable_flow_logs=env_config.enable_flow_logs,
        )

        self.kms_key = EnterpriseKmsKey(
            self,
            "NetworkingKey",
            alias=f"{env_config.name}/networking",
        )

        # Expose for cross-stack references
        self.vpc = self.enterprise_vpc.vpc

        cdk.CfnOutput(self, "VpcId", value=self.vpc.vpc_id, export_name=f"{id}-VpcId")
        cdk.CfnOutput(self, "KmsKeyArn", value=self.kms_key.key.key_arn, export_name=f"{id}-KmsKeyArn")
