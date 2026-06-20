"""Fetch Asia Pacific index data: STI30 (Singapore), ASX20 (Australia), KOSPI20 (South Korea) via yfinance."""
import os, json, math, datetime
import yfinance as yf

INDICES = {
    "STI30": [
        "D05.SI",  "O39.SI",  "U11.SI",  "Z74.SI",  "C6L.SI",
        "BN4.SI",  "J36.SI",  "F34.SI",  "C52.SI",  "S63.SI",
        "V03.SI",  "ME8U.SI", "C38U.SI", "9CI.SI",  "G13.SI",
        "S68.SI",  "A17U.SI", "U96.SI",  "Y92.SI",  "S58.SI",
        "BS6.SI",  "BUOU.SI", "C09.SI",  "D01.SI",  "H78.SI",
        "J69U.SI", "AJBU.SI", "M44U.SI", "N2IU.SI", "U14.SI",
    ],
    "ASX20": [
        "BHP.AX",  "CBA.AX",  "CSL.AX",  "NAB.AX",  "WBC.AX",
        "ANZ.AX",  "WES.AX",  "WOW.AX",  "MQG.AX",  "RIO.AX",
        "TLS.AX",  "GMG.AX",  "COL.AX",  "FMG.AX",  "REA.AX",
        "TCL.AX",  "ALL.AX",  "SHL.AX",  "MIN.AX",  "RMD.AX",
    ],
    "KOSPI20": [
        "005930.KS", "000660.KS", "035720.KS", "035420.KS", "005380.KS",
        "051910.KS", "068270.KS", "207940.KS", "005490.KS", "086790.KS",
        "055550.KS", "000270.KS", "012330.KS", "003550.KS", "017670.KS",
        "066570.KS", "105560.KS", "032830.KS", "028260.KS", "034730.KS",
    ],
}

NAME_MAP = {
    # STI30 (Singapore)
    "D05.SI":"DBS Group",           "O39.SI":"OCBC Bank",           "U11.SI":"UOB",
    "Z74.SI":"Singtel",             "C6L.SI":"Singapore Airlines",  "BN4.SI":"Keppel",
    "J36.SI":"Jardine Matheson",    "F34.SI":"Wilmar",              "C52.SI":"ComfortDelGro",
    "S63.SI":"ST Engineering",      "V03.SI":"Venture Corp",         "ME8U.SI":"Mapletree Log Trust",
    "C38U.SI":"CapitaLand Int. CT", "9CI.SI":"CapitaLand Investment","G13.SI":"Genting Singapore",
    "S68.SI":"Singapore Exchange",  "A17U.SI":"Ascendas REIT",      "U96.SI":"Sembcorp Industries",
    "Y92.SI":"Thai Beverage",       "S58.SI":"SATS",
    "BS6.SI":"Yangzijiang Shipbuilding","BUOU.SI":"Frasers L&CT",   "C09.SI":"City Developments",
    "D01.SI":"DFI Retail Group",    "H78.SI":"Hongkong Land",       "J69U.SI":"Frasers Centrepoint Trust",
    "AJBU.SI":"Keppel DC REIT",     "M44U.SI":"Mapletree Pan Asia CT","N2IU.SI":"Mapletree Industrial Trust",
    "U14.SI":"UOL Group",
    # ASX20 (Australia)
    "BHP.AX":"BHP",               "CBA.AX":"Commonwealth Bank",   "CSL.AX":"CSL",
    "NAB.AX":"NAB",               "WBC.AX":"Westpac",            "ANZ.AX":"ANZ",
    "WES.AX":"Wesfarmers",        "WOW.AX":"Woolworths",         "MQG.AX":"Macquarie",
    "RIO.AX":"Rio Tinto",         "TLS.AX":"Telstra",            "GMG.AX":"Goodman Group",
    "COL.AX":"Coles",             "FMG.AX":"Fortescue",          "REA.AX":"REA Group",
    "TCL.AX":"Transurban",        "ALL.AX":"Aristocrat Leisure",  "SHL.AX":"Sonic Healthcare",
    "MIN.AX":"Mineral Resources",  "RMD.AX":"ResMed",
    # KOSPI20 (South Korea)
    "005930.KS":"Samsung Electronics","000660.KS":"SK Hynix",     "035720.KS":"Kakao",
    "035420.KS":"Naver",           "005380.KS":"Hyundai Motor",   "051910.KS":"LG Chem",
    "068270.KS":"Celltrion",       "207940.KS":"Samsung Biologics","005490.KS":"POSCO Holdings",
    "086790.KS":"Hana Financial",  "055550.KS":"Shinhan Financial","000270.KS":"Kia",
    "012330.KS":"Hyundai Mobis",   "003550.KS":"LG Corp",         "017670.KS":"SK Telecom",
    "066570.KS":"LG Electronics",  "105560.KS":"KB Financial",    "032830.KS":"Samsung Life",
    "028260.KS":"Samsung C&T",     "034730.KS":"SK Inc",
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
    path = os.path.join(os.path.dirname(__file__), "..", "data", "asiapac.json")
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
    path = os.path.join(os.path.dirname(__file__), "..", "data", "asiapac.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(all_stocks)} stocks -> data/asiapac.json")


if __name__ == "__main__":
    main()
