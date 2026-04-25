from aws_cdk import (
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_iam as iam,
    RemovalPolicy,
)
from constructs import Construct


class EnterpriseVpc(Construct):
    """
    Enterprise-grade VPC with public/private/isolated subnets,
    NAT gateways, and optional VPC flow logs.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        cidr: str,
        enable_flow_logs: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            ip_addresses=ec2.IpAddresses.cidr(cidr),
            max_azs=3,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        if enable_flow_logs:
            flow_log_group = logs.LogGroup(
                self,
                "FlowLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=RemovalPolicy.DESTROY,
            )
            flow_log_role = iam.Role(
                self,
                "FlowLogRole",
                assumed_by=iam.ServicePrincipal("vpc-flow-logs.amazonaws.com"),
            )
            flow_log_group.grant_write(flow_log_role)

            ec2.FlowLog(
                self,
                "FlowLog",
                resource_type=ec2.FlowLogResourceType.from_vpc(self.vpc),
                destination=ec2.FlowLogDestination.to_cloud_watch_logs(
                    flow_log_group, flow_log_role
                ),
            )
