# 🚂 Railway + Firebase Deployment Guide

## 📋 Overview

Bu sistem şu şekilde çalışır:
1. **Railway** → Backend (Flask API) hosting
2. **Firebase** → Authentication + Firestore + **Storage (Embedding Cache)**
3. **Embedding Cache** → Her kullanıcı için embedding bir kere yapılır, Firebase Storage'da saklanır

---

## 🎯 Neden Bu Sistem?

### ❌ Önceki Durum:
- Her login'de embedding yapılıyor (10-15 saniye) ❌
- Server restart olunca embedding'ler kayboluyordu ❌
- Production'da bu sürdürülebilir değil ❌

### ✅ Yeni Sistem:
- Embedding **bir kere** yapılır (ilk data upload'da) ✅
- Firebase Storage'da saklanır (kalıcı) ✅
- Sonraki login'lerde Firebase'den indirilir (2-3 saniye) ✅
- Server restart olsa bile embedding'ler kaybolmaz ✅

---

## 🔥 Firebase Setup

### 1. Firebase Storage Aktif Et

1. Firebase Console → **Storage** → **Get Started**
2. **Production mode** seç (security rules ekleyeceğiz)
3. **Storage location** seç (örn: `europe-west3`)

### 2. Storage Security Rules

Firebase Console → Storage → **Rules** → Aşağıdaki kuralları ekle:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // User-specific embeddings
    match /user_embeddings/{userId}/{allPaths=**} {
      // Sadece kendi embedding'lerini okuyabilir/yazabilir
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

### 3. Firebase Service Account

1. Firebase Console → **Project Settings** → **Service Accounts**
2. **Generate New Private Key** → JSON dosyasını indir
3. Dosyayı `firebase-service-account.json` olarak kaydet
4. **GİTİGNORE'A EKLE** (public etme!)

---

## 🚂 Railway Deployment

### 1. Railway Projesi Oluştur

1. [Railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Repository'yi seç: `bug-deduplication-github`
3. Railway otomatik detect edecek (`requirements.txt` var)

### 2. Environment Variables

Railway Dashboard → **Variables** → Şu değişkenleri ekle:

```bash
# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT=/app/firebase-service-account.json
FIREBASE_STORAGE_BUCKET=jira-duplicate-detection.appspot.com

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# CORS
ALLOWED_ORIGINS=https://jira-duplicate-detection.web.app,https://jira-duplicate-detection.firebaseapp.com

# Feature Flags
USE_FIREBASE_CACHE=True
```

### 3. Firebase Service Account Upload

Railway'de service account JSON dosyasını eklemek için 2 yöntem:

#### Yöntem 1: Base64 Encoding (Önerilen)
```bash
# Local'de çalıştır:
cat firebase-service-account.json | base64 > firebase-service-account-base64.txt
```

Railway Variables:
```bash
FIREBASE_SERVICE_ACCOUNT_BASE64=<base64 string buraya yapıştır>
```

`api_server.py`'ye ekle:
```python
# Decode base64 and save
import base64
if os.getenv('FIREBASE_SERVICE_ACCOUNT_BASE64'):
    with open('/tmp/firebase-service-account.json', 'w') as f:
        decoded = base64.b64decode(os.getenv('FIREBASE_SERVICE_ACCOUNT_BASE64'))
        f.write(decoded.decode())
    os.environ['FIREBASE_SERVICE_ACCOUNT'] = '/tmp/firebase-service-account.json'
```

#### Yöntem 2: Railway Volumes
1. Railway → **Settings** → **Volumes**
2. Mount Path: `/app/secrets`
3. Service account'u `/app/secrets/firebase-service-account.json` olarak upload et

### 4. Deploy

```bash
git add .
git commit -m "Railway + Firebase deployment setup"
git push origin main
```

Railway otomatik deploy edecek!

---

## 🌐 Frontend Configuration

### 1. API Base URL Güncelle

`web/app.js` ve `web/create_report.js`:

```javascript
// Production
const API_BASE_URL = 'https://your-app.railway.app/api';

// Veya environment detection:
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:5001/api'
  : 'https://your-app.railway.app/api';
```

### 2. Firebase Hosting Deploy

```bash
firebase deploy --only hosting
```

---

## 🎯 Cache System Nasıl Çalışır?

### İlk Data Upload (Kullanıcı veriyi ilk kez yüklüyor):

```
1. User uploads data.csv
2. Backend embedding yapıyor (10-15 saniye)
   ├─ embeddings.npy oluşturuluyor
   ├─ faiss_index.bin oluşturuluyor
   └─ metadata.json oluşturuluyor
3. Firebase Storage'a upload ediliyor 📤
   └─ user_embeddings/{userId}/
       ├─ embeddings.npy
       ├─ faiss_index.bin
       ├─ metadata.json
       └─ data.csv
4. Kullanıcı search yapabiliyor ✅
```

### Sonraki Login'ler (Cache hit):

```
1. User login yapıyor
2. Backend Firebase Storage'ı kontrol ediyor
3. Artifacts bulunuyor! 📥
4. Firebase'den indiriliy or (2-3 saniye)
5. Local'e kaydediliyor
6. Embedding yapılmıyor! ⏩ Cached version kullanılıyor
7. Kullanıcı HEMEN search yapabiliyor ✅
```

### Veri Değiştiğinde:

```
1. User rapor ekliyor/değiştiriyor
2. Backend embedding yeniliyor (10-15 saniye)
3. Yeni artifacts Firebase'e upload ediliyor 📤
4. Cache güncelleniyor ✅
```

---

## 📊 Monitoring

### Railway Logs

Railway Dashboard → **Logs** → Şunları göreceksin:

```
✅ Firebase Storage initialized
🔍 Checking Firebase Storage for cached embeddings...
✅ Found cached embeddings in Firebase Storage!
📥 Downloading artifacts for user xyz...
✅ Downloaded: embeddings.npy (1.2 MB)
✅ Downloaded: faiss_index.bin (856 KB)
⏩ Skipping embedding generation - using cached version
```

### Firebase Storage

Firebase Console → **Storage** → Göreceksin:

```
user_embeddings/
├─ P8VtJgvODiXSbjOtCMqUTecivHR2/
│  ├─ embeddings.npy (1.2 MB)
│  ├─ faiss_index.bin (856 KB)
│  ├─ metadata.json (2 KB)
│  └─ data.csv (45 KB)
└─ another-user-id/
   └─ ...
```

---

## 🐛 Troubleshooting

### "Firebase Storage not initialized"

```bash
# Railway Variables kontrol et:
FIREBASE_SERVICE_ACCOUNT=/app/firebase-service-account.json
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
```

### "Permission denied" hatası

Firebase Storage Rules'u kontrol et:
```javascript
allow read, write: if request.auth != null && request.auth.uid == userId;
```

### Embedding yapılmaya devam ediyor

Logs'a bak:
```
🔍 Checking Firebase Storage for cached embeddings...
📝 No cached embeddings found, will generate new ones
```

Firebase Storage'da artifacts var mı kontrol et.

---

## 💰 Cost Estimation

### Railway:
- **Starter Plan**: $5/month (500 hours)
- **Hobby Plan**: Free (500 hours/month, enough for development)

### Firebase Storage:
- **Spark Plan (Free)**: 1 GB storage, 1 GB/day download
- **Blaze Plan (Pay as you go)**: 
  - Storage: $0.026/GB/month
  - Download: $0.12/GB
  
**Örnek:** 100 kullanıcı, her biri ~2MB embedding:
- Storage: 200 MB = ~$0.005/month
- Download (her kullanıcı ayda 10 login): 100 * 2MB * 10 = 2GB = ~$0.24/month

**TOPLAM: ~$5-10/month** 🎉

---

## ✅ Checklist

- [ ] Firebase Storage aktif
- [ ] Storage security rules eklendi
- [ ] Service account JSON indirildi
- [ ] Railway projesi oluşturuldu
- [ ] Environment variables eklendi
- [ ] Service account Railway'e upload edildi
- [ ] Frontend API URL güncellendi
- [ ] Firebase Hosting deploy edildi
- [ ] Test: Yeni kullanıcı ile embedding yapıldı ve cache'lendi
- [ ] Test: Aynı kullanıcı logout/login → cache'ten yüklendi

---

## 🚀 Next Steps

1. **Incremental Updates**: Sadece değişen row'ların embedding'ini güncelle
2. **Compression**: Artifacts'ları compress et (gzip)
3. **CDN**: Firebase Storage CDN kullan
4. **Monitoring**: Sentry/LogRocket ekle
5. **Analytics**: Embedding cache hit rate track et

---

## 📞 Support

Sorular için: [GitHub Issues](https://github.com/your-repo/issues)

---

**🎉 Artık production-ready bir sistem var!**

