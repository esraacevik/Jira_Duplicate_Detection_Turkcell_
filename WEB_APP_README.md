# 🌐 Bug Report Web Application

## 📋 Genel Bakış

Raporcuların bug raporu oluştururken **gerçek zamanlı** olarak benzer raporları görebilmelerini sağlayan modern web uygulaması.

### ✨ Özellikler

- 🔍 **Real-time Arama** - Yazdıkça benzer raporları bul
- ⚡ **Çok Hızlı** - FAISS + Cross-Encoder (2.5 saniye)
- 🎯 **Akıllı Filtreleme** - Uygulama, platform, sürüm bazlı
- 📊 **Detaylı Skorlama** - Her sonuç için similarity skorları
- 🎨 **Modern UI** - Responsive, kullanıcı dostu tasarım
- ⚠️ **Uyarı Sistemi** - Benzer rapor bulunduğunda uyarı

---

## 🏗️ Mimari

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│             │  HTTP   │             │  Python │             │
│  Frontend   │ ◄────► │  Flask API  │ ◄────► │   Hybrid    │
│ (HTML/CSS/  │  JSON   │   Server    │         │   Search    │
│    JS)      │         │             │         │   System    │
└─────────────┘         └─────────────┘         └─────────────┘
     │                        │                        │
     │                        │                        │
     ▼                        ▼                        ▼
web/index.html          api_server.py           hybrid_search.py
                                                       │
                                                       ▼
                                                  ┌─────────┐
                                                  │  FAISS  │
                                                  │ Indices │
                                                  └─────────┘
```

---

## 🚀 Hızlı Başlangıç

### 1. Flask Kurulumu

```bash
# Virtual environment aktif olmalı
source venv/bin/activate

# Flask ve dependencies'i yükle
pip install flask flask-cors
```

### 2. Backend Başlatma

#### Seçenek A: Script ile (Önerilen)
```bash
./start_web_app.sh
```

#### Seçenek B: Manuel
```bash
source venv/bin/activate
python api_server.py
```

Çıktı:
```
================================================================================
🚀 BUG REPORT DUPLICATE DETECTION API SERVER
================================================================================

Initializing...
🚀 Hybrid Search System - Başlatılıyor...
✅ Sistem hazır!

================================================================================
✅ SERVER READY!
================================================================================

📍 Endpoints:
   • http://localhost:5000/api/health     - Health check
   • http://localhost:5000/api/search     - Search similar reports (POST)
   • http://localhost:5000/api/stats      - Get system statistics
   • http://localhost:5000/api/applications - Get available applications

🌐 Frontend:
   • Open web/index.html in your browser
```

### 3. Frontend Açma

Tarayıcınızda şu dosyayı açın:
```
web/index.html
```

Veya basit HTTP server ile:
```bash
# Python 3
cd web
python -m http.server 8000

# Tarayıcıda aç: http://localhost:8000
```

---

## 📁 Dosya Yapısı

```
bug-deduplication/
├── 🌐 WEB APPLICATION
│   ├── api_server.py              # Flask API backend
│   ├── start_web_app.sh          # Başlatma scripti
│   └── web/
│       ├── index.html            # Ana sayfa
│       ├── style.css             # Stil dosyası
│       └── app.js                # Frontend logic
│
├── 🔍 SEARCH SYSTEM
│   ├── hybrid_search.py          # Hybrid search system
│   └── data/embedding_outputs/   # FAISS indices & embeddings
│
└── 📚 DOCUMENTATION
    └── WEB_APP_README.md         # Bu dosya
```

---

## 🎯 Kullanım

### Rapor Oluşturma İş Akışı

1. **Rapor Özeti Girin**
   - Minimum 10 karakter
   - Otomatik arama başlar (500ms debounce)

2. **Filtreleri Seçin** (Opsiyonel)
   - Uygulama: BiP, TV+, Fizy, vb.
   - Platform: Android, iOS
   - Sürüm: Örn. 3.70.19

3. **Benzer Raporları Görün**
   - Gerçek zamanlı sonuçlar
   - Similarity skorları
   - Detaylı metadata

4. **Karar Verin**
   - ✅ Benzer rapor yok → Yeni rapor oluştur
   - ⚠️ Benzer rapor var → Mevcut rapora ek bilgi ekle

---

## 🔌 API Endpoints

### 1. Health Check
```http
GET /api/health
```

**Response:**
```json
{
    "status": "healthy",
    "message": "Bug Report API is running",
    "version": "1.0.0"
}
```

---

### 2. Search Similar Reports
```http
POST /api/search
Content-Type: application/json
```

**Request Body:**
```json
{
    "query": "mesaj gönderilirken uygulama çöküyor",
    "application": "BiP",
    "platform": "android",
    "version": "3.70.19",
    "language": null,
    "top_k": 10
}
```

**Response:**
```json
{
    "success": true,
    "query": "mesaj gönderilirken uygulama çöküyor",
    "filters": {
        "application": "BiP",
        "platform": "android",
        "version": "3.70.19",
        "language": null
    },
    "results": [
        {
            "index": 1234,
            "summary": "BiP mesaj gönderilirken crash",
            "description": "...",
            "application": "BiP",
            "platform": "android",
            "app_version": "3.70.19",
            "priority": "high",
            "cross_encoder_score": 5.2145,
            "version_similarity": 1.0,
            "platform_similarity": 1.0,
            "language_similarity": 0.0,
            "final_score": 5.9204
        }
    ],
    "count": 1,
    "search_time": 0.93
}
```

---

### 3. Get Statistics
```http
GET /api/stats
```

**Response:**
```json
{
    "success": true,
    "stats": {
        "total_reports": 14267,
        "platforms": {
            "android": 5726,
            "ios": 5096,
            "unknown": 3445
        },
        "applications": {
            "BiP": 5515,
            "TV+": 3245,
            "Fizy": 2134,
            ...
        }
    }
}
```

---

### 4. Get Applications
```http
GET /api/applications
```

**Response:**
```json
{
    "success": true,
    "applications": [
        "BiP",
        "Dergilik",
        "Fizy",
        "Hesabım",
        "LifeBox",
        "Paycell",
        "TV+",
        "Unknown"
    ]
}
```

---

## 🎨 Frontend Özellikleri

### Real-time Arama
```javascript
// 500ms debounce ile otomatik arama
summaryInput.addEventListener('input', () => {
    if (text.length >= 10) {
        setTimeout(() => performSearch(), 500);
    }
});
```

### Similarity Skorları
- **✅ Excellent (>4.0)** - Neredeyse kesin eşleşme
- **👍 Very Good (>3.0)** - Çok iyi eşleşme
- **🔍 Good (>2.0)** - İyi eşleşme
- **⚠️ Moderate (>1.0)** - Orta eşleşme
- **❓ Weak (<1.0)** - Zayıf eşleşme

### Responsive Design
- Desktop, tablet, mobile uyumlu
- Modern gradient arka plan
- Smooth animasyonlar
- Card-based layout

---

## 🛠️ Geliştirme

### Mock Data ile Test

Backend olmadan test için `app.js` mock data kullanır:
```javascript
// Backend'e ulaşılamazsa otomatik mock data gösterir
catch (error) {
    displayMockResults();
}
```

### Debug Mode

`api_server.py` içinde:
```python
app.run(
    host='0.0.0.0',
    port=5000,
    debug=True  # Development için True yap
)
```

### CORS Ayarları

Farklı origin'den erişim için `api_server.py`:
```python
from flask_cors import CORS
CORS(app)  # Tüm origin'lere izin ver
```

---

## 📊 Performans

### Backend
- **FAISS Stage**: ~0.5 saniye
- **Cross-Encoder Stage**: ~2 saniye
- **Toplam**: ~2.5 saniye

### Frontend
- **İlk yükleme**: <1 saniye
- **Real-time arama**: 500ms debounce
- **UI rendering**: <100ms

---

## 🔒 Güvenlik

### Öneriler (Production için)

1. **Rate Limiting** ekle:
```python
from flask_limiter import Limiter

limiter = Limiter(app, default_limits=["100 per minute"])
```

2. **API Key** kullan:
```python
@app.before_request
def check_api_key():
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != VALID_API_KEY:
        abort(401)
```

3. **HTTPS** kullan (production)

4. **Input validation** güçlendir

---

## 🐛 Sorun Giderme

### Problem: Backend başlamıyor

**Çözüm:**
```bash
# Flask kurulu mu kontrol et
pip list | grep -i flask

# Yükle
pip install flask flask-cors

# Port kullanımda mı kontrol et
lsof -i :5000

# Başka port kullan
python api_server.py --port 5001
```

### Problem: Frontend backend'e bağlanamıyor

**Çözüm 1:** CORS hatası
```javascript
// app.js içinde URL'yi kontrol et
const API_BASE_URL = 'http://localhost:5000/api';
```

**Çözüm 2:** Backend çalışıyor mu?
```bash
curl http://localhost:5000/api/health
```

### Problem: Arama çok yavaş

**Çözüm:**
```python
# hybrid_search.py içinde n_candidates azalt
search = HybridSearch(n_candidates=100)  # Varsayılan: 200
```

---

## 📈 İyileştirme Önerileri

### Kısa Vadeli
- [ ] Toast notification sistemi ekle
- [ ] Loading progress bar
- [ ] Arama geçmişi (localStorage)
- [ ] Export results (JSON/CSV)

### Orta Vadeli
- [ ] User authentication
- [ ] Report submission form
- [ ] Admin dashboard
- [ ] Analytics & metrics

### Uzun Vadeli
- [ ] Real-time collaboration
- [ ] Machine learning feedback loop
- [ ] Integration with JIRA API
- [ ] Multi-language support

---

## 🎓 Öğreticiler

### Test Senaryoları

**Senaryo 1: BiP Android Crash**
```
Summary: mesaj gönderilirken uygulama çöküyor
Application: BiP
Platform: android
Version: 3.70.19

Beklenen: 5+ benzer rapor bulunacak
```

**Senaryo 2: iOS Bildirim Sorunu**
```
Summary: bildirim gelmiyor
Application: BiP
Platform: ios
Version: (boş)

Beklenen: Bildirim ile ilgili raporlar listelenecek
```

**Senaryo 3: Yeni Sorun**
```
Summary: uygulama mor renkli açılıyor
Application: Fizy
Platform: android

Beklenen: Benzer rapor bulunamayacak (yeni sorun)
```

---

## 🤝 Katkıda Bulunma

Web arayüzü ile ilgili önerileriniz için:
1. Issue açın
2. Pull request gönderin
3. Feedback verin

---

## 📞 İletişim

- **Backend**: `api_server.py`
- **Frontend**: `web/` klasörü
- **Search System**: `hybrid_search.py`

---

## 🎉 Sonuç

Web uygulaması sayesinde raporcular:
- ✅ Duplicate raporları önleyebilir
- ✅ Daha kaliteli raporlar oluşturabilir
- ✅ Zamandan tasarruf edebilir
- ✅ Ekip verimliliğini artırabilir

**Sistem şu an kullanıma hazır!** 🚀

---

*Son güncelleme: Ekim 2025*

