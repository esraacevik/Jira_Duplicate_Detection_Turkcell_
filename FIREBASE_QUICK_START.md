# 🚀 Firebase Authentication - Hızlı Başlangıç

## 5 Dakikada Firebase Kurulumu

### 1️⃣ Firebase Projesi Oluştur (2 dakika)

1. https://console.firebase.google.com/ → **Add Project**
2. Proje adı: `bug-report-system`
3. **Create Project**

### 2️⃣ Authentication'ı Aktifleştir (1 dakika)

1. Sol menü → **Authentication** → **Get Started**
2. **Sign-in method** tab → **Email/Password** → **Enable** → **Save**

### 3️⃣ Firestore'u Aktifleştir (1 dakika)

1. Sol menü → **Firestore Database** → **Create database**
2. **Test mode** seç → **eur3 (europe-west)** → **Enable**

### 4️⃣ Config'i Kopyala (1 dakika)

1. Proje ayarları (⚙️) → Scroll down → **Your apps** bölümünden **Web app** ekle
2. Config kodunu kopyala:

```javascript
const firebaseConfig = {
  apiKey: "...",
  authDomain: "...",
  projectId: "...",
  storageBucket: "...",
  messagingSenderId: "...",
  appId: "..."
};
```

### 5️⃣ Yapılandırmayı Güncelle (30 saniye)

`web/firebase-config.js` dosyasını aç ve config'i yapıştır:

```javascript
const firebaseConfig = {
    apiKey: "BURAYA_API_KEY",           // ← Değiştir
    authDomain: "BURAYA_AUTH_DOMAIN",   // ← Değiştir
    projectId: "BURAYA_PROJECT_ID",     // ← Değiştir
    storageBucket: "BURAYA_STORAGE",    // ← Değiştir
    messagingSenderId: "BURAYA_ID",     // ← Değiştir
    appId: "BURAYA_APP_ID"             // ← Değiştir
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();
```

### ✅ Bitti!

Şimdi test et:
```bash
# Web sayfalarını aç
open web/register.html  # Kayıt sayfası
open web/login.html     # Giriş sayfası
```

---

## 🧪 Test

### Yeni Kullanıcı Kaydı
1. `register.html` aç
2. Form doldur:
   - Ad: `Test User`
   - E-posta: `test@turkcell.com.tr`
   - Şifre: `test123`
   - Rol: `Admin`
3. **Kayıt Ol** → Otomatik login'e yönlenecek

### Giriş Yap
1. `login.html` aç
2. E-posta ve şifre gir
3. **Giriş Yap** → Ana sayfaya yönlenecek

---

## 🔥 Firebase Console'da Kontrol

### Kullanıcıları Görüntüle
1. Firebase Console → **Authentication** → **Users** tab
2. Kayıtlı kullanıcıları göreceksiniz

### Firestore Verilerini Görüntüle
1. Firebase Console → **Firestore Database** → **Data** tab
2. `users` collection'ını açın
3. Kullanıcı bilgilerini göreceksiniz

---

## ⚠️ Sorun mu Var?

### "Firebase is not defined"
→ Tarayıcı console'da bu hatayı görüyorsan:
- Sayfayı **hard refresh** yap (Ctrl+Shift+R veya Cmd+Shift+R)
- `firebase-config.js` dosyasının yüklendiğinden emin ol

### "Permission denied" (Firestore)
→ Firestore güvenlik kurallarını güncelle:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### "Email already in use"
→ Bu e-posta ile zaten kayıt olunmuş. Farklı e-posta dene veya login yap.

---

## 💡 Demo Mod

Firebase yapılandırmazsan **Demo Mod** otomatik çalışır:

**Demo Hesap**:
- E-posta: `demo@turkcell.com.tr`
- Şifre: `demo123`

Demo mod'da:
- ✅ Giriş yapabilirsin
- ❌ Yeni kullanıcı kaydedemezsin
- ❌ Şifre sıfırlayamazsın

---

## 📁 Dosya Yapısı

```
web/
├── firebase-config.js      ← Firebase ayarları (GÜNCELLE)
├── register.html           ← Kayıt sayfası
├── login.html             ← Giriş sayfası
└── ...
```

---

## 🎯 Sonraki Adımlar

1. **Güvenlik Kurallarını Sıkılaştır**: Production'da test mode kullanma!
2. **Email Verification Ekle**: Kullanıcılar e-postalarını doğrulasın
3. **Admin Panel**: Kullanıcı yönetimi için admin paneli ekle
4. **Roles & Permissions**: Farklı roller için yetkilendirme ekle

---

## 📚 Daha Fazla Bilgi

Detaylı kurulum için: **FIREBASE_AUTH_SETUP.md**

---

**🎉 Başarılar!** Sorularınız için: Firebase Console → Support

