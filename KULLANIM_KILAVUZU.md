# 📖 Bug Report System - Kullanım Kılavuzu

**Tarih**: 12 Ekim 2025  
**Sistem**: Duplicate Detection with User Login & Configuration

---

## 🎯 Sistem Özellikleri

✅ **Kullanıcı Girişi** - Güvenli authentication sistemi  
✅ **Veri Seçimi** - Mevcut veri veya yeni veri yükleme  
✅ **Sütun Konfigürasyonu** - Cross-encoder için sütun seçimi  
✅ **Benzer Rapor Arama** - Hybrid FAISS + Cross-Encoder  
✅ **Rapor Oluşturma** - Otomatik duplicate kontrolü  
✅ **Session Yönetimi** - LocalStorage tabanlı  

---

## 🚀 Hızlı Başlangıç (5 Dakika)

### Adım 1: Tarayıcıyı Açın

```
http://localhost:8000/login.html
```

### Adım 2: Giriş Yapın

```
📧 Kullanıcı: admin@turkcell.com.tr
🔑 Şifre: admin123
```

### Adım 3: Mevcut Veri Setini Seçin

- "📁 Mevcut Veri Setini Kullan" seçeneğine tıklayın
- "➡️ Devam Et" butonuna tıklayın

### Adım 4: Sütunları Onaylayın

- Summary ve Description otomatik seçili (önerilen)
- "💾 Kaydet ve Sistemi Başlat" butonuna tıklayın

### Adım 5: Sistem Hazır!

Artık benzer raporları arayabilir ve yeni rapor oluşturabilirsiniz! 🎉

---

## 📋 Detaylı Kullanım Adımları

### 🔐 1. Login Sayfası (`login.html`)

#### Görünüm:
```
┌─────────────────────────────────┐
│          🔐                     │
│     Sistem Girişi               │
│  Bug Report Duplicate Detection │
│                                 │
│  Kullanıcı Adı *                │
│  [________________________]     │
│                                 │
│  Şifre *                        │
│  [••••••••••••••••••••••]       │
│                                 │
│  [🚀 Giriş Yap]                 │
│                                 │
│  💡 Demo Giriş:                 │
│  Kullanıcı: admin@turkcell...   │
│  Şifre: admin123                │
└─────────────────────────────────┘
```

#### Demo Kullanıcılar:

| Kullanıcı | Şifre | Rol | Açıklama |
|-----------|-------|-----|----------|
| `admin@turkcell.com.tr` | `admin123` | Admin | Tam yetki |
| `user@turkcell.com.tr` | `user123` | User | Standart kullanıcı |

#### İşlemler:
1. Kullanıcı adı ve şifre girin
2. "🚀 Giriş Yap" butonuna tıklayın
3. Başarılı girişte → `data_selection.html` yönlendirilir
4. Hatalı girişte → Hata mesajı gösterilir

---

### 📊 2. Data Selection Sayfası (`data_selection.html`)

#### Görünüm:
```
┌──────────────────────────────────────────────┐
│ Hoş Geldiniz, Admin User! 👋     [🚪 Çıkış] │
├──────────────────────────────────────────────┤
│ 📊 Hangi veri seti ile çalışmak istersiniz? │
│                                              │
│ ┌──────────────────────────────────────┐    │
│ │ 📁 Mevcut Veri Setini Kullan         │    │
│ │                                      │    │
│ │ data_with_application.csv            │    │
│ │ ✓ 14,268 bug raporu                  │    │
│ │ ✓ Embeddings ve FAISS hazır          │    │
│ │ ✓ Hızlı başlangıç                    │    │
│ │ ✓ BiP, TV+, Fizy, vb.                │    │
│ └──────────────────────────────────────┘    │
│                                              │
│ ┌──────────────────────────────────────┐    │
│ │ 📤 Yeni Veri Seti Yükle              │    │
│ │                                      │    │
│ │ Kendi CSV dosyanızı yükleyin         │    │
│ │ ✓ CSV/Excel yükleme                  │    │
│ │ ✓ Sütun mapping                      │    │
│ │ ✓ Cross-encoder seçimi               │    │
│ │ ✓ Otomatik embedding                 │    │
│ └──────────────────────────────────────┘    │
│                                              │
│         [➡️ Devam Et]                        │
└──────────────────────────────────────────────┘
```

#### Seçenekler:

**Seçenek 1: 📁 Mevcut Veri Setini Kullan**
- Sistemde yüklü `data_with_application.csv` kullanılır
- 14,268 adet bug raporu
- Embeddings ve FAISS index hazır
- ✅ **Önerilen** (hızlı başlangıç için)

**Seçenek 2: 📤 Yeni Veri Seti Yükle**
- Kendi CSV dosyanızı yükleyin
- Sütun eşleştirmesi gerekir
- Embedding oluşturma (zaman alır)
- Büyük veri setleri için uygun

#### İşlemler:
1. Bir seçenek seçin (tıklayarak)
2. Seçilen kutu sarı renkte vurgulanır
3. "➡️ Devam Et" aktif olur
4. Devam Et → `column_mapping.html` yönlendirilir

---

### 🎯 3. Column Mapping Sayfası (`column_mapping.html`)

#### Görünüm:
```
┌───────────────────────────────────────────────┐
│ 🎯 Sütun Eşleştirme ve Konfigürasyon  [← Geri]│
├───────────────────────────────────────────────┤
│ 💡 Cross-Encoder Nedir?                       │
│ Benzer raporları bulmak için seçilen          │
│ sütunlardaki metinleri karşılaştırır.         │
├───────────────────────────────────────────────┤
│ 📋 Mevcut Veri Seti Sütunları                 │
│                                               │
│ Summary [ÖNERİLEN]              [Örn...]  [✓] │
│ Bug özeti (kısa açıklama)                     │
│                                               │
│ Description [ÖNERİLEN]          [Örn...]  [✓] │
│ Detaylı açıklama (test steps...)              │
│                                               │
│ Affects Version                 [Örn...]  [ ] │
│ Etkilenen versiyon                            │
│                                               │
│ Component                       [Örn...]  [ ] │
│ Platform/Bileşen                              │
│                                               │
│ ... (diğer sütunlar) ...                      │
│                                               │
├───────────────────────────────────────────────┤
│ ✓ Seçilen Sütunlar (Cross-Encoder İçin)      │
│ [Summary] [Description]                       │
│                                               │
│ ℹ️ En az 1, en fazla 5 sütun seçebilirsiniz  │
├───────────────────────────────────────────────┤
│ ⚙️ Ek Ayarlar                                 │
│ Embedding Model: [paraphrase-multilingual...▼]│
│ Top-K: [5]                                    │
│ FAISS Index: [Flat ▼]                         │
├───────────────────────────────────────────────┤
│        [💾 Kaydet ve Sistemi Başlat]          │
└───────────────────────────────────────────────┘
```

#### Kullanılabilir Sütunlar:

| Sütun | Açıklama | Önerilen | Örnek |
|-------|----------|----------|-------|
| **Summary** | Bug özeti | ✅ | "BiP mesaj gönderilirken crash..." |
| **Description** | Detaylı açıklama | ✅ | "Test Steps: 1. Open BiP..." |
| Affects Version | Etkilenen versiyon | | "Android 3.70.19" |
| Component | Platform/Bileşen | | "Android Client" |
| Priority | Öncelik seviyesi | | "High" |
| Severity | Önem derecesi | | "Critical" |
| Problem Type | Problem tipi | | "Crash" |
| Frequency | Tekrar sıklığı | | "Always" |
| Application | Uygulama adı | | "BiP" |

#### Önerilen Konfigürasyon:

```
✅ Seçilen Sütunlar:
   • Summary
   • Description

⚙️ Ayarlar:
   • Embedding Model: paraphrase-multilingual-MiniLM-L12-v2
   • Top-K: 5
   • FAISS Index: Flat
```

#### İşlemler:
1. İstediğiniz sütunları seçin (checkbox)
2. En fazla 5 sütun seçebilirsiniz
3. Önerilen: Summary + Description (en iyi sonuçlar)
4. Ek ayarları değiştirin (opsiyonel)
5. "💾 Kaydet ve Sistemi Başlat" tıklayın
6. Konfigürasyon kaydedilir → `index.html` yönlendirilir

---

### 🏠 4. Ana Sistem (`index.html`)

Artık sistem tamamen kullanıma hazır!

#### Özellikler:

**Sağ Üst Köşe:**
```
[14,267 Toplam] [0 Benzer] [👤 Admin]
                              ↑
                         Kullanıcı Menüsü
```

Kullanıcı ikonuna tıklayınca:
```
👤 Admin User
📧 admin@turkcell.com.tr
🎯 Role: admin

⚙️ Konfigürasyon:
• Sütunlar: Summary, Description
• Model: paraphrase-multilingual-MiniLM-L12-v2
• Top-K: 5

Çıkış yapmak istiyor musunuz?
[İptal] [Tamam]
```

---

## 🔍 Sistem Akışı Özeti

```
┌─────────────┐
│ 1. LOGIN    │  admin@turkcell.com.tr / admin123
│ login.html  │  
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 2. DATA     │  📁 Mevcut Veri veya 📤 Yeni Veri
│ SELECTION   │
│ data_sel... │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 3. COLUMN   │  ✓ Summary, Description seç
│ MAPPING     │  ⚙️ Model, Top-K ayarla
│ column_m... │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 4. MAIN     │  🔍 Ara, ➕ Rapor Oluştur
│ SYSTEM      │  👤 Kullanıcı Menüsü
│ index.html  │
└─────────────┘
```

---

## 💾 LocalStorage Verileri

Sistem şu verileri tarayıcınızda saklar:

### 1. `userSession`
```json
{
  "username": "admin@turkcell.com.tr",
  "role": "admin",
  "name": "Admin User",
  "loginTime": "2025-10-12T..."
}
```

### 2. `dataSelection`
```
"existing" veya "new"
```

### 3. `systemConfig`
```json
{
  "selectedColumns": ["Summary", "Description"],
  "embeddingModel": "paraphrase-multilingual-MiniLM-L12-v2",
  "topK": 5,
  "indexType": "Flat",
  "configuredAt": "2025-10-12T..."
}
```

---

## 🔐 Güvenlik

- **Session**: LocalStorage (tarayıcı kapatılınca silinmez)
- **Logout**: Tüm session ve config verileri silinir
- **Auto-Redirect**: 
  - Login yoksa → `login.html`
  - Config yoksa → `data_selection.html`

---

## 🎨 Kullanıcı Deneyimi

### Session Kontrolleri:

**`index.html` açılırken:**
```javascript
1. Session var mı? → Hayır → login.html'e yönlendir
2. Config var mı? → Hayır → data_selection.html'e yönlendir
3. Her ikisi de var → Sistemi göster
```

**`create_report.html` açılırken:**
```javascript
Aynı kontroller (session + config)
```

---

## 🧪 Test Senaryosu

### Senaryo 1: İlk Kez Giriş

```
1. Tarayıcı aç → http://localhost:8000/index.html
2. ❌ Session yok → login.html'e yönlendirilir
3. ✅ Login yap → data_selection.html'e yönlendirilir
4. ✅ Mevcut veri seç → column_mapping.html'e yönlendirilir
5. ✅ Sütunları seç → index.html'e yönlendirilir
6. 🎉 Sistem kullanıma hazır!
```

### Senaryo 2: Tekrar Giriş (Same Browser)

```
1. Tarayıcı aç → http://localhost:8000/index.html
2. ✅ Session var, Config var
3. 🎉 Direkt sistemi kullan (login gerekmez)
```

### Senaryo 3: Logout

```
1. Kullanıcı ikonuna tıkla (sağ üstte)
2. "Çıkış yapmak istiyor musunuz?" → Tamam
3. ✅ Session silindi, Config silindi
4. → login.html'e yönlendirilir
```

---

## 📱 Responsive Tasarım

Tüm sayfalar responsive:
- ✅ Desktop (> 1024px)
- ✅ Tablet (768px - 1024px)
- ✅ Mobile (< 768px)

---

## 🎯 Önerilen Kullanım

### Hızlı Başlangıç İçin:
1. ✅ Mevcut veri setini kullan
2. ✅ Summary + Description seç
3. ✅ Varsayılan ayarları kullan

### Özelleştirilmiş Kullanım İçin:
1. ✅ Yeni veri yükle (CSV)
2. ✅ İhtiyacınıza göre sütunları seç (1-5 arası)
3. ✅ Model ve index tipini değiştir

---

## ❓ Sık Sorulan Sorular

### Q: LocalStorage nerede saklanıyor?
**A:** Tarayıcınızda, `http://localhost:8000` domain'i altında.

### Q: Şifremi unuttum?
**A:** Demo için hardcoded: `admin123` veya `user123`

### Q: Yeni kullanıcı ekleyebilir miyim?
**A:** Evet, `login.html` içindeki `USERS` objesine ekleyin.

### Q: Config'i nasıl değiştirebilirim?
**A:** Logout yap → Tekrar login → Farklı konfigürasyon seç

### Q: Sistem yavaş çalışıyor?
**A:** Daha az sütun seç (sadece Summary) veya daha hızlı model kullan

---

## 🔧 Sorun Giderme

### Problem: Login sayfası açılmıyor
**Çözüm:**
```bash
# HTTP server çalışıyor mu?
curl http://localhost:8000/login.html

# Çalışmıyorsa:
cd web
python3 -m http.server 8000
```

### Problem: Login sonrası yönlendirilmiyor
**Çözüm:**
```javascript
// Console'da kontrol edin (F12):
localStorage.getItem('userSession')

// Silmek için:
localStorage.clear()
```

### Problem: Ana sayfa sürekli login'e yönlendiriyor
**Çözüm:**
```javascript
// Session oluştur (geçici):
localStorage.setItem('userSession', JSON.stringify({
    username: "admin@turkcell.com.tr",
    role: "admin",
    name: "Admin User"
}));
```

---

## 📞 Destek

Sorunlar için:
1. Browser Console'u kontrol edin (F12)
2. LocalStorage'ı kontrol edin
3. Backend loglarını kontrol edin: `tail -f server.log`

---

**✨ Sistem kullanıma hazır! İyi çalışmalar! 🚀**

