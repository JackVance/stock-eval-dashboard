#!/usr/bin/env python3
"""CDK app entry point for Stock Evaluation Dashboard."""
import os

import aws_cdk as cdk

from stacks.api_stack import ApiStack
from stacks.frontend_stack import FrontendStack
from stacks.storage_stack import StorageStack

app = cdk.App()

env_name = app.node.try_get_context("env") or "prod"

common_tags = {
    "project": "stock-dashboard",
    "environment": env_name,
    "managed-by": "cdk",
}

aws_env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

storage_stack = StorageStack(
    app,
    f"StockDashboard-{env_name}-Storage",
    env=aws_env,
)

api_stack = ApiStack(
    app,
    f"StockDashboard-{env_name}-Api",
    table=storage_stack.table,
    env=aws_env,
)

# Override: cdk deploy -c domain=custom.example.com -c hosted_zone=example.com
domain_name = app.node.try_get_context("domain") or "stocks.jhviv.com"
hosted_zone_domain = app.node.try_get_context("hosted_zone") or "jhviv.com"

frontend_stack = FrontendStack(
    app,
    f"StockDashboard-{env_name}-Frontend",
    api_url=api_stack.api_url,
    domain_name=domain_name,
    hosted_zone_domain=hosted_zone_domain,
    env=aws_env,
)

for stack in [storage_stack, api_stack, frontend_stack]:
    for key, value in common_tags.items():
        cdk.Tags.of(stack).add(key, value)

app.synth()
