# Deployment Guide

Step-by-step instructions to deploy the Stock Evaluation Dashboard to your AWS account.

**Time to deploy:** First deployment takes longer due to CDK bootstrap and Docker image builds. Subsequent deployments are incremental.

## Before You Start

Confirm all items in [PREREQUISITES.md](PREREQUISITES.md) are installed and configured. Verify with:

```bash
python --version    # 3.11+
node --version      # 18+
cdk --version       # 2.x
aws sts get-caller-identity   # Should show your account ID
docker info         # Docker daemon running
```

## Step 1: Clone the Repository

```bash
git clone <repo-url>
cd stock-eval-dashboard
```

## Step 2: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

- **Linux/macOS:** `source .venv/bin/activate`
- **Windows (Git Bash):** `source .venv/Scripts/activate`
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`

You should see `(.venv)` in your terminal prompt.

## Step 3: Install Dependencies

```bash
pip install -e ".[dev,cdk]"
cd infra/cdk && pip install -r requirements.txt && cd ../..
```

**Expected output:** Lists of installed packages ending with `Successfully installed ...`

**Common error:** If `pip install` fails on `numpy`, ensure Docker is running — the Lambda bundling step uses Docker for ARM64 cross-compilation.

## Step 4: Bootstrap CDK (First Time Only)

```bash
cd infra/cdk
cdk bootstrap
cd ../..
```

This creates an S3 bucket and IAM roles in your AWS account that CDK uses to stage deployment assets.

**Expected output:** `Environment aws://<account-id>/us-east-1 bootstrapped.`

**Common error:** `SSM parameter /cdk-bootstrap/hnb659fds/version not found` — means you skipped this step.

## Step 5: Deploy

```bash
cd infra/cdk
cdk deploy --all --require-approval never
cd ../..
```

This deploys three CloudFormation stacks in order:

1. **StockDashboard-prod-Storage** — DynamoDB table
2. **StockDashboard-prod-Api** — Lambda function + API Gateway
3. **StockDashboard-prod-Frontend** — S3 bucket + CloudFront + DNS + SSL certificate

**Expected output:** Three stacks created with outputs including `ApiUrl` and `SiteUrl`.

**Common errors:**
- `Operation not permitted` during bundling — Docker volume mount issue on Windows. Ensure the CDK uses `cp -r` (not `cp -au`) in bundling commands.
- Certificate validation timeout — DNS propagation can take a few minutes. The ACM certificate validates automatically via Route 53.

### Custom Domain

By default, the dashboard deploys to `stocks.jhviv.com`. To use your own domain:

```bash
cd infra/cdk
cdk deploy --all --require-approval never \
  -c domain=stocks.example.com \
  -c hosted_zone=example.com
cd ../..
```

Your Route 53 hosted zone must already exist for `example.com`.

## Step 6: Seed Default Tickers

```bash
python scripts/seed_tickers.py
```

This adds 20 default stock tickers (AAPL, MSFT, GOOGL, etc.) to the DynamoDB table.

**Expected output:**
```
Seeding tickers to table: StockDashboard
Successfully seeded 20 tickers:
  - AAPL
  - AMZN
  ...
```

**Common error:** `NoCredentialsError` — your AWS CLI isn't configured or the session has expired.

## Step 7: Verify

1. **Open the dashboard** at the URL shown in the `SiteUrl` CDK output (e.g., `https://stocks.jhviv.com`)
2. **Select a ticker** from the dropdown — charts should load within a few seconds
3. **Verify all 5 chart tabs** render: Price, Volume, Financial Timeline, Company Info, Balance Sheet

### API Verification

Test the API directly:

```bash
# Replace with your API URL from the ApiUrl CDK output
curl https://<api-id>.execute-api.us-east-1.amazonaws.com/api/tickers
```

**Expected output:** `{"tickers": ["AAPL", "AMZN", ...]}`

## Teardown

To remove all AWS resources:

```bash
cd infra/cdk
cdk destroy --all
cd ../..
```

Note: The DynamoDB table has `RemovalPolicy.RETAIN` and will not be deleted automatically. Delete it manually from the AWS Console if desired.

## Updating

To deploy changes after modifying code:

```bash
cd infra/cdk
cdk deploy --all --require-approval never
cd ../..
```

CDK performs incremental updates — only changed resources are modified.
