# Özgün indikatör yarışması — sonuçlar

Veri: Altın 1437 gün · Gümüş 1513 gün · DAX 1514 gün · Nasdaq 1469 gün

İcra her aday için aynı (spread + kayma düşülmüş, tek pozisyon). Karar: net ≥ +0,10R VE 2023+ ≥ +0,10R VE t ≥ 2.

## Çapraz uyumsuzluk — geride kalan yetişir (`capraz`)

Altın ile gümüş, Nasdaq ile DAX normalde birlikte hareket eder. Son 15 dakikada biri kendi olağan oynaklığına göre belirgin yükselip (düşüp) diğeri yerinde saydıysa ve geride kalan aynı yöne kımıldamaya başladıysa, geride kalanda o yöne işlem açılır. Hedef aradaki açığın yarısının kapanması, stop geride kalanın bir normal 15 dakikalık hareketi kadar ters gidiş, en fazla 30 dakika tutulur ve seans sonunda kapanır; DAX'ta yalnız ABD verisi/açılışından Frankfurt kapanışına kadar, Nasdaq'ın DAX'ı sürüklediği saatlerde çalışır.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 1858 | 42 | -0.209 | -388.9 | -394.6 | -9.38 | -0.254 | -0.187 | ❌ |
| DAX | 2805 | 39 | -0.168 | -471.4 | -475.8 | -8.36 | -0.160 | -0.172 | ❌ |
| Gümüş | 197 | 39 | -0.283 | -55.7 | -54.7 | -4.33 | -0.358 | -0.276 | ❌ |

Yıllara göre net ort R: Altın -0.24/-0.26/-0.18/-0.20/-0.20/-0.05 · DAX -0.22/-0.07/-0.22/-0.13/-0.16/-0.19 · Gümüş -0.47/+0.16/-0.43/-0.38/-0.15

## Çapraz uyumsuzluk — öncü geri döner (`capraz_b`)

Altın-gümüş ya da Nasdaq-DAX çiftinde biri son 15 dakikada ortağı eşlik etmeden kendi olağan oynaklığına göre sert yükselip (düşüp) ilk ters mumu attığında, fırlayanın aşırıya kaçtığı varsayılıp tersine işlem açılır. Hedef aradaki açığın yarısının kapanması, stop bir normal 15 dakikalık hareket, en fazla 30 dakika tutulur ve seans sonunda kapanır.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 1292 | 39 | -0.265 | -342.1 | -341.1 | -9.78 | -0.305 | -0.241 | ❌ |
| DAX | 977 | 39 | -0.170 | -166.4 | -166.4 | -4.96 | -0.164 | -0.173 | ❌ |
| Gümüş | 116 | 40 | -0.267 | -31.0 | -32.7 | -3.03 | +0.090 | -0.287 | ❌ |
| Nasdaq | 2430 | 38 | -0.149 | -362.9 | -371.4 | -6.47 | -0.152 | -0.148 | ❌ |

Yıllara göre net ort R: Altın -0.34/-0.28/-0.28/-0.27/-0.16/-0.29 · DAX -0.18/-0.11/-0.25/-0.19/-0.11/-0.12 · Gümüş +0.09/-0.15/-0.26/-0.23/-0.37 · Nasdaq -0.15/-0.15/-0.22/-0.18/-0.15/+0.01

## Rejim (gün tipi) (`rejim`)

Her dakikanın oynaklığını, son 20 günün aynı seans dakikasıyla kıyaslayıp normalize eder; seansın ilk saatinde fiyat normalin 1,5 katı std'den fazla tek yöne gittiyse günü 'trend', sakin ve yönsüz kaldıysa 'yatay' sayar, arada kalırsa hiç işlem yapmaz. Trend gününde ilk geri çekilmeden trend yönüne girer (stop 1σ, hedef 2σ); yatay günde fiyat VWAP'tan 1,5σ uzaklaşıp dönüş mumu yapınca VWAP'a dönüşe oynar. Tüm işlemler seans sonunda kapanır, geceye taşınmaz.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 534 | 37 | -0.118 | -62.9 | -74.2 | -2.33 | -0.227 | -0.057 | ❌ |
| DAX | 481 | 37 | -0.055 | -26.6 | -50.5 | -1.00 | -0.051 | -0.058 | ❌ |
| Gümüş | 481 | 33 | -0.317 | -152.5 | -158.9 | -6.99 | -0.147 | -0.383 | ❌ |
| Nasdaq | 361 | 43 | +0.064 | +23.0 | -13.9 | 1.01 | +0.034 | +0.080 | ❌ |

Yıllara göre net ort R: Altın -0.28/-0.16/-0.10/-0.07/+0.04/-0.15 · DAX +0.04/-0.15/+0.01/-0.29/+0.11/-0.04 · Gümüş -0.08/-0.23/-0.53/-0.51/-0.29/-0.25 · Nasdaq -0.00/+0.07/+0.12/-0.05/+0.18/+0.14

## 15 dk ST (filtresiz, kıyas) (`st15`)

Kemal'in TradingView indikatöründeki kural: 15 dakikalık Supertrend dönünce gir; filtre yok, uyum filtresinin etkisini görmek için kıyas. Stop 15 dk ST çizgisi, 15 dk ST ters dönünce ya da pencere sonunda çık. Pencere: ana seans.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 1611 | 36 | -0.076 | -122.3 | -133.4 | -2.91 | -0.084 | -0.071 | ❌ |
| DAX | 1415 | 43 | +0.026 | +36.6 | -35.3 | 0.98 | +0.042 | +0.018 | ❌ |
| Gümüş | 1666 | 36 | -0.167 | -278.9 | -279.9 | -7.70 | -0.156 | -0.174 | ❌ |
| Nasdaq | 1152 | 49 | +0.050 | +57.4 | -17.7 | 1.83 | +0.049 | +0.050 | ❌ |

Yıllara göre net ort R: Altın -0.10/-0.07/-0.06/-0.12/-0.02/-0.09 · DAX +0.01/+0.07/-0.05/+0.04/+0.08/+0.01 · Gümüş -0.16/-0.15/-0.25/-0.16/-0.15/-0.10 · Nasdaq +0.08/+0.02/+0.04/+0.09/+0.08/-0.04

## 15 dk ST, GECE (Asya) — kıyas (`st15_gece`)

Kemal'in TradingView indikatöründeki kural: 15 dakikalık Supertrend dönünce gir; filtre yok, uyum filtresinin etkisini görmek için kıyas. Stop 15 dk ST çizgisi, 15 dk ST ters dönünce ya da pencere sonunda çık. Pencere: Asya saatleri (Londra 00:00–07:45), metaller.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 1004 | 41 | -0.095 | -95.0 | -103.1 | -4.49 | -0.182 | -0.047 | ❌ |
| Gümüş | 1057 | 35 | -0.194 | -204.7 | -214.1 | -9.73 | -0.277 | -0.147 | ❌ |

Yıllara göre net ort R: Altın -0.15/-0.21/-0.10/-0.05/-0.01/-0.02 · Gümüş -0.32/-0.23/-0.24/-0.17/-0.19/+0.02

## 15 dk ST + 1 saatlik ST uyumlu (TSMC2) (`st1s`)

Kemal'in TradingView indikatöründeki kural: 15 dakikalık Supertrend dönünce gir, ama sadece 1 saatlik Supertrend de aynı yöndeyse (uyumlu). Stop 15 dk ST çizgisi, 15 dk ST ters dönünce ya da pencere sonunda çık. Pencere: ana seans.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 808 | 38 | -0.063 | -50.8 | -67.5 | -1.75 | -0.053 | -0.069 | ❌ |
| DAX | 689 | 46 | +0.057 | +39.3 | -21.6 | 1.54 | +0.066 | +0.053 | ❌ |
| Gümüş | 813 | 36 | -0.153 | -124.3 | -130.4 | -4.69 | -0.182 | -0.136 | ❌ |
| Nasdaq | 518 | 49 | +0.027 | +14.0 | -17.0 | 0.68 | -0.007 | +0.048 | ❌ |

Yıllara göre net ort R: Altın -0.09/-0.02/-0.12/-0.16/+0.03/+0.06 · DAX +0.02/+0.11/-0.01/+0.13/+0.06/+0.05 · Gümüş -0.16/-0.21/-0.18/-0.17/-0.14/-0.02 · Nasdaq -0.06/+0.05/+0.14/+0.12/-0.01/-0.16

## 15 dk ST + 1s uyumlu, GECE (Asya) (`st1s_gece`)

Kemal'in TradingView indikatöründeki kural: 15 dakikalık Supertrend dönünce gir, ama sadece 1 saatlik Supertrend de aynı yöndeyse (uyumlu). Stop 15 dk ST çizgisi, 15 dk ST ters dönünce ya da pencere sonunda çık. Pencere: Asya saatleri (Londra 00:00–07:45), metaller.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 399 | 37 | -0.085 | -33.8 | -45.9 | -2.38 | -0.210 | -0.018 | ❌ |
| Gümüş | 416 | 35 | -0.172 | -71.4 | -81.3 | -5.20 | -0.244 | -0.132 | ❌ |

Yıllara göre net ort R: Altın -0.15/-0.30/-0.15/-0.06/+0.05/+0.12 · Gümüş -0.31/-0.16/-0.24/-0.25/-0.19/+0.15

## Likidite Süpürmesi (`supurme`)

Fiyat açılıştan sonraki ilk saatlerde önceki günün tepesini/dibini ya da gece aralığını kısa süre aşıp oradaki stopları patlatır, ama 15 dakika içinde geri seviyenin içine kapanırsa kırılım tutmamış demektir; ters yöne girilir. Stop süpürmenin ucunun hemen ötesinde, hedef 2R; en fazla 3 saat beklenir ve seans sonunda her durumda kapanır, geceye pozisyon taşınmaz.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 1763 | 29 | -0.308 | -542.5 | -542.1 | -11.12 | -0.365 | -0.280 | ❌ |
| DAX | 1231 | 32 | -0.185 | -228.1 | -240.4 | -5.15 | -0.202 | -0.177 | ❌ |
| Gümüş | 875 | 29 | -0.343 | -300.3 | -304.0 | -9.51 | -0.489 | -0.289 | ❌ |
| Nasdaq | 1372 | 32 | -0.161 | -221.1 | -228.5 | -4.62 | -0.173 | -0.154 | ❌ |

Yıllara göre net ort R: Altın -0.29/-0.45/-0.28/-0.37/-0.24/-0.19 · DAX -0.18/-0.22/-0.18/-0.16/-0.25/-0.11 · Gümüş -0.51/-0.46/-0.29/-0.42/-0.26/-0.22 · Nasdaq -0.12/-0.22/-0.20/-0.22/-0.11/-0.04

## Likidite Süpürmesi B (karşı uç hedefi) (`supurme_b`)

Giriş ve stop ana süpürme sinyaliyle aynı: seviye kısa süre aşılıp 15 dakika içinde geri içeri kapanırsa ters yöne girilir, stop süpürme ucunun ötesinde. Fark hedefte: sabit 2R yerine açılış öncesi aralığın karşı ucu hedeflenir, çünkü bir taraftaki stoplar alındıktan sonra fiyatın sıradaki mıknatısı öbür taraftaki stoplardır. Karşı uç 1R'den yakınsa işlem açılmaz; en fazla 3 saat, seans sonunda kapanır.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 1733 | 19 | -0.333 | -576.6 | -579.5 | -7.76 | -0.493 | -0.253 | ❌ |
| DAX | 1208 | 16 | -0.240 | -290.2 | -305.2 | -3.68 | -0.091 | -0.312 | ❌ |
| Gümüş | 868 | 23 | -0.378 | -328.3 | -329.1 | -7.96 | -0.551 | -0.313 | ❌ |
| Nasdaq | 1333 | 15 | -0.219 | -292.2 | -291.2 | -3.23 | -0.216 | -0.221 | ❌ |

Yıllara göre net ort R: Altın -0.46/-0.53/-0.21/-0.36/-0.28/-0.12 · DAX -0.11/-0.08/-0.35/-0.26/-0.24/-0.40 · Gümüş -0.59/-0.50/-0.36/-0.39/-0.30/-0.24 · Nasdaq -0.25/-0.18/-0.34/-0.24/-0.19/-0.05

