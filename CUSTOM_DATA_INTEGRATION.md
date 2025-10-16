# Custom Data Integration - Kullanım Kılavuzu

## 📋 Genel Bakış

Sistem artık kullanıcıların kendi verilerini yüklemesine ve bu veriler üzerinde arama yapmasına olanak tanıyor. Yüklenen custom data:
- Tüm API endpoint'lerinde kullanılır (search, stats, create_report)
- Frontend'de görsel olarak belirtilir
- Session boyunca bellekte tutulur

---

## 🔄 Sistem Akışı

### 1. **Veri Yükleme** (`data_upload.html`)
```
Kullanıcı → CSV/Excel Seç → Önizleme → Upload
                                         ↓
                              Backend'e POST /api/upload_data
                                         ↓
                              custom_data_store'a kaydet
```

### 2. **Veri Seçimi** (`data_selection.html`)
```
Sayfa Yüklenince → /api/data_status çağır
                         ↓
          Custom data yüklü mü kontrol et
                         ↓
          Yüklüyse: "YÜKLÜ" badge göster
          Değilse: Default bilgileri göster
```

### 3. **İstatistik Gösterimi** (Header'da)
```
index.html & create_report.html yüklenince
                ↓
     /api/stats çağır
                ↓
Custom data yüklüyse:
  - Total Reports: Custom data row count
  - Badge: "📤 {fileName}"
Değilse:
  - Total Reports: 14,267 (default)
```

### 4. **Arama İşlemi**
```
Arama İsteği → /api/search
                    ↓
          custom_data_store dolu mu?
                    ↓
          EVET: Custom data'da ara
          HAYIR: Default hybrid search kullan
```

---

## 🔌 API Endpoint'leri

### 1. POST `/api/upload_data`
Yeni veri yükler.

**Request:**
```json
{
  "fileName": "test_data.csv",
  "data": [
    {
      "Summary": "Bug özeti",
      "Description": "Açıklama",
      "Priority": "High",
      ...
    }
  ],
  "columns": ["Summary", "Description", "Priority", ...]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Data uploaded successfully",
  "info": {
    "fileName": "test_data.csv",
    "rowCount": 5,
    "columns": [...],
    "uploadedAt": "2025-10-14T20:36:43.580976"
  }
}
```

---

### 2. GET `/api/data_status`
Mevcut veri durumunu döner.

**Response (Custom data yüklü):**
```json
{
  "success": true,
  "customDataLoaded": true,
  "fileName": "test_data.csv",
  "rowCount": 5,
  "columnCount": 5,
  "columns": ["Summary", "Description", "Priority", "Component", "Application"],
  "uploadedAt": "2025-10-14T20:36:43.580976"
}
```

**Response (Default data):**
```json
{
  "success": true,
  "customDataLoaded": false,
  "defaultData": {
    "fileName": "data_with_application.csv",
    "rowCount": 14267
  }
}
```

---

### 3. GET `/api/stats`
Sistem istatistiklerini döner.

**Response (Custom data yüklü):**
```json
{
  "success": true,
  "customDataLoaded": true,
  "fileName": "test_data.csv",
  "stats": {
    "total_reports": 5,
    "platforms": {...},
    "applications": {...}
  }
}
```

**Response (Default data):**
```json
{
  "success": true,
  "customDataLoaded": false,
  "stats": {
    "total_reports": 14272,
    "platforms": {
      "android": 8234,
      "ios": 5621,
      "unknown": 417
    },
    "applications": {...}
  }
}
```

---

### 4. POST `/api/search`
Benzer raporları arar.

**Davranış:**
- Custom data yüklüyse: `search_custom_data()` kullanılır (basit text similarity)
- Yoksa: `HybridSearch` sistemi kullanılır (FAISS + Cross-Encoder)

**Request:**
```json
{
  "query": "Fizy şarkı indirme",
  "application": null,
  "platform": null,
  "version": null,
  "top_k": 10
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "summary": "Fizy şarkı indirme sorunu",
      "description": "...",
      "final_score": 8.59,
      "cross_encoder_score": 8.59,
      "version_similarity": 1.0,
      "platform_match": true,
      ...
    }
  ],
  "count": 3,
  "search_time": 0.02
}
```

---

### 5. POST `/api/create_report`
Yeni rapor oluşturur.

**Davranış:**
- Custom data yüklüyse: `custom_data_store['data']`'ya append eder
- Yoksa: `data/data_with_application.csv`'ye append eder

---

## 🖥️ Frontend Entegrasyonu

### 1. `data_selection.html`
```javascript
async function checkForUploadedData() {
    const response = await fetch(`${API_BASE_URL}/data_status`);
    const data = await response.json();
    
    if (data.customDataLoaded) {
        // "Mevcut Veri Setini Kullan" seçeneğini güncelle
        // YÜKLÜ badge göster
        // Dosya adı ve detayları göster
    }
}
```

### 2. `index.html` & `create_report.html`
```javascript
async function loadStatistics() {
    const response = await fetch(`${API_BASE_URL}/stats`);
    const data = await response.json();
    
    // Total Reports'u güncelle
    document.getElementById('totalReports').textContent = 
        data.stats.total_reports.toLocaleString('tr-TR');
    
    // Custom data yüklüyse badge göster
    if (data.customDataLoaded) {
        // Header'a "📤 {fileName}" badge ekle
    }
}
```

### 3. `create_report.js`
```javascript
async function checkDataStatus() {
    const response = await fetch(`${API_BASE_URL}/data_status`);
    const data = await response.json();
    
    if (data.customDataLoaded) {
        // Custom data banner göster
        customDataBanner.style.display = 'block';
        customDataInfo.innerHTML = `...`;
    }
}
```

---

## 🧪 Test Senaryosu

### 1. Backend'i Başlat
```bash
cd bug-deduplication
source venv/bin/activate
python api_server.py
```

### 2. Frontend'i Başlat
```bash
cd web
python3 -m http.server 8000
```

### 3. Test Data Yükle
```bash
curl -X POST http://localhost:5001/api/upload_data \
  -H "Content-Type: application/json" \
  -d @- << 'JSON'
{
  "fileName": "test_data.csv",
  "data": [
    {
      "Summary": "BiP mesaj gönderilirken crash oluyor",
      "Description": "Test açıklaması",
      "Priority": "High",
      "Component": "Android Client",
      "Application": "BiP"
    }
  ],
  "columns": ["Summary", "Description", "Priority", "Component", "Application"]
}
JSON
```

### 4. Kontroller
```bash
# Data status kontrol
curl http://localhost:5001/api/data_status

# Stats kontrol
curl http://localhost:5001/api/stats

# Search test
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "BiP mesaj", "top_k": 3}'
```

### 5. Frontend Test
1. `http://localhost:8000/login.html` → Giriş yap
2. `data_selection.html` → "YÜKLÜ" badge'i görmeli
3. `index.html` → Header'da "5" ve "📤 test_data.csv" görmeli
4. `create_report.html` → Custom data banner görmeli

---

## 📊 Backend Veri Yapısı

```python
custom_data_store = {
    'data': pd.DataFrame,           # Pandas DataFrame
    'fileName': 'test_data.csv',    # Dosya adı
    'rowCount': 5,                   # Satır sayısı
    'columns': [...],                # Sütun isimleri
    'uploadedAt': '2025-10-14...',  # Yükleme zamanı
    'loaded': True                   # Yüklü mü?
}
```

---

## ✅ Tamamlanan Özellikler

- [x] Custom data upload API endpoint'i
- [x] Custom data store (global dictionary)
- [x] `/api/data_status` endpoint'i
- [x] `/api/stats` endpoint'inin custom data desteği
- [x] `/api/search` endpoint'inin custom data desteği
- [x] `/api/create_report` endpoint'inin custom data desteği
- [x] `data_selection.html` - Custom data görünürlüğü
- [x] `index.html` - Header stats güncelleme
- [x] `create_report.html` - Header stats güncelleme
- [x] `create_report.js` - Custom data banner

---

## 🔮 Gelecek Geliştirmeler (İsteğe Bağlı)

1. **Persistence**: Custom data'yı dosyaya kaydet (şu an sadece RAM'de)
2. **Multiple Datasets**: Birden fazla veri seti desteği
3. **Data Validation**: Yüklenen verinin format kontrolü
4. **Advanced Search**: Custom data için FAISS/Cross-Encoder entegrasyonu
5. **Export**: Custom data'yı CSV olarak dışa aktar

---

## 🐛 Bilinen Sınırlamalar

1. Custom data sadece session boyunca saklanır (server restart'ta silinir)
2. Custom data için basit text similarity kullanılır (FAISS/Cross-Encoder yok)
3. Tek bir custom data set desteklenir (birden fazla değil)
4. Maksimum dosya boyutu sınırı yok (büyük dosyalarda performans düşebilir)

---

## 📚 Daha Fazla Bilgi

- Backend API: `api_server.py`
- Search Logic: `search_custom_data()` fonksiyonu
- Frontend: `web/data_selection.html`, `web/app.js`, `web/create_report.js`
- Test Data: `test_data.csv`

