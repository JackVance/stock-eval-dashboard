"""Integration tests: handler ticker CRUD against mocked DynamoDB via moto."""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "lambda"))

from tests.conftest import make_api_event


@pytest.fixture
def dynamodb_env(monkeypatch):
    """Set up moto DynamoDB and patch handler to use it."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("LOCAL_MODE", "false")
    monkeypatch.setenv("TABLE_NAME", "StockDashboard")


@pytest.fixture
def handler_with_dynamo(dynamodb_env):
    """Import handler with a real moto DynamoDB table."""
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="us-east-1")
        table = resource.create_table(
            TableName="StockDashboard",
            KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()

        # Re-import handler with fresh module state pointing at moto table
        import importlib
        import handler as handler_mod

        handler_mod.LOCAL_MODE = False
        handler_mod.table = table

        yield handler_mod

        # Restore LOCAL_MODE so other tests aren't affected
        handler_mod.LOCAL_MODE = True


class TestTickerCRUDWithDynamoDB:

    def test_get_tickers_empty_table_returns_defaults(self, handler_with_dynamo):
        event = make_api_event("GET", "/api/tickers")
        result = handler_with_dynamo.main(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert len(body["tickers"]) > 0  # defaults

    def test_add_then_get_ticker(self, handler_with_dynamo):
        # Add
        add_event = make_api_event("POST", "/api/tickers", body=json.dumps({"ticker": "GOOG"}))
        add_result = handler_with_dynamo.main(add_event, None)
        assert add_result["statusCode"] == 201

        # Get — should include GOOG
        get_event = make_api_event("GET", "/api/tickers")
        get_result = handler_with_dynamo.main(get_event, None)
        body = json.loads(get_result["body"])
        assert "GOOG" in body["tickers"]

    def test_add_and_delete_ticker(self, handler_with_dynamo):
        # Add a ticker NOT in DEFAULT_TICKERS
        add_event = make_api_event("POST", "/api/tickers", body=json.dumps({"ticker": "PLTR"}))
        handler_with_dynamo.main(add_event, None)

        # Verify it's there
        get_event = make_api_event("GET", "/api/tickers")
        get_result = handler_with_dynamo.main(get_event, None)
        assert "PLTR" in json.loads(get_result["body"])["tickers"]

        # Delete
        del_event = make_api_event("DELETE", "/api/tickers/PLTR")
        del_result = handler_with_dynamo.main(del_event, None)
        assert del_result["statusCode"] == 200

        # Verify removed
        get_result = handler_with_dynamo.main(get_event, None)
        body = json.loads(get_result["body"])
        assert "PLTR" not in body["tickers"]

    def test_add_multiple_tickers_persists_all(self, handler_with_dynamo):
        for ticker in ["GOOG", "AMZN", "NFLX"]:
            event = make_api_event("POST", "/api/tickers", body=json.dumps({"ticker": ticker}))
            handler_with_dynamo.main(event, None)

        get_event = make_api_event("GET", "/api/tickers")
        get_result = handler_with_dynamo.main(get_event, None)
        body = json.loads(get_result["body"])
        for ticker in ["GOOG", "AMZN", "NFLX"]:
            assert ticker in body["tickers"]

    def test_delete_nonexistent_ticker_succeeds(self, handler_with_dynamo):
        # Seed at least one ticker so the item exists
        add_event = make_api_event("POST", "/api/tickers", body=json.dumps({"ticker": "AAPL"}))
        handler_with_dynamo.main(add_event, None)

        del_event = make_api_event("DELETE", "/api/tickers/ZZZZ")
        result = handler_with_dynamo.main(del_event, None)
        assert result["statusCode"] == 200
