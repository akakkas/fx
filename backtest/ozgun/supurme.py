"""Likidite süpürmesi / başarısız kırılım (Tahtacı Süpürme).

Mantık: belirgin seviyelerin (seans öncesi aralık, önceki seans yüksek/düşük,
metallerde NY penceresi için Asya aralığı) hemen ötesinde stop emirleri birikir.
Açılıştan sonraki ilk saatlerde fiyat bu seviyeyi kısa süre aşıp stopları
tetikler, sonra kabul görmeden geri içeri kapanırsa kırılım başarısızdır:
ters yöne girilir, stop süpürme ucunun ötesine konur.

Parametreler (veriye bakılmadan sabitlendi, optimizasyon yok):
  GERI_DK   = 15   kırılımdan sonra seviyenin içine kapanış için tanınan süre (dk).
                   Bir 15 dk mum içinde geri dönemeyen hareket "kabul görmüş" sayılır.
  PENCERE   = 150  açılıştan sonra süpürme aranan süre (dk). Açılış likiditesinin
                   en yoğun olduğu ilk 2,5 saat; öğleden sonra seviyeler bayatlar.
  HEDEF_R   = 2.0  hedef = 2R. Başarısız kırılım hızlı geri dönüş üretir; 2R,
                   %40 civarı isabetle maliyet sonrası artı kalmaya yetecek eşik.
  ZAMAN_DK  = 180  girişten en fazla 3 saat; ayrıca seans sonunda mutlaka kapanır.
Stop: süpürme ucunun (kırılım mumu..dönüş mumu arası en uç fiyat) 1 spread ötesi.
"""
from datetime import time as _time, datetime as _dt
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

AD = "Likidite Süpürmesi"
ACIKLAMA = (
    "Fiyat açılıştan sonraki ilk saatlerde önceki günün tepesini/dibini ya da gece "
    "aralığını kısa süre aşıp oradaki stopları patlatır, ama 15 dakika içinde geri "
    "seviyenin içine kapanırsa kırılım tutmamış demektir; ters yöne girilir. "
    "Stop süpürmenin ucunun hemen ötesinde, hedef 2R; en fazla 3 saat beklenir ve "
    "seans sonunda her durumda kapanır, geceye pozisyon taşınmaz."
)
SEMBOLLER = ["XAUUSD", "XAGUSD", "DEUIDXEUR", "USATECHIDXUSD"]

GERI_DK = 15
PENCERE = 150
HEDEF_R = 2.0
ZAMAN_DK = 180

LON = ZoneInfo("Europe/London")
NY = ZoneInfo("America/New_York")
BER = ZoneInfo("Europe/Berlin")

# Her sembol için: ana seans (önceki seans H/L bundan), giriş pencereleri.
# Pencere: (açılış saati, tz, seans-öncesi aralığın başlangıcı: ("önceki_seans_sonu" | (saat, tz)), ek seviye)
AYAR = {
    "metal": dict(
        seans=((8, 0, LON), (16, 30, NY)),           # Londra açılışı -> NY öğleden sonra
        pencereler=[
            dict(acilis=(8, 0, LON), aralik_bas=(0, 0, LON), asya=False),      # Londra: Asya aralığı
            dict(acilis=(9, 30, NY), aralik_bas=(8, 0, LON), asya=True),       # NY: Londra sabahı aralığı (+Asya)
        ]),
    "DEUIDXEUR": dict(
        seans=((9, 0, BER), (17, 30, BER)),          # Xetra
        pencereler=[dict(acilis=(9, 0, BER), aralik_bas="onceki_son", asya=False)]),
    "USATECHIDXUSD": dict(
        seans=((9, 30, NY), (16, 0, NY)),            # NYSE/Nasdaq nakit seans
        pencereler=[dict(acilis=(9, 30, NY), aralik_bas="onceki_son", asya=False)]),
}


def _ns(d, hm):
    h, m, tz = hm
    return pd.Timestamp(_dt.combine(d, _time(h, m), tzinfo=tz)).tz_convert("UTC").value


def _sl(ix, a, b):
    """[a, b) aralığının tamsayı indeksleri (ix: int64 ns, sıralı)."""
    return int(np.searchsorted(ix, a, "left")), int(np.searchsorted(ix, b, "left"))


def _hedef(yon, giris, stop, ctx):
    r = abs(giris - stop)
    return giris + HEDEF_R * r if yon == "L" else giris - HEDEF_R * r


def sinyaller(sym, data, hedef_fn=None):
    hedef_fn = hedef_fn or _hedef
    m = data[sym]
    if m is None or not len(m):
        return []
    ay = AYAR["metal"] if sym in ("XAUUSD", "XAGUSD") else AYAR[sym]
    idx = m.index if m.index.tz is not None else m.index.tz_localize("UTC")
    ix = idx.as_unit("ns").asi8          # zaman birimi (us/ns) farkına karşı sabit ns
    H, L, C, S = (m[k].to_numpy(float) for k in "hlcs")

    # Takvim günleri (ana seans açılış saat diliminde)
    tz0 = ay["seans"][0][2]
    gunler = sorted(set(idx.tz_convert(tz0).date))
    onceki = None  # (seans_hi, seans_lo, seans_son_ns)
    asya_cache = {}
    out = []
    for d in gunler:
        if d.weekday() >= 5:
            continue
        s_bas, s_son = _ns(d, ay["seans"][0]), _ns(d, ay["seans"][1])
        a, b = _sl(ix, s_bas, s_son)
        if b <= a:              # veri yok (tatil)
            continue
        for p in ay["pencereler"]:
            acl = _ns(d, p["acilis"])
            pend = acl + PENCERE * 60_000_000_000
            # seans-öncesi aralık
            if p["aralik_bas"] == "onceki_son":
                if onceki is None:
                    continue
                r0 = onceki[2]
            else:
                r0 = _ns(d, p["aralik_bas"])
            ra, rb = _sl(ix, r0, acl)
            if rb - ra < 30:
                continue
            seviyeler = []  # (taraf, seviye, oluşum_bitişi_ns)
            seviyeler += [("U", H[ra:rb].max(), acl), ("D", L[ra:rb].min(), acl)]
            if onceki is not None:
                seviyeler += [("U", onceki[0], onceki[2]), ("D", onceki[1], onceki[2])]
            if p["asya"]:
                aa, ab = _sl(ix, _ns(d, (0, 0, LON)), _ns(d, (8, 0, LON)))
                if ab - aa >= 30:
                    seviyeler += [("U", H[aa:ab].max(), _ns(d, (8, 0, LON))),
                                  ("D", L[aa:ab].min(), _ns(d, (8, 0, LON)))]
            wa, wb = _sl(ix, acl, pend)
            if wb <= wa:
                continue
            gorulen = set()
            for taraf, lv, olus in seviyeler:
                key = (taraf, round(float(lv), 6))
                if key in gorulen:
                    continue
                gorulen.add(key)
                # seviye pencere açılışına kadar alınmamış olmalı (taze likidite)
                xa, xb = _sl(ix, olus, acl)
                if xb > xa:
                    if taraf == "U" and H[xa:xb].max() >= lv:
                        continue
                    if taraf == "D" and L[xa:xb].min() <= lv:
                        continue
                # pencere içindeki ilk ihlal
                hw = H[wa:wb] > lv if taraf == "U" else L[wa:wb] < lv
                if not hw.any():
                    continue
                bi = wa + int(np.argmax(hw))
                # süre sınırı: kırılım mumundan itibaren GERI_DK dakika (zaman bazlı)
                ce = int(np.searchsorted(ix, ix[bi] + GERI_DK * 60_000_000_000, "left"))
                geri = C[bi:ce] < lv if taraf == "U" else C[bi:ce] > lv
                if not geri.any():
                    continue        # kırılım kabul gördü -> işlem yok
                j = bi + int(np.argmax(geri))
                if taraf == "U":
                    uc = H[bi:j + 1].max()
                    stop = uc + S[j]
                    yon = "S"
                else:
                    uc = L[bi:j + 1].min()
                    stop = uc - S[j]
                    yon = "L"
                t = idx[j]
                bitis = min(t + pd.Timedelta(minutes=ZAMAN_DK), pd.Timestamp(s_son, tz="UTC"))
                if bitis <= t + pd.Timedelta(minutes=1):
                    continue
                ctx = dict(ust=H[ra:rb].max(), alt=L[ra:rb].min())
                hd = hedef_fn(yon, C[j], stop, ctx)
                if hd is False:
                    continue
                out.append({"t": t, "yon": yon, "stop": float(stop),
                            "hedef": None if hd is None else float(hd), "bitis": bitis})
        if b - a >= 60:         # eksik/tatil seansı "önceki seans" sayılmaz (gün bittikten sonra karar)
            onceki = (H[a:b].max(), L[a:b].min(), s_son)
    out.sort(key=lambda s: s["t"])
    return out
