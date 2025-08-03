# ✨ CosmicAPI - Gelişmiş Astroloji Motoru v3.0

Profesyonel, yüksek hassasiyetli ve modern bir astroloji API'si. CosmicAPI, doğum haritası verilerini, sinastri (ilişki) analizlerini, anlık transitleri ve detaylı astrolojik raporları sunmak için tasarlanmıştır.

**Canlı API Adresi:** `https://cosmicapiv1-1.onrender.com`

Bu API, **Redis tabanlı önbellekleme** sistemi sayesinde son derece hızlıdır ve **API Anahtarı ile korunan** güvenli bir yapıya sahiptir.

## 📚 API Entegrasyon Kılavuzu

Bu kılavuz, CosmicAPI'yi kendi web sitenize, mobil uygulamanıza veya bot'unuza nasıl entegre edeceğinizi adım adım açıklar.

### 1. Temel Bilgiler

*   **Ana URL (Base URL):** Tüm istekler bu adrese gönderilmelidir:
    `https://cosmicapiv1-1.onrender.com/v1`
*   **Metot:** Tüm endpoint'ler `POST` metodunu kullanır (bilgi almak için bile).
*   **Veri Formatı:** Tüm istek gövdeleri (`Request Body`) `Content-Type: application/json` formatında olmalıdır.

### 2. Yetkilendirme (Authentication)

CosmicAPI'ye yapılan her istekte, HTTP başlığı (header) olarak geçerli bir API anahtarı göndermeniz zorunludur.

*   **Header Adı:** `X-API-Key`
*   **Anahtar Değeri:** `COSMIC_API_SECRET_KEY_12345`

Eğer anahtar gönderilmez veya yanlış gönderilirse, API `401 Unauthorized` durum kodu ile hata döndürecektir.

### 3. Ana Veri Modeli: `BirthData`

Tüm natal harita istekleri, aşağıda belirtilen alanları içeren bir JSON nesnesi bekler.

| Alan | Tür | Gerekli mi? | Açıklama | Örnek Değer |
| :--- | :--- | :--- | :--- | :--- |
| `date` | `string` | Evet | Doğum tarihi (YYYY-MM-DD formatında) | `"1990-05-15"` |
| `time` | `string` | Evet | Doğum saati (HH:MM formatında, 24 saat) | `"10:30"` |
| `lat` | `float` | Evet | Enlem (Kuzey için pozitif, Güney için negatif) | `41.0082` |
| `lon` | `float` | Evet | Boylam (Doğu için pozitif, Batı için negatif) | `28.9784` |
| `house_system` | `string` | Hayır | Ev sistemi (Varsayılan: "P"). | `"W"` |
| `rulership_system`| `string` | Hayır | Yönetici sistemi (Varsayılan: "modern"). | `"traditional"` |

**Mevcut Ev Sistemleri:** `P` (Placidus), `K` (Koch), `R` (Regiomontanus), `C` (Campanus), `A` (Equal from ASC), `W` (Whole Sign), `O` (Porphyry), `B` (Alcabitius), `T` (Topocentric).

---

### 4. Pratik Kullanım Örnekleri

Aşağıda, farklı programlama dilleri için CosmicAPI'nin nasıl kullanılacağına dair pratik örnekler bulunmaktadır.

#### Örnek 1: JavaScript (Fetch API ile Web Sitesi İçin)

Bir web sitesinden tam harita verisini almak için bu kodu kullanabilirsiniz:

```javascript
const birthData = {
    date: "1990-05-15",
    time: "10:30",
    lat: 41.0082,
    lon: 28.9784
};

const apiKey = 'COSMIC_API_SECRET_KEY_12345';
const apiUrl = 'https://cosmicapiv1-1.onrender.com/v1/natal/full-chart';

fetch(apiUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey
    },
    body: JSON.stringify(birthData)
})
.then(response => {
    if (!response.ok) {
        // Hata durumunda, API'den gelen JSON mesajını da logla
        return response.json().then(err => Promise.reject(err));
    }
    return response.json();
})
.then(data => {
    console.log("Harita Verisi:", data);
    // Gelen 'data'yı web sitenizde gösterebilirsiniz.
    // Örneğin, Güneş'in burcunu göstermek için:
    // const sunSign = data.planets.find(p => p.planet === 'Sun').sign;
    // document.getElementById('sun-sign-element').innerText = `Güneş Burcu: ${sunSign}`;
})
.catch(error => {
    console.error('API isteğinde hata oluştu:', error);
});
```

#### Örnek 2: Python (Requests Kütüphanesi ile)

Bir Python script'inden veya başka bir backend servisinden Yükselen Raporu almak için:

```python
import requests
import json

api_url = "https://cosmicapiv1-1.onrender.com/v1/natal/report/ascendant"
api_key = "COSMIC_API_SECRET_KEY_12345"

birth_data = {
    "date": "1992-11-10",
    "time": "08:30",
    "lat": 41.0082,
    "lon": 28.9784
}

headers = {
    "Content-Type": "application/json",
    "X-API-Key": api_key
}

try:
    response = requests.post(api_url, headers=headers, data=json.dumps(birth_data))
    response.raise_for_status()  # Hata durumunda (4xx veya 5xx) exception fırlatır

    report_data = response.json()
    print("Yükselen Raporu:")
    print(f"Burç: {report_data.get('sign')}")
    print(f"Yorum: {report_data.get('interpretation')}")

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP Hatası: {http_err}")
    print(f"Hata Mesajı: {response.json()}")
except Exception as err:
    print(f"Bir hata oluştu: {err}")
```

#### Örnek 3: cURL (Terminalden Hızlı Test İçin)

Bir haritanın görselini (`.png`) doğrudan bir dosyaya kaydetmek için:

```bash
curl -X 'POST' \
  'https://cosmicapiv1-1.onrender.com/v1/natal/wheel-chart' \
  -H 'accept: image/png' \
  -H 'X-API-Key: COSMIC_API_SECRET_KEY_12345' \
  -H 'Content-Type: application/json' \
  -d '{ "date": "1988-03-20", "time": "06:00", "lat": 36.8969, "lon": 30.7133 }' \
  --output dogum_haritasi.png
```
Bu komut, bulunduğunuz klasörde `dogum_haritasi.png` adında bir resim dosyası oluşturacaktır.

---
## 🚀 API Endpoint'leri Hakkında Detaylı Bilgi
Tüm endpoint'lerin tam listesi, parametreleri ve döndürdükleri cevap yapıları için lütfen interaktif **Swagger UI dokümantasyonunu** ziyaret edin:

**[https://cosmicapiv1-1.onrender.com/docs](https://cosmicapiv1-1.onrender.com/docs)**

---

## ⚙️ Kurulum ve Başlatma (Yerel Geliştirme İçin)

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin.

### 1. Ön Gereksinimler

*   Python 3.8+
*   Docker (Redis için tavsiye edilir) veya yerel bir Redis kurulumu.

### 2. Kurulum Adımları

**a. Projeyi Klonlayın (veya İndirin):**
```bash
git clone https://github.com/kdrytmz27/cosmicapiv1.1.git
cd cosmicapiv1.1
```

**b. Sanal Ortam (Virtual Environment) Oluşturun ve Aktif Edin:**
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