# 🚂 Railway Deployment - Hızlı Başlangıç

## 📋 Genel Bakış

Bu sistem şu şekilde çalışır:
- **Railway** → Backend (Flask API) + Persistent Volume (embedding storage)
- **Firebase** → Authentication + Firestore
- **Firebase Storage** → Optional embedding cache (gelecekte)

## 🎯 Embedding Sistemi

### Nasıl Çalışır?

1. **Kullanıcı veri yükler** → Embedding yapılır (10-15 saniye)
2. **Embedding Railway volume'da saklanır** → `/app/data/user_embeddings/{user_id}/`
3. **Kullanıcı logout/login yapar** → Embedding'ler Railway volume'dan yüklenir (1-2 saniye)
4. **Yeni rapor eklenir** → Sadece yeni rapor için embedding yapılır ve eklenir

### Railway Volume Yapısı

```
/app/data/user_embeddings/
├── user_id_1/
│   ├── data.csv                    # User'ın data'sı
│   ├── embeddings.npy              # Bi-encoder embeddings
│   ├── faiss_index.bin             # FAISS index
│   └── metadata.json               # Metadata (columns, row count, etc.)
└── user_id_2/
    └── ...
```

## 🚀 Railway Deployment Adımları

### 1. Railway Projesi Oluştur

1. [Railway.app](https://railway.app) → **GitHub ile giriş yap**
2. **New Project** → **Deploy from GitHub repo**
3. Repository seç: `esraacevik/Jira_Duplicate_Detection_Turkcell_`
4. Railway otomatik detect edecek (`requirements.txt` + `Procfile`)

### 2. Persistent Volume Ekle

Railway Dashboard → **Settings** → **Volumes** → **Add Volume**

```
Mount Path: /app/data/user_embeddings
```

⚠️ **ÖNEMLİ:** Volume eklemeden deploy etme! Aksi halde embedding'ler server restart olunca silinir.

### 3. Environment Variables

Railway Dashboard → **Variables** sekmesi → Şu değişkenleri ekle:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
PORT=8080

# Firebase Storage (optional - şimdilik kullanmıyoruz)
FIREBASE_STORAGE_BUCKET=jira-duplicate-detection.appspot.com
USE_FIREBASE_CACHE=False

# CORS - Firebase Hosting URL'leri
ALLOWED_ORIGINS=https://jira-duplicate-detection.web.app,https://jira-duplicate-detection.firebaseapp.com
```

⚠️ **Service Account (Şimdilik atlayabiliriz):**  
Firebase Storage'ı kullanmıyorsan, `FIREBASE_SERVICE_ACCOUNT_BASE64` şimdilik gerekli değil.

### 4. Deploy

Railway otomatik deploy edecek. Build logs'u takip et:

```
✅ Installing dependencies from requirements.txt
✅ Building application
✅ Starting server: python api_server.py
✅ Server listening on port 8080
```

### 5. Domain Al

Railway Dashboard → **Settings** → **Networking** → **Generate Domain**

Örnek URL: `https://your-app.up.railway.app`

## 🌐 Frontend Güncelleme

Railway domain'i aldıktan sonra, frontend'de API URL'i güncelle:

### `web/app.js`

```javascript
// Railway backend URL
const API_BASE_URL = 'https://your-app.up.railway.app/api';
```

### `web/create_report.js`

```javascript
// Railway backend URL
const API_BASE_URL = 'https://your-app.up.railway.app/api';
```

### Firebase Hosting Deploy

```bash
firebase deploy --only hosting
```

## ✅ Test

### 1. Health Check

```bash
curl https://your-app.up.railway.app/api/health
```

Beklenen cevap:
```json
{
  "status": "healthy",
  "message": "Bug Report Duplicate Detection API is running",
  "version": "2.0",
  "timestamp": "2025-10-18T12:00:00Z"
}
```

### 2. User Flow Test

1. Firebase frontend'e git: `https://jira-duplicate-detection.web.app`
2. Yeni kullanıcı kaydet
3. Login yap
4. CSV yükle → **Embedding yapılıyor... (10-15 saniye)**
5. Logout yap
6. Tekrar login yap → **Embedding yükleniyor... (1-2 saniye)** ✅
7. Yeni rapor ekle → **Sadece yeni rapor için embedding yapılıyor** ✅

## 📊 Monitoring

### Railway Logs

Railway Dashboard → **Deployments** → **View Logs**

Görecekleriniz:

```
🚀 BUG REPORT DUPLICATE DETECTION API SERVER
================================================================================
⚠️  USER-SPECIFIC MODE:
   • No default data loaded
   • Each user must upload their own data
   • Users can only see their own data
   • Embeddings are created per user
   • Firebase Storage caching enabled

🔥 Firebase Configuration:
   • Service Account: Not set
   • Storage Bucket: jira-duplicate-detection.appspot.com

✅ SERVER READY!
================================================================================
📍 Server will start on port: 8080
🔥 Starting Flask server...
```

### Volume Monitoring

Railway Dashboard → **Volumes** → Kullanım görüntüle

- Her user için ~2-5 MB embedding
- 100 kullanıcı = ~200-500 MB

## 🐛 Troubleshooting

### "No such file or directory: data/user_embeddings"

**Çözüm:** Volume eklenmiş mi kontrol et. Settings → Volumes → `/app/data/user_embeddings`

### "Server keeps restarting"

**Çözüm:** Logs'a bak. Genellikle:
- Python dependency eksik → `requirements.txt` kontrol et
- Port hatası → `PORT` env variable set edilmiş mi?

### "Embedding'ler kayboldu"

**Çözüm:** Volume eklenmiş mi? Volume olmadan her restart'ta embedding'ler silinir.

### "CORS error"

**Çözüm:** `ALLOWED_ORIGINS` env variable'ına frontend URL'ini ekle:
```
ALLOWED_ORIGINS=https://jira-duplicate-detection.web.app
```

## 💰 Maliyet

### Railway Pricing

- **Starter Plan**: $5/month
  - 5GB disk (volume için yeterli)
  - 8GB RAM
  - Unlimited bandwidth

**Örnek:** 100 kullanıcı × 5MB = 500 MB volume kullanımı → $5/month yeterli!

## 🔐 Güvenlik

### Production Checklist

- [x] CORS doğru şekilde yapılandırıldı
- [x] Environment variables set edildi
- [x] Volume persist enabled
- [ ] Firebase Authentication rules kontrol et
- [ ] Rate limiting ekle (isteğe bağlı)
- [ ] Monitoring/alerting ekle (isteğe bağlı)

## 📞 Destek

Sorular için:
- Railway Docs: https://docs.railway.app
- GitHub Issues: https://github.com/esraacevik/Jira_Duplicate_Detection_Turkcell_/issues

---

**🎉 Deployment tamamlandı! Artık production-ready!**

