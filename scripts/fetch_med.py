"""Fetch Mediterranean index data: IBEX35 (Spain), FTSEMIB (Italy), PSI20 (Portugal), ATHEX25 (Greece) via yfinance."""
import os, json, math, datetime
import yfinance as yf

INDICES = {
    "IBEX35": [
        "SAN.MC",  "BBVA.MC", "ITX.MC",  "TEF.MC",  "IBE.MC",
        "REP.MC",  "AMS.MC",  "CABK.MC", "MAP.MC",  "ELE.MC",
        "NTGY.MC", "FER.MC",  "GRF.MC",  "IAG.MC",  "BKT.MC",
        "AENA.MC", "RED.MC",  "SAB.MC",  "ACS.MC",  "COL.MC",
        "ACX.MC",  "LOG.MC",  "ENG.MC",  "MTS.MC",  "ANA.MC",
        "ANE.MC",  "CLNX.MC", "FDR.MC",  "IDR.MC",  "MRL.MC",
        "PUIG.MC", "ROVI.MC", "SCYR.MC", "SLR.MC",  "UNI.MC",
    ],
    "FTSEMIB": [
        "ENI.MI",   "ENEL.MI",  "ISP.MI",   "UCG.MI",  "STM.MI",
        "LDO.MI",   "G.MI",     "MB.MI",    "STLAM.MI","MONC.MI",
        "PRY.MI",   "NEXI.MI",  "BZU.MI",   "CPR.MI",  "TEN.MI",
        "PIRC.MI",  "SRG.MI",   "TRN.MI",   "A2A.MI",  "BAMI.MI",
        "RACE.MI",  "CNHI.MI",  "REC.MI",   "TIT.MI",  "SPM.MI",
        "AMP.MI",   "AZM.MI",   "BMED.MI",  "BGN.MI",  "BMPS.MI",
        "BPE.MI",   "DIA.MI",   "FBK.MI",   "HER.MI",  "INW.MI",
        "IG.MI",    "IP.MI",    "IVG.MI",   "PST.MI",  "UNI.MI",
    ],
    "PSI20": [
        "EDP.LS",  "EDPR.LS", "GALP.LS", "JMT.LS",  "SEM.LS",
        "SON.LS",  "BCP.LS",  "NOS.LS",  "CTT.LS",  "NVG.LS",
        "RENE.LS", "COR.LS",  "ALTR.LS", "EGL.LS",  "IBS.LS",
        "NBA.LS",  "PHR.LS",  "SONC.LS",
    ],
    "ATHEX25": [
        "OPAP.AT",    "ALPHA.AT",   "EUROB.AT",   "ETE.AT",    "PPC.AT",
        "TPEIR.AT",   "HTO.AT",     "MYTIL.AT",   "ELPE.AT",   "TITC.AT",
        "ADMIE.AT",   "GEKTERNA.AT","CENTR.AT",   "LAMDA.AT",
        "EEE.AT",     "MOH.AT",     "ELHA.AT",    "EXAE.AT",   "VIO.AT",
        "OTOEL.AT",
    ],
}

NAME_MAP = {
    # IBEX35
    "SAN.MC":"Santander",        "BBVA.MC":"BBVA",             "ITX.MC":"Inditex",
    "TEF.MC":"Telefónica",       "IBE.MC":"Iberdrola",         "REP.MC":"Repsol",
    "AMS.MC":"Amadeus",          "CABK.MC":"CaixaBank",        "MAP.MC":"Mapfre",
    "ELE.MC":"Endesa",           "NTGY.MC":"Naturgy",          "FER.MC":"Ferrovial",
    "GRF.MC":"Grifols",          "IAG.MC":"IAG",               "BKT.MC":"Bankinter",
    "AENA.MC":"Aena",            "RED.MC":"Redeia",            "SAB.MC":"Sabadell",
    "ACS.MC":"ACS",              "COL.MC":"Colonial",          "ACX.MC":"Acerinox",
    "LOG.MC":"Logista",          "ENG.MC":"Enagás",            "MTS.MC":"ArcelorMittal",
    "ANA.MC":"Acciona",          "ANE.MC":"Acciona Energía",   "CLNX.MC":"Cellnex",
    "FDR.MC":"Fluidra",          "IDR.MC":"Indra",             "MRL.MC":"Merlin Properties",
    "PUIG.MC":"Puig Brands",     "ROVI.MC":"Laboratorios Rovi","SCYR.MC":"Sacyr",
    "SLR.MC":"Solaria",          "UNI.MC":"Unicaja Banco",
    # FTSE MIB
    "ENI.MI":"Eni",              "ENEL.MI":"Enel",             "ISP.MI":"Intesa Sanpaolo",
    "UCG.MI":"UniCredit",        "STM.MI":"STMicroelectronics","LDO.MI":"Leonardo",
    "G.MI":"Generali",           "MB.MI":"Mediobanca",         "STLAM.MI":"Stellantis",
    "MONC.MI":"Moncler",         "PRY.MI":"Prysmian",          "NEXI.MI":"Nexi",
    "BZU.MI":"Buzzi",            "CPR.MI":"Campari",           "TEN.MI":"Tenaris",
    "PIRC.MI":"Pirelli",         "SRG.MI":"Snam",              "TRN.MI":"Terna",
    "A2A.MI":"A2A",              "BAMI.MI":"Banco BPM",        "RACE.MI":"Ferrari",
    "CNHI.MI":"CNH Industrial",  "REC.MI":"Recordati",         "TIT.MI":"Telecom Italia",
    "SPM.MI":"Saipem",           "AMP.MI":"Amplifon",          "AZM.MI":"Azimut Holding",
    "BMED.MI":"Banca Mediolanum","BGN.MI":"Banca Generali",    "BMPS.MI":"Monte dei Paschi",
    "BPE.MI":"BPER Banca",       "DIA.MI":"DiaSorin",          "FBK.MI":"FinecoBank",
    "HER.MI":"Hera",             "INW.MI":"INWIT",             "IG.MI":"Italgas",
    "IP.MI":"Interpump",         "IVG.MI":"Iveco Group",       "PST.MI":"Poste Italiane",
    "UNI.MI":"Unipol",
    # PSI20
    "EDP.LS":"EDP",              "EDPR.LS":"EDP Renováveis",   "GALP.LS":"Galp",
    "JMT.LS":"Jerónimo Martins", "SEM.LS":"Semapa",            "SON.LS":"Sonae",
    "BCP.LS":"Millennium BCP",   "NOS.LS":"NOS",               "CTT.LS":"CTT",
    "NVG.LS":"Navigator",        "RENE.LS":"REN",              "COR.LS":"Corticeira Amorim",
    "ALTR.LS":"Altri",           "EGL.LS":"Mota-Engil",        "IBS.LS":"Ibersol",
    "NBA.LS":"Novabase",         "PHR.LS":"Pharol",            "SONC.LS":"Sonae Capital",
    # ATHEX25
    "OPAP.AT":"OPAP",            "ALPHA.AT":"Alpha Bank",      "EUROB.AT":"Eurobank",
    "ETE.AT":"Nat. Bank Greece", "PPC.AT":"Public Power",      "TPEIR.AT":"Piraeus Bank",
    "HTO.AT":"Hellenic Telecom", "MYTIL.AT":"Mytilineos",      "ELPE.AT":"HELLENiQ Energy",
    "TITC.AT":"Titan Cement",    "ADMIE.AT":"ADMIE",           "GEKTERNA.AT":"GEK Terna",
    "CENTR.AT":"Cenergy",        "LAMDA.AT":"Lamda Development",
    "EEE.AT":"Coca-Cola HBC",    "MOH.AT":"Motor Oil Hellas",  "ELHA.AT":"Elvalhalcor",
    "EXAE.AT":"Athens Exchange", "VIO.AT":"Viohalco",          "OTOEL.AT":"Autohellas",
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
    path = os.path.join(os.path.dirname(__file__), "..", "data", "med.json")
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
    path = os.path.join(os.path.dirname(__file__), "..", "data", "med.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(all_stocks)} stocks -> data/med.json")


if __name__ == "__main__":
    main()
