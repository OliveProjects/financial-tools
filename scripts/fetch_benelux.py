"""Fetch Benelux index data: AEX25 (Netherlands), BEL20 (Belgium) via yfinance."""
import os, json, math, datetime
import yfinance as yf

INDICES = {
    "AEX25": [
        "ASML.AS",  "HEIA.AS",  "INGA.AS",  "AD.AS",    "WKL.AS",
        "PRX.AS",   "NN.AS",    "KPN.AS",   "AKZA.AS",  "PHIA.AS",
        "ABN.AS",   "RAND.AS",  "BESI.AS",  "IMCD.AS",  "MT.AS",
        "DSFIR.AS", "AGN.AS",   "ADYEN.AS", "URW.AS",   "LIGHT.AS",
        "SBMO.AS",  "ASRNL.AS", "EXOR.AS",  "GLPG.AS",  "TKWY.AS",
    ],
    "BEL20": [
        "ABI.BR",   "AGS.BR",   "ACKB.BR",  "AED.BR",   "AZE.BR",
        "APAM.BR",  "ARGX.BR",  "COLR.BR",  "DIE.BR",   "ELI.BR",
        "GBLB.BR",  "KBC.BR",   "LOTB.BR",  "MELE.BR",  "MONT.BR",
        "SOF.BR",   "SOLB.BR",  "SYENS.BR", "UCB.BR",   "UMI.BR",
        "WDP.BR",
    ],
}

NAME_MAP = {
    # AEX25
    "ASML.AS":"ASML",              "HEIA.AS":"Heineken",          "INGA.AS":"ING Group",
    "AD.AS":"Ahold Delhaize",      "WKL.AS":"Wolters Kluwer",     "PRX.AS":"Prosus",
    "NN.AS":"NN Group",            "KPN.AS":"KPN",                "AKZA.AS":"AkzoNobel",
    "PHIA.AS":"Philips",           "ABN.AS":"ABN AMRO",           "RAND.AS":"Randstad",
    "BESI.AS":"BE Semiconductor",  "IMCD.AS":"IMCD",              "MT.AS":"ArcelorMittal",
    "DSFIR.AS":"dsm-firmenich",    "AGN.AS":"Aegon",              "ADYEN.AS":"Adyen",
    "URW.AS":"Unibail-Rodamco",    "LIGHT.AS":"Signify",          "SBMO.AS":"SBM Offshore",
    "ASRNL.AS":"ASR Nederland",    "EXOR.AS":"Exor",              "GLPG.AS":"Galapagos",
    "TKWY.AS":"Just Eat Takeaway",
    # BEL20
    "ABI.BR":"AB InBev",           "AGS.BR":"Ageas",              "ACKB.BR":"Ackermans & van Haaren",
    "AED.BR":"Aedifica",           "AZE.BR":"Azelis",             "APAM.BR":"Aperam",
    "ARGX.BR":"argenx",            "COLR.BR":"Colruyt",           "DIE.BR":"D'Ieteren",
    "ELI.BR":"Elia Group",         "GBLB.BR":"GBL",               "KBC.BR":"KBC",
    "LOTB.BR":"Lotus Bakeries",    "MELE.BR":"Melexis",           "MONT.BR":"Montea",
    "SOF.BR":"Sofina",             "SOLB.BR":"Solvay",            "SYENS.BR":"Syensqo",
    "UCB.BR":"UCB",                "UMI.BR":"Umicore",            "WDP.BR":"WDP",
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
    path = os.path.join(os.path.dirname(__file__), "..", "data", "benelux.json")
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
    path = os.path.join(os.path.dirname(__file__), "..", "data", "benelux.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(all_stocks)} stocks -> data/benelux.json")


if __name__ == "__main__":
    main()
