# Prerequisites

Everything you need before deploying the Stock Evaluation Dashboard.

## Operator Prerequisites

These tools must be installed on the machine running the deployment.

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| **Python** | 3.11+ | Lambda runtime, CDK, scripts | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ | AWS CDK CLI | [nodejs.org](https://nodejs.org/) |
| **AWS CDK CLI** | 2.x | Infrastructure deployment | `npm install -g aws-cdk` |
| **AWS CLI** | 2.x | Credential management, seeding | [AWS CLI install](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| **Docker** | 20+ | Lambda code bundling (ARM64 cross-compile) | [docker.com](https://www.docker.com/get-started/) |
| **Git** | 2.x | Clone the repository | [git-scm.com](https://git-scm.com/) |

## AWS Account Configuration

1. **AWS account** with permissions to create: Lambda, API Gateway, DynamoDB, S3, CloudFront, Route 53, ACM, IAM roles
2. **AWS CLI configured** with credentials:
   ```bash
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output format (json)
   ```
3. **Route 53 hosted zone** for your domain (required for custom domain + HTTPS)

## Optional

- **Custom domain** — defaults to `stocks.jhviv.com`. Override with CDK context flags:
  ```bash
  cdk deploy --all -c domain=stocks.example.com -c hosted_zone=example.com
  ```
- **Make** — for running shortcut commands (`make deploy`, `make test`). All commands can be run manually without Make.

## Runtime Prerequisites

The deployed application has no additional runtime prerequisites. All dependencies are bundled into the Lambda deployment package. The frontend is static HTML/CSS/JS served from S3 via CloudFront — no server required.

**External services used at runtime** (no API keys needed):
- [Yahoo Finance](https://finance.yahoo.com/) via the `yfinance` Python library (stock prices, company info)
- [SEC EDGAR](https://www.sec.gov/edgar) public API (historical financial statements, 10+ years)
