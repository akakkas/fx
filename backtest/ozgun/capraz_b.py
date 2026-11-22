"""Çapraz piyasa uyumsuzluğu — ÖNCÜNÜN GERİ DÖNMESİ (varyant B).

Aynı ölçü ve aynı 4 parametre (W=15, K=2.0, STOP_U=1.0, H=30) capraz.py'den gelir; tek fark işlemin
tarafı: kendi enstrüman ortağı izlemeden tek başına K'dan fazla fırladıysa (z_kendi >= K, D <= -K)
ve sinyal mumu ters kapandıysa (ilk dönüş), fırlayanı tersine işle. Hedef açığın yarısı, stop bir U.
Dört sembolde de çalışır; Nasdaq/DAX için pencere 08:30 New York – 17:00 Frankfurt.
"""
import importlib.util
import os

_f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capraz.py")
_spec = importlib.util.spec_from_file_location("_capraz_ortak", _f)
_c = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_c)

AD = "Çapraz uyumsuzluk — öncü geri döner"
ACIKLAMA = (
    "Altın-gümüş ya da Nasdaq-DAX çiftinde biri son 15 dakikada ortağı eşlik etmeden kendi olağan "
    "oynaklığına göre sert yükselip (düşüp) ilk ters mumu attığında, fırlayanın aşırıya kaçtığı "
    "varsayılıp tersine işlem açılır. Hedef aradaki açığın yarısının kapanması, stop bir normal "
    "15 dakikalık hareket, en fazla 30 dakika tutulur ve seans sonunda kapanır."
)
SEMBOLLER = ["XAUUSD", "XAGUSD", "DEUIDXEUR", "USATECHIDXUSD"]


def sinyaller(sym, data):
    return _c.uret(sym, data, "sondur")
