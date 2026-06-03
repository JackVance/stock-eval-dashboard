"""Weekly cron: refresh the TOP_TICKERS DynamoDB record with top-N by market cap."""
import json
import logging
from typing import Any

import boto3
import yfinance as yf

from config import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(config.TABLE_NAME)


def main(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """EventBridge cron entry point. Fetches market caps for the candidate list and stores the top N."""
    logger.info(f"Refresh start: {len(config.CANDIDATE_TICKERS)} candidates, top_n={config.TOP_N}")

    market_caps: list[tuple[str, int]] = []
    failed: list[str] = []

    for ticker in config.CANDIDATE_TICKERS:
        try:
            info = yf.Ticker(ticker).info
            cap = info.get("marketCap")
            if cap and cap > 0:
                market_caps.append((ticker, int(cap)))
            else:
                logger.warning(f"No market cap for {ticker} (got {cap!r})")
                failed.append(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch {ticker}: {e}")
            failed.append(ticker)

    if not market_caps:
        logger.error("All yfinance calls failed — refusing to overwrite TOP_TICKERS")
        return {
            "status": "error",
            "message": "no market caps returned",
            "failed_count": len(failed),
        }

    market_caps.sort(key=lambda t: t[1], reverse=True)
    top = market_caps[: config.TOP_N]
    top_tickers = [t for t, _ in top]

    logger.info(
        f"Top {len(top_tickers)} by market cap: "
        + ", ".join(f"{t}=${c:,}" for t, c in top)
    )

    # Store as a List (not Set) so the market-cap descending order is preserved.
    table.put_item(
        Item={
            "PK": config.TOP_TICKERS_PK,
            "tickers": top_tickers,
        }
    )

    return {
        "status": "ok",
        "top_tickers": top_tickers,
        "successful_count": len(market_caps),
        "failed_count": len(failed),
    }


if __name__ == "__main__":
    # Local invocation for testing
    print(json.dumps(main({}, None), indent=2, default=list))
