"""Unit tests for Lambda handler routing and ticker CRUD in LOCAL_MODE."""
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "lambda"))

# Force LOCAL_MODE before importing handler
os.environ["LOCAL_MODE"] = "true"

# Must import after setting LOCAL_MODE
import handler
from tests.conftest import make_api_event


@pytest.fixture(autouse=True)
def reset_local_tickers():
    """Reset in-memory ticker set between tests."""
    from config import config
    handler._local_tickers = set(config.DEFAULT_TICKERS)
    yield


# --- Routing ---


class TestRouting:

    def test_unknown_path_returns_404(self):
        event = make_api_event("GET", "/api/unknown")
        result = handler.main(event, None)
        assert result["statusCode"] == 404

    def test_wrong_method_returns_404(self):
        event = make_api_event("PUT", "/api/tickers")
        result = handler.main(event, None)
        assert result["statusCode"] == 404

    def test_response_has_cors_headers(self):
        event = make_api_event("GET", "/api/tickers")
        result = handler.main(event, None)
        assert result["headers"]["Access-Control-Allow-Origin"] == "*"
        assert result["headers"]["Content-Type"] == "application/json"


# --- GET /api/tickers ---


class TestGetTickers:

    def test_returns_sorted_tickers(self):
        event = make_api_event("GET", "/api/tickers")
        result = handler.main(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        tickers = body["tickers"]
        assert tickers == sorted(tickers)
        assert "AAPL" in tickers

    def test_returns_defaults_when_empty(self):
        handler._local_tickers = set()
        event = make_api_event("GET", "/api/tickers")
        result = handler.main(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert len(body["tickers"]) > 0  # falls back to DEFAULT_TICKERS


# --- POST /api/tickers ---


class TestAddTicker:

    def test_add_valid_ticker(self):
        event = make_api_event("POST", "/api/tickers", body=json.dumps({"ticker": "GOOG"}))
        result = handler.main(event, None)

        assert result["statusCode"] == 201
        body = json.loads(result["body"])
        assert body["success"] is True
        assert body["ticker"] == "GOOG"
        assert "GOOG" in handler._local_tickers

    def test_add_ticker_normalizes_to_uppercase(self):
        event = make_api_event("POST", "/api/tickers", body=json.dumps({"ticker": "msft"}))
        result = handler.main(event, None)

        assert result["statusCode"] == 201
        assert json.loads(result["body"])["ticker"] == "MSFT"

    def test_add_empty_ticker_returns_400(self):
        event = make_api_event("POST", "/api/tickers", body=json.dumps({"ticker": ""}))
        result = handler.main(event, None)
        assert result["statusCode"] == 400

    def test_add_invalid_ticker_format_returns_400(self):
        event = make_api_event("POST", "/api/tickers", body=json.dumps({"ticker": "INVALID!!!"}))
        result = handler.main(event, None)
        assert result["statusCode"] == 400

    def test_add_ticker_invalid_json_returns_400(self):
        event = make_api_event("POST", "/api/tickers", body="not json")
        result = handler.main(event, None)
        assert result["statusCode"] == 400

    def test_add_ticker_with_hyphen(self):
        event = make_api_event("POST", "/api/tickers", body=json.dumps({"ticker": "BRK-B"}))
        result = handler.main(event, None)

        assert result["statusCode"] == 201
        assert json.loads(result["body"])["ticker"] == "BRK-B"


# --- DELETE /api/tickers/{ticker} ---


class TestDeleteTicker:

    def test_delete_existing_ticker(self):
        assert "AAPL" in handler._local_tickers
        event = make_api_event("DELETE", "/api/tickers/AAPL")
        result = handler.main(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["success"] is True
        assert "AAPL" not in handler._local_tickers

    def test_delete_nonexistent_ticker_succeeds(self):
        event = make_api_event("DELETE", "/api/tickers/ZZZZ")
        result = handler.main(event, None)
        assert result["statusCode"] == 200

    def test_delete_invalid_path_returns_400(self):
        event = make_api_event("DELETE", "/api/tickers/")
        result = handler.main(event, None)
        # Path won't match the regex, falls through to 404
        assert result["statusCode"] in (400, 404)


# --- GET /api/stock/{ticker} ---


class TestGetStock:

    @patch.object(handler.provider, "get_stock_data")
    def test_valid_ticker_returns_200(self, mock_get, sample_stock_data):
        mock_get.return_value = sample_stock_data
        event = make_api_event("GET", "/api/stock/AAPL")
        result = handler.main(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["info"]["symbol"] == "AAPL"
        assert "prices" in body
        assert "financials" in body

    @patch.object(handler.provider, "get_stock_data")
    def test_with_year_params(self, mock_get, sample_stock_data):
        mock_get.return_value = sample_stock_data
        event = make_api_event("GET", "/api/stock/AAPL", query={"start_year": "2020", "end_year": "2024"})
        result = handler.main(event, None)

        assert result["statusCode"] == 200
        mock_get.assert_called_once()

    def test_invalid_ticker_chars_returns_400(self):
        event = make_api_event("GET", "/api/stock/$BAD!")
        result = handler.main(event, None)
        assert result["statusCode"] == 400

    def test_invalid_year_params_returns_400(self):
        event = make_api_event("GET", "/api/stock/AAPL", query={"start_year": "abc"})
        result = handler.main(event, None)
        assert result["statusCode"] == 400

    def test_year_range_inverted_returns_400(self):
        event = make_api_event("GET", "/api/stock/AAPL", query={"start_year": "2025", "end_year": "2020"})
        result = handler.main(event, None)
        assert result["statusCode"] == 400

    @patch.object(handler.provider, "get_stock_data", side_effect=ValueError("Not found"))
    def test_ticker_not_found_returns_404(self, mock_get):
        event = make_api_event("GET", "/api/stock/XYZZY")
        result = handler.main(event, None)
        assert result["statusCode"] == 404

    @patch.object(handler.provider, "get_stock_data", side_effect=RuntimeError("API down"))
    def test_provider_error_returns_500(self, mock_get):
        event = make_api_event("GET", "/api/stock/AAPL")
        result = handler.main(event, None)
        assert result["statusCode"] == 500
