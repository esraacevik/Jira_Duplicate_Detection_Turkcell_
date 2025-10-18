# 🔥 Firebase Authentication Kurulum Kılavuzu

## 📋 İçindekiler
1. [Firebase Projesi Oluşturma](#1-firebase-projesi-oluşturma)
2. [Firebase Authentication Aktifleştirme](#2-firebase-authentication-aktifleştirme)
3. [Firebase Firestore Aktifleştirme](#3-firebase-firestore-aktifleştirme)
4. [Proje Yapılandırması](#4-proje-yapılandırması)
5. [Kullanım](#5-kullanım)
6. [Sorun Giderme](#6-sorun-giderme)

---

## 1. Firebase Projesi Oluşturma

### Adım 1: Firebase Console'a Giriş
1. https://console.firebase.google.com/ adresine gidin
2. Google hesabınızla giriş yapın
3. **"Add project"** (Proje Ekle) butonuna tıklayın

### Adım 2: Proje Ayarları
1. **Proje Adı**: `bug-report-system` (veya istediğiniz isim)
2. **Google Analytics**: İsteğe bağlı (kapatabilirsiniz)
3. **Create Project** butonuna tıklayın
4. Proje hazır olana kadar bekleyin (~1 dakika)

### Adım 3: Web App Ekleme
1. Firebase Console'da projenizi açın
2. **"</>** (Web)" ikonuna tıklayın
3. **App nickname**: `Bug Report Web App`
4. **Firebase Hosting**: ✅ İşaretleyin (opsiyonel)
5. **Register app** butonuna tıklayın

### Adım 4: Firebase Config Bilgilerini Kopyalayın
```javascript
// Bu bilgileri kaydedin - sonra kullanacağız!
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "bug-report-system.firebaseapp.com",
  projectId: "bug-report-system",
  storageBucket: "bug-report-system.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef1234567890"
};
```

---

## 2. Firebase Authentication Aktifleştirme

### Adım 1: Authentication'ı Aktifleştir
1. Sol menüden **"Build"** > **"Authentication"** seçin
2. **"Get started"** butonuna tıklayın

### Adım 2: Email/Password Sign-in Metodunu Aktifleştir
1. **"Sign-in method"** tab'ına gidin
2. **"Email/Password"** seçeneğini bulun
3. **"Enable"** toggle'ını açın
4. **"Email link (passwordless sign-in)"** KAPALI bırakın
5. **"Save"** butonuna tıklayın

✅ Artık kullanıcılar e-posta ve şifre ile kayıt olabilir!

---

## 3. Firebase Firestore Aktifleştirme

### Adım 1: Firestore Database Oluştur
1. Sol menüden **"Build"** > **"Firestore Database"** seçin
2. **"Create database"** butonuna tıklayın

### Adım 2: Güvenlik Kurallarını Seç
**Test Mode** seçin (geliştirme için):
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

### Adım 3: Location Seç
- **eur3 (europe-west)** seçin (Türkiye'ye en yakın)
- **Enable** butonuna tıklayın

### Adım 4: Firestore Güvenlik Kurallarını Güncelle (Önemli!)
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users collection - sadece kendi verisini okuyabilir
    match /users/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow create: if request.auth != null;
      allow update: if request.auth != null && request.auth.uid == userId;
      allow delete: if false; // Kullanıcılar kendi hesaplarını silemez
    }
    
    // Reports collection - tüm authenticated kullanıcılar okuyabilir
    match /reports/{reportId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
      allow update: if request.auth != null;
      allow delete: if request.auth != null;
    }
  }
}
```

**Publish** butonuna tıklayın.

---

## 4. Proje Yapılandırması

### Adım 1: Firebase Config Dosyasını Güncelle

`web/firebase-config.js` dosyasını açın ve Firebase Console'dan aldığınız bilgilerle güncelleyin:

```javascript
// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",  // BURAYA KENDİ DEĞERLER
    authDomain: "bug-report-system.firebaseapp.com",
    projectId: "bug-report-system",
    storageBucket: "bug-report-system.appspot.com",
    messagingSenderId: "123456789012",
    appId: "1:123456789012:web:abcdef1234567890"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Get Firebase services
const auth = firebase.auth();
const db = firebase.firestore();

console.log('🔥 Firebase initialized successfully!');
```

### Adım 2: Firebase Hosting (Opsiyonel)

Eğer Firebase Hosting kullanmak isterseniz:

```bash
# Firebase CLI'yi yükleyin
npm install -g firebase-tools

# Firebase'e login olun
firebase login

# Projeyi başlatın
firebase init

# Seçenekler:
# - Hosting: Configure files for Firebase Hosting
# - What do you want to use as your public directory? -> web
# - Configure as a single-page app? -> Yes
# - Set up automatic builds and deploys with GitHub? -> No

# Deploy edin
firebase deploy
```

---

## 5. Kullanım

### Kullanıcı Kayıt Olma

1. Tarayıcıda `register.html` sayfasını açın
2. Formu doldurun:
   - **Ad Soyad**: En az 3 karakter
   - **E-posta**: Geçerli e-posta adresi
   - **Şifre**: En az 6 karakter (büyük harf, küçük harf, rakam önerilir)
   - **Rol**: Kullanıcı/Admin/Developer/Tester
3. **"Kayıt Ol"** butonuna tıklayın
4. Başarılı olursa otomatik olarak login sayfasına yönlendirileceksiniz

### Kullanıcı Giriş Yapma

1. Tarayıcıda `login.html` sayfasını açın
2. E-posta ve şifrenizi girin
3. **"Giriş Yap"** butonuna tıklayın
4. Başarılı olursa `data_selection.html` sayfasına yönlendirileceksiniz

### Şifre Sıfırlama

1. Login sayfasında **"Şifremi unuttum?"** linkine tıklayın
2. E-posta adresinizi girin
3. E-posta kutunuzu kontrol edin
4. Gelen linke tıklayarak yeni şifre oluşturun

---

## 6. Sorun Giderme

### Hata: "Firebase yapılandırılmamış!"

**Neden**: `firebase-config.js` dosyasındaki API key'ler güncellenmemiş.

**Çözüm**:
1. Firebase Console'dan config bilgilerini kopyalayın
2. `web/firebase-config.js` dosyasını güncelleyin
3. Sayfayı yenileyin

---

### Hata: "Email already in use"

**Neden**: Bu e-posta adresi ile zaten bir kullanıcı kayıtlı.

**Çözüm**:
- Farklı bir e-posta adresi kullanın
- Veya login yapın

---

### Hata: "CORS error" veya "Firebase is not defined"

**Neden**: Firebase SDK'ları yüklenmemiş.

**Çözüm**:
HTML dosyalarında bu satırları kontrol edin:
```html
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-firestore-compat.js"></script>
<script src="firebase-config.js"></script>
```

---

### Hata: "Permission denied" (Firestore)

**Neden**: Firestore güvenlik kuralları yanlış yapılandırılmış.

**Çözüm**:
1. Firebase Console > Firestore Database > Rules
2. Yukarıdaki güvenlik kurallarını kopyalayın
3. **Publish** edin

---

### Demo Mod Kullanımı

Firebase yapılandırılmamışsa sistem otomatik olarak **Demo Mod**'a geçer:

**Demo Hesaplar**:
- E-posta: `demo@turkcell.com.tr`
- Şifre: `demo123`

veya

- E-posta: `admin@turkcell.com.tr`
- Şifre: `admin123`

---

## 📊 Firestore Veri Yapısı

### Users Collection

```javascript
/users/{userId}
{
  uid: "firebase-user-id",
  email: "user@turkcell.com.tr",
  fullName: "Ahmet Yılmaz",
  role: "admin",  // user, admin, developer, tester
  createdAt: Timestamp,
  lastLogin: Timestamp
}
```

### Reports Collection (Gelecek için)

```javascript
/reports/{reportId}
{
  userId: "firebase-user-id",
  summary: "Bug summary",
  description: "Bug description",
  application: "BiP",
  platform: "android",
  priority: "high",
  createdAt: Timestamp,
  updatedAt: Timestamp
}
```

---

## 🔐 Güvenlik Önerileri

1. **API Key'leri Saklamayın**: 
   - `.gitignore` dosyasına `firebase-config.js` ekleyin
   - Production'da environment variables kullanın

2. **Güvenlik Kurallarını Sıkılaştırın**:
   - Test mode'dan production mode'a geçin
   - Sadece gerekli read/write izinleri verin

3. **Email Verification Ekleyin**:
   ```javascript
   await user.sendEmailVerification();
   ```

4. **Rate Limiting**:
   - Firebase App Check kullanın
   - Çok fazla başarısız giriş denemelerini engelleyin

---

## ✅ Checklist

- [ ] Firebase projesi oluşturuldu
- [ ] Authentication aktifleştirildi
- [ ] Firestore aktifleştirildi
- [ ] `firebase-config.js` güncellendi
- [ ] Kayıt sayfası test edildi
- [ ] Login sayfası test edildi
- [ ] Şifre sıfırlama test edildi
- [ ] Firestore güvenlik kuralları güncellendi

---

## 📚 Ek Kaynaklar

- [Firebase Authentication Docs](https://firebase.google.com/docs/auth)
- [Firebase Firestore Docs](https://firebase.google.com/docs/firestore)
- [Firebase Security Rules](https://firebase.google.com/docs/rules)
- [Firebase Best Practices](https://firebase.google.com/docs/rules/rules-and-auth)

---

**Yardıma mı ihtiyacınız var?** Firebase Console'da sağ altta bulunan "?" butonuna tıklayarak support alabilirsiniz.

🎉 **Kurulum Tamamlandı!** Artık kullanıcılar Firebase ile kayıt olup giriş yapabilir!

