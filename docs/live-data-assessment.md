# Canlı Veri ve Veri Doğruluğu Değerlendirmesi

Maçlar `fixtures` tablosunda durur. Puan tablosu ve takım metrikleri API'den kopyalanmaz, tamamlanmış maçlardan (`FT`, `AET`, `PEN`) her okumada hesaplanır. Doğrulanamayan bilgiler "doğrulanamadı" ile işaretlenir. Canlı takip şu an uygulanmış bir özellik değildir.

## En Önemli 5 Risk

### 1. Maç bitmiş ama veritabanında hâlâ "canlı" ya da "başlamadı" görünmesi

- **Ne zaman olur:** Bir güncelleme atlanır ya da hata verir. Zamanlayıcı canlı maçları en iyi ihtimalle saatte bir güncellediği için bu açık zaten küçük değildir.
- **Etkisi:** Maç listesinde yanlış durum görünür. Puan tablosunda o maçın sonucu eksik kalır.
- **Nasıl fark edilir:**
  - Başlamasının üzerinden 3 saatten fazla geçmiş ama hâlâ tamamlanmamış maçlar aranır.
  - Son başarılı senkronizasyonun zamanına bakılır.
  - `sync_runs` tablosunda art arda başarısız kayıt olup olmadığına bakılır.
- **Nasıl düzeltilir:** Sadece o maçlar id ile yeniden çekilir. Arayüzde "veriler eski olabilir" uyarısı gösterilebilir.

### 2. Bitmiş maçın sonucu sonradan değişir, ama bitti sayılan sezon bir daha çekilmez

- **Ne zaman olur:** Maçtan sonra skor düzeltilir ya da hükmen karar verilir. Bizim zamanlayıcı, tüm maçları bitmiş bir sezonu bir daha hiç güncellemez.
- **Etkisi:** Yanlış sonuç kalıcı olur.
- **Nasıl fark edilir:** Bitmiş bir maçın durumu ya da skoru değiştiğinde bunun kaydı `fixture_changes` tablosuna yazılır ve yüksek öncelikli uyarı oluşturulur.
- **Nasıl düzeltilir:** Bitmiş sezonlar için haftada 1 istek atılabilir, değişiklik varsa kaydedilir.

### 3. Beklenmedik durum kodları (`AWD`, `WO`, `ABD`, `SUSP`, `PST`, `CANC`)

Bu kodlar hükmen sonuç, yarıda kalan, durdurulan, ertelenen ve iptal edilen maçları gösterir. Bizim saydığımız durumlar yalnızca `FT`, `AET` ve `PEN`'dir.

- **Ne zaman olur:** Sezon içinde hükmen sonuçlanan, yarıda kalan ya da ertelenen bir maç olduğunda.
- **Etkisi:** Hükmen maçlar tabloya girmez. Yarıda kalan ya da ertelenen maçlar oynanmamış maç sayısını şişirir ve sezonun bitmiş sayılmasını engeller.
- **Nasıl fark edilir:** Bitmiş sezonlarda durum dağılımı sorgulanır. Toplam maç sayısı, beklenen sayı ile karşılaştırılır (takım sayısı × (takım sayısı − 1)).
- **Nasıl düzeltilir:** Hangi durumun puana ve gol ortalamasına gireceği, hangisinin sezonu kapanmış sayacağı tek bir yerde yazılı bir durum politikasıyla tanımlanır.

### 4. Aynı eşleşmenin iki farklı ID ile bulunması

- **Ne zaman olur:** Yeniden planlanan bir maç, sağlayıcıda yeni bir kayıt olarak görünür. Ya da sağlayıcı verisinde bir hata vardır.
- **Etkisi:** İki kayıt da tamamlanmış görünürse maç tabloda iki kez sayılır.
- **Nasıl fark edilir:** Aynı lig, sezon, ev sahibi ve deplasman takımıyla yakın tarihli birden fazla kayıt aranır. Bir takımın maç sayısının beklenenden fazla çıkması da işaret eder.
- **Nasıl düzeltilir:** Bir tekilleştirme kuralı belirlenir ve yönetici inceler. Kayıt silinmez, geçersiz olarak işaretlenir. Böylece geçmiş korunur.

### 5. Kota tükenmesi nedeniyle güncellemelerin durması

- **Ne zaman olur:** Yoğun maç gününde otomatik bütçe (70) biter ve güncellemeler durur.
- **Etkisi:** Kullanıcı canlı sandığı ekranda eski skoru görür. Şu anki uyarı yalnızca 24 saatten eski veride çıkıyor, bu canlı için yetersizdir.
- **Nasıl fark edilir:**
  - Kullanım belli bir eşiği (70'ten yüksek) geçince uyarı verilir.
  - Canlı maç penceresinde son başarılı güncelleme zamanına bakılır.
- **Nasıl düzeltilir:**
  - Kalan bütçeye göre yoklama aralığı uzatılır.
  - Canlı maçlarda son güncelleme zamanı ekranda gösterilir.
  - Bütçe dolunca bu durum arayüzde açıkça yazılır.

---

## Günlük 100 istekle canlı maç takibi

- Yoklama yalnızca canlı pencerelerde yapılır. Pencere, veritabanındaki başlama saatlerinden hesaplanır: ilk maçtan 5 dakika önce başlar, son maçtan 2 saat 15 dakika sonra biter. Pencere dışında 0 istek harcanır.
- Her yoklama tek istektir. Maliyeti maç ve lig sayısından bağımsızdır, yalnızca süreyle artar.
- 100 isteğin 30'u manuel güncellemeye ayrılır, 70'i otomatik takibe. Zaten şu anda da böyledir.
- Pencere bitince biten maçlar `ids` ile tek istekte teyit edilir. Bir maçın canlı listeden kaybolması "bitti" anlamına gelmez. Durum her zaman API'nin durum alanından okunur.

### Yaklaşık hesaplama

| Pencere sayısı | Canlı süre | Yoklama aralığı | İstek |
|---|---|---|---|
| 1 pencere | 150 dk | 3 dk | 50 + 1 teyit |
| 2 pencere | 300 dk | 5 dk | 60 + 2 teyit |
| 3 pencere | 450 dk | 7 dk | yaklaşık 65 + 3 teyit |

Sunulabilecek güncelleme sıklığı 3 ile 7 dakika arasındadır. Sağlayıcı veriyi 15 saniyede bir yenilediği için bizim gecikmemiz bu aralık kadardır. Dakika altı güncelleme 100 istekle mümkün değildir. 1 dakika aralıkla tek bir 2,5 saatlik pencere bile 150 istek atar.

---

## Skor sonradan değişirse, maç hükmen sonuçlanırsa, puan silinirse

**Bugünkü davranış:** Bir maç yeniden çekildiğinde değişiklik güncellenir. Durum, skor ve saat değişimi `fixture_changes` tablosuna yazılır. Puan tablosu ve takım metrikleri her okumada hesaplandığı için düzeltilmiş skor bir sonraki istekte kendiliğinden yansır. Saklanan toplam olmadığından tutarsız toplam oluşmaz.

**Sorun oluşturabilecek noktalar:**
- Bitmiş sezonların bir daha çekilmemesi.
- `AWD` ve `WO` maçların sayılmaması.
- Puan silme cezalarının maç sonuçlarından türetilememesi.

Bunları aşağıdaki çözümlerle düzeltebiliriz.

- **Skor değişimi:** Ek bir işlem gerektirmeden, bitmiş bir maç değiştiğinde yüksek öncelikli uyarı üretilir ve skor güncellenir.
- **Hükmen:** Verilen skorla puan tablosuna sayılır. Oynanmadığı için gol ortalaması ve son 5 maç formu gibi oynanan maç metriklerinden hariç tutulur.
- **Puan silme:** Ceza, maç sonucunu değiştirmez. Bu yüzden "maçlardan hesaplama" şartı bozulmadan, ayrı ve denetlenebilir bir düzeltme olarak tutulur.
  - Tablo puanı, maçlardan hesaplanan puan ile düzeltmelerin toplamıdır.
  - Ceza ayrı bir dipnot olarak gösterilir.
  - Galibiyet oranı, form ve gol metrikleri değişmez.
  - Düzeltmeyi yönetici, kaynak belirterek girer.
  - API'nin puan tablosu görüntülenmez, yalnızca karşılaştırma için kullanılır. Hesaplanan puan ile farklıysa uyarı üretilir.

---

## Scheduler'ın canlıda güvenilir çalışması için gerekenler

Şu anda scheduler, `docker compose` içinde uzun ömürlü bir döngü olarak planlandı. Canlı ortamda ücretsiz plan kullandığımız için çalıştırılamıyor. Karar mantığı veritabanındaki maçlardan türetildiği için kaçan bir tur sonraki turda kendiliğinden telafi edilir. Aşağıdaki değişiklikler yapılabilir:

1. **Ayrı ve sürekli çalışan bir süreç olmalı.** Web servisinden bağımsız küçük bir sunucu olabilir. Canlı pencerelerde 3-7 dakika gerektiği için dakika düzeyinde çalışan ve gecikmeli tetiklenen harici zamanlayıcılar yeterince güvenilir olmayabilir.
2. **Çift tur oluşmaması için** iki scheduler çalışırsa `pg_try_advisory_lock` ile bir öncelik seçimi yapılabilir.
3. **Pencere farkındalığı ve uyarlanabilir aralık** eklenebilir (yukarıdaki "Günlük 100 istekle canlı maç takibi" bölümünde açıklandı).
4. **Kota rezervasyonu** (uygulandı, bkz. `quota-and-concurrency.md`).
5. **Dayanıklılık:** Veritabanı bağlantısı için yeniden deneme, API hatalarında bekleme ve kapatma sinyalinde çalışan senkronizasyonu tamamlayıp çıkma gerekir.
6. **İzleme:** Her senkronizasyondan sonra "son başarılı güncelleme" zamanı yeniden yazılır. Canlı pencerede bir süredir senkronizasyon yoksa uyarı verilmelidir.
