import json
import yfinance as yf
import pandas as pd
import logging
import time

# Set cache location to avoid Yahoo Finance blocking
yf.set_tz_cache_location("/tmp/yfinance_cache")


# AAPL, "15m", "2024-12-11", "2024-12-18"
def get_df_selected_tf(
    ticker, _interval, _start_date, _end_date
):
    print(
        f"Downloading {ticker} from {_start_date} to {_end_date} with interval {_interval}"
    )

    max_retries = 3
    data = None

    for attempt in range(max_retries):
        try:
            data = yf.download(
                tickers=ticker,
                start=_start_date,
                end=_end_date,
                interval=_interval,
                progress=False,
                auto_adjust=False,
                actions=False,
                group_by="column",
                repair=True,
                keepna=False,
            )

            print(
                f"[DEBUG] Download complete (attempt {attempt + 1}). Type: {type(data)}, Shape: {data.shape if hasattr(data, 'shape') else 'N/A'}, Empty: {data.empty if hasattr(data, 'empty') else 'N/A'}"
            )

            if data is not None and not data.empty:
                break

            if attempt < max_retries - 1:
                print(f"[DEBUG] Empty data received, retrying in 2 seconds...")
                time.sleep(2)
        except Exception as e:
            print(f"[DEBUG] Download error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise

    if data is None or data.empty:
        raise ValueError(
            f"Failed to download data for {ticker} after {max_retries} attempts. Check ticker symbol, date range, and internet connection."
        )

    if isinstance(data.columns, pd.MultiIndex):
        print(f"[DEBUG] Flattening multi-index columns")
        data.columns = data.columns.get_level_values(0)

    cols_to_drop = [
        col
        for col in [
            "Dividends",
            "Stock Splits",
            "Capital Gains",
            "Adj Close",
            "Repaired?",
        ]
        if col in data.columns
    ]
    if cols_to_drop:
        data = data.drop(columns=cols_to_drop)

    print(f"[DEBUG] Final columns: {data.columns.tolist()}")

    return data, ticker


# AAPL, "15m", "5d"
def get_df_recent(ticker, _interval, _period):
    max_retries = 3
    data = None

    for attempt in range(max_retries):
        try:
            data = yf.download(
                tickers=ticker,
                period=_period,
                interval=_interval,
                progress=False,
                auto_adjust=False,
                actions=False,
                group_by="column",
                repair=True,
                keepna=False,
            )

            if data is not None and not data.empty:
                break

            if attempt < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise

    if data is None or data.empty:
        raise ValueError(
            f"Failed to download data for {ticker} after {max_retries} attempts. Check ticker symbol, period, and internet connection."
        )

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    cols_to_drop = [
        col
        for col in [
            "Dividends",
            "Stock Splits",
            "Capital Gains",
            "Adj Close",
            "Repaired?",
        ]
        if col in data.columns
    ]
    if cols_to_drop:
        data = data.drop(columns=cols_to_drop)

    return data, ticker


def get_settings():
    with open("config.json", "r") as settings:
        return json.load(settings)
