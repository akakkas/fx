"""Çapraz piyasa uyumsuzluğu — GERİDE KALANIN YETİŞMESİ (varyant A).

Fikir: Birbirine bağlı iki enstrümandan (Altın-Gümüş, Nasdaq-DAX) biri son W dakikada
kendi oynaklığına göre belirgin hareket ederken diğeri yerinde saydıysa, geride kalan
"yetişir". Ölçü oynaklığa göre normalize getiri farkıdır:

    z_x = log(c_t / c_{t-W}) / sigmaW_x      (sigmaW: son 5 günün W dakikalık log getirilerinin std'si)
    D   = z_ortak - z_kendi

Giriş (uzun; kısa için işaretler ters):
    z_ortak >= K  VE  D >= K  VE  kendi sinyal mumu yükselişle kapanır (c > o: geride kalan kımıldadı)
    Aynı olayda tekrar girmemek için bir tetikten sonra W dakika yeni tetik yok.
Birim hareket U = sigmaW_kendi * fiyat  (kendinin "normal" bir W dakikalık hareketi)
    stop  = c -/+ STOP_U * U
    hedef = c +/- 0.5 * D * U   (açığın yarısı: açık iki taraftan kapanır, geride kalanın payı yarı)
    bitis = min(t + 1 + H dk, seans sonu)

Serbest parametreler (veriye bakmadan sabitlendi, toplam 4):
    W = 15       dk  — haber/akış şoku ile yayılmanın tipik süresi; 1-5 dk gürültü, 60 dk "aynı gün trendi"
    K = 2.0          — normalize fark; Altın-Gümüş / DAX-Nasdaq 15 dk getiri korelasyonu ~0,7-0,8 iken
                       D'nin std'si ~sqrt(2(1-rho)) ≈ 0,6-0,8 → K=2 yaklaşık 2,5-3 sigma, seyrek olay
    STOP_U = 1.0     — kendinin bir normal W hareketi kadar ters gidiş tezi bozar
    H = 30       dk  — yetişme gerçekse W'nin ~2 katında olur; daha uzunu başka hikâye
Seanslar (zoneinfo, yaz/kış saati otomatik):
    Metaller: giriş 08:00 Londra – 12:00 New York, çıkış en geç 16:00 New York (Asya seansı ince, hariç)
    DAX: giriş 08:30 New York (ABD veri saati) – 17:00 Frankfurt, çıkış en geç 17:30 Frankfurt (Xetra kapanışı)
"""
import os
from datetime import time as dtime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

AD = "Çapraz uyumsuzluk — geride kalan yetişir"
ACIKLAMA = (
    "Altın ile gümüş, Nasdaq ile DAX normalde birlikte hareket eder. Son 15 dakikada biri kendi "
    "olağan oynaklığına göre belirgin yükselip (düşüp) diğeri yerinde saydıysa ve geride kalan "
    "aynı yöne kımıldamaya başladıysa, geride kalanda o yöne işlem açılır. Hedef aradaki açığın "
    "yarısının kapanması, stop geride kalanın bir normal 15 dakikalık hareketi kadar ters gidiş, "
    "en fazla 30 dakika tutulur ve seans sonunda kapanır; DAX'ta yalnız ABD verisi/açılışından "
    "Frankfurt kapanışına kadar, Nasdaq'ın DAX'ı sürüklediği saatlerde çalışır."
)
SEMBOLLER = ["XAUUSD", "XAGUSD", "DEUIDXEUR"]

# --- serbest parametreler (4) ---
W = 15
K = 2.0
STOP_U = 1.0
H = 30

ORTAK = {"XAUUSD": "XAGUSD", "XAGUSD": "XAUUSD", "DEUIDXEUR": "USATECHIDXUSD", "USATECHIDXUSD": "DEUIDXEUR"}
LON, NY, FRA = ZoneInfo("Europe/London"), ZoneInfo("America/New_York"), ZoneInfo("Europe/Berlin")
METAL = {"XAUUSD", "XAGUSD"}
BAYAT = 2          # ortağın son fiyatı en fazla 2 dk eski olabilir (hizalama toleransı, parametre değil)
VOL_PENCERE = "5D"  # oynaklık: son 5 günün W dk log getiri std'si (seans içi mevsimselliği ortalar)


def _pencere(sym):
    """(giriş başlangıç (tz, saat), giriş bitiş (tz, saat), seans sonu (tz, saat))"""
    if sym in METAL:
        return (LON, dtime(8, 0)), (NY, dtime(12, 0)), (NY, dtime(16, 0))
    return (NY, dtime(8, 30)), (FRA, dtime(17, 0)), (FRA, dtime(17, 30))


def _ana_seriler(sym, data):
    """Kendi ve ortağın z skorları, kendi sigma'sı — hepsi kendi 1 dk indeksinde, yalnız geçmiş veriyle."""
    m = data[sym]
    p = data.get(ORTAK[sym])
    if p is None or not len(p) or not len(m):
        return None
    lo = min(m.index[0], p.index[0])
    hi = max(m.index[-1], p.index[-1])
    grid = pd.date_range(lo, hi, freq="1min")

    def zser(df):
        lc = np.log(df.c.astype(float))
        lcg = lc.reindex(grid).ffill(limit=BAYAT)          # t'de bilinen son kapanış (≤2 dk bayat)
        ret = lcg - lcg.shift(W)                           # W dk getiri, aynı ızgarada
        # ölçek: son 5 günün W dakikalık getirilerinin std'si (1 dk std×sqrt(W) değil: 1 dk getirilerdeki
        # oto-korelasyon/mikro yapı gürültüsü ölçeği bozmasın). Yalnız t'ye kadarki getiriler.
        sigW = ret.rolling(VOL_PENCERE, min_periods=1000).std()
        return ret / sigW, sigW

    zs, ss = zser(m)
    zp, _ = zser(p)
    return pd.DataFrame({"zs": zs, "zp": zp, "sig": ss}).reindex(m.index)


def _saat_maskesi(idx, sym):
    (tz0, h0), (tz1, h1), _ = _pencere(sym)
    # sinyal mumu t'nin kapanışı t+1 dk; giriş o anda
    t1 = idx + pd.Timedelta("1min")
    a = t1.tz_convert(tz0)
    b = t1.tz_convert(tz1)
    ta = a.hour * 60 + a.minute
    tb = b.hour * 60 + b.minute
    wd = a.weekday
    return (ta >= h0.hour * 60 + h0.minute) & (tb <= h1.hour * 60 + h1.minute) & (wd < 5)


def _seans_sonu(t, sym):
    _, _, (tz, h) = _pencere(sym)
    loc = (t + pd.Timedelta("1min")).tz_convert(tz)
    son = pd.Timestamp.combine(loc.date(), h).tz_localize(tz)
    return son.tz_convert("UTC")


def aday_noktalari(sym, data, mod):
    """mod='yetis': kendi geride kaldı, ortağın yönünde gir.  mod='sondur': kendi öne fırladı, tersine gir.
    Dönüş: (m, S, uzun_mask, kisa_mask) — S hizalı seriler."""
    m = data[sym]
    S = _ana_seriler(sym, data)
    if S is None:
        return None
    zs, zp = S.zs.values, S.zp.values
    D = zp - zs
    yukari = m.c.values > m.o.values
    asagi = m.c.values < m.o.values
    saat = _saat_maskesi(m.index, sym)
    with np.errstate(invalid="ignore"):
        if mod == "yetis":
            L = (zp >= K) & (D >= K) & yukari          # ortak yükseldi, kendi geride, kendi kımıldadı
            Sh = (zp <= -K) & (D <= -K) & asagi
        else:
            L = (zs <= -K) & (D >= K) & yukari         # kendi tek başına düştü, ilk dönüş mumu
            Sh = (zs >= K) & (D <= -K) & asagi
    ok = saat & np.isfinite(D) & np.isfinite(S.sig.values) & (S.sig.values > 0)
    return m, S, L & ok, Sh & ok


def uret(sym, data, mod):
    r = aday_noktalari(sym, data, mod)
    if r is None:
        return []
    m, S, L, Sh = r
    idx = np.flatnonzero(L | Sh)
    out = []
    son = None
    c = m.c.values
    zs, zp, sig = S.zs.values, S.zp.values, S.sig.values
    tix = m.index
    for i in idx:                       # aday sayısı az (olay bazlı); dakika döngüsü değil
        t = tix[i]
        if son is not None and t - son < pd.Timedelta(minutes=W):
            continue                    # aynı olay: tek tetik
        son = t
        yon = "L" if L[i] else "S"
        sg = 1 if yon == "L" else -1
        U = sig[i] * c[i]
        gap = abs(zp[i] - zs[i]) * U
        bitis = min(t + pd.Timedelta(minutes=1 + H), _seans_sonu(t, sym))
        if bitis <= t + pd.Timedelta("1min"):
            continue
        out.append({"t": t, "yon": yon, "stop": float(c[i] - sg * STOP_U * U),
                    "hedef": float(c[i] + sg * 0.5 * gap), "bitis": bitis})
    return out


def sinyaller(sym, data):
    return uret(sym, data, "yetis")
