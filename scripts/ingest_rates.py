#!/usr/bin/env python3
"""
Usage:
  python ingest_rates.py --transactions path/to/transactions.csv --output output/raw_rates

Requires:
  pip install requests pandas python-dateutil
"""

import os
import argparse
import requests
import pandas as pd
from dateutil import parser
from datetime import datetime, timedelta
import time
import json

BINANCE_API = "https://api.binance.com"
KLINES_PATH = "/api/v3/klines"
MAX_LIMIT = 1000  # Binance max per request

def read_transactions(path):
    df = pd.read_csv(path, parse_dates=["created_at"], dtype=str)
    # ensure created_at is datetime
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
    return df

def distinct_dest_currencies(df):
    return sorted(df['destination_currency'].dropna().unique())

def min_max_dates(df):
    return df['created_at'].min(), df['created_at'].max()

def pair_exists(symbol):
    r = requests.get(f"{BINANCE_API}/api/v3/exchangeInfo", params={"symbol": symbol}, timeout=30)
    if r.status_code != 200:
        return False
    data = r.json()
    return 'symbols' in data and len(data['symbols']) > 0

def fetch_klines(symbol, interval, start_ts, end_ts):
    """Generator of klines in JSON from start_ts (ms) to end_ts (ms)."""
    out = []
    cur_start = start_ts
    while cur_start < end_ts:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": cur_start,
            "endTime": end_ts,
            "limit": MAX_LIMIT
        }
        r = requests.get(BINANCE_API + KLINES_PATH, params=params, timeout=60)
        if r.status_code == 429:
            # rate limited, sleep and retry
            print("Rate limited, sleeping 1s...")
            time.sleep(1)
            continue
        r.raise_for_status()
        klines = r.json()
        if not klines:
            break
        for k in klines:
            # k format: [open_time, open, high, low, close, volume, close_time, ...]
            out.append({
                "symbol": symbol,
                "open_time": int(k[0]),
                "open": k[1],
                "high": k[2],
                "low": k[3],
                "close": k[4],
                "volume": k[5],
                "close_time": int(k[6]),
                "quote_asset_volume": k[7],
                "num_trades": k[8],
                "taker_buy_base_asset_volume": k[9],
                "taker_buy_quote_asset_volume": k[10],
            })
        # move cur_start to last open_time + 1 ms to paginate
        last_open = klines[-1][0]
        # if we've hit limit, continue after last_open
        cur_start = last_open + 1
        # polite sleep to avoid hitting limits
        time.sleep(0.2)
    return out

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def main(transactions_csv, output_dir):
    df = read_transactions(transactions_csv)
    currencies = distinct_dest_currencies(df)
    start_ts, end_ts = min_max_dates(df)
    print(f"Found destination currencies: {currencies}")
    print(f"Date range: {start_ts} to {end_ts} (UTC)")

    ensure_dir(output_dir)
    # convert to ms epoch for API
    start_ms = int(start_ts.timestamp() * 1000)
    # extend end by +1 hour to include last hour candle
    end_ms = int((end_ts + timedelta(hours=1)).timestamp() * 1000)

    for cur in currencies:
        # skip if is USDT already (no need)
        if cur.upper() == "USDT":
            print(f"Skipping USDT.")
            continue
        symbol = f"{cur.upper()}USDT"
        print(f"Checking {symbol} ...")
        try:
            # check pair existence via exchangeInfo
            r = requests.get(f"{BINANCE_API}/api/v3/exchangeInfo", params={"symbol": symbol}, timeout=30)
            if r.status_code != 200 or 'symbols' not in r.json() or len(r.json()['symbols']) == 0:
                print(f"  Pair {symbol} not available on Binance or no data. Skipping.")
                continue
        except Exception as e:
            print(f"  Error checking pair {symbol}: {e}. Skipping.")
            continue

        print(f"  Fetching klines for {symbol} from {start_ts} to {end_ts} ...")
        try:
            klines = fetch_klines(symbol, "1h", start_ms, end_ms)
            if not klines:
                print(f"  No klines returned for {symbol}.")
                continue
            out_path = os.path.join(output_dir, f"{symbol}.jsonl")
            with open(out_path, "w", encoding="utf-8") as f:
                for k in klines:
                    f.write(json.dumps(k) + "\n")
            print(f"  Saved {len(klines)} rows to {out_path}")
        except Exception as e:
            print(f"  Error fetching {symbol}: {e}")
            continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--transactions", required=True, help="Path to transactions.csv")
    parser.add_argument("--output", required=False, default="output/raw_rates/", help="Output folder")
    args = parser.parse_args()
    main(args.transactions, args.output)
