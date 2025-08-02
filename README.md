# ✨ CosmicAPI - Gelişmiş Astroloji Motoru v2.8

Profesyonel, yüksek hassasiyetli ve modern bir astroloji API'si. CosmicAPI, doğum haritası verilerini, sinastri (ilişki) analizlerini, anlık transitleri ve detaylı astrolojik raporları sunmak için tasarlanmıştır.

API, modüler yapısı, **Redis tabanlı önbellekleme** sistemi, **API Anahtarı ile korunan** güvenli yapısı ve kolayca genişletilebilir mimarisi ile öne çıkar.

## 🚀 Temel Özellikler

*   **Yüksek Hassasiyetli Hesaplamalar:** Endüstri standardı olan **Swiss Ephemeris** kütüphanesi ile çalışır.
*   **Kapsamlı Natal Harita Analizi:**
    *   Tüm gezegenler, asteroitler (Chiron, Ceres, Pallas, Juno, Vesta), Ay Düğümleri ve Lilith'in konumları.
    *   8 farklı ev sistemi (Placidus, Whole Sign vb.) ve Modern/Geleneksel yönetici seçeneği.
    *   Boylam temelli tüm Major, Minor ve Creative açılar.
    *   **Yükselen (ASC) ve Tepe Noktası (MC) ile yapılan açılar.**
    *   **İleri Seviye Deklinasyon Açıları:** Paralel ve Kontra-Paralel.
    *   Açı kalıpları (Stellium, T-Kare, Büyük Üçgen).
*   **Görsel Harita Üretimi:**
    *   Profesyonel ve estetik **Natal Harita Görseli** (`.png`).
    *   Detaylı **Sinastri (Bi-Wheel) Harita Görseli** (`.png`).
*   **Detaylı Raporlama Motoru:**
    *   Tüm gezegenlerin, Yükselen'in, MC'nin, Ay Düğümleri'nin, Lilith'in ve Chiron'un Burç ve Ev yorumları.
    *   Tüm açıların (gezegen-gezegen, gezegen-aks, deklinasyon) yorumları.
    *   Ev yöneticileri ve retro gezegenler için özel raporlar.
*   **Modern Altyapı:** Hızlı, verimli ve otomatik interaktif dokümantasyon sağlayan **FastAPI** üzerine kurulmuştur.

---

## 📚 API Dokümantasyonu ve Kullanımı

Bu bölüm, CosmicAPI'yi kendi uygulamanıza nasıl entegre edeceğinizi adım adım açıklar.

### 1. Yetkilendirme (Authentication)

CosmicAPI, güvenliği sağlamak için API Anahtarı (API Key) kullanır. Her istekte, HTTP başlığı (header) olarak geçerli bir API anahtarı göndermeniz gerekmektedir.

*   **Header Adı:** `X-API-Key`
*   **Varsayılan Anahtar:** `COSMIC_API_SECRET_KEY_12345` (Bu değeri `core/config.py` dosyasından değiştirebilirsiniz.)

**Örnek (cURL ile):**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/v1/natal/full-chart' \
  -H 'accept: application/json' \
  -H 'X-API-Key: COSMIC_API_SECRET_KEY_12345' \
  -H 'Content-Type: application/json' \
  -d '{ "date": "1990-05-15", "time": "10:30", "lat": 41.0082, "lon": 28.9784 }'
```

### 2. Temel İstek (Request) Yapısı

Tüm `POST` istekleri, gövdesinde (body) `application/json` formatında bir veri bekler. Ana veri modeli **`BirthData`**'dır.

#### `BirthData` Modeli

| Alan | Tür | Gerekli mi? | Açıklama | Örnek Değer |
| :--- | :--- | :--- | :--- | :--- |
| `date` | `string` | Evet | Doğum tarihi (YYYY-MM-DD formatında) | `"1990-05-15"` |
| `time` | `string` | Evet | Doğum saati (HH:MM formatında, 24 saat) | `"10:30"` |
| `lat` | `float` | Evet | Enlem (Kuzey için pozitif, Güney için negatif) | `41.0082` |
| `lon` | `float` | Evet | Boylam (Doğu için pozitif, Batı için negatif) | `28.9784` |
| `house_system` | `string` | Hayır | Ev sistemi (Varsayılan: "P"). | `"W"` |
| `rulership_system`| `string` | Hayır | Yönetici sistemi (Varsayılan: "modern"). | `"traditional"` |

**Mevcut Ev Sistemleri:** `P` (Placidus), `K` (Koch), `R` (Regiomontanus), `C` (Campanus), `A` (Equal from ASC), `W` (Whole Sign), `O` (Porphyry), `B` (Alcabitius), `T` (Topocentric).

### 3. API Endpoint'leri

Tüm endpoint'ler `http://127.0.0.1:8000/v1/` adresi altında bulunur.

---
#### **A. Ham Veri ve Görseller**
##### `POST /natal/full-chart`
Bir haritanın tüm astrolojik verilerini (gezegenler, evler, açılar, yöneticiler vb.) tek bir JSON nesnesinde döndürür. Bu, en kapsamlı veri çıktısıdır.

##### `POST /natal/wheel-chart`
Verilen doğum bilgisi için profesyonel bir doğum haritası görseli oluşturur. Dönen cevap bir `image/png` dosyasıdır.

---
#### **B. Raporlar**
Tüm rapor endpoint'leri, ilgili astrolojik konumun tüm verilerini ve `interpretation` anahtarı altında yorum metnini döndürür.

##### **Ana Noktalar**
*   `/natal/report/ascendant` - Yükselen burç yorumu.
*   `/natal/report/mc-sign` - Tepe Noktası (MC) burç yorumu.

##### **Gezegen Yorumları**
*   `/natal/report/sun-sign` - Güneş burcu yorumu.
*   `/natal/report/moon-sign` - Ay burcu yorumu.
*   `/natal/report/planets-in-houses` - Tüm gezegenlerin ev konumlarına göre yorumları (liste döner).
*   `/natal/report/retrogrades` - Haritadaki tüm retro gezegenlerin yorumları (liste döner).

##### **İleri Seviye Yorumlar**
*   `/natal/report/aspects` - Tüm açıların (boylam ve deklinasyon) yorumları (liste döner).
*   `/natal/report/house-rulers-in-houses` - Tüm ev yöneticilerinin konum yorumları (liste döner).

##### **Karmik ve Psikolojik Noktalar**
*   `/natal/report/north-node-sign` - Kuzey Ay Düğümü'nün burç yorumu.
*   `/natal/report/north-node-in-house` - Kuzey Ay Düğümü'nün ev yorumu.
*   `/natal/report/lilith-sign` - Lilith'in burç yorumu.
*   `/natal/report/lilith-in-house` - Lilith'in ev yorumu.
*   `/natal/report/chiron-sign` - Chiron'un burç yorumu.
*   `/natal/report/chiron-in-house` - Chiron'un ev yorumu.

---
#### **C. Sinastri (İlişki) Analizi**
Bu endpoint'ler, istek gövdesinde `person1` ve `person2` anahtarları altında iki adet `BirthData` nesnesi bekler.

*   `/synastry/house-overlays` - Birinci kişinin gezegenlerinin, ikinci kişinin evlerine nasıl düştüğünü gösterir.
*   `/synastry/aspects` - İki harita arasındaki açıları listeler.
*   `/synastry/bi-wheel-chart` - İki haritayı iç içe çizen bir `image/png` görseli döndürür.

---
### 4. İnteraktif Test (`/docs`)
API'yi canlı olarak denemek ve tüm bu endpoint'leri test etmek için, sunucuyu çalıştırdıktan sonra tarayıcınızda **`http://127.0.0.1:8000/docs`** adresini ziyaret edin. Bu arayüz, API anahtarınızı girmenize ve tüm istekleri kolayca göndermenize olanak tanır.

---

## ⚙️ Kurulum ve Başlatma

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin.

### 1. Ön Gereksinimler

*   Python 3.8+
*   Docker (Redis için tavsiye edilir) veya yerel bir Redis kurulumu.

### 2. Kurulum Adımları

**a. Projeyi Klonlayın (veya İndirin):**
```bash
git clone https://github.com/KULLANICI_ADINIZ/cosmicapi.git
cd cosmicapi
```

**b. Sanal Ortam (Virtual Environment) Oluşturun ve Aktif Edin:**
Bu, projenin bağımlılıklarını sisteminizdeki diğer projelerden izole etmek için şiddetle tavsiye edilir.
*   **Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
*   **macOS / Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

**c. Gerekli Kütüphaneleri Yükleyin:**
```bash
pip install -r requirements.txt
```

### 3. Redis Sunucusunu Başlatma

API'nin önbellekleme sistemi için arka planda çalışan bir Redis sunucusuna ihtiyacı vardır.
*   **Docker ile (Tavsiye Edilen):**
    ```bash
    docker run -d --name cosmicapi-redis -p 6379:6379 redis
    ```
*   **Yerel Kurulum (Linux/WSL):**
    ```bash
    sudo service redis-server start
    ```

### 4. API Sunucusunu Başlatma

Kurulum tamamlandıktan ve Redis çalıştıktan sonra, API sunucusunu başlatabilirsiniz:
```bash
uvicorn main:app --reload
```
Sunucu başarıyla başladığında, terminalde `Uvicorn running on http://127.0.0.1:8000` mesajını göreceksiniz.

---

## 📂 Proje Yapısı

```
cosmicapi/
├── api/
│   └── v1/             # API endpoint'lerinin bulunduğu modüller (natal, synastry vb.)
├── core/
│   └── config.py       # Projenin tüm sabitleri ve ayarları
├── data/
│   ├── ephe/           # Swiss Ephemeris veri dosyaları
│   └── interpretations/  # Astroloji yorumlarını içeren JSON dosyaları
├── models/
│   └── pydantic_models.py # API girdi/çıktı veri modelleri
├── services/
│   ├── astrology_engine.py # Tüm astrolojik hesaplamaların yapıldığı yer
│   └── chart_drawer.py   # Harita görsellerini çizen modül
├── main.py               # FastAPI uygulamasının ana giriş noktası
├── requirements.txt      # Proje bağımlılıkları
└── README.md             # Bu dosya
```

## 🗺️ Gelecek Geliştirmeler (Roadmap)

- [x] **Caching:** Sık istenen verileri önbelleğe alarak API performansını artırmak. **(Tamamlandı)**
- [x] **İleri Seviye Raporlar:** Ev yöneticileri, retro gezegenler, ASC/MC açıları, Paralel açılar gibi detaylı yorumlar eklemek. **(Tamamlandı)**
- [ ] **Testler:** Projenin kararlılığını sağlamak için `pytest` ile birim ve entegrasyon testleri yazmak.
- [ ] **Öngörüm Teknikleri:** İlerletim (Progression), Solar Arc ve Güneş Dönüşü (Solar Return) haritaları için yeni modüller eklemek.
- [ ] **`.env` Dosyası:** Gizli anahtarları (`API_KEY`) koddan ayırıp `.env` dosyasına taşımak.

## 📄 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır.