# Futbol Panosu

API-Football'dan gerçek futbol verisini çeken, PostgreSQL'de saklayan, FastAPI ile sunan ve Next.js arayüzünde gösteren bir uygulama. Lig ve sezon seçimi, puan tablosu, maç listesi (takım, durum ve tarih filtreli), takım performans analizi ve maç istatistikleri içerir.

**Canlı uygulama:** https://football-app-1-wd4t.onrender.com/

> Uygulama ücretsiz barındırma planında çalışıyor. Bir süre kullanılmadığında servisler uykuya geçiyor, bu yüzden ilk açılış 1-2 dakika sürebilir. Sayfa açılmazsa ya da hata gösterirse bir dakika bekleyip yenileyin.

## İçindekiler

- [Teknolojiler](#teknolojiler)
- [Mimari](#mimari)
- [Kurulum](#kurulum)
- [Testler](#testler)
- [Özellikler](#özellikler)
- [Backend API](#backend-api)
- [Veri güncelleme ve API limit stratejisi](#veri-güncelleme-ve-api-limit-stratejisi)
- [Canlıya alma](#canlıya-alma)
- [Bonus görevler](#bonus-görevler)
- [Bilinen sınırlamalar](#bilinen-sınırlamalar)
- [Proje yapısı](#proje-yapısı)
- [Kullanılan yapay zekâ araçları](#kullanılan-yapay-zekâ-araçları)

## Teknolojiler

| Katman     | Teknoloji                                                                  |
| ---------- | -------------------------------------------------------------------------- |
| Frontend   | Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui, Recharts |
| Backend    | Python, FastAPI, psycopg, httpx                                            |
| Veritabanı | PostgreSQL 16                                                              |
| Veri çekme | Python (`app.sync`, `app.scheduler`)                                       |
| Test ve CI | pytest, GitHub Actions                                                     |
| Çalıştırma | Docker Compose                                                             |

## Mimari

```
API-Football ──► sync (Python) ──► PostgreSQL ──► FastAPI ──► Next.js
                    ▲                                           │
         scheduler + "Verileri güncelle" butonu ◄───────────────┘
```

- API-Football'a **yalnızca backend** erişir. API anahtarı `.env` dosyasında durur, Git'e girmez ve tarayıcıya gitmez.
- Arayüz yalnızca veritabanındaki veriyi okur. API-Football'a erişilemese bile mevcut veriler gösterilmeye devam eder.
- Puan tablosu ve takım performans metrikleri API'den kopyalanmaz. Veritabanındaki tamamlanmış maç sonuçlarından hesaplanır (galibiyet oranı, son 5 maç formu, maç başına gol ortalamaları, iç saha/deplasman performansı).

Ayrıntılı belgeler:

- Database Şeması(mail üzerinden): ilişki diyagramı ve tablo açıklamaları
- API kullanımı ve veri güncelleme stratejisi(mail üzerinden)
- [Kota koruması ve eşzamanlılık](docs/quota-and-concurrency.md): eşzamanlı isteklerde kota, hata durumlarında kayıt, `force` yetkisi
- [Canlı veri değerlendirmesi](docs/live-data-assessment.md): riskler, 100 istekle canlı takip planı, skor düzeltmeleri

## Kurulum

Gereksinimler: Docker ve Docker Compose, bir **API-Football anahtarı** (ücretsiz plan yeterli, [dashboard.api-football.com](https://dashboard.api-football.com) adresinden birkaç dakikada alınır).

### 1. Ortam dosyası

```bash
cp .env.example .env
```

Windows Komut İstemi'nde `copy .env.example .env`. Ardından `.env` dosyasındaki `API_FOOTBALL_KEY` değerine anahtarınızı yazın (**tırnaksız**, `=` işaretinden hemen sonra). `.env` dosyası Git'e girmez.

### 2. Servisleri başlatın

```bash
docker compose up -d --build
```

| Servis                 | Adres                      |
| ---------------------- | -------------------------- |
| Arayüz                 | http://localhost:3000      |
| Backend API ve Swagger | http://localhost:8000/docs |
| PostgreSQL             | localhost:5432             |

Veritabanı şeması ([`backend/schema.sql`](backend/schema.sql)), boş bir veritabanı ilk oluşturulurken otomatik uygulanır.

### 3. İlk veriyi çekin

Veritabanı boş başlar. Lig ve sezonu siz seçersiniz:

```bash
docker compose run --rm backend python -m app.sync --league 203 --season 2024   # Süper Lig 2024/25
docker compose run --rm backend python -m app.sync --league 203 --season 2023   # Süper Lig 2023/24
docker compose run --rm backend python -m app.sync --league 39  --season 2024   # Premier Lig 2024/25
docker compose run --rm backend python -m app.sync --league 140 --season 2024   # La Liga 2024/25
```

Her lig-sezonun ilk yüklemesi **3 API isteği** harcar (lig, takımlar, maçlar). Komutlar arasında hız sınırı nedeniyle birkaç saniye beklenir. Birini yeterince görmek için yalnızca ilk satırı çalıştırmanız yeterlidir. Yükleme bitince http://localhost:3000 adresini yenileyin.

> **Ücretsiz plan kısıtı:** Yalnızca 2022-2024 sezonları erişilebilir (daha yenisi `Free plans do not have access to this season` hatası verir) ve günlük 100 istek, dakikada 10 istek sınırı vardır. Bu projede erişilebilen güncel sezon 2024/25'tir.

### Geliştirme

Backend kodu konteynere bağlıdır (`--reload`), değişiklikler anında yansır. Frontend'i hızlı geliştirmek için Docker'daki frontend'i durdurup yerelde çalıştırın:

```bash
docker compose stop frontend
cd frontend
npm install
npm run dev     # http://localhost:3000
```

`frontend/.env.local` dosyasına `NEXT_PUBLIC_API_URL=http://localhost:8000` yazın.

| Değişiklik                  | Yapılması gereken                                         |
| --------------------------- | --------------------------------------------------------- |
| Backend kodu                | Hiçbir şey (otomatik yenilenir)                           |
| Scheduler'ın kullandığı kod | `docker compose up -d --build scheduler`                  |
| Docker'daki frontend        | `docker compose up -d --build frontend`                   |
| `.env`                      | `docker compose up -d --force-recreate backend scheduler` |

### Windows notları

Komutlar Komut İstemi ve PowerShell'de çalışır. Şemayı elle uygulamanız gerekirse (yalnızca şemaya yeni tablo eklediyseniz):

```powershell
Get-Content backend/schema.sql | docker compose exec -T db psql -U football -d football
```

## Testler

Backend için 48 test vardır. Hiçbiri gerçek API-Football'a istek atmaz. 39'u veritabanı gerektirmez. Kota testleri (9) gerçek bir PostgreSQL ister ve `TEST_DATABASE_URL` ayarlı değilse atlanır.

```bash
docker compose run --rm -e TEST_DATABASE_URL=postgresql://football:football@db:5432/football_test backend sh -c "pip install -q -r requirements-dev.txt && python -m pytest -v"
```

`TEST_DATABASE_URL`, adı `test` ile biten ayrı bir veritabanına işaret etmelidir. Testler başka adlı bir veritabanında çalışmayı reddeder. Veritabanı yoksa testler onu kendisi oluşturur.

Test edilenler:

- **Takım performans hesaplamaları** (`app/stats.py`): galibiyet oranı, gol ortalamaları, son 5 maç formu (sıralama dahil), iç saha/deplasman ayrımı ve birikmiş puan. Beklenen değerler elle hesaplanmış örnek maçlara dayanır.
- **Takım istatistikleri uç noktası**: yanıtın ortak `compute_team_stats` fonksiyonuyla ve elle hesaplanmış değerlerle (3G 2B 2M, 11 puan, form `LLDWW`) örtüştüğü.
- **Kota koruması** (`app/quota.py`): 99. istekte eşzamanlı işlemlerin kotayı aşmaması, bağlantı hatasında kotanın düşmemesi, okuma zaman aşımında düşmesi.
- **`force` yetkisi**: `X-Admin-Token` olmadan `force` isteğinin reddedilmesi.
- **API verisinin temizlenmesi** (`normalize_fixture`): eksik zorunlu alanlı maçların atlanması, oynanmamış maçın boş skorunun korunması.
- **İstatistik değerlerinin sayıya çevrilmesi** (`parse_value`): `"40%"` → 40, `"0.36"` → 0.36, boş ve geçersiz değerler.

GitHub Actions her push'ta backend testlerini ve frontend kontrollerini (tip denetimi, lint, build) çalıştırır ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Özellikler

- **Genel görünüm:** lig ve sezon seçimi, oynanan ve tamamlanmamış maç sayısı, toplam gol, son veri güncelleme zamanı
- **Puan tablosu:** sıra, oynanan, galibiyet, beraberlik, mağlubiyet, atılan ve yenilen gol, averaj, puan
- **Maçlar:** tarihe göre liste, takım, durum ve tarih aralığı filtresi, ev sahibi/deplasman ve skor, sayfalama
- **Takım analizi:** son 5 maç ve form, galibiyet oranı, maç başına atılan ve yenilen gol, iç saha ve deplasman karşılaştırması, sezon boyunca birikmiş puan grafiği
- **Maç istatistikleri:** şut, korner, topa sahip olma ve diğer değerler (bonus, aşağıya bakın)
- **Veri güncelleme:** "Verileri güncelle" butonu, son güncelleme zamanı, günlük API kullanım göstergesi, güncelleme başarısız olduğunda ya da veri eski olduğunda uyarı

## Backend API

Swagger arayüzü: `http://localhost:8000/docs`

| Uç nokta                                  | Açıklama                                                                                                                                                                             |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `GET /leagues`                            | Ligler ve sezonları                                                                                                                                                                  |
| `GET /seasons/{id}/overview`              | Oynanan ve tamamlanmamış maç sayısı, toplam gol, son senkronizasyon                                                                                                                  |
| `GET /seasons/{id}/teams`                 | Takım listesi                                                                                                                                                                        |
| `GET /seasons/{id}/fixtures`              | Maçlar. Filtreler: `team_id`, `status`, `date_from`, `date_to`, `limit`, `offset`                                                                                                    |
| `GET /seasons/{id}/standings`             | Puan tablosu (maç sonuçlarından hesaplanır)                                                                                                                                          |
| `GET /seasons/{id}/teams/{team_id}/stats` | Son 5 maç formu, galibiyet oranı, gol ortalamaları, iç saha/deplasman, puan grafiği verisi                                                                                           |
| `GET /fixtures/{id}`                      | Tek maç                                                                                                                                                                              |
| `GET /fixtures/{id}/statistics`           | Maç istatistikleri (ilk istekte API'den çekilir, sonra veritabanından gelir)                                                                                                         |
| `POST /sync`                              | Bir lig ve sezonu arka planda güncelle (`{"league_id":203,"season":2024}`). `force: true` soğuma süresini atlar ve yalnızca `X-Admin-Token` başlığı ile kabul edilir (aşağıya bakın) |
| `GET /sync/status`                        | Son senkronizasyon durumu                                                                                                                                                            |
| `GET /usage`                              | Günlük API kullanımı                                                                                                                                                                 |
| `GET /health`                             | Sağlık kontrolü (veritabanına dokunmaz)                                                                                                                                              |

`force` yönetici anahtarı: `.env` içinde `ADMIN_TOKEN` tanımlıdır ve istek `X-Admin-Token: <değer>` başlığını taşırsa `force` kabul edilir. Aksi halde HTTP 403 döner. `ADMIN_TOKEN` boşsa `force` HTTP üzerinden tamamen kapalıdır. Normal güncelleme (`force` olmadan) anahtar istemez. Komut satırındaki `--force` bundan etkilenmez.

Puan tablosu sıralaması: puan, averaj, atılan gol, takım adı. Takım istatistikleri yalnızca tamamlanmış maçlardan (`FT`, `AET`, `PEN`) hesaplanır. Tarih filtreleri İstanbul saatine göre yorumlanır (`APP_TIMEZONE` ile değiştirilebilir).

## Veri güncelleme ve API limit stratejisi

Ayrıntılar API kullanımı ve veri güncelleme stratejisi belgesindedir. Özet:

| Veri                           | Ne zaman güncellenir                                          | API isteği              |
| ------------------------------ | ------------------------------------------------------------- | ----------------------- |
| Lig ve sezon bilgisi, takımlar | İlk senkronizasyonda, sonra 7 günde bir                       | 2                       |
| Maçlar (tarih, durum, skor)    | Zamanlayıcı kurallarına göre                                  | 1                       |
| Maç istatistikleri             | Kullanıcı bir maçı ilk açtığında, yalnızca bitmiş maçlar için | 1 (maç başına, bir kez) |

Zamanlayıcı her 15 dakikada bir karar verir ve sezonun durumuna göre davranır: tüm maçları bitmiş sezonları hiç güncellemez, oynanan ya da sonucu beklenen maçı olan sezonları saatte bir, yalnızca ileri tarihli maçı olanları günde bir günceller.

**Gerekçe:** Günlük 100 istek küçük bir bütçedir. Bitmiş bir sezon değişmez, lig ve takım bilgisi nadiren değişir, bu yüzden düzenli güncelleme tek istekle (`/fixtures`) yapılır. Ek önlemler:

- Aynı lig-sezon son 15 dakika içinde güncellendiyse yeni istek atılmaz (soğuma süresi)
- Aynı lig-sezon için iki senkronizasyon aynı anda çalışmaz
- Her istek `api_requests` tablosuna yazılır, günlük kullanım buradan hesaplanır. Otomatik güncelleme günlük 70 istekte durur, kalan 30 manuel güncelleme için ayrılır
- İstekler arasında en az 6,5 saniye beklenir. Ağ hatası ve 5xx yanıtları 2, 4 ve 8 saniye bekleyerek 4 kez denenir
- Başarısız senkronizasyon yazılan verileri geri alır, `sync_runs` kaydı hata mesajıyla saklanır ve arayüz uyarı gösterir
- Arayüz API-Football'a hiç gitmediği için, API'ye erişilemese ya da bütçe dolsa bile mevcut veriler gösterilir

Manuel güncelleme: arayüzdeki "Verileri güncelle" butonu, `POST /sync` ya da `python -m app.sync --league 203 --season 2024 [--force]`.

## Canlıya alma

Canlı sürüm ücretsiz planlarda çalışır:

| Parça      | Hizmet                                | Not                                                                                                                                                             |
| ---------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Veritabanı | Neon (PostgreSQL)                     | Backend'e **havuzsuz (direct)** bağlantı adresi verilmelidir. Havuzlu (`-pooler`) adreste, yedekten yükleme sonrası `search_path` boş kalıp tablolar bulunamadı |
| Backend    | Render (Docker, ücretsiz web servisi) | Ortam değişkenleri: `DATABASE_URL`, `API_FOOTBALL_KEY`                                                                                                          |
| Frontend   | Render (Docker, ücretsiz web servisi) | Ortam değişkeni: `API_URL` (backend adresi, sonunda `/` olmadan)                                                                                                |

Notlar:

- Render'ın ücretsiz servisleri 15 dakika istek almazsa uykuya geçer ve ilk istek yaklaşık bir dakika sürer. Ücretsiz plan, tüm servisler için ortak 750 saatlik aylık kota verir, bu yüzden iki servisi 7/24 uyanık tutmak mümkün değildir. Bilinçli olarak uyandırma pingi kurulmadı.
- **Canlı ortamda scheduler çalışmıyor.** Scheduler yerelde Docker Compose ile çalışır. Ücretsiz Render planında sürekli çalışan arka plan işi yoktur ve erişilebilen sezonların tamamı bitmiş olduğu için güncellenecek bir şey de yoktur. Canlıda veri, "Verileri güncelle" butonuyla manuel güncellenir.
- Canlı veritabanı, yerel veritabanının `pg_dump` yedeğiyle yüklendi (API kotası harcanmadan).

## Bonus görevler

| Bonus                     | Durum                                                                                                                                                                                                                                    |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **B: Maç istatistikleri** | Yapıldı. Biten bir maçın skoruna tıklayınca şut, korner, topa sahip olma, pas ve diğer değerler karşılaştırmalı gösterilir. Veri maç başına bir kez çekilip saklanır. API veri sağlamıyorsa ya da bütçe doluysa maç sayfası bunu açıklar |
| **D: Docker**             | Yapıldı. Veritabanı, backend, scheduler ve frontend `docker compose up -d --build` ile çalışır                                                                                                                                           |
| A: Canlı skor             | Yapılmadı. Ücretsiz planda erişilebilen sezonların hepsi bittiği için gerçek canlı veriyle denenemezdi                                                                                                                                   |
| C: Yapay zekâ analizi     | Yapılmadı                                                                                                                                                                                                                                |

## Bilinen sınırlamalar

- `POST /sync` normal kullanımda kimlik doğrulaması istemez. Yalnızca `force` yönetici anahtarı ister. Kota; soğuma süresi, günlük bütçe ve veritabanı kilidi ile korunur ([ayrıntılar](docs/quota-and-concurrency.md)). Kullanıcı hesabı sistemi yoktur ve IP başına hız sınırı yoktur.
- Kota, ortak veritabanı üzerinden sayılır. Aynı API anahtarını farklı veritabanlarıyla kullanan iki ortam (yerel Docker ve canlı) birbirinin kullanımını görmez.
- Maç istatistikleri uç noktası, veritabanında olmayan her maç için bir kez API'ye gidebilir. Günlük bütçe sınırı bu uç noktayı da kapsar, ancak çok sayıda farklı maç numarası denenirse kota tüketilebilir.
- Puan sıralaması, eşit puanda ikili averaj kuralını uygulamaz. Bazı sezonlarda resmi tablodan farklı sıra çıkabilir. Puanlar ve averajlar doğrudur.
- Zamanlayıcının kuralları sabittir, ligin takvimine göre uyum sağlamaz. Ertelenmiş (`PST`) bir maçı olan sezon, planlanan saatinden sonraki ilk 3 gün saatte bir, sonra günde bir güncellenmeye devam eder.
- Frontend için otomatik test yoktur, yalnızca tip denetimi, lint ve build CI'da çalışır.
- Ücretsiz barındırma nedeniyle canlı sürümde ilk açılış yavaştır.

## Proje yapısı

```
backend/
  app/
    main.py           FastAPI uç noktaları
    stats.py          Takım performans hesaplamaları
    sync.py           Lig/sezon senkronizasyonu (idempotent upsert, güncelleme geçmişi)
    scheduler.py      Otomatik güncelleme kararları
    api_client.py     API-Football istemcisi (hız sınırı, yeniden deneme, kullanım kaydı)
    match_stats.py    Maç istatistiklerini çekme ve saklama
    usage.py          Günlük kullanım hesabı
    quota.py          Kota rezervasyonu (kilit altında, eşzamanlı güvenli)
  tests/              pytest testleri
  schema.sql          Veritabanı şeması
frontend/
  app/                Sayfalar (genel görünüm, maçlar, maç detayı, takım)
  components/         Arayüz bileşenleri
  lib/                API istemcisi, tipler, biçimlendirme
docs/                 Şema, strateji, kota ve canlı veri belgeleri
docker-compose.yml
.env.example
```

## Kullanılan yapay zekâ araçları

Geliştirme sürecinde kod yazımı, hata ayıklama ve belge hazırlığı için Claude (Anthropic)'dan yardım alındı.
