# 🔥 Firebase Hosting Setup Rehberi

## 1️⃣ Firebase Login

Terminal'de şu komutu çalıştır:

```bash
firebase login
```

Tarayıcı açılacak:
- **esracevik456@gmail.com** ile giriş yap
- "Allow Firebase CLI" tıkla
- Terminal'e dön, başarılı mesajı göreceksin

---

## 2️⃣ Firebase Projesi Oluştur

### Seçenek A: Console'dan (Önerilen)

1. **https://console.firebase.google.com** aç
2. **esracevik456@gmail.com** ile giriş yap
3. **"Add project"** tıkla
4. Proje adı: **jira-duplicate-detection**
5. Google Analytics: **Disable** (veya enable, tercihinize kalmış)
6. **"Create project"** tıkla
7. Proje ID'yi not al (örn: `jira-duplicate-detection-xxxxx`)

### Seçenek B: CLI'dan

```bash
firebase projects:create jira-duplicate-detection
```

---

## 3️⃣ Firebase Init (Bu Klasörde)

Terminal'de:

```bash
cd /Users/cemirhans/Downloads/JIRA_DUPLICATE_DETECTION-main-2/bug-deduplication-github
firebase init
```

### Sorulacak Sorular ve Cevaplar:

**1. Which Firebase features?**
```
❯ ◯ Hosting: Configure files for Firebase Hosting
```
→ Space ile seç, Enter

**2. Project Setup**
```
❯ Use an existing project
```
→ Enter

**3. Select a default Firebase project**
```
❯ jira-duplicate-detection (jira-duplicate-detection-xxxxx)
```
→ Enter

**4. What do you want to use as your public directory?**
```
? web
```
→ `web` yaz, Enter

**5. Configure as a single-page app?**
```
? Yes
```
→ `y` Enter

**6. Set up automatic builds and deploys with GitHub?**
```
? No
```
→ `N` Enter

**7. File web/index.html already exists. Overwrite?**
```
? No
```
→ `N` Enter (önemli! mevcut dosyayı koruyoruz)

---

## 4️⃣ Firebase Deploy

```bash
firebase deploy
```

Çıktı:
```
✔  Deploy complete!

Project Console: https://console.firebase.google.com/project/jira-duplicate-detection-xxxxx/overview
Hosting URL: https://jira-duplicate-detection-xxxxx.web.app
```

---

## 5️⃣ Test Et

Tarayıcıda aç:
- **https://jira-duplicate-detection-xxxxx.web.app**

---

## ⚠️ Önemli Notlar

1. **Backend Bağlantısı**:
   - Şu anda frontend yayında ama backend lokal
   - Backend'i de deploy etmek için Railway kullanacağız (sonraki adım)

2. **API URL Güncellemesi**:
   - Backend deploy olduktan sonra:
   - `web/app.js` ve `web/create_report.js` içinde
   - `API_BASE_URL` değiştir
   - `firebase deploy` tekrar çalıştır

---

## 🎯 Özet Komutlar

```bash
# 1. Login
firebase login

# 2. Init
cd /Users/cemirhans/Downloads/JIRA_DUPLICATE_DETECTION-main-2/bug-deduplication-github
firebase init

# 3. Deploy
firebase deploy
```

---

## 📋 Sonraki Adım: Backend Deploy

Backend için Railway kullanacağız:
1. https://railway.app → GitHub ile giriş
2. "New Project" → "Deploy from GitHub repo"
3. esraacevik/JIRA_DUPLICATE_DETECTION seç
4. Deploy

---

## 🆘 Sorun Çözme

**"Firebase command not found"**
```bash
npm install -g firebase-tools
```

**"Login failed"**
```bash
firebase logout
firebase login --reauth
```

**"Project not found"**
- Console'dan proje oluştur
- Proje ID'yi doğru yaz

---

## ✅ Başarı Kontrol

Şunları görmelisin:
```
✔  Firebase initialization complete!
✔  Deploy complete!

Hosting URL: https://jira-duplicate-detection-xxxxx.web.app
```

---

🎉 **İyi Şanslar!**

