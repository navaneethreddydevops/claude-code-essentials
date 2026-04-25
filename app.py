#!/usr/bin/env python3
"""
Enterprise CDK App — multi-account entry point.

Stack deployment model:
  GlobalStack      → always us-east-1  (IAM, Route53, ACM-for-CF, WAF-for-CF)
  NetworkingStack  → env's primary region
  PlatformStack    → env's primary region

Usage:
  CDK_ENV=dev     cdk deploy --all --profile dev
  CDK_ENV=staging cdk deploy --all --profile staging
  CDK_ENV=prod    cdk deploy --all --profile prod
  CDK_ENV=dev     cdk synth
"""
import os
import aws_cdk as cdk
from infra.config.accounts import ENVIRONMENTS
from infra.stacks.global_stack import GlobalStack
from infra.stacks.networking_stack import NetworkingStack
from infra.stacks.platform_stack import PlatformStack

app = cdk.App()

env_name = os.getenv("CDK_ENV", "dev")
if env_name not in ENVIRONMENTS:
    raise ValueError(f"Unknown CDK_ENV '{env_name}'. Choose from: {list(ENVIRONMENTS.keys())}")

env_config = ENVIRONMENTS[env_name]
prefix = env_name.capitalize()

# Regional CDK environment (networking, compute, storage)
regional_env = cdk.Environment(
    account=env_config.account.account_id,
    region=env_config.account.region,
)

# ── Global stack (us-east-1) ──────────────────────────────────────────────
# GlobalStack pins itself to us-east-1 internally; do NOT pass env= here.
global_stack = GlobalStack(
    app,
    f"{prefix}Global",
    env_config=env_config,
    description=f"Global resources (IAM, Route53, ACM) – {env_name}",
)

# ── Regional stacks ───────────────────────────────────────────────────────
networking = NetworkingStack(
    app,
    f"{prefix}Networking",
    env_config=env_config,
    env=regional_env,
    description=f"Networking layer – {env_name} – {env_config.account.region}",
)

PlatformStack(
    app,
    f"{prefix}Platform",
    env_config=env_config,
    vpc=networking.vpc,
    app_role=global_stack.app_role,
    env=regional_env,
    description=f"Platform layer – {env_name} – {env_config.account.region}",
)

app.synth()
