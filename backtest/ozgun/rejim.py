"""Oynaklık rejimi / gün tipi ayrımı (özgün aday).

Fikir
-----
Her seans dakikası için "normal" oynaklığı, SON N İŞLEM GÜNÜNÜN AYNI SEANS
DAKİKASINDAKİ ortalama karesel getiriden kurarız (bugün ve gelecek hariç).
Böylece açılıştaki doğal oynaklık patlaması ile öğle durgunluğu ayrı ayrı
normalize edilir. Seansın ilk W dakikası ("açılış dengesi") bittiğinde:

  D = ilk W dakikadaki net hareket / o W dakikada beklenen hareketin std'si
  A = ilk W dakikadaki gerçekleşen varyans / beklenen varyans

  TREND GÜNÜ : |D| >= Z_TREND                       -> yön = sign(D)
  YATAY GÜN  : |D| <= Z_TREND/3  VE  A <= 1          (sakin ve yönsüz)
  aksi halde : belirsiz -> o gün işlem yok

Trend günü: yön tarafında ilk geri çekilmede (bu mum, o ana kadarki seans
tepesinin 0,5σ altına inmiş, yine de yukarı kapatmış ve VWAP'ın üstünde)
giriş. Fiyat VWAP'ın ters tarafında kapanırsa trend tezi bozulur, o gün
giriş aranmaz. Stop 1σ, hedef 2σ, en geç seans sonu.

Yatay gün: fiyat VWAP'tan Z_SAPMA·σ kadar uzaklaşıp ters mum (dönüş) yapınca
VWAP'a dönüş işlemi. Stop 1σ öte, hedef girişteki VWAP. Günde en fazla 2
işlem; ikinci işlem için fiyatın önce VWAP'a (|z|<0,5) değmiş olması gerekir.
Gün içinde açılıştan net hareket Z_TREND·σ'yı aşarsa "yatay" teşhisi
çökmüştür, o andan sonra ortalamaya dönüş işlemi açılmaz.

σ (birim): o dakikada biten W dakikalık pencere için, profilden gelen
beklenen hareket std'si (log getiri), fiyat birimine çevrilmiş hali.

VWAP: veride hacim yok. Hacim ile mum aralığı (h-l) güçlü korelasyonlu
olduğu için ağırlık = mum aralığı, fiyat = (h+l+c)/3; seans açılışından
kümülatif. ("aralık ağırlıklı VWAP")

Gelecek verisi: profil yalnız önceki günlerden; t mumundaki tüm koşullar
t mumunun o,h,l,c'si ve öncesiyle hesaplanır.
"""
import datetime as _dt
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

AD = "Rejim (gün tipi)"
ACIKLAMA = (
    "Her dakikanın oynaklığını, son 20 günün aynı seans dakikasıyla kıyaslayıp normalize eder; "
    "seansın ilk saatinde fiyat normalin 1,5 katı std'den fazla tek yöne gittiyse günü 'trend', "
    "sakin ve yönsüz kaldıysa 'yatay' sayar, arada kalırsa hiç işlem yapmaz. "
    "Trend gününde ilk geri çekilmeden trend yönüne girer (stop 1σ, hedef 2σ); yatay günde fiyat "
    "VWAP'tan 1,5σ uzaklaşıp dönüş mumu yapınca VWAP'a dönüşe oynar. Tüm işlemler seans sonunda kapanır, geceye taşınmaz."
)
SEMBOLLER = ["XAUUSD", "XAGUSD", "DEUIDXEUR", "USATECHIDXUSD"]

# ---- serbest parametreler (veriye bakmadan sabitlendi) ----
N_GUN = 20      # profil geriye bakışı: ~1 işlem ayı
W_DK = 60       # açılış dengesi penceresi (ilk saat)
Z_TREND = 1.5   # trend günü eşiği (normalize net hareket)
Z_SAPMA = 1.5   # yatay günde VWAP'tan normalize sapma eşiği

# ---- yapısal sabitler (σ birimine bağlı, ayarlanmadı) ----
GERI_CEKILME = 0.5        # trend girişinde tepeden min geri çekilme (σ)
STOP_SIG = 1.0            # stop mesafesi (σ) = 1R
TREND_HEDEF = 2.0         # trend hedefi (σ) = 2R
YENIDEN_KUR = 0.5         # yatay günde ikinci işlem için |z| < 0.5 (VWAP'a değme)
SON_GIRIS_DK = 60         # seans bitimine 60 dk kala yeni giriş yok
MAX_YATAY = 2

SEANS = {
    # sym: (açılış tz, açılış saati, kapanış tz, kapanış saati)
    "XAUUSD": ("Europe/London", _dt.time(8, 0), "America/New_York", _dt.time(16, 0)),
    "XAGUSD": ("Europe/London", _dt.time(8, 0), "America/New_York", _dt.time(16, 0)),
    "DEUIDXEUR": ("Europe/Berlin", _dt.time(9, 0), "Europe/Berlin", _dt.time(17, 30)),
    "USATECHIDXUSD": ("America/New_York", _dt.time(9, 30), "America/New_York", _dt.time(16, 0)),
}


def _seans_takvimi(sym, idx):
    tzo, to, tzc, tc = SEANS[sym]
    zo, zc = ZoneInfo(tzo), ZoneInfo(tzc)
    loc = idx.tz_convert(tzo)
    gunler = pd.bdate_range(loc[0].date(), loc[-1].date())
    acil, kapa = [], []
    for g in gunler:
        d = g.date()
        acil.append(pd.Timestamp(_dt.datetime.combine(d, to, tzinfo=zo)).tz_convert("UTC"))
        kapa.append(pd.Timestamp(_dt.datetime.combine(d, tc, tzinfo=zc)).tz_convert("UTC"))
    acil = pd.DatetimeIndex(acil)
    kapa = pd.DatetimeIndex(kapa)
    uzun = ((kapa - acil) / pd.Timedelta("1min")).astype(int).values
    return acil, kapa, uzun


def _matris(m, acil, K):
    """Gün × seans dakikası matrisleri (eksik dakika NaN)."""
    D = len(acil)
    off = (np.arange(K) * 60_000_000_000).astype("int64")
    grid = (acil.as_unit("ns").asi8[:, None] + off[None, :]).ravel()
    gi = pd.DatetimeIndex(grid.astype("datetime64[ns]")).tz_localize("UTC")
    src = m[["o", "h", "l", "c"]]
    if src.index.unit != "ns":
        src = src.copy()
        src.index = src.index.as_unit("ns")
    r = src.reindex(gi)
    return {k: r[k].values.reshape(D, K) for k in "ohlc"}


def _profil(r2, n):
    """P[d,k] = son n günün (d hariç) k. dakikasındaki ortalama r². Yetersizse NaN."""
    v = np.where(np.isfinite(r2), r2, 0.0)
    c = np.isfinite(r2).astype(float)
    cs = np.vstack([np.zeros((1, v.shape[1])), np.cumsum(v, axis=0)])
    cc = np.vstack([np.zeros((1, c.shape[1])), np.cumsum(c, axis=0)])
    D = r2.shape[0]
    d = np.arange(D)
    lo = np.maximum(d - n, 0)
    s = cs[d] - cs[lo]
    k = cc[d] - cc[lo]
    with np.errstate(invalid="ignore", divide="ignore"):
        P = s / k
    P[k < 0.75 * n] = np.nan
    return P


def sinyaller(sym, data):
    m = data[sym]
    if m is None or len(m) < 2:
        return []
    acil, kapa, uzun = _seans_takvimi(sym, m.index)
    K = int(uzun.max())
    M = _matris(m, acil, K)
    O, H, L, C = M["o"], M["h"], M["l"], M["c"]
    D = len(acil)
    W = W_DK

    # 1 dk log getiri (seans içinde); ilk dakika kendi açılışına göre
    prevc = np.concatenate([O[:, :1], C[:, :-1]], axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.log(C / prevc)
    r2 = r * r
    for d in range(D):
        r2[d, uzun[d]:] = np.nan

    P = _profil(r2, N_GUN)
    Pz = np.where(np.isfinite(P), P, np.nan)
    cumP = np.nancumsum(np.where(np.isfinite(Pz), Pz, 0.0), axis=1)
    cumP_W = cumP.copy()
    cumP_W[:, W:] = cumP[:, W:] - cumP[:, :-W]
    sigW = np.sqrt(cumP_W)            # o dakikada biten W dk'lık beklenen std (log)
    sig0 = np.sqrt(cumP)              # açılıştan o dakikaya beklenen std (log)
    prof_ok = np.isfinite(P[:, :W]).all(axis=1)

    # aralık ağırlıklı VWAP (seans başından kümülatif)
    tp = (H + L + C) / 3.0
    w = np.where(np.isfinite(H - L), (H - L), 0.0) + 1e-9 * np.nan_to_num(C, nan=0.0)
    tpz = np.nan_to_num(tp, nan=0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        vwap = np.cumsum(w * tpz, axis=1) / np.cumsum(w * np.isfinite(tp), axis=1)

    out = []
    one = pd.Timedelta("1min")
    for d in range(D):
        n = uzun[d]
        if n <= W + SON_GIRIS_DK or not prof_ok[d]:
            continue
        c0, o0 = C[d, :W], O[d, 0]
        if not np.isfinite(o0) or np.isfinite(c0).sum() < 0.9 * W or not np.isfinite(C[d, W - 1]):
            continue
        sW = sigW[d, W - 1]
        if not (np.isfinite(sW) and sW > 0):
            continue
        Dstat = np.log(C[d, W - 1] / o0) / sW
        A = np.nansum(r2[d, :W]) / cumP[d, W - 1]

        son = n - SON_GIRIS_DK                       # bu indeksten itibaren yeni giriş yok
        ks = np.arange(W, son)
        c, o, h, l = C[d, ks], O[d, ks], H[d, ks], L[d, ks]
        vw = vwap[d, ks]
        sg = sigW[d, ks] * c                         # σ fiyat biriminde
        valid = np.isfinite(c) & np.isfinite(o) & np.isfinite(vw) & np.isfinite(sg) & (sg > 0)
        bitis = kapa[d]

        if abs(Dstat) >= Z_TREND:
            yon = 1 if Dstat > 0 else -1
            if yon > 0:
                ext = np.fmax.accumulate(np.nan_to_num(H[d, :son], nan=-np.inf))[ks - 1]
                derin = ext - l
                yan = c > vw
                don = c > o
            else:
                ext = np.fmin.accumulate(np.nan_to_num(L[d, :son], nan=np.inf))[ks - 1]
                derin = h - ext
                yan = c < vw
                don = c < o
            bozul = valid & ~yan
            ilk_bozul = np.argmax(bozul) if bozul.any() else len(ks)
            kos = valid & yan & don & (derin >= GERI_CEKILME * sg)
            kos[ilk_bozul:] = False
            if kos.any():
                i = int(np.argmax(kos))
                e, s1 = c[i], sg[i]
                out.append({"t": acil[d] + int(ks[i]) * one, "yon": "L" if yon > 0 else "S",
                            "stop": e - yon * STOP_SIG * s1, "hedef": e + yon * TREND_HEDEF * s1,
                            "bitis": bitis})

        elif abs(Dstat) <= Z_TREND / 3.0 and A <= 1.0:
            z = (c - vw) / sg
            # açılıştan net hareket trend boyutuna ulaşırsa yatay teşhisi çöker
            with np.errstate(invalid="ignore", divide="ignore"):
                net = np.log(c / o0) / sig0[d, ks]
            cok = valid & (np.abs(net) >= Z_TREND)
            ilk_cok = np.argmax(cok) if cok.any() else len(ks)
            ksa = valid & (z >= Z_SAPMA) & (c < o)
            lng = valid & (z <= -Z_SAPMA) & (c > o)
            aday = ksa | lng
            aday[ilk_cok:] = False
            yakin = valid & (np.abs(z) < YENIDEN_KUR)
            bas, adet = 0, 0
            while adet < MAX_YATAY:
                rel = np.flatnonzero(aday[bas:])
                if not len(rel):
                    break
                i = bas + int(rel[0])
                yon = -1 if ksa[i] else 1
                e, s1 = c[i], sg[i]
                out.append({"t": acil[d] + int(ks[i]) * one, "yon": "L" if yon > 0 else "S",
                            "stop": e - yon * STOP_SIG * s1, "hedef": float(vw[i]),
                            "bitis": bitis})
                adet += 1
                rel2 = np.flatnonzero(yakin[i + 1:])
                if not len(rel2):
                    break
                bas = i + 1 + int(rel2[0])
    return out
