#!/usr/bin/env python3
"""Seed default tickers to DynamoDB."""
import os
import sys

import boto3

DEFAULT_TICKERS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "GOOG",
    "AMZN",
    "TSLA",
    "BRK-B",
    "NVDA",
    "META",
    "UNH",
    "V",
    "JNJ",
    "WMT",
    "JPM",
    "PG",
    "MA",
    "BAC",
    "XOM",
    "HD",
    "CVX",
]


def main() -> None:
    table_name = os.environ.get("TABLE_NAME", "StockDashboard")

    print(f"Seeding tickers to table: {table_name}")

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        # ADD on string set — creates item if missing, merges if exists
        table.update_item(
            Key={"PK": "TICKERS"},
            UpdateExpression="ADD tickers :t",
            ExpressionAttributeValues={":t": set(DEFAULT_TICKERS)},
        )

        print(f"Successfully seeded {len(DEFAULT_TICKERS)} tickers:")
        for ticker in sorted(DEFAULT_TICKERS):
            print(f"  - {ticker}")

    except Exception as e:
        print(f"Error seeding tickers: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
