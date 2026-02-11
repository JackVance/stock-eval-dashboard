"""Routes HTTP API Gateway events to stock data handlers."""
import json
import logging
import os
import re
from datetime import date
from typing import Any

from config import config
from providers import CompositeProvider

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

LOCAL_MODE = os.environ.get("LOCAL_MODE", "false").lower() == "true"
_local_tickers: set[str] = set(config.DEFAULT_TICKERS)

if LOCAL_MODE:
    logger.info("Running in LOCAL_MODE - using in-memory ticker storage")
    table = None
else:
    import boto3
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(config.TABLE_NAME)

provider = CompositeProvider()


def main(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda entry point."""
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        http = event.get("requestContext", {}).get("http", {})
        method = http.get("method", "GET")
        path = http.get("path", "")

        if path.startswith("/api/stock/") and method == "GET":
            return handle_get_stock(event)
        elif path == "/api/tickers" and method == "GET":
            return handle_get_tickers(event)
        elif path == "/api/tickers" and method == "POST":
            return handle_add_ticker(event)
        elif path.startswith("/api/tickers/") and method == "DELETE":
            return handle_delete_ticker(event)
        else:
            return response(404, {"error": "Not found", "path": path})

    except Exception as e:
        logger.exception("Unhandled error")
        return response(500, {"error": str(e)})


def handle_get_stock(event: dict[str, Any]) -> dict[str, Any]:
    """GET /api/stock/{ticker} — prices, financials, balance sheets."""
    path = event.get("requestContext", {}).get("http", {}).get("path", "")
    match = re.match(r"/api/stock/([A-Za-z0-9\-\.]+)", path)
    if not match:
        return response(400, {"error": "Invalid ticker"})

    ticker = match.group(1).upper()

    if not re.match(r"^[A-Z0-9\-\.]{1,10}$", ticker):
        return response(400, {"error": "Invalid ticker format"})

    params = event.get("queryStringParameters") or {}
    current_year = date.today().year

    try:
        start_year = int(params.get("start_year", current_year - config.DEFAULT_YEARS_BACK))
        end_year = int(params.get("end_year", current_year))
    except ValueError:
        return response(400, {"error": "Invalid year parameters"})

    if start_year < 1900 or end_year > current_year + 1 or start_year > end_year:
        return response(400, {"error": "Invalid year range"})

    try:
        start_date = date(start_year, 1, 1)
        end_date = date(end_year, 12, 31) if end_year < current_year else date.today()

        stock_data = provider.get_stock_data(ticker, start_date, end_date)
        return response(200, stock_data.to_dict())

    except ValueError as e:
        logger.warning(f"Data not found for {ticker}: {e}")
        return response(404, {"error": "Ticker not found", "ticker": ticker})
    except Exception as e:
        logger.exception(f"Error fetching data for {ticker}")
        return response(500, {"error": f"Failed to fetch data: {str(e)}"})


def handle_get_tickers(event: dict[str, Any]) -> dict[str, Any]:
    """GET /api/tickers — saved ticker list, falls back to defaults."""
    try:
        if LOCAL_MODE:
            tickers = list(_local_tickers)
        else:
            result = table.get_item(Key={"PK": config.TICKERS_PK})
            item = result.get("Item", {})
            tickers = list(item.get("tickers", set()))

        if not tickers:
            tickers = config.DEFAULT_TICKERS

        return response(200, {"tickers": sorted(tickers)})

    except Exception as e:
        logger.exception("Error fetching tickers")
        return response(500, {"error": str(e)})


def handle_add_ticker(event: dict[str, Any]) -> dict[str, Any]:
    """POST /api/tickers — add ticker to saved set."""
    try:
        body = json.loads(event.get("body", "{}"))
        ticker = body.get("ticker", "").upper().strip()

        if not ticker or not re.match(r"^[A-Z0-9\-\.]{1,10}$", ticker):
            return response(400, {"error": "Invalid ticker"})

        if LOCAL_MODE:
            _local_tickers.add(ticker)
        else:
            # DynamoDB ADD on string set — creates item if missing
            table.update_item(
                Key={"PK": config.TICKERS_PK},
                UpdateExpression="ADD tickers :t",
                ExpressionAttributeValues={":t": {ticker}},
            )

        logger.info(f"Added ticker: {ticker}")
        return response(201, {"success": True, "ticker": ticker})

    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON body"})
    except Exception as e:
        logger.exception("Error adding ticker")
        return response(500, {"error": str(e)})


def handle_delete_ticker(event: dict[str, Any]) -> dict[str, Any]:
    """DELETE /api/tickers/{ticker}."""
    path = event.get("requestContext", {}).get("http", {}).get("path", "")
    match = re.match(r"/api/tickers/([A-Za-z0-9\-\.]+)", path)
    if not match:
        return response(400, {"error": "Invalid ticker"})

    ticker = match.group(1).upper()

    try:
        if LOCAL_MODE:
            _local_tickers.discard(ticker)
        else:
            # DynamoDB DELETE on string set — no-op if ticker absent
            table.update_item(
                Key={"PK": config.TICKERS_PK},
                UpdateExpression="DELETE tickers :t",
                ExpressionAttributeValues={":t": {ticker}},
            )

        logger.info(f"Deleted ticker: {ticker}")
        return response(200, {"success": True, "ticker": ticker})

    except Exception as e:
        logger.exception("Error deleting ticker")
        return response(500, {"error": str(e)})


def response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Wrap body in API Gateway response format with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
