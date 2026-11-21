"""Dukascopy'den 1 dakikalık BID ve ASK mumlarını indirir.

Çıktı: data/{SYM}.parquet  (index: UTC zaman, kolonlar: bo,bh,bl,bc,ao,ah,al,ac,v)
"""
import concurrent.futures as cf
import datetime as dt
import lzma
import os
import struct
import sys
import time
import urllib.request

import numpy as np
import pandas as pd

SYMBOLS = {
    "XAUUSD": (1000, 6000),
    "XAGUSD": (10, 150),
    "DEUIDXEUR": (8000, 35000),
    "USATECHIDXUSD": (8000, 40000),
}
START = dt.date(2021, 1, 1)
END = dt.date.today() - dt.timedelta(days=1)
URL = "https://datafeed.dukascopy.com/datafeed/{s}/{y}/{m:02d}/{d:02d}/{side}_candles_min_1.bi5"
OUT = os.path.join(os.path.dirname(__file__), "data")


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return b""
            time.sleep(1 + i * 2)
        except Exception:
            time.sleep(1 + i * 2)
    return None


def parse(raw, day):
    if not raw:
        return None
    try:
        buf = lzma.decompress(raw)
    except Exception:
        return None
    n = len(buf) // 24
    if n == 0:
        return None
    arr = np.frombuffer(buf[: n * 24], dtype=">i4").reshape(n, 6)
    vol = np.frombuffer(buf[: n * 24], dtype=">f4").reshape(n, 6)[:, 5]
    base = pd.Timestamp(day, tz="UTC")
    idx = base + pd.to_timedelta(arr[:, 0], unit="s")
    # sıra: open, close, low, high
    return pd.DataFrame(
        {"o": arr[:, 1], "c": arr[:, 2], "l": arr[:, 3], "h": arr[:, 4], "v": vol.astype(float)},
        index=idx,
    )


def fetch_day(sym, day):
    out = {}
    for side in ("BID", "ASK"):
        raw = get(URL.format(s=sym, y=day.year, m=day.month - 1, d=day.day, side=side))
        if raw is None:
            return day, None, "err"
        out[side] = parse(raw, day)
    if out["BID"] is None or out["ASK"] is None:
        return day, None, "empty"
    b, a = out["BID"], out["ASK"]
    df = pd.DataFrame(
        {
            "bo": b.o, "bh": b.h, "bl": b.l, "bc": b.c,
            "ao": a.o, "ah": a.h, "al": a.l, "ac": a.c,
            "v": b.v,
        }
    ).dropna()
    df = df[df.v > 0]
    return day, df, "ok"


def scale(df, lo, hi):
    med = df.bc.median()
    for k in range(0, 7):
        p = med / 10 ** k
        if lo <= p <= hi:
            return 10 ** k
    raise ValueError(f"ölçek bulunamadı, medyan={med}")


def main(symbols):
    os.makedirs(OUT, exist_ok=True)
    days = [START + dt.timedelta(days=i) for i in range((END - START).days + 1)]
    days = [d for d in days if d.weekday() < 5]
    for sym in symbols:
        path = os.path.join(OUT, f"{sym}.parquet")
        if os.path.exists(path):
            print(sym, "önbellekte var, atlanıyor", flush=True)
            continue
        parts, stats = [], {"ok": 0, "empty": 0, "err": 0}
        t0 = time.time()
        with cf.ThreadPoolExecutor(12) as ex:
            for day, df, st in ex.map(lambda d: fetch_day(sym, d), days):
                stats[st] += 1
                if df is not None and len(df):
                    parts.append(df)
        full = pd.concat(parts).sort_index()
        k = scale(full, *SYMBOLS[sym])
        for c in ["bo", "bh", "bl", "bc", "ao", "ah", "al", "ac"]:
            full[c] = full[c].astype(float) / k
        full.to_parquet(path)
        print(f"{sym}: {len(full)} dakika, ölçek={k}, {stats}, {time.time()-t0:.0f} sn", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or list(SYMBOLS))
