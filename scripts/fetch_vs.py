import yfinance as yf
import json
import os
from datetime import datetime, timezone
import pandas as pd

MAG7     = ["MSFT", "AAPL", "NVDA", "AMZN", "GOOGL", "META", "TSLA"]
GRANOLAS = ["GSK", "RHHBY", "ASML", "NSRGY", "NVS", "NVO", "LRLCY", "LVMUY", "AZN", "SAP", "SNY"]

PERIODS = {
    "1w":  ("7d",  "1d"),
    "1m":  ("1mo", "1d"),
    "3m":  ("3mo", "1d"),
    "6m":  ("6mo", "1wk"),
    "ytd": ("ytd", "1d"),
    "1y":  ("1y",  "1wk"),
    "3y":  ("3y",  "1wk"),
    "5y":  ("5y",  "1wk"),
}

def fetch_normalized(tickers, period, interval):
    frames = []
    for t in tickers:
        try:
            hist = yf.Ticker(t).history(period=period, interval=interval, auto_adjust=True)
            if not hist.empty:
                frames.append(hist["Close"].rename(t))
        except Exception as e:
            print(f"  Warning: {t} failed — {e}")

    if not frames:
        return []

    combined = pd.concat(frames, axis=1)
    combined = combined.dropna(how="all")
    if combined.empty:
        return []

    avg = combined.mean(axis=1)
    base = avg.iloc[0]
    if base == 0:
        return []

    normalized = (avg / base * 100).round(2)
    result = []
    for ts, v in normalized.items():
        if pd.isna(v):
            continue
        epoch_ms = int(ts.timestamp() * 1000)
        result.append({"t": epoch_ms, "v": float(v)})
    return result

output = {
    "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "series": {},
}

for key, (period, interval) in PERIODS.items():
    print(f"Fetching {key} ({period} / {interval})...")
    output["series"][key] = {
        "mag7":     fetch_normalized(MAG7,     period, interval),
        "granolas": fetch_normalized(GRANOLAS, period, interval),
    }

os.makedirs("data", exist_ok=True)
with open("data/vs.json", "w") as f:
    json.dump(output, f, separators=(",", ":"))

print("data/vs.json written.")
