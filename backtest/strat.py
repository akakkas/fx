"""BBO (Bollinger kırılımı) ve ST (Supertrend) geri testi — 15 dk, seans içi, gece pozisyon yok.

Kurallar baştan sabit:
  BBO: 15dk kapanış BB(20,2) dışına ilk kez çıkarsa o yöne gir. Stop = orta bant.
  ST : ST(10,3) yön değiştirince gir. Stop = ST çizgisi.
  Ortak: stop < 0.3*ATR ise atla (gürültü). Yarısı 1R'da kapanır, stop girişe çekilir.
         Kalan: BBO'da kapanış orta bandın ters tarafına geçince, ST'de ST tersine dönünce çıkar.
         Seans sonunda her şey kapanır.
Çıktı: results/sonuc_bbo_st.md, results/islemler_bbo_st.csv
"""
import datetime as dt
import glob
import math
import os
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "data")
RES = os.path.join(HERE, "results")
SLIP = {"XAUUSD": 0.10, "XAGUSD": 0.005, "DEUIDXEUR": 0.5, "USATECHIDXUSD": 0.5}
NAME = {"XAUUSD": "Altın", "XAGUSD": "Gümüş", "DEUIDXEUR": "DAX", "USATECHIDXUSD": "Nasdaq"}
# İşlem penceresi (borsa yerel saati): sinyal bu aralıkta, her şey bitişte kapanır
SESS = {
    "XAUUSD": ("Europe/London", "08:00", "America/New_York", "16:00"),
    "XAGUSD": ("Europe/London", "08:00", "America/New_York", "16:00"),
    "DEUIDXEUR": ("Europe/Berlin", "09:00", "Europe/Berlin", "17:30"),
    "USATECHIDXUSD": ("America/New_York", "09:30", "America/New_York", "16:00"),
}
TF = "15min"
OOS_FROM = 2023


def load(sym):
    fs = sorted(glob.glob(os.path.join(DATA, f"{sym}_*.parquet")))
    df = pd.concat(pd.read_parquet(f) for f in fs).sort_index()
    df = df[~df.index.duplicated()]
    m = pd.DataFrame(index=df.index)
    for k in "ohlc":
        m[k] = (df["b" + k] + df["a" + k]) / 2
    m["s"] = (df.ac - df.bc).clip(lower=0)
    return m


def bars(m):
    b = m.resample(TF, label="left", closed="left").agg({"o": "first", "h": "max", "l": "min", "c": "last"}).dropna()
    tr = pd.concat([b.h - b.l, (b.h - b.c.shift()).abs(), (b.l - b.c.shift()).abs()], axis=1).max(axis=1)
    b["atr"] = tr.rolling(14).mean()
    mid = b.c.rolling(20).mean()
    sd = b.c.rolling(20).std(ddof=0)
    b["mid"], b["up"], b["dn"] = mid, mid + 2 * sd, mid - 2 * sd
    # Supertrend(10,3)
    atr10 = tr.ewm(alpha=1 / 10, adjust=False).mean()
    hl2 = (b.h + b.l) / 2
    ub, lb = (hl2 + 3 * atr10).values, (hl2 - 3 * atr10).values
    c = b.c.values
    fub, flb = ub.copy(), lb.copy()
    st, dirn = np.full(len(b), np.nan), np.zeros(len(b), dtype=int)
    for i in range(1, len(b)):
        fub[i] = ub[i] if (ub[i] < fub[i - 1] or c[i - 1] > fub[i - 1]) else fub[i - 1]
        flb[i] = lb[i] if (lb[i] > flb[i - 1] or c[i - 1] < flb[i - 1]) else flb[i - 1]
        if dirn[i - 1] >= 0:
            dirn[i] = -1 if c[i] < flb[i] else 1
        else:
            dirn[i] = 1 if c[i] > fub[i] else -1
        st[i] = flb[i] if dirn[i] == 1 else fub[i]
    b["st"], b["dir"] = st, dirn
    return b


def windows(sym, days):
    tz1, h1, tz2, h2 = SESS[sym]
    out = {}
    for d in days:
        if d.weekday() >= 5:
            continue
        a = pd.Timestamp(dt.datetime.combine(d, dt.time.fromisoformat(h1)), tz=ZoneInfo(tz1)).tz_convert("UTC")
        b = pd.Timestamp(dt.datetime.combine(d, dt.time.fromisoformat(h2)), tz=ZoneInfo(tz2)).tz_convert("UTC")
        out[d] = (a, b)
    return out


def run(sym, strat, m, b, costs):
    s_on, slip = costs
    rows = []
    days = sorted(set(b.index.date))
    for d, (ws, we) in windows(sym, days).items():
        day_b = b.loc[ws:we - pd.Timedelta("1ns")]
        if len(day_b) < 8:
            continue
        free_at = ws
        for i in range(1, len(day_b)):
            t = day_b.index[i]
            close_t = t + pd.Timedelta(TF) - pd.Timedelta("1min")
            if t < free_at or close_t >= we - pd.Timedelta("15min"):
                continue
            r, p = day_b.iloc[i], day_b.iloc[i - 1]
            if not np.isfinite(r.atr) or not np.isfinite(r.mid):
                continue
            side = None
            if strat == "BBO":
                if r.c > r.up and p.c <= p.up:
                    side, stop = "L", r.mid
                elif r.c < r.dn and p.c >= p.dn:
                    side, stop = "S", r.mid
            else:
                if r.dir == 1 and p.dir == -1:
                    side, stop = "L", r.st
                elif r.dir == -1 and p.dir == 1:
                    side, stop = "S", r.st
            if not side:
                continue
            sign = 1 if side == "L" else -1
            if close_t not in m.index:
                continue
            sp = m.at[close_t, "s"] / 2 if s_on else 0.0
            entry = r.c + sign * (sp + slip)
            risk = (entry - stop) * sign
            if risk <= 0.3 * r.atr:
                continue
            res, exit_t = simulate(m, b, strat, side, close_t, entry, stop, risk, we, s_on, slip)
            rows.append({"enstruman": NAME[sym], "strateji": strat, "tarih": d, "yon": side, "R": res})
            free_at = exit_t
    return rows


def simulate(m, b, strat, side, t0, entry, stop, risk, end, s_on, slip):
    sign = 1 if side == "L" else -1
    tp1 = entry + sign * risk
    half, cur, pnl = False, stop, 0.0
    seg = m.loc[t0 + pd.Timedelta("1min"):end - pd.Timedelta("1ns")]
    last_t = t0
    for t, r in zip(seg.index, seg.itertuples()):
        last_t = t
        sp = r.s / 2 if s_on else 0.0
        lo = r.l - sign * sp if side == "L" else r.l + sp
        hi = r.h - sp if side == "L" else r.h + sp
        rem = 0.5 if half else 1.0
        if (side == "L" and lo <= cur) or (side == "S" and hi >= cur):
            return pnl + rem * sign * (cur - sign * slip - entry) / risk, t
        if not half and ((side == "L" and hi >= tp1) or (side == "S" and lo <= tp1)):
            pnl += 0.5 * (tp1 - entry) * sign / risk
            half, cur = True, entry
            continue
        if (t + pd.Timedelta("1min")).minute % 15 == 0:
            bt = t + pd.Timedelta("1min") - pd.Timedelta(TF)
            if bt in b.index:
                br = b.loc[bt]
                rev = (br.c < br.mid if side == "L" else br.c > br.mid) if strat == "BBO" else (br.dir == -sign)
                if rev:
                    px = r.c - sign * sp - sign * slip
                    return pnl + rem * sign * (px - entry) / risk, t
    if len(seg):
        r = seg.iloc[-1]
        sp = r.s / 2 if s_on else 0.0
        px = r.c - sign * sp - sign * slip
        return pnl + (0.5 if half else 1.0) * sign * (px - entry) / risk, last_t
    return pnl, last_t


def stats(x):
    x = pd.Series(x).dropna()
    n = len(x)
    if n < 2:
        return dict(n=n, kaz=np.nan, ort=np.nan, top=np.nan, dd=np.nan, t=np.nan)
    eq = x.cumsum()
    sd = x.std(ddof=1)
    return dict(n=n, kaz=(x > 0).mean() * 100, ort=x.mean(), top=x.sum(),
                dd=(eq - eq.cummax()).min(), t=x.mean() / (sd / math.sqrt(n)) if sd > 0 else np.nan)


def main():
    os.makedirs(RES, exist_ok=True)
    allrows = []
    cover = []
    for sym in SLIP:
        m = load(sym)
        b = bars(m)
        nd = len(set(m.index.date))
        cover.append(f"{NAME[sym]}: {nd} gün veri")
        for strat in ("BBO", "ST"):
            g = pd.DataFrame(run(sym, strat, m, b, (False, 0.0)))
            n = pd.DataFrame(run(sym, strat, m, b, (True, SLIP[sym])))
            if len(n):
                n["brutR"] = g.R.mean() if len(g) else np.nan
                allrows.append(n)
            print(NAME[sym], strat, len(n), "işlem", flush=True)
    tr = pd.concat(allrows)
    tr["yil"] = pd.to_datetime(tr.tarih).dt.year
    tr.to_csv(os.path.join(RES, "islemler_bbo_st.csv"), index=False)
    L = ["# BBO ve ST geri test sonuçları (15 dk, seans içi)", "", "Veri kapsamı: " + " · ".join(cover), "",
         "| Enstrüman | Sinyal | İşlem | Kazanma % | Brüt ort R | Net ort R | Net toplam R | Max DD R | t | 2021-22 net | 2023+ net |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    verdict = []
    for (ens, strat), g in tr.groupby(["enstruman", "strateji"]):
        s = stats(g.R)
        ins, oos = g[g.yil < OOS_FROM].R.mean(), g[g.yil >= OOS_FROM].R.mean()
        L.append(f"| {ens} | {strat} | {s['n']} | {s['kaz']:.0f} | {g.brutR.iloc[0]:+.3f} | {s['ort']:+.3f} | {s['top']:+.1f} | "
                 f"{s['dd']:.1f} | {s['t']:.2f} | {ins:+.3f} | {oos:+.3f} |")
        ok = s["ort"] >= 0.10 and oos >= 0.10 and (s["t"] or 0) >= 2
        verdict.append(f"- {'✅' if ok else '❌'} {ens} / {strat}: net {s['ort']:+.3f}R, 2023+ {oos:+.3f}R, t={s['t']:.2f}, n={s['n']}")
    L += ["", "## Yıllara göre net ortalama R", ""]
    piv = tr.pivot_table(index=["enstruman", "strateji"], columns="yil", values="R", aggfunc="mean")
    L.append("| Enstrüman / sinyal | " + " | ".join(map(str, piv.columns)) + " |")
    L.append("|---|" + "---|" * len(piv.columns))
    for idx in piv.index:
        L.append(f"| {idx[0]} {idx[1]} | " + " | ".join(f"{v:+.2f}" if np.isfinite(v) else "–" for v in piv.loc[idx]) + " |")
    L += ["", "## Karar kuralı: net ort ≥ +0,10R VE 2023+ ≥ +0,10R VE t ≥ 2", ""] + verdict
    open(os.path.join(RES, "sonuc_bbo_st.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
