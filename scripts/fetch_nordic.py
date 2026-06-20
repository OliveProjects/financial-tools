"""Fetch Nordic index data: OMX30, OBX25, OMXC25, OMXH25 — all via yfinance."""
import os, json, math, datetime
import yfinance as yf

INDICES = {
    "OMX30": [
        "ATCO-B.ST", "INVE-B.ST", "NDA-SE.ST", "VOLV-B.ST", "SEB-A.ST",
        "SWED-A.ST", "ERIC-B.ST", "SHB-A.ST",  "SAND.ST",   "ABB.ST",
        "ASSA-B.ST", "HM-B.ST",   "EVO.ST",    "SAAB-B.ST", "SKF-B.ST",
        "ALFA.ST",   "NIBE-B.ST", "BOL.ST",    "ESSITY-B.ST","SKA-B.ST",
        "TEL2-B.ST", "GETI-B.ST", "SCA-B.ST",  "TELIA.ST",  "SSAB-A.ST",
        "KINV-B.ST", "HUSQ-B.ST", "LIFCO-B.ST","LATO-B.ST", "SINCH.ST",
    ],
    "OBX25": [
        "EQNR.OL",  "DNB.OL",   "MOWI.OL",  "TEL.OL",   "NHY.OL",
        "ORK.OL",   "YAR.OL",   "AKRBP.OL", "KOG.OL",   "SUBC.OL",
        "SALM.OL",  "STB.OL",   "GJF.OL",   "AUTO.OL",  "AKER.OL",
        "LSG.OL",   "BAKKA.OL", "BWLPG.OL", "FRO.OL",   "NSKOG.OL",
        "VEI.OL",   "RECSI.OL", "ATEA.OL",  "NEL.OL",   "MPCC.OL",
    ],
    "OMXC25": [
        "NOVO-B.CO",  "MAERSK-B.CO","DSV.CO",    "CARL-B.CO","COLO-B.CO",
        "GMAB.CO",    "ORSTED.CO",  "PNDORA.CO", "DEMANT.CO","VWS.CO",
        "TRYG.CO",    "RBREW.CO",   "GN.CO",     "AMBU-B.CO","BAVA.CO",
        "FLS.CO",     "ROCK-B.CO",  "ISS.CO",    "RILBA.CO", "JYSK.CO",
        "NETC.CO",    "DFDS.CO",    "NNIT.CO",
    ],
    "OMXH25": [
        "NOKIA.HE",  "NESTE.HE",  "KNEBV.HE", "SAMPO.HE", "UPM.HE",
        "STERV.HE",  "WRT1V.HE",  "METSO.HE", "VALMT.HE", "OUT1V.HE",
        "ELISA.HE",  "KEMIRA.HE", "ORNBV.HE", "HUH1V.HE", "FORTUM.HE",
        "TYRES.HE",  "METSB.HE",  "AKTIA.HE", "TEM1V.HE", "CAPMAN.HE",
    ],
}

NAME_MAP = {
    # OMX30
    "ATCO-B.ST":"Atlas Copco",  "INVE-B.ST":"Investor",    "NDA-SE.ST":"Nordea",
    "VOLV-B.ST":"Volvo",        "SEB-A.ST":"SEB",          "SWED-A.ST":"Swedbank",
    "ERIC-B.ST":"Ericsson",     "SHB-A.ST":"Handelsbanken","SAND.ST":"Sandvik",
    "ABB.ST":"ABB",             "ASSA-B.ST":"ASSA ABLOY",  "HM-B.ST":"H&M",
    "EVO.ST":"Evolution",       "SAAB-B.ST":"Saab",        "SKF-B.ST":"SKF",
    "ALFA.ST":"Alfa Laval",     "NIBE-B.ST":"NIBE",        "BOL.ST":"Boliden",
    "ESSITY-B.ST":"Essity",     "SKA-B.ST":"Skanska",      "TEL2-B.ST":"Tele2",
    "GETI-B.ST":"Getinge",      "SCA-B.ST":"SCA",          "TELIA.ST":"Telia",
    "SSAB-A.ST":"SSAB",         "KINV-B.ST":"Kinnevik",    "HUSQ-B.ST":"Husqvarna",
    "LIFCO-B.ST":"Lifco",       "LATO-B.ST":"Latour",      "SINCH.ST":"Sinch",
    # OBX25
    "EQNR.OL":"Equinor",        "DNB.OL":"DNB",            "MOWI.OL":"Mowi",
    "TEL.OL":"Telenor",         "NHY.OL":"Norsk Hydro",    "ORK.OL":"Orkla",
    "YAR.OL":"Yara",            "AKRBP.OL":"Aker BP",      "KOG.OL":"Kongsberg",
    "SUBC.OL":"Subsea 7",       "SALM.OL":"SalMar",        "STB.OL":"Storebrand",
    "GJF.OL":"Gjensidige",      "AUTO.OL":"AutoStore",     "AKER.OL":"Aker ASA",
    "LSG.OL":"Lerøy Seafood",   "BAKKA.OL":"Bakkafrost",   "BWLPG.OL":"BW LPG",
    "FRO.OL":"Frontline",       "NSKOG.OL":"Norske Skog",  "VEI.OL":"Veidekke",
    "RECSI.OL":"REC Silicon",   "ATEA.OL":"Atea",          "NEL.OL":"Nel",
    "MPCC.OL":"MPC Containerships",
    # OMXC25
    "NOVO-B.CO":"Novo Nordisk",   "MAERSK-B.CO":"A.P. Møller","DSV.CO":"DSV",
    "CARL-B.CO":"Carlsberg",      "COLOB.CO":"Coloplast",     "GMAB.CO":"Genmab",
    "ORSTED.CO":"Ørsted",         "PNDORA.CO":"Pandora",      "DEMANT.CO":"Demant",
    "VWS.CO":"Vestas",            "TRYG.CO":"Tryg",           "NZYM-B.CO":"Novozymes",
    "RBREW.CO":"Royal Unibrew",   "GN.CO":"GN Store Nord",    "AMBU-B.CO":"Ambu",
    "BAVA.CO":"Bavarian Nordic",  "FLS.CO":"FLSmidth",        "ROCK-B.CO":"Rockwool",
    "ISS.CO":"ISS",               "RILBA.CO":"Ringkjøbing LB","JYSK.CO":"Jyske Bank",
    "NETC.CO":"Netcompany",       "DFDS.CO":"DFDS",          "NNIT.CO":"NNIT",
    # OMXH25
    "NOKIA.HE":"Nokia",           "NESTE.HE":"Neste",         "KNEBV.HE":"Kone",
    "SAMPO.HE":"Sampo",           "UPM.HE":"UPM",             "STERV.HE":"Stora Enso",
    "WRTBV.HE":"Wärtsilä",        "METSO.HE":"Metso",         "VALMT.HE":"Valmet",
    "OUT1V.HE":"Outokumpu",       "ELISA.HE":"Elisa",         "CGCBV.HE":"Cargotec",
    "KEMIRA.HE":"Kemira",         "ORNBV.HE":"Orion",         "HUH1V.HE":"Huhtamäki",
    "FORTUM.HE":"Fortum",         "TYRES.HE":"Nokian Tyres",  "METSB.HE":"Metsä Board",
    "AKTIA.HE":"Aktia",           "TEM1V.HE":"Tietoevry",      "CAPMAN.HE":"CapMan",
    "WRT1V.HE":"Wärtsilä",
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
        hist = t.history(period="1mo", interval="1d")
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

        gm = info.get("grossMargins")
        gm = round(gm * 100, 2) if _is_valid(gm) else None

        rg = info.get("revenueGrowth")
        rg = round(rg * 100, 2) if _is_valid(rg) else None

        beta   = info.get("beta")
        beta   = round(float(beta), 3) if _is_valid(beta) else None

        pb     = info.get("priceToBook")
        pb     = round(float(pb), 2) if _is_valid(pb) else None

        target = info.get("targetMeanPrice")
        target = round(float(target), 2) if _is_valid(target) else None

        rsi = calc_rsi(closes)

        buy = hold = sell = 0
        try:
            recs = t.recommendations
            if recs is not None and not recs.empty:
                row = recs.sort_index(ascending=False).iloc[0]
                def _i(v):
                    try:
                        return int(v) if _is_valid(v) else 0
                    except Exception:
                        return 0
                buy  = _i(row.get("strongBuy", 0)) + _i(row.get("buy", 0))
                hold = _i(row.get("hold", 0))
                sell = _i(row.get("sell", 0)) + _i(row.get("strongSell", 0))
        except Exception:
            pass

        return {
            "ticker":        ticker,
            "name":          name,
            "index":         index_name,
            "currency":      currency,
            "price":         price,
            "pe":            round(float(pe), 2) if _is_valid(pe) else None,
            "peg":           round(float(peg), 2) if _is_valid(peg) else None,
            "roe":           roe,
            "grossMargin":   gm,
            "revenueGrowth": rg,
            "rsi":           rsi,
            "beta":          beta,
            "priceToBook":   pb,
            "buy":           buy,
            "hold":          hold,
            "sell":          sell,
            "target":        target,
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def load_existing():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "nordic.json")
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
                # Keep old data rather than dropping the stock
                all_stocks.append(existing[ticker])
                print(f"kept cached ({existing[ticker].get('price')})")
            else:
                print("SKIP")

    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    out = {
        "lastYahooUpdate": now,
        "generatedAt":     now,
        "stocks":          all_stocks,
    }

    path = os.path.join(os.path.dirname(__file__), "..", "data", "nordic.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\nWrote {len(all_stocks)} stocks -> data/nordic.json")


if __name__ == "__main__":
    main()
