"""Varyant B: Likidite süpürmesi, hedef = karşı likidite.

Giriş, stop ve zaman kuralları supurme.py ile birebir aynı (aynı 4 parametre).
Tek fark hedef: sabit 2R yerine seans-öncesi aralığın KARŞI ucu (üstte süpürme ->
aralığın dibi, altta süpürme -> aralığın tepesi). Mantık: süpürülen taraftaki stoplar
alındıktan sonra fiyatın bir sonraki mıknatısı öbür taraftaki birikmiş stoplardır.
Karşı uç 1R'den yakınsa ödül/risk yetersiz sayılır, işlem açılmaz.
"""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    "oz_supurme_cekirdek", os.path.join(os.path.dirname(os.path.abspath(__file__)), "supurme.py"))
_s = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_s)

AD = "Likidite Süpürmesi B (karşı uç hedefi)"
ACIKLAMA = (
    "Giriş ve stop ana süpürme sinyaliyle aynı: seviye kısa süre aşılıp 15 dakika içinde "
    "geri içeri kapanırsa ters yöne girilir, stop süpürme ucunun ötesinde. Fark hedefte: "
    "sabit 2R yerine açılış öncesi aralığın karşı ucu hedeflenir, çünkü bir taraftaki "
    "stoplar alındıktan sonra fiyatın sıradaki mıknatısı öbür taraftaki stoplardır. "
    "Karşı uç 1R'den yakınsa işlem açılmaz; en fazla 3 saat, seans sonunda kapanır."
)
SEMBOLLER = list(_s.SEMBOLLER)


def _karsi(yon, giris, stop, ctx):
    r = abs(giris - stop)
    h = ctx["alt"] if yon == "S" else ctx["ust"]
    mesafe = (giris - h) if yon == "S" else (h - giris)
    return h if mesafe >= r else False


def sinyaller(sym, data):
    return _s.sinyaller(sym, data, hedef_fn=_karsi)
