# Deployment Log — 2026-02-16

First deployment of the Stock Evaluation Dashboard to AWS.

## Environment

- **OS:** Windows 11
- **CDK CLI:** 2.1106.0
- **Python:** 3.13.12
- **AWS Region:** us-east-1
- **Account:** 153765355464

## Issues Encountered

### 1. `lambda_.BundlingOptions` removed in newer CDK

**Symptom:** `cdk synth` failed with `AttributeError: module 'aws_cdk.aws_lambda' has no attribute 'BundlingOptions'`.

**Cause:** `BundlingOptions` was moved from `aws_cdk.aws_lambda` to the core `aws_cdk` module in a newer version of `aws-cdk-lib`.

**Fix:** Changed import from `lambda_.BundlingOptions(...)` to `BundlingOptions(...)` imported from `aws_cdk`.

**File:** `infra/cdk/stacks/api_stack.py`

---

### 2. numpy fails to build from source in SAM Docker image

**Symptom:** `cdk synth` bundling step failed. Docker container tried to compile numpy 2.4.2 from source inside the SAM build image (`public.ecr.aws/sam/build-python3.11`), but GCC 7.3.1 in that image is too old.

**Cause:** The Lambda architecture is ARM_64, but the bundling image was x86_64. pip couldn't find a compatible prebuilt wheel for the container's platform, so it fell back to building from source.

**Fix:** Added `--platform manylinux2014_aarch64 --only-binary=:all:` to the pip install command in the bundling options, plus `platform="linux/arm64"` on the `BundlingOptions`. This forces pip to download prebuilt ARM64 wheels instead of compiling.

**File:** `infra/cdk/stacks/api_stack.py`

---

### 3. `cp -au` fails on Windows Docker volume mounts

**Symptom:** Bundling succeeded (pip install worked) but failed at the final `cp -au . /asset-output` step with `Operation not permitted`.

**Cause:** The `-a` flag (archive/preserve timestamps and ownership) doesn't work on Docker volume mounts from Windows hosts due to filesystem permission differences.

**Fix:** Changed `cp -au` to `cp -r` (recursive copy without preserving ownership).

**File:** `infra/cdk/stacks/api_stack.py`

---

### 4. CDK not bootstrapped

**Symptom:** `cdk deploy` failed with `SSM parameter /cdk-bootstrap/hnb659fds/version not found`.

**Cause:** First-time CDK deployment to this account/region. CDK requires a one-time bootstrap step that creates an S3 bucket, ECR repo, and IAM roles for asset deployment.

**Fix:** Ran `cdk bootstrap` before deploying.

---

### 5. IAM approval needed in non-interactive terminal

**Symptom:** `cdk deploy --require-approval broadening` hung and then failed with `terminal (TTY) is not attached so we are unable to get a confirmation`.

**Cause:** The API stack creates IAM roles (Lambda execution role with DynamoDB permissions), which requires interactive approval by default. The deploy was running in a non-interactive background process.

**Fix:** Re-ran with `--require-approval never` after verifying the IAM changes were expected (Lambda service role + DynamoDB read/write on StockDashboard table).

---

### 6. config.js overwritten by frontend deploy (data not loading)

**Symptom:** Dashboard loaded but showed "failed to fetch" for all data. The S3 config.js contained `http://localhost:3000` instead of the real API Gateway URL.

**Cause:** Two `BucketDeployment` constructs in the FrontendStack:
1. `DeployFrontend` — uploads all files from `src/frontend/`, including `js/config.js` (with localhost URL)
2. `DeployConfig` — writes a generated `js/config.js` with the real API URL

CloudFormation executed them in parallel, and `DeployFrontend` overwrote the config after `DeployConfig` had already set the correct URL.

**Fix:**
- Added `deploy_config.node.add_dependency(deploy_frontend)` to enforce ordering
- Added `prune=False` on `DeployConfig` so it doesn't delete other files

**File:** `infra/cdk/stacks/frontend_stack.py`

---

## Final State

All 3 stacks deployed successfully:

| Stack | Resources |
|-------|-----------|
| `StockDashboard-prod-Storage` | DynamoDB table |
| `StockDashboard-prod-Api` | Lambda (ARM64, Python 3.11) + HTTP API Gateway (4 routes) |
| `StockDashboard-prod-Frontend` | S3 bucket + CloudFront + ACM certificate + Route 53 DNS |

**Live URL:** https://stocks.jhviv.com
**API URL:** https://kyve3jq529.execute-api.us-east-1.amazonaws.com
**20 tickers seeded** via `scripts/seed_tickers.py`
