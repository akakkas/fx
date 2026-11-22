import importlib.util, os
_s = importlib.util.spec_from_file_location("_stcore", os.path.join(os.path.dirname(__file__), "_stcore.py"))
_c = importlib.util.module_from_spec(_s); _s.loader.exec_module(_c)
AD = "15 dk ST (filtresiz, kıyas)"
ACIKLAMA = ("Kemal'in TradingView indikatöründeki kural: 15 dakikalık Supertrend dönünce gir"
            + (", ama sadece 1 saatlik Supertrend de aynı yöndeyse (uyumlu)." if False else "; filtre yok, uyum filtresinin etkisini görmek için kıyas.")
            + " Stop 15 dk ST çizgisi, 15 dk ST ters dönünce ya da pencere sonunda çık."
            + (" Pencere: Asya saatleri (Londra 00:00–07:45), metaller." if "gunduz" == "gece" else " Pencere: ana seans."))
SEMBOLLER = ["XAUUSD", "XAGUSD", "DEUIDXEUR", "USATECHIDXUSD"]


def sinyaller(sym, data):
    return _c.sinyaller(sym, data, False, "gunduz")
