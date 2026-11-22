# Özgün indikatör yarışması — sonuçlar

Veri: Altın 1483 gün · Gümüş 1518 gün · DAX 1518 gün · Nasdaq 1507 gün

İcra her aday için aynı (spread + kayma düşülmüş, tek pozisyon). Karar: net ≥ +0,10R VE 2023+ ≥ +0,10R VE t ≥ 2.

## Çapraz uyumsuzluk — geride kalan yetişir (`capraz`)

Altın ile gümüş, Nasdaq ile DAX normalde birlikte hareket eder. Son 15 dakikada biri kendi olağan oynaklığına göre belirgin yükselip (düşüp) diğeri yerinde saydıysa ve geride kalan aynı yöne kımıldamaya başladıysa, geride kalanda o yöne işlem açılır. Hedef aradaki açığın yarısının kapanması, stop geride kalanın bir normal 15 dakikalık hareketi kadar ters gidiş, en fazla 30 dakika tutulur ve seans sonunda kapanır; DAX'ta yalnız ABD verisi/açılışından Frankfurt kapanışına kadar, Nasdaq'ın DAX'ı sürüklediği saatlerde çalışır.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 1908 | 43 | -0.205 | -390.4 | -400.1 | -9.26 | -0.254 | -0.181 | ❌ |
| DAX | 2928 | 39 | -0.165 | -482.0 | -486.6 | -8.35 | -0.160 | -0.167 | ❌ |
| Gümüş | 231 | 37 | -0.303 | -70.0 | -69.0 | -5.03 | -0.358 | -0.299 | ❌ |

Yıllara göre net ort R: Altın -0.24/-0.26/-0.18/-0.19/-0.20/-0.06 · DAX -0.22/-0.07/-0.22/-0.13/-0.15/-0.17 · Gümüş -0.47/+0.16/-0.39/-0.38/-0.24

## Çapraz uyumsuzluk — öncü geri döner (`capraz_b`)

Altın-gümüş ya da Nasdaq-DAX çiftinde biri son 15 dakikada ortağı eşlik etmeden kendi olağan oynaklığına göre sert yükselip (düşüp) ilk ters mumu attığında, fırlayanın aşırıya kaçtığı varsayılıp tersine işlem açılır. Hedef aradaki açığın yarısının kapanması, stop bir normal 15 dakikalık hareket, en fazla 30 dakika tutulur ve seans sonunda kapanır.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 1326 | 39 | -0.257 | -340.5 | -339.6 | -9.54 | -0.305 | -0.230 | ❌ |
| DAX | 1014 | 39 | -0.174 | -176.9 | -176.9 | -5.18 | -0.164 | -0.179 | ❌ |
| Gümüş | 144 | 40 | -0.232 | -33.4 | -35.1 | -2.93 | +0.090 | -0.246 | ❌ |
| Nasdaq | 2543 | 38 | -0.147 | -372.7 | -373.2 | -6.49 | -0.152 | -0.144 | ❌ |

Yıllara göre net ort R: Altın -0.34/-0.28/-0.28/-0.27/-0.17/-0.15 · DAX -0.18/-0.11/-0.24/-0.20/-0.12/-0.15 · Gümüş +0.09/-0.15/-0.23/-0.23/-0.26 · Nasdaq -0.15/-0.15/-0.22/-0.18/-0.15/-0.01

## Rejim (gün tipi) (`rejim`)

Her dakikanın oynaklığını, son 20 günün aynı seans dakikasıyla kıyaslayıp normalize eder; seansın ilk saatinde fiyat normalin 1,5 katı std'den fazla tek yöne gittiyse günü 'trend', sakin ve yönsüz kaldıysa 'yatay' sayar, arada kalırsa hiç işlem yapmaz. Trend gününde ilk geri çekilmeden trend yönüne girer (stop 1σ, hedef 2σ); yatay günde fiyat VWAP'tan 1,5σ uzaklaşıp dönüş mumu yapınca VWAP'a dönüşe oynar. Tüm işlemler seans sonunda kapanır, geceye taşınmaz.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 570 | 37 | -0.118 | -67.5 | -75.9 | -2.42 | -0.227 | -0.064 | ❌ |
| DAX | 484 | 37 | -0.059 | -28.5 | -52.8 | -1.07 | -0.051 | -0.063 | ❌ |
| Gümüş | 483 | 33 | -0.318 | -153.4 | -159.8 | -7.00 | -0.147 | -0.384 | ❌ |
| Nasdaq | 376 | 43 | +0.067 | +25.4 | -13.9 | 1.09 | +0.034 | +0.084 | ❌ |

Yıllara göre net ort R: Altın -0.28/-0.16/-0.10/-0.07/+0.02/-0.12 · DAX +0.04/-0.15/-0.02/-0.29/+0.11/-0.03 · Gümüş -0.08/-0.23/-0.53/-0.52/-0.29/-0.25 · Nasdaq -0.00/+0.07/+0.12/-0.05/+0.24/+0.07

## 15 dk ST (filtresiz, kıyas) (`st15`)

Kemal'in TradingView indikatöründeki kural: 15 dakikalık Supertrend dönünce gir; filtre yok, uyum filtresinin etkisini görmek için kıyas. Stop 15 dk ST çizgisi, 15 dk ST ters dönünce ya da pencere sonunda çık. Pencere: ana seans.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 1647 | 36 | -0.072 | -119.2 | -131.5 | -2.80 | -0.084 | -0.066 | ❌ |
| DAX | 1420 | 43 | +0.024 | +34.0 | -35.9 | 0.90 | +0.042 | +0.015 | ❌ |
| Gümüş | 1674 | 36 | -0.168 | -281.3 | -282.3 | -7.75 | -0.156 | -0.175 | ❌ |
| Nasdaq | 1178 | 49 | +0.047 | +55.2 | -17.8 | 1.75 | +0.049 | +0.046 | ❌ |

Yıllara göre net ort R: Altın -0.10/-0.07/-0.06/-0.12/-0.01/-0.07 · DAX +0.01/+0.07/-0.05/+0.03/+0.08/+0.00 · Gümüş -0.16/-0.15/-0.25/-0.17/-0.15/-0.11 · Nasdaq +0.08/+0.02/+0.04/+0.09/+0.08/-0.04

## 15 dk ST, GECE (Asya) — kıyas (`st15_gece`)

Kemal'in TradingView indikatöründeki kural: 15 dakikalık Supertrend dönünce gir; filtre yok, uyum filtresinin etkisini görmek için kıyas. Stop 15 dk ST çizgisi, 15 dk ST ters dönünce ya da pencere sonunda çık. Pencere: Asya saatleri (Londra 00:00–07:45), metaller.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 1042 | 41 | -0.087 | -90.8 | -99.6 | -4.15 | -0.182 | -0.038 | ❌ |
| Gümüş | 1063 | 35 | -0.192 | -203.6 | -213.4 | -9.63 | -0.277 | -0.144 | ❌ |

Yıllara göre net ort R: Altın -0.15/-0.21/-0.10/-0.05/+0.00/+0.01 · Gümüş -0.32/-0.23/-0.24/-0.17/-0.19/+0.02

## 15 dk ST + 1 saatlik ST uyumlu (TSMC2) (`st1s`)

Kemal'in TradingView indikatöründeki kural: 15 dakikalık Supertrend dönünce gir, ama sadece 1 saatlik Supertrend de aynı yöndeyse (uyumlu). Stop 15 dk ST çizgisi, 15 dk ST ters dönünce ya da pencere sonunda çık. Pencere: ana seans.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 823 | 39 | -0.053 | -43.6 | -67.0 | -1.47 | -0.053 | -0.053 | ❌ |
| DAX | 692 | 46 | +0.058 | +40.0 | -21.6 | 1.56 | +0.066 | +0.054 | ❌ |
| Gümüş | 818 | 36 | -0.152 | -124.5 | -131.4 | -4.68 | -0.182 | -0.135 | ❌ |
| Nasdaq | 531 | 49 | +0.023 | +12.4 | -17.0 | 0.61 | -0.007 | +0.042 | ❌ |

Yıllara göre net ort R: Altın -0.09/-0.02/-0.12/-0.16/+0.08/+0.06 · DAX +0.02/+0.11/-0.01/+0.14/+0.06/+0.05 · Gümüş -0.16/-0.21/-0.18/-0.18/-0.14/-0.02 · Nasdaq -0.06/+0.05/+0.14/+0.12/-0.02/-0.14

## 15 dk ST + 1s uyumlu, GECE (Asya) (`st1s_gece`)

Kemal'in TradingView indikatöründeki kural: 15 dakikalık Supertrend dönünce gir, ama sadece 1 saatlik Supertrend de aynı yöndeyse (uyumlu). Stop 15 dk ST çizgisi, 15 dk ST ters dönünce ya da pencere sonunda çık. Pencere: Asya saatleri (Londra 00:00–07:45), metaller.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 419 | 38 | -0.068 | -28.4 | -45.8 | -1.93 | -0.210 | +0.003 | ❌ |
| Gümüş | 418 | 34 | -0.173 | -72.4 | -81.3 | -5.23 | -0.244 | -0.135 | ❌ |

Yıllara göre net ort R: Altın -0.15/-0.30/-0.15/-0.06/+0.06/+0.16 · Gümüş -0.31/-0.16/-0.24/-0.25/-0.19/+0.13

## Likidite Süpürmesi (`supurme`)

Fiyat açılıştan sonraki ilk saatlerde önceki günün tepesini/dibini ya da gece aralığını kısa süre aşıp oradaki stopları patlatır, ama 15 dakika içinde geri seviyenin içine kapanırsa kırılım tutmamış demektir; ters yöne girilir. Stop süpürmenin ucunun hemen ötesinde, hedef 2R; en fazla 3 saat beklenir ve seans sonunda her durumda kapanır, geceye pozisyon taşınmaz.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 1831 | 29 | -0.301 | -551.9 | -552.4 | -11.06 | -0.365 | -0.272 | ❌ |
| DAX | 1232 | 32 | -0.186 | -228.6 | -240.9 | -5.15 | -0.202 | -0.178 | ❌ |
| Gümüş | 879 | 29 | -0.343 | -301.6 | -305.3 | -9.53 | -0.489 | -0.289 | ❌ |
| Nasdaq | 1409 | 32 | -0.156 | -219.3 | -228.0 | -4.51 | -0.173 | -0.146 | ❌ |

Yıllara göre net ort R: Altın -0.29/-0.45/-0.28/-0.37/-0.26/-0.16 · DAX -0.18/-0.22/-0.18/-0.17/-0.25/-0.11 · Gümüş -0.51/-0.46/-0.29/-0.42/-0.26/-0.22 · Nasdaq -0.12/-0.22/-0.20/-0.22/-0.11/-0.00

## Likidite Süpürmesi B (karşı uç hedefi) (`supurme_b`)

Giriş ve stop ana süpürme sinyaliyle aynı: seviye kısa süre aşılıp 15 dakika içinde geri içeri kapanırsa ters yöne girilir, stop süpürme ucunun ötesinde. Fark hedefte: sabit 2R yerine açılış öncesi aralığın karşı ucu hedeflenir, çünkü bir taraftaki stoplar alındıktan sonra fiyatın sıradaki mıknatısı öbür taraftaki stoplardır. Karşı uç 1R'den yakınsa işlem açılmaz; en fazla 3 saat, seans sonunda kapanır.

| Enstrüman | İşlem | Kazanma % | Net ort R | Net toplam R | Max DD R | t | 2021-22 | 2023+ | Karar |
|---|---|---|---|---|---|---|---|---|---|
| Altın | 1801 | 19 | -0.327 | -588.8 | -590.4 | -7.75 | -0.493 | -0.249 | ❌ |
| DAX | 1209 | 16 | -0.241 | -291.1 | -306.2 | -3.69 | -0.091 | -0.312 | ❌ |
| Gümüş | 872 | 23 | -0.378 | -329.6 | -330.4 | -7.98 | -0.551 | -0.313 | ❌ |
| Nasdaq | 1370 | 15 | -0.185 | -253.9 | -286.2 | -2.63 | -0.216 | -0.169 | ❌ |

Yıllara göre net ort R: Altın -0.46/-0.53/-0.21/-0.36/-0.28/-0.13 · DAX -0.11/-0.08/-0.35/-0.26/-0.24/-0.40 · Gümüş -0.59/-0.50/-0.36/-0.40/-0.30/-0.24 · Nasdaq -0.25/-0.18/-0.34/-0.24/-0.16/+0.15

