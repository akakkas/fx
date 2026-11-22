"""Kemal'in TSMC2 fikri: 15 dk Supertrend dönüşü + 1 saatlik ST aynı yönde ("uyumlu").
Karşılaştırma için aynı icrayla filtresiz 15 dk ST de test edilir. Parametreler sabit: ST(10,3), 1s ST(10,3).
Çıkış: ilk stop = 15 dk ST çizgisi (sabit), 15 dk ST ters dönünce kapanış, en geç pencere sonu.
"""
import datetime as dt
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd


def st(b, n=10, k=3.0):
    h, l, c = b.h.values, b.l.values, b.c.values
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))
    atr = pd.Series(tr).ewm(alpha=1 / n, adjust=False).mean().values
    atr14 = pd.Series(tr).rolling(14).mean().values
    hl2 = (h + l) / 2
    ub, lb = hl2 + k * atr, hl2 - k * atr
    fub, flb = ub.copy(), lb.copy()
    d = np.zeros(len(b), dtype=int)
    line = np.full(len(b), np.nan)
    for i in range(1, len(b)):
        fub[i] = ub[i] if (ub[i] < fub[i - 1] or c[i - 1] > fub[i - 1]) else fub[i - 1]
        flb[i] = lb[i] if (lb[i] > flb[i - 1] or c[i - 1] < flb[i - 1]) else flb[i - 1]
        d[i] = (-1 if c[i] < flb[i] else 1) if d[i - 1] >= 0 else (1 if c[i] > fub[i] else -1)
        line[i] = flb[i] if d[i] == 1 else fub[i]
    return d, line, atr14


def bars(m, tf):
    return m.resample(tf, label="left", closed="left").agg({"o": "first", "h": "max", "l": "min", "c": "last"}).dropna()


PENCERE = {
    "gunduz": {"XAUUSD": ("Europe/London", "08:00", "America/New_York", "16:00"),
               "XAGUSD": ("Europe/London", "08:00", "America/New_York", "16:00"),
               "DEUIDXEUR": ("Europe/Berlin", "09:00", "Europe/Berlin", "17:30"),
               "USATECHIDXUSD": ("America/New_York", "09:30", "America/New_York", "16:00")},
    "gece": {"XAUUSD": ("Europe/London", "00:00", "Europe/London", "07:45"),
             "XAGUSD": ("Europe/London", "00:00", "Europe/London", "07:45")},
}


def sinyaller(sym, data, filtre, pencere):
    m = data[sym]
    b15 = bars(m, "15min")
    d15, l15, a15 = st(b15)
    b60 = bars(m, "60min")
    d60, _, _ = st(b60)
    # 1s yönü: 15 dk mum kapanışında (T) en son KAPANMIŞ 1 saatlik mumun yönü
    close15 = b15.index + pd.Timedelta("15min")
    close60 = b60.index + pd.Timedelta("60min")
    idx = np.searchsorted(close60.values, close15.values, side="right") - 1
    d1s = np.where(idx >= 0, d60[np.clip(idx, 0, None)], 0)
    tz1, h1, tz2, h2 = PENCERE[pencere][sym]
    out = []
    flips = np.where(np.r_[False, d15[1:] != d15[:-1]])[0]
    flipset = set(flips.tolist())
    days = sorted(set(b15.index.date))
    win = {}
    for d in days:
        if d.weekday() >= 5:
            continue
        a = pd.Timestamp(dt.datetime.combine(d, dt.time.fromisoformat(h1)), tz=ZoneInfo(tz1)).tz_convert("UTC")
        e = pd.Timestamp(dt.datetime.combine(d, dt.time.fromisoformat(h2)), tz=ZoneInfo(tz2)).tz_convert("UTC")
        win[d] = (a, e)
    for i in flips:
        if i < 30:
            continue
        T = close15[i]
        dd = (T - pd.Timedelta("1min")).date()
        if dd not in win:
            continue
        a, e = win[dd]
        if not (a < T <= e - pd.Timedelta("15min")):
            continue
        yon = "L" if d15[i] == 1 else "S"
        if filtre and d1s[i] != d15[i]:
            continue
        stop = l15[i]
        if not np.isfinite(stop) or not np.isfinite(a15[i]) or abs(b15.c.values[i] - stop) <= 0.3 * a15[i]:
            continue
        # çıkış: sonraki 15 dk ST dönüşünün kapanışı ya da pencere sonu
        j = next((f for f in flips[flips > i]), None)
        bitis = min(close15[j], e) if j is not None else e
        out.append({"t": T - pd.Timedelta("1min"), "yon": yon, "stop": float(stop), "hedef": None, "bitis": bitis})
    return out
