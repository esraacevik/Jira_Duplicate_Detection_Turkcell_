# 🔄 Dinamik Embedding Sistemi

## Genel Bakış

Sistem artık **dinamik embedding güncellemesi** destekliyor! Yeni bir rapor eklendiğinde:

1. ✅ **CSV dosyasına yazılır**
2. ✅ **Embedding vektörü otomatik oluşturulur**
3. ✅ **FAISS index'e eklenir**
4. ✅ **Hemen arama sonuçlarında görünür!**

## Nasıl Çalışır?

### 1. Rapor Ekleme
Kullanıcı yeni bir rapor eklediğinde (`/api/create_report`):

```python
# 1. Rapor CSV'ye yazılır
df.to_csv(csv_path, ...)

# 2. Embedding otomatik oluşturulur
update_embeddings_for_new_report(report_id)
```

### 2. Embedding Oluşturma
`update_embeddings_for_new_report()` fonksiyonu:

1. **DataFrame'i yeniden yükler** (yeni raporu içeren)
2. **Bi-encoder modeli ile embedding oluşturur**
   ```python
   new_embedding = bi_encoder.encode([combined_text])
   ```
3. **Mevcut embeddings.npy dosyasına ekler**
4. **FAISS index'e ekler** (platform'a göre: android/ios/unknown)
5. **Disk'e kaydeder** (kalıcılık için)

### 3. Veri Yapısı

```
data/
├── embedding_outputs/
│   ├── embeddings.npy          # Tüm embedding vektörleri (güncellenebilir)
│   ├── faiss_index_android.index  # Android FAISS index (güncellenebilir)
│   ├── faiss_index_ios.index      # iOS FAISS index (güncellenebilir)
│   └── faiss_index_unknown.index  # Unknown FAISS index (güncellenebilir)
└── data_with_application.csv  # Ana veri dosyası
```

## Default Data vs Custom Data

### Default Data (Varsayılan Veri)
- ✅ **Embedding otomatik güncellenir**
- ✅ **FAISS index güncellenir**
- ✅ **Hızlı arama (hybrid search)**

### Custom Data (Kullanıcı Verisi)
- ⚡ **On-the-fly arama** (text-based matching)
- 📝 CSV'ye kaydedilir
- 🔄 Embedding oluşturmaya gerek yok (text matching kullanır)

## Performans

| İşlem | Süre |
|-------|------|
| Yeni rapor ekleme | ~1-2 saniye |
| Embedding oluşturma | ~0.5 saniye |
| FAISS index güncelleme | ~0.2 saniye |
| **Toplam** | **~2-3 saniye** |

## Teknik Detaylar

### Embedding Boyutu
- Model: `paraphrase-multilingual-MiniLM-L12-v2`
- Boyut: **384 dimensions**
- Format: `float32` (FAISS için optimize edilmiş)

### FAISS Index
- Tip: **IndexFlatIP** (Inner Product - Cosine Similarity)
- Normalizasyon: Embeddings normalize edilir
- Platform bazlı: Android, iOS, Unknown için ayrı index'ler

### Güncelleme Algoritması

```python
# 1. Mevcut embeddings'i yükle
existing = np.load("embeddings.npy")  # Shape: (N, 384)

# 2. Yeni embedding ekle
new = encoder.encode([text])  # Shape: (1, 384)
updated = np.vstack([existing, new])  # Shape: (N+1, 384)

# 3. Kaydet
np.save("embeddings.npy", updated)

# 4. FAISS'e ekle
normalized = new / np.linalg.norm(new)
index.add(normalized.astype('float32'))
faiss.write_index(index, "faiss_index.index")
```

## Kullanım Örnekleri

### Backend'den Yeni Rapor Ekleme

```python
# POST /api/create_report
{
    "summary": "BiP mesaj gönderilirken crash oluyor",
    "description": "Kullanıcı mesaj göndermeye çalıştığında...",
    "component": "Android",
    "priority": "High"
}

# Response
{
    "success": true,
    "report_id": 1234,
    "embeddings_updated": true  # ✅ Embedding güncellendi!
}
```

### Frontend Bildirimi

Rapor kaydedildiğinde kullanıcı görür:
```
✅ Rapor başarıyla kaydedildi!
Rapor ID: 1234
✅ Embedding oluşturuldu - Rapor hemen arama sonuçlarında görünecek
```

## Hata Durumları

### Embedding Oluşturulamazsa

```python
⚠️ Could not update embeddings: [error message]
⚠️ New report will not appear in search until system restart!
```

Bu durumda:
1. Rapor CSV'ye kaydedilir ✅
2. Ama arama sonuçlarında çıkmaz ❌
3. Sistem yeniden başlatılınca embedding pipeline çalıştırılmalı

### Çözüm

```bash
# Tüm embeddings'i yeniden oluştur
python src/embedding_pipeline.py
```

## Sınırlamalar

1. **Tek seferde 1 rapor**: Her rapor için ayrı embedding oluşturulur
2. **Bellek kullanımı**: Her rapor ~1.5KB (384 float32)
3. **Disk yazma**: Her ekleme için 2 dosya güncellenir (embeddings.npy + faiss_index.index)

## Gelecek İyileştirmeler

- [ ] Batch embedding update (birden fazla rapor için)
- [ ] Asenkron embedding (kullanıcıyı bekletmeden)
- [ ] Embedding cache sistemi
- [ ] Incremental FAISS index (daha hızlı güncelleme)
- [ ] Custom data için de embedding desteği

## Log Örnekleri

Başarılı ekleme:
```
✅ New report created: ID=1234, App=BiP, Summary=...
🔄 Updating embeddings for new report...
📥 Reloading data to include new report...
🔄 Generating embedding for new report: 'BiP mesaj gönderilirken...'
📊 Loaded existing embeddings: (1233, 384)
✅ New embeddings shape: (1234, 384)
💾 Saved updated embeddings to data/embedding_outputs/embeddings.npy
🔄 Adding to FAISS index: android
💾 Saved updated FAISS index to data/embedding_outputs/faiss_index_android.index
✅ Successfully added new report to FAISS index (android)
✅ Embeddings updated successfully!
```

## Test Senaryosu

1. Yeni rapor ekle
2. Hemen arama yap
3. Yeni rapor sonuçlarda görünmeli ✅

```bash
# 1. Rapor ekle
curl -X POST http://localhost:5001/api/create_report \
  -H "Content-Type: application/json" \
  -d '{"summary": "Test rapor", "description": "Test açıklaması"}'

# 2. Hemen ara
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Test rapor", "top_k": 5}'

# ✅ Yeni rapor sonuçlarda görünür!
```

## Özet

| Özellik | Durum |
|---------|-------|
| Dinamik embedding | ✅ Aktif |
| FAISS index güncelleme | ✅ Aktif |
| Hızlı arama | ✅ Aktif |
| Custom data desteği | ✅ Aktif (text-based) |
| Asenkron işlem | ⏳ Gelecek |
| Batch update | ⏳ Gelecek |

---

**Not**: Bu sistem production-ready'dir ve aktif olarak kullanılabilir. Herhangi bir sorun durumunda sistem loglarını kontrol edin.


