"""Frontend stack: S3 bucket, CloudFront distribution, Route 53 DNS."""
import hashlib
from pathlib import Path

from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as targets
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from constructs import Construct


class FrontendStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api_url: str,
        domain_name: str = "stocks.jhviv.com",
        hosted_zone_domain: str = "jhviv.com",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        hosted_zone = route53.HostedZone.from_lookup(
            self,
            "HostedZone",
            domain_name=hosted_zone_domain,
        )

        # Must be us-east-1 for CloudFront; DNS validation auto-creates Route 53 records
        certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=domain_name,
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # Private bucket — only accessible via CloudFront OAC
        self.bucket = s3.Bucket(
            self,
            "FrontendBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,  # Allow cleanup for dev
            auto_delete_objects=True,  # Clean up objects on stack destroy
        )

        oac = cloudfront.S3OriginAccessControl(
            self,
            "OAC",
            signing=cloudfront.Signing.SIGV4_ALWAYS,
        )

        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(
                    self.bucket,
                    origin_access_control=oac,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",  # SPA routing
                ),
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,  # US, Canada, Europe only
            domain_names=[domain_name],
            certificate=certificate,
        )

        route53.ARecord(
            self,
            "AliasRecord",
            zone=hosted_zone,
            record_name=domain_name,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(self.distribution)
            ),
        )

        frontend_path = Path(__file__).parent.parent.parent.parent / "src" / "frontend"

        deploy_frontend = s3deploy.BucketDeployment(
            self,
            "DeployFrontend",
            sources=[s3deploy.Source.asset(str(frontend_path))],
            destination_bucket=self.bucket,
            distribution=self.distribution,
            distribution_paths=["/*"],  # Invalidate cache on deploy
        )

        # Inject runtime API URL so frontend knows where to call.
        # Must run AFTER DeployFrontend to overwrite the local dev config.js.
        # The frontend-folder hash in the comment ensures CDK detects a change
        # to this BucketDeployment whenever DeployFrontend's source changes —
        # otherwise CDK skips re-running this step and the dev localhost
        # config.js (uploaded by DeployFrontend) stays live on S3.
        frontend_hasher = hashlib.sha256()
        for fp in sorted(frontend_path.rglob("*")):
            if fp.is_file():
                frontend_hasher.update(fp.read_bytes())
        frontend_hash = frontend_hasher.hexdigest()[:12]

        config_content = (
            f"// build {frontend_hash}\n"
            f"window.CONFIG = {{ API_URL: '{api_url}' }};"
        )
        deploy_config = s3deploy.BucketDeployment(
            self,
            "DeployConfig",
            sources=[
                s3deploy.Source.data("js/config.js", config_content),
            ],
            destination_bucket=self.bucket,
            distribution=self.distribution,
            distribution_paths=["/js/config.js"],
            prune=False,  # Don't delete other files when deploying config only
        )
        deploy_config.node.add_dependency(deploy_frontend)

        CfnOutput(
            self,
            "SiteUrl",
            value=f"https://{domain_name}",
            description="Dashboard URL",
        )

        CfnOutput(
            self,
            "DistributionUrl",
            value=f"https://{self.distribution.distribution_domain_name}",
            description="CloudFront distribution URL (direct)",
        )

        CfnOutput(
            self,
            "BucketName",
            value=self.bucket.bucket_name,
            description="S3 bucket name for frontend files",
        )
