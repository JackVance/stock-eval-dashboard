.PHONY: install install-dev install-cdk lint test deploy deploy-dev local-api seed clean destroy help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -e ".[dev]"

install-cdk:  ## Install CDK dependencies
	pip install -e ".[cdk]"
	cd infra/cdk && pip install -r requirements.txt

lint:  ## Run linting and type checking
	ruff check src/ tests/
	ruff format --check src/ tests/
	mypy src/lambda/

test:  ## Run all tests
	pytest tests/ -v --cov=src/lambda --cov-report=term-missing

deploy:  ## Deploy all stacks to AWS (prod)
	cd infra/cdk && cdk deploy --all --require-approval never

deploy-dev:  ## Deploy all stacks to AWS (dev)
	cd infra/cdk && cdk deploy --all --require-approval never -c env=dev

local-api:  ## Run Lambda locally for testing
	python scripts/local_lambda.py

seed:  ## Seed default tickers to DynamoDB
	python scripts/seed_tickers.py

build-lambda:  ## Build Lambda container image locally
	docker build -t stock-dashboard-lambda -f docker/Dockerfile .

clean:  ## Remove build artifacts
	rm -rf .pytest_cache __pycache__ .ruff_cache .mypy_cache
	rm -rf src/*.egg-info build/ dist/
	rm -rf infra/cdk/cdk.out
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

destroy:  ## Tear down all AWS resources
	cd infra/cdk && cdk destroy --all
