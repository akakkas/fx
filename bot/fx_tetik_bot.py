#!/usr/bin/env python3
"""FX Tetik nöbetçi botu — uygulama kapalıyken de sinyal bildirimi (Termux).

Uygulamadaki sinyal mantığının birebir kopyası (BBO, ST, ORB; Altın ve Gümüş).
Saf Python: pandas/numpy/zoneinfo gerekmez.

Kurulum (bir kere):
  pkg install python termux-api        # + Play Store/F-Droid'den "Termux:API" uygulaması
  echo 'export TD_KEY="twelve-data-anahtarin"' >> ~/.bashrc && source ~/.bashrc
Çalıştırma:
  termux-wake-lock                     # ekran kapalıyken Android uyutmasın
  python fx_tetik_bot.py
Deneme:  python fx_tetik_bot.py --test   (tek bildirim atar, çıkar)
"""
import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

# ---------- AYARLAR (uygulamadaki Ayarlar ile aynı tut) ----------
ACIK = {  # hangi sinyal türleri açık
    "XAU": {"BBO": False, "ST": True, "ORB": False},
    "XAG": {"BBO": False, "ST": False, "ORB": False},
}
RISK_USD = 100          # işlem başı risk (lot hesabı için)
GECE = True             # seans dışı (gece) sinyalleri de bildir — DİKKAT: gece saatleri test edilmedi
TELEGRAM = (os.environ.get("TG_TOKEN"), os.environ.get("TG_CHAT"))  # isteğe bağlı

INST = {"XAU": {"ad": "Altın", "feed": "XAU/USD", "dec": 2, "contract": 100},
        "XAG": {"ad": "Gümüş", "feed": "XAG/USD", "dec": 3, "contract": 5000}}
KREDI_SINIRI = 380      # günlük en fazla bu kadar kredi harca (uygulamaya da pay kalsın; ücretsiz plan 800)
DURUM = os.path.expanduser("~/.fx_tetik_bot.json")

# ---------- saat dilimi (DST kuralları elle) ----------
def _nth_sunday(y, m, n):
    d = dt.date(y, m, 1)
    d += dt.timedelta(days=(6 - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def _last_sunday(y, m):
    d = dt.date(y, m + 1, 1) - dt.timedelta(days=1) if m < 12 else dt.date(y, 12, 31)
    return d - dt.timedelta(days=(d.weekday() + 1) % 7)


def utc_offset(tz, utc):
    """utc: aware datetime. Dönen: saat cinsinden fark."""
    y = utc.year
    if tz == "NY":  # 2. Mart pazarı 02:00 yerel (07:00 UTC) – 1. Kasım pazarı 02:00 yerel (06:00 UTC)
        a = dt.datetime.combine(_nth_sunday(y, 3, 2), dt.time(7), dt.timezone.utc)
        b = dt.datetime.combine(_nth_sunday(y, 11, 1), dt.time(6), dt.timezone.utc)
        return -4 if a <= utc < b else -5
    if tz in ("BER", "LON"):  # son Mart pazarı – son Ekim pazarı, 01:00 UTC
        a = dt.datetime.combine(_last_sunday(y, 3), dt.time(1), dt.timezone.utc)
        b = dt.datetime.combine(_last_sunday(y, 10), dt.time(1), dt.timezone.utc)
        base = 1 if tz == "BER" else 0
        return base + (1 if a <= utc < b else 0)
    raise ValueError(tz)


def zoned(tz, hhmm, ref_ms):
    """ref anının o saat dilimindeki günü için yerel hh:mm'i UTC ms'ye çevirir."""
    ref = dt.datetime.fromtimestamp(ref_ms / 1000, dt.timezone.utc)
    local_day = (ref + dt.timedelta(hours=utc_offset(tz, ref))).date()
    h, m = map(int, hhmm.split(":"))
    guess = dt.datetime.combine(local_day, dt.time(h, m), dt.timezone.utc)
    off = utc_offset(tz, guess - dt.timedelta(hours=utc_offset(tz, guess)))
    return int((guess - dt.timedelta(hours=off)).timestamp() * 1000)


ORBW = {"XAU": ("NY", "09:30"), "XAG": ("NY", "09:30")}

# ---------- haber takvimi (uygulamadakiyle aynı) ----------
HABER = []
for d in ["2026-12-09", "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09", "2027-07-28", "2027-09-15", "2027-11-17"]:
    HABER.append((d, "14:00", "NY", "Fed faiz kararı", 30, 60))
for d in ["2026-12-10", "2027-01-13", "2027-02-11", "2027-03-10", "2027-04-13", "2027-07-14"]:
    HABER.append((d, "08:30", "NY", "ABD enflasyon (CPI)", 30, 30))
for d in ["2026-12-04", "2027-01-08", "2027-02-05", "2027-04-02", "2027-07-02"]:
    HABER.append((d, "08:30", "NY", "ABD istihdam (NFP)", 30, 30))
HABER = [(zoned(tz, h, int(dt.datetime.fromisoformat(d + "T12:00:00+00:00").timestamp() * 1000)), ad, on, son)
         for d, h, tz, ad, on, son in HABER]


def haber_engel(ms):
    for t, ad, on, son in HABER:
        if t - on * 60000 <= ms <= t + son * 60000:
            return ad
    return None


def tr_saat(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone(dt.timedelta(hours=3))).strftime("%H:%M")


def haber_bugun(ms):
    gun = lambda x: dt.datetime.fromtimestamp(x / 1000, dt.timezone(dt.timedelta(hours=3))).date()
    return [f"{ad} {tr_saat(t)}" for t, ad, _, _ in HABER if gun(t) == gun(ms)]


def seans_ici(ms):
    """Geri testteki pencere: Londra 08:00 – New York 16:00."""
    return zoned("LON", "08:00", ms) <= ms <= zoned("NY", "16:00", ms)

# ---------- indikatörler (uygulamadakiyle birebir) ----------
def agg(b5, mins):
    out = []
    for b in b5:
        k = (b["t"] // (mins * 60000)) * mins * 60000
        if not out or out[-1]["t"] != k:
            out.append({"t": k, "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]})
        else:
            c = out[-1]
            c["h"], c["l"], c["c"] = max(c["h"], b["h"]), min(c["l"], b["l"]), b["c"]
    return out


def indicators(b):
    n = len(b)
    for i in range(n):
        b[i]["tr"] = (max(b[i]["h"] - b[i]["l"], abs(b[i]["h"] - b[i - 1]["c"]), abs(b[i]["l"] - b[i - 1]["c"]))
                      if i else b[i]["h"] - b[i]["l"])
    for i in range(n):
        if i >= 13:
            b[i]["atr"] = sum(b[k]["tr"] for k in range(i - 13, i + 1)) / 14
        if i >= 19:
            cs = [b[k]["c"] for k in range(i - 19, i + 1)]
            m = sum(cs) / 20
            sd = (sum((x - m) ** 2 for x in cs) / 20) ** 0.5
            b[i]["mid"], b[i]["up"], b[i]["dn"] = m, m + 2 * sd, m - 2 * sd
    a = fub = flb = 0.0
    d = 0
    for i in range(n):
        a = a + (b[i]["tr"] - a) / 10 if i else b[i]["tr"]
        hl2 = (b[i]["h"] + b[i]["l"]) / 2
        ub, lb = hl2 + 3 * a, hl2 - 3 * a
        if i == 0:
            fub, flb, d = ub, lb, 1
        else:
            pc = b[i - 1]["c"]
            fub = ub if (ub < fub or pc > fub) else fub
            flb = lb if (lb > flb or pc < flb) else flb
            d = (-1 if b[i]["c"] < flb else 1) if d >= 0 else (1 if b[i]["c"] > fub else -1)
        b[i]["st"] = flb if d == 1 else fub
        b[i]["dir"] = d
    return b


def mk(inst, typ, side, entry, stop, t, why):
    risk, sg = abs(entry - stop), (1 if side == "L" else -1)
    return {"id": f"{inst}-{typ}-{t}", "inst": inst, "type": typ, "side": side, "entry": entry, "stop": stop,
            "tp1": entry + sg * risk, "t": t, "why": why}


def detect(inst, b5, now):
    sigs, tf = [], 15 * 60000
    b15 = indicators([x for x in agg(b5, 15) if x["t"] + tf <= now])
    b5c = indicators([dict(x) for x in b5 if x["t"] + 300000 <= now])
    on = ACIK[inst]
    for j in (-1, -2, -3):  # son 3 kapanmış mum: veri gecikirse dönüş kaçmasın (aynı sinyal ID ile bir kez bildirilir)
        if len(b15) <= 25 - j:
            break
        r, p = b15[j], b15[j - 1]
        close_t = r["t"] + tf
        if now - close_t < 35 * 60000:
            if on["BBO"] and r.get("mid"):
                side = "L" if (r["c"] > r["up"] and p["c"] <= p["up"]) else "S" if (r["c"] < r["dn"] and p["c"] >= p["dn"]) else None
                if side and abs(r["c"] - r["mid"]) > 0.3 * r["atr"]:
                    sigs.append(mk(inst, "BBO", side, r["c"], r["mid"], close_t, "Bollinger kırılımı, stop orta bant"))
            if on["ST"] and r["dir"] != p["dir"]:
                s2 = "L" if r["dir"] == 1 else "S"
                if abs(r["c"] - r["st"]) > 0.3 * r["atr"]:
                    sigs.append(mk(inst, "ST", s2, r["c"], r["st"], close_t, "Supertrend döndü, stop ST çizgisi"))
    if on["ORB"] and len(b5c) > 20:
        tz, hh = ORBW[inst]
        o = zoned(tz, hh, now)
        if o + 15 * 60000 <= now <= o + 80 * 60000:
            rng = [x for x in b5c if o <= x["t"] < o + 15 * 60000]
            if len(rng) == 3:
                hi, lo = max(x["h"] for x in rng), min(x["l"] for x in rng)
                for x in [x for x in b5c if x["t"] >= o + 15 * 60000 and x["t"] + 300000 <= o + 75 * 60000]:
                    buf = 0.1 * (x.get("atr") or 0)
                    sd = "L" if x["c"] > hi + buf else "S" if x["c"] < lo - buf else None
                    if sd:
                        sigs.append(mk(inst, "ORB", sd, x["c"], lo if sd == "L" else hi, x["t"] + 300000, "Açılış aralığı kırıldı"))
                        break
    return sigs

# ---------- veri ve bildirim ----------
def durum_oku():
    try:
        return json.load(open(DURUM))
    except Exception:
        return {"goruldu": [], "kredi": {"d": "", "n": 0}}


def durum_yaz(s):
    s["goruldu"] = s["goruldu"][-300:]
    json.dump(s, open(DURUM, "w"))


def temiz(b):
    """Hafta sonu ve ölü (hareketsiz) mumları at — uygulamadaki temiz() ile aynı."""
    out = []
    for x in b:
        d = dt.datetime.fromtimestamp(x["t"] / 1000, dt.timezone.utc)
        if d.weekday() == 5 or (d.weekday() == 6 and d.hour < 21) or (d.weekday() == 4 and d.hour >= 22):
            continue
        if x["h"] > x["l"]:
            out.append(x)
    return out


def cek(key, feeds):
    q = urllib.parse.urlencode({"symbol": ",".join(feeds), "interval": "5min", "outputsize": 1200,
                                "timezone": "UTC", "order": "ASC", "apikey": key})
    with urllib.request.urlopen("https://api.twelvedata.com/time_series?" + q, timeout=30) as r:
        js = json.load(r)
    out = {}
    for k in ACIK:
        o = js.get(INST[k]["feed"]) if len(feeds) > 1 else js
        if not o or o.get("status") == "error" or not o.get("values"):
            print("veri hatası", k, (o or {}).get("message", "")[:80], flush=True)
            continue
        out[k] = temiz([{"t": int(dt.datetime.fromisoformat(v["datetime"].replace(" ", "T") + "+00:00").timestamp() * 1000),
                         "o": float(v["open"]), "h": float(v["high"]), "l": float(v["low"]), "c": float(v["close"])}
                        for v in o["values"]])
    return out


def lot(inst, entry, stop):
    d = abs(entry - stop)
    return int(RISK_USD / (d * INST[inst]["contract"]) * 100) / 100 if d > 0 else 0


def bildir(baslik, metin, sid="fx"):
    print(time.strftime("%H:%M"), baslik, "|", metin, flush=True)
    try:
        subprocess.run(["termux-notification", "--id", sid[-40:], "--title", baslik, "--content", metin,
                        "--priority", "max", "--sound", "--vibrate", "300,150,300",
                        "--action", "termux-open-url https://akakkas.github.io/fx/"], timeout=15)
    except Exception as e:
        print("termux-notification yok/çalışmadı:", e, flush=True)
    tok, chat = TELEGRAM
    if tok and chat:
        try:
            urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage?" +
                                   urllib.parse.urlencode({"chat_id": chat, "text": baslik + "\n" + metin}), timeout=15)
        except Exception as e:
            print("telegram hatası:", e, flush=True)


def sinyal_metni(s):
    d = INST[s["inst"]]["dec"]
    f = lambda v: f"{v:.{d}f}"
    gece = "" if seans_ici(s["t"]) else "🌙 GECE (test edilmedi) · "
    hb = haber_bugun(s["t"])
    uyari = ("⚠️ Bugün " + ", ".join(hb) + " · ") if hb else ""
    return (f"🎯 {INST[s['inst']]['ad']} {s['type']} {'AL' if s['side'] == 'L' else 'SAT'}",
            f"{gece}{uyari}Giriş {f(s['entry'])} · Stop {f(s['stop'])} · Hedef {f(s['tp1'])} · Lot {lot(s['inst'], s['entry'], s['stop']):.2f}")


def gerek_var(now_ms):
    """Bu turda veri çekmek gerekli mi? BBO/ST 15 dk'da bir, ORB penceresinde 5 dk'da bir."""
    d = dt.datetime.fromtimestamp(now_ms / 1000, dt.timezone.utc)
    if d.weekday() == 5 or (d.weekday() == 6 and d.hour < 22) or (d.weekday() == 4 and d.hour >= 22):
        return False  # hafta sonu piyasa kapalı
    if any(v["ORB"] for v in ACIK.values()):
        o = zoned("NY", "09:30", now_ms)
        if o + 15 * 60000 <= now_ms <= o + 80 * 60000:
            return True
    return 5 <= (now_ms // 60000) % 15 < 10  # 15 dk'lık mum kapandıktan 5 dk sonra (veri sağlayıcının gecikmesine pay)


def tur(key, st):
    now = int(time.time() * 1000)
    if not gerek_var(now):
        return
    bugun = time.strftime("%Y-%m-%d")
    if st["kredi"]["d"] != bugun:
        st["kredi"] = {"d": bugun, "n": 0}
    feeds = [INST[k]["feed"] for k in ACIK if any(ACIK[k].values())]
    if not feeds:
        return
    if st["kredi"]["n"] + len(feeds) > KREDI_SINIRI:
        print("günlük kredi sınırı, bekliyorum", flush=True)
        return
    data = cek(key, feeds)
    st["kredi"]["n"] += len(feeds)
    for k, b5 in data.items():
        for s in detect(k, b5, now):
            if s["id"] in st["goruldu"]:
                continue
            st["goruldu"].append(s["id"])
            if not GECE and not seans_ici(s["t"]):
                print("gece sinyali atlandı", s["id"], flush=True)
                continue
            hb = haber_engel(s["t"])
            if hb:
                print("haber penceresi, atlandı:", hb, s["id"], flush=True)
                continue
            bildir(*sinyal_metni(s), sid=s["id"])
    durum_yaz(st)


def main():
    if "--test" in sys.argv:
        bildir("🎯 FX Tetik deneme", "Bildirim çalışıyor. Sinyal gelince böyle görünecek.")
        return
    key = os.environ.get("TD_KEY", "").strip()
    if not key:
        sys.exit("TD_KEY yok. ~/.bashrc'ye ekle: export TD_KEY=\"anahtarin\"")
    st = durum_oku()
    print("FX Tetik nöbette. Açık sinyaller:", {k: [t for t, v in d.items() if v] for k, d in ACIK.items()}, "· gece:", GECE, flush=True)
    while True:
        try:
            tur(key, st)
        except Exception as e:
            print("hata:", repr(e)[:200], flush=True)
        now = time.time()
        time.sleep(max(5, (int(now // 300) + 1) * 300 + 25 - now))  # her 5 dk'nın 25. saniyesi


if __name__ == "__main__":
    main()
