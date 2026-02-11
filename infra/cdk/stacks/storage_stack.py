"""Storage stack: DynamoDB table for ticker persistence."""
from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


class StorageStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # On-demand billing stays within free tier (25 RCU/WCU)
        self.table = dynamodb.Table(
            self,
            "StockDashboardTable",
            table_name="StockDashboard",
            partition_key=dynamodb.Attribute(
                name="PK",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,  # Don't delete data on stack destroy
            point_in_time_recovery=False,  # Not needed for this use case
        )
