"""API stack: Lambda function and API Gateway HTTP API."""
import os
from pathlib import Path

from aws_cdk import BundlingOptions, CfnOutput, Duration, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_integrations as integrations
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as lambda_
from constructs import Construct


class ApiStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        table: dynamodb.Table,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_code_path = Path(__file__).parent.parent.parent.parent / "src" / "lambda"

        # Zip deployment for MVP; switch to container image if deps grow
        self.function = lambda_.Function(
            self,
            "StockApiFunction",
            function_name="stock-dashboard-api",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.main",
            code=lambda_.Code.from_asset(
                str(lambda_code_path),
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    platform="linux/arm64",
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements.txt "
                        "--platform manylinux2014_aarch64 "
                        "--only-binary=:all: "
                        "-t /asset-output "
                        "&& cp -r . /asset-output",
                    ],
                ),
            ),
            memory_size=512,  # pandas needs headroom
            timeout=Duration.seconds(30),  # External API calls can be slow
            architecture=lambda_.Architecture.ARM_64,  # 20% cheaper
            environment={
                "TABLE_NAME": table.table_name,
                "POWERTOOLS_SERVICE_NAME": "stock-dashboard",
                "LOG_LEVEL": "INFO",
            },
            reserved_concurrent_executions=10,  # Cost protection
        )

        table.grant_read_write_data(self.function)

        # HTTP API — 70% cheaper than REST API, 1M free requests/mo
        self.api = apigwv2.HttpApi(
            self,
            "StockApi",
            api_name="stock-dashboard-api",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],  # TODO: restrict to CloudFront domain
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                    apigwv2.CorsHttpMethod.DELETE,
                    apigwv2.CorsHttpMethod.OPTIONS,
                ],
                allow_headers=["Content-Type", "Authorization"],
                max_age=Duration.hours(1),
            ),
        )

        integration = integrations.HttpLambdaIntegration(
            "LambdaIntegration",
            self.function,
        )

        self.api.add_routes(
            path="/api/stock/{ticker}",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration,
        )
        self.api.add_routes(
            path="/api/tickers",
            methods=[apigwv2.HttpMethod.GET, apigwv2.HttpMethod.POST],
            integration=integration,
        )
        self.api.add_routes(
            path="/api/tickers/{ticker}",
            methods=[apigwv2.HttpMethod.DELETE],
            integration=integration,
        )

        self.api_url = self.api.url or ""

        CfnOutput(
            self,
            "ApiUrl",
            value=self.api_url,
            description="HTTP API endpoint URL",
        )
