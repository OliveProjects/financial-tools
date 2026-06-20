"""Fetch Baltic index data: OMXT (Estonia), OMXR (Latvia), OMXV (Lithuania) via yfinance."""
import os, json, math, datetime
import yfinance as yf

INDICES = {
    "OMXT": [
        "TAL1T.TL", "LHV1T.TL", "EGR1T.TL", "CPA1T.TL", "NCN1T.TL",
        "SFG1T.TL", "MRK1T.TL", "PRF1T.TL", "EFT1T.TL", "TKM1T.TL",
        "HAE1T.TL",
    ],
    "OMXR": [
        "LVN1R.RG", "OLF1R.RG", "SAF1R.RG", "GRD1R.RG",
    ],
    "OMXV": [
        "SB1L.VS", "IGN1L.VS", "APG1L.VS", "TEL1L.VS", "LNR1L.VS",
    ],
}

NAME_MAP = {
    # OMXT (Tallinn)
    "TAL1T.TL":"Tallink",         "LHV1T.TL":"LHV Group",       "EGR1T.TL":"Enefit Green",
    "CPA1T.TL":"Coop Pank",       "NCN1T.TL":"Nordecon",        "SFG1T.TL":"Silvano Fashion",
    "MRK1T.TL":"Merko Ehitus",    "PRF1T.TL":"Premia Foods",    "EFT1T.TL":"Eften Real Estate",
    "TKM1T.TL":"Tallinna Kaubamaja","HAE1T.TL":"Hepsor",
    # OMXR (Riga)
    "LVN1R.RG":"Latvenergo",      "OLF1R.RG":"Olainfarm",       "SAF1R.RG":"SAF Tehnika",
    "GRD1R.RG":"Grindeks",
    # OMXV (Vilnius)
    "SB1L.VS":"Šiaulių Bankas",   "IGN1L.VS":"Ignitis Group",   "APG1L.VS":"Apranga",
    "TEL1L.VS":"Telia Lietuva",   "LNR1L.VS":"Linas Agro",
}


def _is_valid(v):
    try:
        f = float(v)
        return v is not None and not math.isnan(f) and not math.isinf(f)
    except Exception:
        return False


def calc_rsi(closes, period=14):
    clean = [c for c in (closes or []) if _is_valid(c)]
    if len(clean) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(clean)):
        d = clean[i] - clean[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        ag = (ag * 13 + gains[i]) / 14
        al = (al * 13 + losses[i]) / 14
    if al == 0:
        return 100
    return round(100 - (100 / (1 + ag / al)))


def fetch_stock(ticker, index_name):
    try:
        t    = yf.Ticker(ticker)
        hist = t.history(period="6mo", interval="1d")
        if hist.empty:
            return None
        closes = [float(c) for c in hist["Close"].tolist() if _is_valid(c)]
        if not closes:
            return None
        try:
            price = round(float(t.fast_info.last_price), 2)
        except Exception:
            price = round(closes[-1], 2)
        info     = t.info
        name     = NAME_MAP.get(ticker) or info.get("shortName") or info.get("longName") or ticker
        currency = info.get("currency") or "–"
        pe  = info.get("trailingPE")
        peg = info.get("pegRatio")
        roe = info.get("returnOnEquity")
        roe = round(roe * 100, 2) if _is_valid(roe) else None
        gm  = info.get("grossMargins")
        gm  = round(gm * 100, 2) if _is_valid(gm) else None
        rg  = info.get("revenueGrowth")
        rg  = round(rg * 100, 2) if _is_valid(rg) else None
        beta   = info.get("beta")
        beta   = round(float(beta), 3) if _is_valid(beta) else None
        pb     = info.get("priceToBook")
        pb     = round(float(pb), 2) if _is_valid(pb) else None
        target = info.get("targetMeanPrice")
        target = round(float(target), 2) if _is_valid(target) else None
        rsi    = calc_rsi(closes)
        buy = hold = sell = 0
        try:
            recs = t.recommendations
            if recs is not None and not recs.empty:
                row = recs.sort_index(ascending=False).iloc[0]
                def _i(v):
                    try: return int(v) if _is_valid(v) else 0
                    except: return 0
                buy  = _i(row.get("strongBuy", 0)) + _i(row.get("buy", 0))
                hold = _i(row.get("hold", 0))
                sell = _i(row.get("sell", 0)) + _i(row.get("strongSell", 0))
        except Exception:
            pass
        return {
            "ticker": ticker, "name": name, "index": index_name,
            "currency": currency, "price": price,
            "pe":  round(float(pe), 2) if _is_valid(pe) else None,
            "peg": round(float(peg), 2) if _is_valid(peg) else None,
            "roe": roe, "grossMargin": gm, "revenueGrowth": rg,
            "rsi": rsi, "beta": beta, "priceToBook": pb,
            "buy": buy, "hold": hold, "sell": sell, "target": target,
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def load_existing():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "baltic.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return {s["ticker"]: s for s in json.load(f).get("stocks", [])}
    return {}


def main():
    existing = load_existing()
    all_stocks = []
    for index_name, tickers in INDICES.items():
        print(f"\n{index_name}:")
        for ticker in tickers:
            print(f"  {ticker}...", end=" ", flush=True)
            result = fetch_stock(ticker, index_name)
            if result:
                all_stocks.append(result)
                print(f"{result['price']} {result['currency']}")
            elif ticker in existing:
                all_stocks.append(existing[ticker])
                print(f"kept cached ({existing[ticker].get('price')})")
            else:
                print("SKIP")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    out = {"lastYahooUpdate": now, "generatedAt": now, "stocks": all_stocks}
    path = os.path.join(os.path.dirname(__file__), "..", "data", "baltic.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(all_stocks)} stocks -> data/baltic.json")


if __name__ == "__main__":
    main()
