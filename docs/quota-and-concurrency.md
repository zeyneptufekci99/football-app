# Kota Koruması, Eşzamanlılık ve Yetkilendirme

Kota kontrolü ilk sürümde "say, sonra isteği at, sonra kaydet" sırasıyla yapılıyordu. Bu sıra iki sebepten güvenli değildi:

1. **Kontrol ile yazma arasındaki boşluk.** Günlük kullanım 99 iken iki işlem aynı anda gelirse ikisi de isteği atar.
2. **Kaydın geç yazılması.** Kayıt istek bittikten sonra yazılıyordu. Yolda olan, yani henüz yanıtlanmamış bir istek hiçbir yerde görünmediği için o sırada kontrol yapan başka bir işlem kotayı olduğundan düşük görür.

## Çözüm: API isteği atılmadan önce kota rezerve edilir

1. Veritabanında, tüm işlemlerin paylaştığı tek bir kilit alınır (`pg_advisory_xact_lock`).
2. Kilit altında bugünkü sayılan istekler (`reserved` ve `completed` durumları) sayılır.
3. Sayı limite ulaştıysa istek hiç atılmaz. Değilse `api_requests` tablosuna `reserved` durumunda bir satır eklenir ve işlem kesinleşir (commit).
4. Kilit bırakılır, ardından HTTP isteği atılır. Kilit istek süresince tutulmaz, yalnızca sayma ve ekleme sırasında tutulur. Bu yüzden işlemler birbirlerinin API isteğini beklemez.
5. Yanıt gelince satır güncellenir ve `completed` olur.

Sayma ve ekleme aynı kilit altında yapıldığı için iki işlem aynı slotu alamaz. 99 iken eşzamanlı iki istek gelirse biri 100. slotu alır, diğeri reddedilir.

## Kapsam: farklı maçlar, sezonlar ve ligler

Kota, API anahtarına bağlı tek bir ortak havuzdur. Bu yüzden kilit lige, sezona ya da maça bağlı değildir. Tek ve genel bir anahtardır. `POST /sync`, zamanlayıcı, komut satırı ve maç istatistikleri uç noktası aynı kotayı paylaşır.

Limit çağıran tarafından belirlenir. Manuel güncelleme 100'e, zamanlayıcı 70'e kadar rezervasyon alabilir. Böylece otomatik güncelleme günün sonunda manuel güncelleme için 30 isteği ayrılmış bırakır.

## Başarısızlık ve kesinti durumunda ne olur

İlke: **kota asla olduğundan az sayılmaz.** Belirsiz durumlarda istek harcanmış kabul edilir.

| Durum | Kayıt | Kotadan düşer mi |
|---|---|---|
| Yanıt alındı | `completed` | Evet |
| Bağlantı hiç kurulmadı | `released` | Hayır |
| Gönderildikten sonra kesildi | `completed` | Evet |
| Rezervasyondan sonra işlem öldü | `reserved` | Evet |
| Kayıt güncellenemedi | `reserved` | Evet |
| Rezervasyon yapılamadı | kayıt yok | İstek atılmaz |
| Limit dolu | kayıt yok | İstek atılmaz |

Yeniden denemeler her deneme için ayrı rezervasyon alır, çünkü her deneme ayrı bir API isteği olabilir.

Yarıda kalan `reserved` satırları bilerek temizlenmez. İsteğin API'ye ulaşıp ulaşmadığı bilinemediği için onları saymamak kotayı aşma riskini taşır. Saymak ise en fazla birkaç istek fazla göstermeye yol açar.

## Doğrulama

`test_quota_concurrency.py` dosyası gerçek bir PostgreSQL üzerinde, dış API'ye hiç istek atmadan, sahte bir API ile çalışır.

- 99 kullanım varken 8 işlem aynı anda istek atar: yalnızca biri geçer, yedisi reddedilir. Sahte API'ye yalnızca 1 istek gider, toplam 100'de kalır.
- Limit 10 iken 30 eşzamanlı işlem: tam olarak 10 istek geçer.
- Zamanlayıcı bütçesi (70) dolduğunda manuel bütçe hâlâ açıktır.
- Bağlantı hatası kotadan düşmez. Okuma zaman aşımı ve HTTP 500 düşer.
- Yarıda kalan rezervasyon sayılmaya devam eder.
- Limit doluyken sahte API'ye hiç istek gitmez.

Testler veritabanı gerektirir. `TEST_DATABASE_URL` ayarlı değilse atlanır. Testler asıl veritabanına dokunmaz: adı `test` ile biten ayrı bir veritabanı kullanır ve başka adlı bir veritabanında çalışmayı reddeder. GitHub Actions'ta bir PostgreSQL servisiyle çalışır.

---

## `force` seçeneği ve yetkilendirme

`POST /sync` içindeki `force`, 15 dakikalık soğuma süresini atlar. Günlük bütçeyi **atlamaz**, kota her istekte rezervasyonla korunur. Yine de açık bir uç noktada `force` tehlikelidir. Soğuma süresi, tek bir çağıranın aynı lig-sezonu döngüyle tekrar tekrar çekerek bütçeyi hızla tüketmesini engelleyen asıl önlemdir.

### Kim neyi yapabilmeli

Bu tablo olması gereken yetkiyi gösterir. Hangilerinin uygulandığı aşağıda belirtilmiştir.

| İşlem | Kim yapabilmeli | Gerekçe |
|---|---|---|
| Okuma uç noktaları | Herkes | Yalnızca veritabanını okur, API kotasına dokunmaz. |
| Maç istatistiği görüntüleme | Herkes, ama sınırlı | Veritabanında yoksa bir API isteği harcar. Maç başına bir kez çekilir ve saklanır. |
| `POST /sync`, `force` olmadan, veritabanında zaten bulunan lig-sezon | Yetkisiz kullanıcı yapabilir | Soğuma süresi, eşzamanlılık kilidi ve günlük bütçe ile sınırlıdır. Güncelle butonu budur. |
| `POST /sync` ile veritabanında olmayan yeni lig ya da sezon | Yalnızca yönetici | İlk yükleme 3 istek harcar. Rastgele lig ve sezon numaralarıyla kota tüketmenin en kolay yoludur. |
| `force = true` | Yalnızca yönetici | Soğuma süresini atlar. |
| Zamanlayıcı ayarları, kota limitleri | Yalnızca sunucu yapılandırması | Kullanıcı girdisi olmamalı. |

### Bu projede ne uygulandı

- `force = true`, yalnızca geçerli bir `X-Admin-Token` başlığıyla kabul edilir. Başlık, `ADMIN_TOKEN` ortam değişkeniyle karşılaştırılır.
- `ADMIN_TOKEN` tanımlı değilse `force` HTTP üzerinden tamamen kapalıdır. Güvenli varsayılan budur, ek ayar gerekmez.
- Arayüzdeki buton `force` göndermediği için bundan etkilenmez.
- Komut satırındaki `--force` ve zamanlayıcı doğrudan kodu çağırdığı için bu kontrole takılmaz.
- Kapsamlı bir kullanıcı sistemi yapılmadı. Paylaşılan tek bir yönetici anahtarı, herkese açık ama kritik bir işlemi bilinçli olarak yalnızca operatöre ayırma ihtiyacı için yeterlidir.

### Önerilen (uygulanmadı)

- IP başına hız sınırı (`POST /sync` ve istatistik uç noktası için).
- Veritabanında olmayan lig-sezon için `POST /sync`'in yönetici anahtarı istemesi.
- Maç istatistikleri için günlük bütçeden ayrı bir üst sınır.
