"""Özgün indikatör yarışması — ortak test düzeneği.

Her aday backtest/ozgun/<kod>.py dosyasıdır ve şunları tanımlar:
  AD: str                kısa ad
  ACIKLAMA: str          Türkçe, 2-4 cümle: fikir ve neden çalışabilir
  SEMBOLLER: list[str]   hangi enstrümanlarda (XAUUSD, XAGUSD, DEUIDXEUR, USATECHIDXUSD)
  def sinyaller(sym, data) -> list[dict]
      data: {sym: DataFrame} — 1 dk UTC, kolonlar o,h,l,c (orta fiyat), s (spread), tüm semboller
      Her sinyal: {"t": Timestamp (sinyalin oluştuğu 1 dk mumunun açılış zamanı; giriş o mumun kapanışında),
                   "yon": "L" | "S", "stop": float, "hedef": float | None, "bitis": Timestamp}
      bitis = en geç çıkış zamanı (zaman stopu / seans sonu). Gelecek veriye bakmak YASAK:
      t anındaki sinyal yalnız t mumunun kapanışına kadarki veriyi kullanabilir.

Düzenek her aday için aynı icrayı yapar (aday icrayı seçemez, hile olmasın):
  giriş = t mumunun kapanışı ± yarım spread ± kayma; stop/hedef 1 dk mumlarla kontrol;
  aynı mumda ikisi de değerse stop sayılır; bitis'te piyasadan kapanır.
  Aynı sembolde aynı anda tek pozisyon. Stop mesafesi ≥ 3×spread değilse işlem atlanır.
Karar kuralı: net ort ≥ +0,10R VE 2023+ net ≥ +0,10R VE t ≥ 2.
"""
import glob
import importlib.util
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RES = os.path.join(HERE, "results")
SLIP = {"XAUUSD": 0.10, "XAGUSD": 0.005, "DEUIDXEUR": 0.5, "USATECHIDXUSD": 0.5}
NAME = {"XAUUSD": "Altın", "XAGUSD": "Gümüş", "DEUIDXEUR": "DAX", "USATECHIDXUSD": "Nasdaq"}
OOS_FROM = 2023


def load(sym):
    fs = sorted(glob.glob(os.path.join(DATA, f"{sym}_*.parquet")))
    if not fs:
        return None
    df = pd.concat(pd.read_parquet(f) for f in fs).sort_index()
    df = df[~df.index.duplicated()]
    m = pd.DataFrame(index=df.index)
    for k in "ohlc":
        m[k] = (df["b" + k] + df["a" + k]) / 2
    m["s"] = (df.ac - df.bc).clip(lower=0)
    return m


def sentetik(sym, gun=60, seed=0):
    """Yerel deneme için sahte 1 dk veri (gerçek sonuç değildir)."""
    rng = np.random.default_rng(seed + hash(sym) % 1000)
    base = {"XAUUSD": 2000, "XAGUSD": 25, "DEUIDXEUR": 16000, "USATECHIDXUSD": 15000}[sym]
    idx = pd.date_range("2022-12-01", periods=gun * 1440, freq="1min", tz="UTC")
    idx = idx[idx.weekday < 5]
    ret = rng.normal(0, 0.0003, len(idx))
    c = base * np.exp(np.cumsum(ret))
    o = np.r_[c[0], c[:-1]]
    hi = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.0001, len(idx))))
    lo = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.0001, len(idx))))
    s = np.full(len(idx), base * 0.00008)
    return pd.DataFrame({"o": o, "h": hi, "l": lo, "c": c, "s": s}, index=idx)


def icra(sym, m, sig, slip):
    t, yon, stop, hedef, bitis = sig["t"], sig["yon"], float(sig["stop"]), sig.get("hedef"), sig["bitis"]
    if t not in m.index:
        return None
    sign = 1 if yon == "L" else -1
    r0 = m.loc[t]
    entry = r0.c + sign * (r0.s / 2 + slip)
    risk = (entry - stop) * sign
    if not np.isfinite(risk) or risk <= 3 * max(r0.s, 1e-12):
        return None
    seg = m.loc[t + pd.Timedelta("1min"): bitis - pd.Timedelta("1ns")]
    if not len(seg):
        return None
    bid_l = seg.l.values - seg.s.values / 2   # long kapatırken satış fiyatı (dip)
    ask_h = seg.h.values + seg.s.values / 2   # short kapatırken alış fiyatı (tepe)
    bid_h = seg.h.values - seg.s.values / 2
    ask_l = seg.l.values + seg.s.values / 2
    for i in range(len(seg)):
        if yon == "L":
            if bid_l[i] <= stop:
                return (stop - slip - entry) / risk, seg.index[i]
            if hedef is not None and bid_h[i] >= hedef:
                return (hedef - entry) / risk, seg.index[i]
        else:
            if ask_h[i] >= stop:
                return (entry - stop - slip) / risk, seg.index[i]
            if hedef is not None and ask_l[i] <= hedef:
                return (entry - hedef) / risk, seg.index[i]
    last = seg.iloc[-1]
    px = last.c - sign * (last.s / 2 + slip)
    return sign * (px - entry) / risk, seg.index[-1]


def stats(x):
    x = pd.Series(x).dropna()
    n = len(x)
    if n < 2:
        return dict(n=n, kaz=np.nan, ort=np.nan, top=np.nan, dd=np.nan, t=np.nan)
    eq = x.cumsum()
    sd = x.std(ddof=1)
    return dict(n=n, kaz=(x > 0).mean() * 100, ort=x.mean(), top=x.sum(),
                dd=(eq - eq.cummax()).min(), t=x.mean() / (sd / math.sqrt(n)) if sd > 0 else np.nan)


def adaylar():
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, "ozgun", "*.py"))):
        if os.path.basename(f).startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location("oz_" + os.path.basename(f)[:-3], f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out.append((os.path.basename(f)[:-3], mod))
    return out


def calistir(data, sadece=None):
    rows = []
    for kod, mod in adaylar():
        if sadece and kod != sadece:
            continue
        for sym in mod.SEMBOLLER:
            if sym not in data or data[sym] is None:
                continue
            m = data[sym]
            sigs = sorted(mod.sinyaller(sym, data), key=lambda s: s["t"])
            free = None
            for sg in sigs:
                if free is not None and sg["t"] < free:
                    continue
                r = icra(sym, m, sg, SLIP[sym])
                if r is None:
                    continue
                R, ex = r
                rows.append({"aday": kod, "ad": mod.AD, "enstruman": NAME[sym], "tarih": sg["t"].date(), "yon": sg["yon"], "R": R})
                free = ex + pd.Timedelta("1min")
            print(kod, sym, sum(1 for x in rows if x["aday"] == kod and x["enstruman"] == NAME[sym]), "işlem", flush=True)
    return pd.DataFrame(rows)


def rapor(tr, cover, mods):
    L = ["# Özgün indikatör yarışması — sonuçlar", "", "Veri: " + cover, "",
         "İcra her aday için aynı (spread + kayma düşülmüş, tek pozisyon). Karar: net ≥ +0,10R VE 2023+ ≥ +0,10R VE t ≥ 2.", ""]
    for kod, mod in mods:
        L += [f"## {mod.AD} (`{kod}`)", "", mod.ACIKLAMA.strip(), ""]
        g0 = tr[tr.aday == kod] if len(tr) else tr
        if not len(g0):
            L += ["İşlem yok.", ""]
            continue
        L += ["| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |", "|---|---|---|---|---|---|---|---|---|---|"]
        for ens, g in g0.groupby("enstruman"):
            s = stats(g.R)
            y = pd.to_datetime(g.tarih).dt.year
            ins, oos = g[y < OOS_FROM].R.mean(), g[y >= OOS_FROM].R.mean()
            ok = (s["ort"] or -9) >= 0.10 and (oos if np.isfinite(oos) else -9) >= 0.10 and (s["t"] or 0) >= 2
            L.append(f"| {ens} | {s['n']} | {s['kaz']:.0f} | {s['ort']:+.3f} | {s['top']:+.1f} | {s['dd']:.1f} | {s['t']:.2f} | {ins:+.3f} | {oos:+.3f} | {'✅' if ok else '❌'} |")
        piv = g0.assign(yil=pd.to_datetime(g0.tarih).dt.year).pivot_table(index="enstruman", columns="yil", values="R", aggfunc="mean")
        L += ["", "Yıllara göre net ort R: " + " · ".join(f"{e} " + "/".join(f"{v:+.2f}" for v in piv.loc[e].dropna()) for e in piv.index), ""]
    return "\n".join(L) + "\n"


def main():
    sent = "--sentetik" in sys.argv
    syms = list(SLIP)
    data = {s: (sentetik(s) if sent else load(s)) for s in syms}
    cover = " · ".join(f"{NAME[s]} {len(set(data[s].index.date)) if data[s] is not None else 0} gün" for s in syms) + (" (SENTETİK — anlamsız)" if sent else "")
    sadece = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--aday=")), None)
    tr = calistir(data, sadece)
    mods = [x for x in adaylar() if not sadece or x[0] == sadece]
    txt = rapor(tr, cover, mods)
    if not sent:
        os.makedirs(RES, exist_ok=True)
        open(os.path.join(RES, "sonuc_ozgun.md"), "w").write(txt)
        tr.to_csv(os.path.join(RES, "islemler_ozgun.csv"), index=False)
    print(txt)


if __name__ == "__main__":
    main()
