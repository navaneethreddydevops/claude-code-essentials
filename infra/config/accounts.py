"""
Account and environment configuration for multi-account deployments.
Add your AWS account IDs and regions here, or override via environment variables.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AccountConfig:
    account_id: str
    region: str
    profile: Optional[str] = None


@dataclass
class EnvironmentConfig:
    name: str
    account: AccountConfig
    vpc_cidr: str
    enable_flow_logs: bool = True
    enable_cloudtrail: bool = True
    removal_policy_destroy: bool = False  # True only for dev/sandbox
    tags: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Define your accounts here. Override with env vars in CI/CD.
# ---------------------------------------------------------------------------

ACCOUNTS = {
    "dev": AccountConfig(
        account_id=os.getenv("DEV_ACCOUNT_ID", "111111111111"),
        region=os.getenv("DEV_REGION", "us-east-1"),
        profile=os.getenv("DEV_PROFILE", "dev"),
    ),
    "staging": AccountConfig(
        account_id=os.getenv("STAGING_ACCOUNT_ID", "222222222222"),
        region=os.getenv("STAGING_REGION", "us-east-1"),
        profile=os.getenv("STAGING_PROFILE", "staging"),
    ),
    "prod": AccountConfig(
        account_id=os.getenv("PROD_ACCOUNT_ID", "333333333333"),
        region=os.getenv("PROD_REGION", "us-east-1"),
        profile=os.getenv("PROD_PROFILE", "prod"),
    ),
}

ENVIRONMENTS: dict[str, EnvironmentConfig] = {
    "dev": EnvironmentConfig(
        name="dev",
        account=ACCOUNTS["dev"],
        vpc_cidr="10.0.0.0/16",
        enable_flow_logs=False,
        enable_cloudtrail=False,
        removal_policy_destroy=True,
        tags={"Environment": "dev", "ManagedBy": "CDK", "CostCenter": "engineering"},
    ),
    "staging": EnvironmentConfig(
        name="staging",
        account=ACCOUNTS["staging"],
        vpc_cidr="10.1.0.0/16",
        tags={"Environment": "staging", "ManagedBy": "CDK", "CostCenter": "engineering"},
    ),
    "prod": EnvironmentConfig(
        name="prod",
        account=ACCOUNTS["prod"],
        vpc_cidr="10.2.0.0/16",
        tags={"Environment": "prod", "ManagedBy": "CDK", "CostCenter": "engineering"},
    ),
}
