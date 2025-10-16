# Sütun Seçimi Özelliği - Kullanım Kılavuzu

## 📋 Genel Bakış

Kullanıcılar kendi verilerini yüklediklerinde, **hangi sütunların arama için kullanılacağını** seçebilirler. Bu özellik, arama kalitesini artırmak ve ilgisiz sütunları filtrelemek için kullanılır.

---

## 🔄 Sistem Akışı

### 1. Veri Yükleme
```
Kullanıcı → CSV/Excel Yükle → Backend'e POST /api/upload_data
                                         ↓
                           custom_data_store['data'] = DataFrame
                           custom_data_store['columns'] = [...]
```

### 2. Sütun Seçimi
```
column_mapping.html → Sütunları Listele
                              ↓
                  Kullanıcı 1-5 sütun seçer
                              ↓
                  saveConfiguration() → POST /api/update_selected_columns
                              ↓
                  custom_data_store['selectedColumns'] = [...]
```

### 3. Arama İşlemi
```
Arama İsteği → /api/search
                    ↓
       custom_data_store['selectedColumns'] var mı?
                    ↓
       EVET: Sadece seçilen sütunlarda ara
       HAYIR: Auto-detect (summary, description, vb.)
```

---

## 🎯 Öncelik Sırası

`search_custom_data()` fonksiyonu 3 öncelik seviyesi kullanır:

### Öncelik 1: Kullanıcı Seçimi (En Yüksek)
```python
if selected_columns and len(selected_columns) > 0:
    text_columns = selected_columns
    # Örn: ["Summary", "Description"]
```

### Öncelik 2: Otomatik Algılama
```python
for col in df.columns:
    if 'summary' in col.lower() or 'description' in col.lower():
        text_columns.append(col)
# Örn: ["Summary", "Description", "Özet"]
```

### Öncelik 3: Fallback (Tüm String Sütunları)
```python
text_columns = df.select_dtypes(include=['object']).columns.tolist()[:2]
# İlk 2 string sütun
```

---

## 🔌 API Endpoint'leri

### 1. POST `/api/update_selected_columns`
Seçilen sütunları günceller.

**Request:**
```json
{
  "selectedColumns": ["Summary", "Description"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Selected columns updated",
  "selectedColumns": ["Summary", "Description"]
}
```

**cURL Örneği:**
```bash
curl -X POST http://localhost:5001/api/update_selected_columns \
  -H "Content-Type: application/json" \
  -d '{"selectedColumns": ["Summary", "Description"]}'
```

---

### 2. GET `/api/data_status`
Yüklü veri durumu ve seçilen sütunları döner.

**Response:**
```json
{
  "success": true,
  "customDataLoaded": true,
  "fileName": "test_data.csv",
  "rowCount": 5,
  "columnCount": 5,
  "columns": ["Summary", "Description", "Priority", "Component", "Application"],
  "selectedColumns": ["Summary", "Description"],
  "uploadedAt": "2025-10-14T20:36:43.580976"
}
```

---

## 🖥️ Frontend Kullanımı

### `column_mapping.html` - Sütun Seçimi

```javascript
// Kullanıcı sütun seçiyor
selectedColumns = ["Summary", "Description"];

// Kaydet butonuna basınca
async function saveConfiguration() {
    // localStorage'a kaydet
    localStorage.setItem('systemConfig', JSON.stringify({
        selectedColumns: selectedColumns,
        ...
    }));
    
    // Backend'e gönder (custom data varsa)
    if (dataSelection === 'new' && uploadedDataInfo) {
        await fetch('http://localhost:5001/api/update_selected_columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                selectedColumns: selectedColumns
            })
        });
    }
    
    // create_report.html'e yönlendir
    window.location.href = 'create_report.html';
}
```

---

## 🧪 Test Senaryoları

### Senaryo 1: Summary + Description
```bash
# 1. Sütunları seç
curl -X POST http://localhost:5001/api/update_selected_columns \
  -H "Content-Type: application/json" \
  -d '{"selectedColumns": ["Summary", "Description"]}'

# 2. Ara
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Fizy şarkı indirme", "top_k": 3}'

# Sonuç: En iyi eşleşme score: 10.04
```

### Senaryo 2: Sadece Summary
```bash
# 1. Sütunları seç
curl -X POST http://localhost:5001/api/update_selected_columns \
  -H "Content-Type: application/json" \
  -d '{"selectedColumns": ["Summary"]}'

# 2. Ara
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "BiP mesaj gönderilirken", "top_k": 2}'

# Sonuç: En iyi eşleşme score: 13.80
```

---

## 📊 Backend Veri Yapısı

```python
custom_data_store = {
    'data': pd.DataFrame,              # Yüklenen veri
    'fileName': 'test_data.csv',       # Dosya adı
    'rowCount': 5,                      # Satır sayısı
    'columns': [                        # TÜM sütunlar
        'Summary', 
        'Description', 
        'Priority', 
        'Component', 
        'Application'
    ],
    'selectedColumns': [                # SEÇILEN sütunlar (arama için)
        'Summary', 
        'Description'
    ],
    'uploadedAt': '2025-10-14...',     # Yükleme zamanı
    'loaded': True                      # Yüklü mü?
}
```

---

## 🎨 Frontend UI

### Sütun Listesi
```html
<div class="column-row">
    <div>
        <div class="column-label">
            Summary
            <span class="badge-recommended">ÖNERİLEN</span>
        </div>
        <div class="description">Bug özeti (kısa açıklama)</div>
    </div>
    <div class="column-preview">BiP mesaj gönderilirken crash...</div>
    <input type="checkbox" checked onchange="toggleColumn('Summary')">
</div>
```

### Seçilen Sütunlar Önizleme
```html
<div class="selected-columns">
    <span class="column-badge">Summary</span>
    <span class="column-badge">Description</span>
</div>
```

---

## 🔍 Arama Mantığı

### `search_custom_data()` Fonksiyonu

```python
def search_custom_data(query, df, top_k=10, selected_columns=None):
    # 1. Hangi sütunları kullanacağını belirle
    text_columns = []
    
    if selected_columns and len(selected_columns) > 0:
        # Kullanıcı seçimini kullan (ÖNCELİK 1)
        text_columns = [col for col in selected_columns if col in df.columns]
        logger.info(f"🎯 Using user-selected columns: {text_columns}")
    elif auto_detect_text_columns(df):
        # Otomatik algıla (ÖNCELİK 2)
        text_columns = auto_detect_text_columns(df)
        logger.info(f"🔍 Auto-detected: {text_columns}")
    else:
        # Fallback (ÖNCELİK 3)
        text_columns = df.select_dtypes(include=['object']).columns[:2]
        logger.info(f"⚠️ Using fallback: {text_columns}")
    
    # 2. Her satır için similarity hesapla
    for idx, row in df.iterrows():
        combined_text = ' '.join([str(row[col]) for col in text_columns])
        score = calculate_similarity(query, combined_text)
        ...
    
    # 3. Sonuçları sırala ve döndür
    return sorted(results, key=lambda x: x['final_score'], reverse=True)[:top_k]
```

---

## 📈 Performans Etkisi

### Sütun Sayısı ve Arama Hızı

| Seçilen Sütun Sayısı | Arama Süresi | Doğruluk |
|---------------------|-------------|----------|
| 1 (Summary)         | ~0.00s      | Orta     |
| 2 (Summary + Desc)  | ~0.01s      | Yüksek   |
| 3+ sütun            | ~0.02s      | Değişken |
| 5 sütun (max)       | ~0.03s      | Düşük    |

**Öneri:** En iyi performans için **2-3 sütun** seçin (örn: Summary, Description)

---

## ✅ Yapılan Değişiklikler

### Backend (`api_server.py`)
- [x] `custom_data_store['selectedColumns']` alanı eklendi
- [x] `search_custom_data()` fonksiyonu `selected_columns` parametresi aldı
- [x] Öncelik sistemi eklendi (User > Auto-detect > Fallback)
- [x] `POST /api/update_selected_columns` endpoint'i eklendi
- [x] `/api/data_status` endpoint'i `selectedColumns` döndürüyor

### Frontend (`column_mapping.html`)
- [x] `saveConfiguration()` async yapıldı
- [x] Custom data varsa seçilen sütunları backend'e POST ediyor
- [x] Kullanıcıya başarı/hata mesajı gösteriliyor

---

## 🐛 Hata Ayıklama

### Log Kontrolü
```bash
# Backend log'unda seçilen sütunları görmek için
tail -f server.log | grep "Using user-selected"

# Örnek çıktı:
# 2025-10-14 20:53:40 - INFO - 🎯 Using user-selected columns: ['Summary', 'Description']
```

### Test Komutu
```bash
# 1. Data status kontrol
curl http://localhost:5001/api/data_status | jq '.selectedColumns'

# 2. Sütunları güncelle
curl -X POST http://localhost:5001/api/update_selected_columns \
  -H "Content-Type: application/json" \
  -d '{"selectedColumns": ["Summary"]}'

# 3. Arama yap ve log kontrol
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query test", "top_k": 3}'
```

---

## 🔮 Gelecek Geliştirmeler

1. **Ağırlıklandırma**: Her sütuna farklı ağırlık vermek
   ```json
   {
     "selectedColumns": [
       {"name": "Summary", "weight": 2.0},
       {"name": "Description", "weight": 1.0}
     ]
   }
   ```

2. **Sütun Önizleme**: Sütun seçiminde ilk 3 satırı göstermek

3. **Otomatik Öneri**: ML ile en iyi sütun kombinasyonunu önermek

4. **Sütun İstatistikleri**: Her sütunun unique value count, null count göstermek

---

## 📚 İlgili Dosyalar

- **Backend**: `api_server.py` → `search_custom_data()`, `update_selected_columns()`
- **Frontend**: `web/column_mapping.html` → Sütun seçimi UI
- **Dokümantasyon**: `CUSTOM_DATA_INTEGRATION.md` → Genel veri yükleme
- **Test**: `test_data.csv` → Test verisi

---

## 💡 Kullanım İpuçları

1. **Summary + Description** sütunlarını seçmek genellikle en iyi sonucu verir
2. Çok fazla sütun seçmek aramayı yavaşlatabilir ve doğruluğu düşürebilir
3. Maksimum 5 sütun seçebilirsiniz (UI kısıtlaması)
4. Seçilen sütunlar localStorage'da ve backend'de saklanır
5. Yeni veri yüklendiğinde sütun seçimini tekrar yapmanız gerekir

