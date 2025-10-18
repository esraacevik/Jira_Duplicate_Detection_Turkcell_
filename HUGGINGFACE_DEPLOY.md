# 🤗 Hugging Face Spaces Deployment Guide

## 🎯 Neden Hugging Face Spaces?

- ✅ **Tamamen Ücretsiz** - AI/ML projeleri için özel
- ✅ **PyTorch, Transformers önceden kurulu** - Image size sorunu yok
- ✅ **Persistent Storage** - Embedding'ler kaybolmaz
- ✅ **GitHub Entegrasyonu** - Otomatik deploy
- ✅ **Public API** - Herkes erişebilir

---

## 🚀 Deployment Adımları

### 1. Hugging Face Hesabı Oluştur

1. 🌐 **Hugging Face'e git:** https://huggingface.co/join
2. 📧 **Email ile kayıt ol** (veya GitHub ile)
3. ✅ Email doğrula

---

### 2. Yeni Space Oluştur

1. Hugging Face'te **"New"** → **"Space"** tıkla
2. **Space Bilgileri:**
   - **Name**: `jira-duplicate-detection` (veya istediğin isim)
   - **License**: `MIT`
   - **Space SDK**: **Docker** seç ⚠️ (ÖNEMLİ!)
   - **Visibility**: `Public` (veya `Private`)

3. **"Create Space"** tıkla

---

### 3. GitHub Repository'yi Bağla

Space oluşturulduktan sonra:

#### Yöntem A: Git ile Push (Önerilen)

```bash
cd /Users/cemirhans/Downloads/JIRA_DUPLICATE_DETECTION-main-2/bug-deduplication-github

# Hugging Face remote ekle
git remote add huggingface https://huggingface.co/spaces/KULLANICI_ADIN/jira-duplicate-detection

# Push et
git push huggingface main
```

⚠️ **Username ve Token:**
- Username: Hugging Face kullanıcı adın
- Password: **Access Token** (şifre değil!)
  - Settings → Access Tokens → New Token → Write access

#### Yöntem B: Manuel Upload

1. Space sayfasında **"Files"** sekmesi
2. **"Add file"** → **"Upload files"**
3. Tüm dosyaları sürükle-bırak

---

### 4. Environment Variables (Opsiyonel)

Space Settings → **"Repository secrets"** → Ekle:

```bash
FLASK_ENV=production
USE_FIREBASE_CACHE=False
ALLOWED_ORIGINS=*
```

---

### 5. Deploy'u İzle

Space'in ana sayfasında **"Building..."** göreceksin.

**Build Logs:**
- **"App"** sekmesi → **"Logs"** buton

Build tamamlanınca:
```
✅ Container started
✅ App running on https://KULLANICI_ADIN-jira-duplicate-detection.hf.space
```

---

## 🌐 API URL

Deploy olduktan sonra API URL'in:

```
https://KULLANICI_ADIN-jira-duplicate-detection.hf.space/api
```

---

## 🧪 Test

### Health Check

```bash
curl https://KULLANICI_ADIN-jira-duplicate-detection.hf.space/api/health
```

Beklenen cevap:
```json
{
  "status": "healthy",
  "message": "Bug Report Duplicate Detection API is running"
}
```

---

## 🔧 Frontend Entegrasyonu

Deploy tamamlandıktan sonra, frontend'de API URL'i güncelle:

### `web/app.js`

```javascript
const API_BASE_URL = 'https://KULLANICI_ADIN-jira-duplicate-detection.hf.space/api';
```

### `web/create_report.js`

```javascript
const API_BASE_URL = 'https://KULLANICI_ADIN-jira-duplicate-detection.hf.space/api';
```

---

## 📦 Persistent Storage

Hugging Face Spaces, `/data` dizinini otomatik persist ediyor:

```
/app/data/user_embeddings/  ← User embedding'leri burada saklanır
```

Her kullanıcının embedding'i bir kere yapılır ve disk'te kalır!

---

## 🐛 Troubleshooting

### "Application startup failed"

**Çözüm:** Logs'a bak:
- Settings → Repository secrets → Environment variables eksik mi?
- Dockerfile doğru mu? (`EXPOSE 7860` olmalı)

### "Out of memory"

**Çözüm:** Hugging Face Spaces free tier:
- **RAM**: 16 GB (bizim için yeterli!)
- **CPU**: 8 core
- **Disk**: 50 GB

Bizim uygulama rahat çalışır. Eğer sorun varsa:
- `requirements.txt`'de gereksiz paketleri kaldır

### "Port binding failed"

**Çözüm:** `api_server.py`'de port 7860 olmalı:

```python
port = int(os.getenv('PORT', 7860))  # Hugging Face default port
```

Zaten ayarlı, sorun olmaz!

---

## 💰 Maliyet

**$0/month** - Tamamen ücretsiz! 🎉

---

## 🔐 Güvenlik

### CORS

Hugging Face Spaces public olduğu için CORS'u açık bırakabiliriz:

```python
CORS(app, origins="*")  # Herkes erişebilir
```

Veya sadece Firebase frontend'ine izin ver:

```python
CORS(app, origins=[
    "https://jira-duplicate-detection.web.app",
    "https://jira-duplicate-detection.firebaseapp.com"
])
```

---

## 📊 Monitoring

Hugging Face Space Dashboard:
- **"App"** sekmesi → Canlı logs
- **"Community"** sekmesi → Kullanıcı yorumları
- **Settings** → Analytics (ziyaretçi sayısı)

---

## 🎉 Avantajlar

✅ **Ücretsiz**  
✅ **AI için optimize** - PyTorch, transformers hazır  
✅ **Persistent storage** - Embedding'ler kaybolmaz  
✅ **Public URL** - Herkes kullanabilir  
✅ **Otomatik deploy** - Git push = yeni deploy  
✅ **Community** - Hugging Face community'de paylaşılabilir

---

## 📞 Destek

- Hugging Face Docs: https://huggingface.co/docs/hub/spaces
- Discord: https://huggingface.co/join/discord
- GitHub Issues: https://github.com/esraacevik/Jira_Duplicate_Detection_Turkcell_/issues

---

**🚀 Artık backend production-ready ve tamamen ücretsiz!**

