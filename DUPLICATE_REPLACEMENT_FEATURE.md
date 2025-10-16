# 🔄 Duplicate Rapor Değiştirme Özelliği

## Genel Bakış

Bu özellik, kullanıcıların yeni bir rapor oluştururken sistemde bulunan benzer (duplicate) raporları tespit edip, eski raporu silip yeni raporu bunun yerine kaydetmesini sağlar.

## 🎯 Kullanım Senaryosu

```
Kullanıcı: Yeni bug raporu oluşturuyor
  ↓
Sistem: Otomatik benzer raporlar arıyor
  ↓
Kullanıcı: "Bu rapor zaten var!" diyor
  ↓
Sistem: "Eski raporu sil, yenisini kaydet mi?" diye soruyor
  ↓
Kullanıcı: Onaylıyor
  ↓
Sistem: Eski rapor siliniyor, yeni rapor kaydediliyor
  ↓
Sonuç: Veri temiz, duplicate yok! ✅
```

## 📋 Özellikler

### Frontend (create_report.js)

1. **Her Benzer Rapor Kartında Buton:**
   - 🔄 "Bu Raporu Değiştir" butonu
   - Turuncu gradient tasarım
   - "Eski rapor silinecek" uyarısı

2. **Onay Dialogu:**
   ```
   🔄 Duplicate Rapor Değiştirme
   
   Bu işlem:
   1. Eski raporu datadan silecek
   2. Yeni raporu bunun yerine kaydedecek
   
   Bu işlem geri alınamaz!
   
   Devam etmek istiyor musunuz?
   ```

3. **Görsel Feedback:**
   - Seçilen kart turuncu border ile işaretlenir
   - Diğer kartlar %50 opacity olur
   - Uyarı mesajı gösterilir
   - Form başına scroll yapılır

4. **Başarı Mesajı:**
   ```
   🔄 Duplicate rapor başarıyla değiştirildi!
   
   Eski rapor silindi ve yeni rapor kaydedildi.
   Rapor ID: #1234
   ```

### Backend (api_server.py)

1. **Yeni Parametreler:**
   - `replace_report`: boolean - Değiştirme modu aktif mi?
   - `old_report_summary`: string - Silinecek raporun özeti
   - `old_report_id`: string - Silinecek raporun ID'si

2. **Silme Mantığı:**
   ```python
   # Custom Data için
   if replace_report and old_report_summary:
       mask = custom_data_store['data'].apply(
           lambda row: old_report_summary.lower() in str(row.get('Summary')).lower(), 
           axis=1
       )
       custom_data_store['data'] = custom_data_store['data'][~mask]
   
   # Default Data için
   if replace_report and old_report_summary:
       mask = df['Summary'].str.lower().str.contains(old_report_summary.lower(), na=False)
       df = df[~mask]
   ```

3. **Loglar:**
   ```
   🔄 Replacing old report: BiP mesaj gönderilirken crash...
   🗑️  Deleted 1 old report(s)
   ✅ Report added to custom data and saved to data/user_data/test.csv
   ```

## 🛠️ Teknik Detaylar

### JavaScript Global State

```javascript
let reportToReplace = null;  // { index, summary, reportId }
```

### API Request Format

```json
{
  "summary": "BiP uygulaması çöküyor mesaj gönderirken",
  "description": "...",
  "component": "Android",
  "app_version": "3.70.19",
  "replace_report": true,
  "old_report_summary": "BiP mesaj gönderilirken crash oluyor",
  "old_report_id": "1234"
}
```

### API Response Format

```json
{
  "success": true,
  "message": "Report created successfully",
  "report_id": 1235,
  "application": "BiP"
}
```

## 📊 Veri Akışı

```
1. Kullanıcı Summary girer
   ↓
2. Real-time benzer rapor arama (debounced)
   ↓
3. API: POST /api/search
   Response: { results: [...] }
   ↓
4. Her kartta "Bu Raporu Değiştir" butonu
   ↓
5. Kullanıcı butona tıklar
   ↓
6. replaceReport(index, summary, reportId) çağrılır
   ↓
7. Onay dialogu gösterilir
   ↓
8. Kullanıcı onaylar
   ↓
9. reportToReplace = { index, summary, reportId } set edilir
   ↓
10. Görsel işaretleme yapılır
   ↓
11. Kullanıcı "Raporu Kaydet" butonuna tıklar
   ↓
12. handleFormSubmit() çağrılır
   ↓
13. formData.replace_report = true eklenir
   ↓
14. API: POST /api/create_report
   Body: { ...formData, replace_report: true, ... }
   ↓
15. Backend eski raporu siler
   ↓
16. Backend yeni raporu ekler
   ↓
17. CSV dosyası güncellenir
   ↓
18. Response: { success: true, report_id: ... }
   ↓
19. Frontend başarı mesajı gösterir
   ↓
20. reportToReplace = null (state sıfırlanır)
```

## 🎨 UI/UX Detayları

### Benzer Rapor Kartı

```html
<div class="result-card">
  <div class="result-header">
    <span class="result-rank">#1</span>
    <span class="match-badge excellent">✅ Mükemmel Eşleşme</span>
    <span class="result-score">Score: 5.2145</span>
  </div>
  
  <h3 class="result-title">BiP mesaj gönderilirken crash oluyor</h3>
  <p class="result-description">Mesaj gönderme sırasında...</p>
  
  <div class="result-meta">
    <span class="meta-tag">📱 BiP</span>
    <span class="meta-tag">💻 android</span>
    <span class="meta-tag">🔢 3.70.18</span>
    <span class="meta-tag">⚡ high</span>
  </div>
  
  <div class="result-scores">
    <div class="score-item">
      <span class="score-label">Cross-Encoder:</span>
      <span class="score-value">5.2145</span>
    </div>
    <div class="score-item">
      <span class="score-label">Version:</span>
      <span class="score-value">1.0000</span>
    </div>
    <div class="score-item">
      <span class="score-label">Platform:</span>
      <span class="score-value">✓</span>
    </div>
  </div>
  
  <!-- YENİ: Değiştirme Butonu -->
  <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--gray-200);">
    <button 
      onclick="replaceReport(0, 'BiP mesaj...', '1234')"
      class="btn btn-secondary" 
      style="background: linear-gradient(135deg, #FF9500 0%, #FF6B00 100%); color: white;"
    >
      <span>🔄</span>
      <span>Bu Raporu Değiştir</span>
    </button>
    <span style="font-size: 0.75rem; color: var(--gray-500);">
      (Eski rapor silinecek)
    </span>
  </div>
</div>
```

### Seçili Kart Görseli

```css
/* Seçilen kart */
.result-card.selected {
  border: 3px solid #FF9500;
  background: linear-gradient(135deg, #FFF9E6 0%, #FFEDD5 100%);
}

/* Diğer kartlar */
.result-card.not-selected {
  opacity: 0.5;
}
```

### Uyarı Mesajı

```html
<div id="replaceMessage" style="
  background: linear-gradient(135deg, #FF9500 0%, #FF6B00 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin: 16px 0;
  text-align: center;
  font-weight: 600;
  animation: pulse 2s infinite;
">
  <span style="font-size: 1.2rem;">🔄</span>
  <span>Seçilen rapor değiştirilecek! "Raporu Kaydet" butonuna tıklayın.</span>
</div>
```

## 🧪 Test Senaryoları

### Senaryo 1: Başarılı Değiştirme

1. Yeni rapor oluştur: "BiP çöküyor mesaj gönderirken"
2. Benzer rapor bulundu: "BiP mesaj gönderilirken crash" (Score: 5.4)
3. "Bu Raporu Değiştir" butonuna tıkla
4. Onay dialogunda "Tamam" seç
5. "Raporu Kaydet" butonuna tıkla
6. ✅ Başarı: "Duplicate rapor başarıyla değiştirildi!"
7. CSV'yi kontrol et: Eski rapor silinmiş, yeni rapor eklenmiş

### Senaryo 2: İptal Etme

1. Yeni rapor oluştur
2. Benzer rapor bulundu
3. "Bu Raporu Değiştir" butonuna tıkla
4. Onay dialogunda "İptal" seç
5. ✅ Hiçbir şey olmadı, normal kayıt devam ediyor

### Senaryo 3: Değiştirme Sonrası İptal

1. Yeni rapor oluştur
2. Benzer rapor bulundu
3. "Bu Raporu Değiştir" butonuna tıkla
4. Onay dialogunda "Tamam" seç
5. Kartlar işaretlendi
6. "İptal" butonuna tıkla (formu iptal et)
7. ✅ Sayfadan çık, hiçbir şey silinmedi

### Senaryo 4: Custom Data ile Değiştirme

1. Kullanıcı veri yükledi (test_turkce_veri.csv)
2. Yeni rapor oluştur
3. Benzer rapor bulundu (custom data'dan)
4. "Bu Raporu Değiştir" butonuna tıkla
5. "Raporu Kaydet"
6. ✅ Custom CSV güncellenmiş olmalı

## ⚠️ Dikkat Edilmesi Gerekenler

1. **Geri Alınamaz:** Silme işlemi kalıcıdır
2. **CSV Backup:** Kritik veriler için backup alınmalı
3. **Similarity Threshold:** Düşük score'larda kullanıcı uyarılmalı
4. **Multiple Match:** Birden fazla eski rapor silinebilir (summary match)
5. **Encoding:** UTF-8 desteği şart (Türkçe karakterler)

## 🚀 Gelecek Geliştirmeler

- [ ] Silme işlemi öncesi preview
- [ ] Undo/Redo özelliği
- [ ] Deleted reports log
- [ ] Email bildirimi
- [ ] Admin approval
- [ ] Merge reports (iki raporu birleştir)
- [ ] Similarity threshold ayarı
- [ ] Bulk replacement (çoklu silme)

## 📝 Değiştirilen Dosyalar

```
web/create_report.js    (+80 satır)
  - replaceReport() fonksiyonu eklendi
  - handleFormSubmit() güncellendi
  - displaySimilarReports() güncellendi
  
api_server.py           (+30 satır)
  - create_report() endpoint'i güncellendi
  - Replace parametreleri eklendi
  - Silme mantığı eklendi (custom + default data)

web/create_report.html  (cache-busting)
  - Script version: v=111 → v=120
```

## 📚 İlgili Dökümanlar

- `WEB_APP_README.md` - Genel web app dökümantasyonu
- `CREATE_REPORT_README.md` - Rapor oluşturma özelliği
- `REAL_TIME_SEARCH_FEATURE.md` - Real-time arama dökümantasyonu
- `CUSTOM_DATA_INTEGRATION.md` - Custom data entegrasyonu

---

**Geliştirme Tarihi:** 16 Ekim 2024  
**Versiyon:** 1.0  
**Durum:** ✅ Tamamlandı ve test edildi

