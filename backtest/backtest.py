"""Seans açılış kırılımı (ORB) geri testi — kurallar baştan sabit, optimizasyon yok.

Kullanım: python backtest.py   → results/sonuc.md ve results/islemler.csv
"""
import datetime as dt
import math
import os
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "data")
RES = os.path.join(HERE, "results")
TR = ZoneInfo("Europe/Istanbul")

# Ek kayma (her yön, fiyat birimi) — Dukascopy spread'ine EK olarak yurtdışı kurum payı
SLIP = {"XAUUSD": 0.10, "XAGUSD": 0.005, "DEUIDXEUR": 0.5, "USATECHIDXUSD": 0.5}
NAME = {"XAUUSD": "Altın", "XAGUSD": "Gümüş", "DEUIDXEUR": "DAX", "USATECHIDXUSD": "Nasdaq"}

# (etiket, sembol, borsa saat dilimi, açılış yerel saati)
WINDOWS = [
    ("Altın 11:00 (Londra)", "XAUUSD", "Europe/London", "08:00"),
    ("Altın 16:30 (ABD verisi)", "XAUUSD", "America/New_York", "08:30"),
    ("Altın 17:30 (NY açılış)", "XAUUSD", "America/New_York", "09:30"),
    ("Gümüş 17:30 (NY açılış)", "XAGUSD", "America/New_York", "09:30"),
    ("DAX 11:00", "DEUIDXEUR", "Europe/Berlin", "09:00"),
    ("Nasdaq 11:00", "USATECHIDXUSD", "Europe/Berlin", "09:00"),
    ("Nasdaq 17:30", "USATECHIDXUSD", "America/New_York", "09:30"),
]

OR_MIN = 15          # açılış aralığı
ENTRY_MIN = 75       # açılıştan sonra en geç giriş
CLOSE_MIN = 120      # açılıştan sonra her şey kapanır
BUF_ATR = 0.10       # kırılım tamponu: 0.1 x ATR(5dk)
SKIP_WIDE = 0.60     # aralık > 0.6 x günlük ATR ise işlem yok
MID_STOP = 0.35      # aralık > 0.35 x günlük ATR ise stop aralık ortası
OOS_FROM = 2023      # 2023 ve sonrası: örneklem dışı kontrol


def load(sym):
    import glob
    df = pd.concat(pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(DATA, f"{sym}_*.parquet")))).sort_index()
    df = df[~df.index.duplicated()]
    out = pd.DataFrame(index=df.index)
    for k in "ohlc":
        out[k] = (df["b" + k] + df["a" + k]) / 2
    out["s"] = (df.ac - df.bc).clip(lower=0)
    out["v"] = df.v
    return out


def five_min(m):
    b = m.resample("5min", label="left", closed="left").agg(
        {"o": "first", "h": "max", "l": "min", "c": "last", "v": "sum"}
    ).dropna()
    tr = pd.concat([b.h - b.l, (b.h - b.c.shift()).abs(), (b.l - b.c.shift()).abs()], axis=1).max(axis=1)
    b["atr"] = tr.rolling(14).mean()
    b["ema"] = b.c.ewm(span=20, adjust=False).mean()
    return b


def daily_atr(m):
    d = m.resample("1D").agg({"h": "max", "l": "min", "c": "last"}).dropna()
    tr = pd.concat([d.h - d.l, (d.h - d.c.shift()).abs(), (d.l - d.c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(14).mean().shift(1)  # dünün bilgisiyle


def first_friday(d):
    return d.weekday() == 4 and d.day <= 7


def simulate(sess, b5, side, entry_t, entry, stop, end_t, variant, s_on, slip):
    """sess: 1dk mumlar (UTC index). Dönüş: R sonucu."""
    risk = abs(entry - stop)
    sign = 1 if side == "L" else -1
    tp1 = entry + sign * (1.5 if variant == "A" else 1.0) * risk
    tp2 = entry + sign * 2.5 * risk
    half_done, cur_stop, pnl = False, stop, 0.0
    after = sess[(sess.index > entry_t) & (sess.index < end_t)]
    for t, r in after.iterrows():
        sp = r.s / 2 if s_on else 0.0
        lo_exec = r.l - sp if side == "L" else r.l + sp  # long: bid low ; short: ask low
        hi_exec = r.h - sp if side == "L" else r.h + sp
        rem = 0.5 if half_done else 1.0
        # stop önce (temkinli)
        if (side == "L" and lo_exec <= cur_stop) or (side == "S" and hi_exec >= cur_stop):
            px = cur_stop - sign * slip
            return pnl + rem * sign * (px - entry) / risk
        # hedefler
        if not half_done and ((side == "L" and hi_exec >= tp1) or (side == "S" and lo_exec <= tp1)):
            pnl += 0.5 * sign * (tp1 - entry) / risk
            half_done, cur_stop = True, entry
            continue
        if variant == "B":
            if half_done and ((side == "L" and hi_exec >= tp2) or (side == "S" and lo_exec <= tp2)):
                return pnl + 0.5 * sign * (tp2 - entry) / risk
            mins = (t - entry_t).total_seconds() / 60
            close_px = r.c - sign * sp - sign * slip
            if not half_done and mins >= 45:  # zaman stopu
                return pnl + sign * (close_px - entry) / risk
            if half_done and (t + pd.Timedelta(minutes=1)).minute % 5 == 0:
                bar_t = t - pd.Timedelta(minutes=4)
                if bar_t in b5.index:
                    bc, em = b5.at[bar_t, "c"], b5.at[bar_t, "ema"]
                    if (side == "L" and bc < em) or (side == "S" and bc > em):
                        return pnl + 0.5 * sign * (close_px - entry) / risk
    # seans sonu
    if len(after):
        r = after.iloc[-1]
        sp = r.s / 2 if s_on else 0.0
        px = r.c - sign * sp - sign * slip
        return pnl + (0.5 if half_done else 1.0) * sign * (px - entry) / risk
    return pnl


def run_window(label, sym, tzname, hhmm, m, b5, datr):
    tz = ZoneInfo(tzname)
    h, mi = map(int, hhmm.split(":"))
    local_days = sorted(set(m.index.tz_convert(tz).date))
    rows = []
    for d in local_days:
        if d.weekday() >= 5 or first_friday(d):
            continue
        o = pd.Timestamp(dt.datetime(d.year, d.month, d.day, h, mi, tzinfo=tz)).tz_convert("UTC")
        or_end, ent_end, end = (o + pd.Timedelta(minutes=x) for x in (OR_MIN, ENTRY_MIN, CLOSE_MIN))
        sess = m.loc[o:end - pd.Timedelta('1ns')]
        if len(sess) < CLOSE_MIN * 0.8:
            continue
        orb = sess[sess.index < or_end]
        if len(orb) < OR_MIN * 0.8:
            continue
        orh, orl = orb.h.max(), orb.l.min()
        width = orh - orl
        dkey = pd.Timestamp(o.date(), tz="UTC")
        da = datr.get(dkey, np.nan)
        if not np.isfinite(da) or width <= 0 or width > SKIP_WIDE * da:
            continue
        pv = (sess.c * sess.v).cumsum() / sess.v.cumsum().replace(0, np.nan)
        bars = b5.loc[or_end:ent_end - pd.Timedelta(minutes=5)]
        for bt, bar in bars.iterrows():
            close_t = bt + pd.Timedelta(minutes=4)
            if close_t not in sess.index or not np.isfinite(bar.atr):
                continue
            buf = BUF_ATR * bar.atr
            vw = pv.get(close_t, np.nan)
            side = None
            if bar.c > orh + buf and bar.c > vw:
                side = "L"
            elif bar.c < orl - buf and bar.c < vw:
                side = "S"
            if not side:
                continue
            stop = (orh + orl) / 2 if width > MID_STOP * da else (orl if side == "L" else orh)
            sp = sess.at[close_t, "s"] / 2
            sign = 1 if side == "L" else -1
            res = {"pencere": label, "enstruman": NAME[sym], "tarih": d, "yon": side,
                   "aralik": width, "spread_pay": 0.0}
            for tag, s_on, slip in (("brut", False, 0.0), ("net", True, SLIP[sym])):
                entry = bar.c + sign * ((sp if s_on else 0) + slip)
                if (entry - stop) * sign <= 0:
                    res[f"A_{tag}"] = res[f"B_{tag}"] = np.nan
                    continue
                for var in ("A", "B"):
                    res[f"{var}_{tag}"] = simulate(sess, b5, side, close_t, entry, stop, end, var, s_on, slip)
                if tag == "net":
                    res["spread_pay"] = (sp * 2 + 2 * slip) / abs(entry - stop)
            rows.append(res)
            break  # günde 1 işlem
    return rows


def stats(x):
    x = pd.Series(x).dropna()
    n = len(x)
    if n == 0:
        return dict(n=0)
    eq = x.cumsum()
    dd = (eq - eq.cummax()).min()
    sd = x.std(ddof=1) if n > 1 else np.nan
    return dict(n=n, kazanma=(x > 0).mean() * 100, ortR=x.mean(), toplamR=x.sum(),
                maxDD=dd, t=x.mean() / (sd / math.sqrt(n)) if sd and sd > 0 else np.nan)


def main():
    os.makedirs(RES, exist_ok=True)
    cache, allrows = {}, []
    for label, sym, tzname, hhmm in WINDOWS:
        if sym not in cache:
            m = load(sym)
            cache[sym] = (m, five_min(m), daily_atr(m))
        m, b5, da = cache[sym]
        rows = run_window(label, sym, tzname, hhmm, m, b5, da)
        print(label, len(rows), "işlem", flush=True)
        allrows += rows
    tr = pd.DataFrame(allrows)
    tr["yil"] = pd.to_datetime(tr.tarih).dt.year
    tr.to_csv(os.path.join(RES, "islemler.csv"), index=False)

    L = ["# ORB geri test sonuçları", "",
         f"Veri: Dukascopy 1 dk alış/satış, {tr.tarih.min()} – {tr.tarih.max()}. "
         "Net = gerçek spread + ek kayma düşülmüş. R = stop mesafesi (1R = işlem başı risk).", "",
         "A = yarısı 1,5R, kalan başabaş/seans sonu · B = yarısı 1R, kalan EMA20 takip / 2,5R, 45 dk zaman stopu", ""]
    L.append("| Pencere | Varyant | İşlem | Kazanma % | Brüt ort R | Net ort R | Net toplam R | Max DD R | t | 2021-22 net | 2023+ net | Spread/R |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    summ = []
    for label, *_ in WINDOWS:
        g = tr[tr.pencere == label]
        for var in ("A", "B"):
            sb, sn = stats(g[f"{var}_brut"]), stats(g[f"{var}_net"])
            ins = g[g.yil < OOS_FROM][f"{var}_net"].mean()
            oos = g[g.yil >= OOS_FROM][f"{var}_net"].mean()
            cost = g.spread_pay.median()
            if sn.get("n", 0) == 0:
                continue
            summ.append((label, var, sn["ortR"], oos, sn["n"], sn["t"]))
            L.append(f"| {label} | {var} | {sn['n']} | {sn['kazanma']:.0f} | {sb['ortR']:+.3f} | {sn['ortR']:+.3f} | "
                     f"{sn['toplamR']:+.1f} | {sn['maxDD']:.1f} | {sn['t']:.2f} | {ins:+.3f} | {oos:+.3f} | {cost:.2f} |")
    L += ["", "## Yıllara göre net ortalama R (varyant B)", ""]
    piv = tr.pivot_table(index="pencere", columns="yil", values="B_net", aggfunc="mean")
    L.append("| Pencere | " + " | ".join(str(c) for c in piv.columns) + " |")
    L.append("|---|" + "---|" * len(piv.columns))
    for lab in piv.index:
        L.append(f"| {lab} | " + " | ".join(f"{v:+.2f}" if np.isfinite(v) else "–" for v in piv.loc[lab]) + " |")
    L += ["", "## Karar kuralı: net ort ≥ +0,10R VE 2023+ net ≥ +0,10R VE t ≥ 2", ""]
    for label, var, avg, oos, n, t in summ:
        ok = avg >= 0.10 and oos >= 0.10 and (t or 0) >= 2
        L.append(f"- {'✅' if ok else '❌'} {label} / {var}: net {avg:+.3f}R, 2023+ {oos:+.3f}R, t={t:.2f}, n={n}")
    open(os.path.join(RES, "sonuc.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
