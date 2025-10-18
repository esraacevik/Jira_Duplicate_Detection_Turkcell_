# 🔐 Kullanıcı Kimlik Doğrulama Sistemi

## ✨ Özellikler

### 🎯 Temel Özellikler
- ✅ **Firebase Authentication** ile güvenli kimlik doğrulama
- ✅ **Kullanıcı Kayıt** sistemi (register.html)
- ✅ **Kullanıcı Girişi** (login.html)
- ✅ **Şifre Sıfırlama** özelliği
- ✅ **Şifre Gücü Göstergesi** (kayıt sırasında)
- ✅ **Demo Mod** (Firebase yapılandırılmamışsa)
- ✅ **Firestore** ile kullanıcı verilerini saklama
- ✅ **Rol Bazlı Yetkilendirme** (Admin, User, Developer, Tester)

---

## 📱 Sayfalar

### 1. register.html - Kayıt Sayfası
**Özellikler**:
- 👤 Ad Soyad girişi
- 📧 E-posta doğrulama
- 🔒 Güvenli şifre oluşturma
- 📊 Şifre gücü göstergesi (Zayıf/Orta/Güçlü)
- 🎭 Rol seçimi
- ✅ Gerçek zamanlı form doğrulama
- 🎨 Modern animasyonlu UI

**Validasyonlar**:
- Ad Soyad: Minimum 3 karakter
- E-posta: Geçerli format (@turkcell.com.tr)
- Şifre: Minimum 6 karakter
- Şifre eşleşmesi kontrolü
- Rol seçimi zorunlu

**Kullanım**:
```
1. Ad Soyad gir
2. E-posta gir
3. Şifre belirle (güç göstergesi yeşil olmalı)
4. Şifreyi tekrar gir
5. Rol seç
6. "Kayıt Ol" butonuna tıkla
7. ✅ Otomatik login sayfasına yönlendirilir
```

---

### 2. login.html - Giriş Sayfası
**Özellikler**:
- 📧 E-posta ile giriş
- 🔒 Şifre ile kimlik doğrulama
- 🔄 Şifremi unuttum linki
- 💡 Demo mod desteği
- 🎨 Modern animasyonlu arka plan

**Kullanım**:
```
1. E-posta gir
2. Şifre gir
3. "Giriş Yap" butonuna tıkla
4. ✅ Ana sayfaya yönlendirilir
```

**Demo Hesaplar** (Firebase yapılandırılmamışsa):
- `demo@turkcell.com.tr` / `demo123`
- `admin@turkcell.com.tr` / `admin123`

---

## 🔥 Firebase Entegrasyonu

### Kullanılan Firebase Servisleri

#### 1. Firebase Authentication
```javascript
// Kullanıcı kaydı
await auth.createUserWithEmailAndPassword(email, password);

// Kullanıcı girişi
await auth.signInWithEmailAndPassword(email, password);

// Şifre sıfırlama
await auth.sendPasswordResetEmail(email);

// Çıkış
await auth.signOut();
```

#### 2. Firebase Firestore
```javascript
// Kullanıcı verisi kaydetme
await db.collection('users').doc(userId).set({
  uid: userId,
  email: email,
  fullName: name,
  role: role,
  createdAt: serverTimestamp(),
  lastLogin: serverTimestamp()
});

// Kullanıcı verisi okuma
const userDoc = await db.collection('users').doc(userId).get();
const userData = userDoc.data();
```

---

## 🗄️ Veri Yapısı

### LocalStorage
```javascript
{
  "userSession": {
    "uid": "firebase-user-id",
    "email": "user@turkcell.com.tr",
    "username": "user@turkcell.com.tr",
    "name": "Ahmet Yılmaz",
    "role": "admin",
    "loginTime": "2025-01-15T10:30:00.000Z",
    "authProvider": "firebase"  // veya "demo"
  }
}
```

### Firestore - users collection
```javascript
/users/{userId}
{
  uid: "firebase-user-id",
  email: "user@turkcell.com.tr",
  fullName: "Ahmet Yılmaz",
  role: "admin",  // user, admin, developer, tester
  createdAt: Timestamp(2025-01-15 10:30:00),
  lastLogin: Timestamp(2025-01-15 10:30:00)
}
```

---

## 🎭 Roller ve Yetkiler

### Kullanılabilir Roller
1. **👤 User** (Kullanıcı)
   - Rapor oluşturabilir
   - Arama yapabilir
   - Kendi raporlarını görebilir

2. **👨‍💼 Admin** (Yönetici)
   - Tüm User yetkileri
   - Tüm raporları görebilir
   - Sistem ayarlarını değiştirebilir
   - Kullanıcı yönetimi (gelecekte)

3. **👨‍💻 Developer** (Geliştirici)
   - Tüm User yetkileri
   - Teknik detayları görebilir
   - Debug modunu aktifleştirebilir

4. **🧪 Tester** (Test Uzmanı)
   - Tüm User yetkileri
   - Test raporları oluşturabilir
   - Test verileri yükleyebilir

---

## 🔒 Güvenlik

### Şifre Gereksinimleri
- ✅ Minimum 6 karakter
- 🟢 Önerilen: 10+ karakter
- 🟢 Önerilen: Büyük + küçük harf
- 🟢 Önerilen: En az 1 rakam
- 🟢 Önerilen: Özel karakter

### Şifre Gücü Göstergesi
```
🔴 Zayıf    : < 3 kriter
🟡 Orta     : 3-4 kriter
🟢 Güçlü    : 5+ kriter
```

### Firebase Security Rules
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read: if request.auth.uid == userId;
      allow create: if request.auth != null;
      allow update: if request.auth.uid == userId;
    }
  }
}
```

---

## 🎨 UI/UX Özellikleri

### Animasyonlar
- 🌟 Animasyonlu arka plan (250 kutucuk)
- ✨ Hover efektleri (kutucuklar sarı olur)
- 🎯 Smooth scroll
- 💫 Gradient animasyonları

### Responsive Design
- 📱 Mobil uyumlu (600px)
- 💻 Tablet uyumlu (900px)
- 🖥️ Desktop optimized

### Form Validasyonu
- ⚡ Gerçek zamanlı validasyon
- 🎨 Görsel geri bildirim (kırmızı border)
- 📝 Hata mesajları (Türkçe)
- ✅ Başarı mesajları

---

## 🔄 Akış Diyagramları

### Kayıt Akışı
```
Kullanıcı register.html açar
    ↓
Form doldurulur
    ↓
Validasyon kontrolü
    ↓
Firebase'e kayıt
    ↓
Firestore'a kullanıcı verisi
    ↓
✅ login.html'e yönlendirme
```

### Giriş Akışı
```
Kullanıcı login.html açar
    ↓
E-posta ve şifre girer
    ↓
Firebase Authentication
    ↓
Firestore'dan kullanıcı verisi
    ↓
LocalStorage'a session kaydet
    ↓
✅ data_selection.html'e yönlendirme
```

### Şifre Sıfırlama Akışı
```
"Şifremi unuttum?" tıkla
    ↓
E-posta gir
    ↓
Firebase reset email gönder
    ↓
E-posta kutusunu kontrol et
    ↓
Reset linkine tıkla
    ↓
Yeni şifre belirle
    ↓
✅ Giriş yap
```

---

## 📊 Hata Yönetimi

### Firebase Hataları
| Hata Kodu | Mesaj | Açıklama |
|-----------|-------|----------|
| `auth/email-already-in-use` | "Bu e-posta zaten kullanımda!" | Kayıt sırasında |
| `auth/invalid-email` | "Geçersiz e-posta adresi!" | E-posta formatı hatalı |
| `auth/user-not-found` | "Kullanıcı bulunamadı!" | Giriş sırasında |
| `auth/wrong-password` | "Hatalı şifre!" | Şifre yanlış |
| `auth/weak-password` | "Şifre çok zayıf!" | Min. 6 karakter |
| `auth/too-many-requests` | "Çok fazla deneme!" | Rate limit |

### Kullanıcı Dostu Mesajlar
```javascript
✅ Başarı: "Kayıt başarılı! Giriş sayfasına yönlendiriliyorsunuz..."
⚠️ Uyarı: "Şifreler eşleşmiyor!"
❌ Hata: "E-posta adresi zaten kullanımda!"
```

---

## 🚀 Gelecek Geliştirmeler

### Planlanan Özellikler
- [ ] Email verification (e-posta doğrulama)
- [ ] Social login (Google, Microsoft)
- [ ] 2FA (Two-factor authentication)
- [ ] User profile sayfası
- [ ] Admin panel
- [ ] Password strength meter iyileştirmesi
- [ ] Remember me özelliği
- [ ] Session timeout
- [ ] Login history

---

## 📝 Kod Örnekleri

### Kullanıcı Session Kontrolü
```javascript
// Her sayfada kullanıcı kontrolü
const userSession = JSON.parse(localStorage.getItem('userSession'));
if (!userSession) {
    window.location.href = 'login.html';
}
```

### Firebase ile Logout
```javascript
async function logout() {
    if (confirm('Çıkış yapmak istediğinizden emin misiniz?')) {
        try {
            await auth.signOut();
            localStorage.removeItem('userSession');
            window.location.href = 'login.html';
        } catch (error) {
            console.error('Logout error:', error);
        }
    }
}
```

### Rol Bazlı Erişim Kontrolü
```javascript
function checkAdminAccess() {
    const session = JSON.parse(localStorage.getItem('userSession'));
    if (session.role !== 'admin') {
        alert('Bu sayfaya erişim yetkiniz yok!');
        window.location.href = 'index.html';
    }
}
```

---

## 🎓 Eğitim Videoları (Gelecekte)

- [ ] Firebase projesi oluşturma
- [ ] Kayıt sistemi kullanımı
- [ ] Admin paneli kullanımı
- [ ] Güvenlik kuralları yapılandırması

---

## 📞 Destek

**Sorun mu yaşıyorsunuz?**
1. `FIREBASE_QUICK_START.md` dosyasını okuyun
2. `FIREBASE_AUTH_SETUP.md` detaylı kurulum kılavuzu
3. Firebase Console → Support
4. GitHub Issues

---

**Son Güncelleme**: 2025-01-15
**Versiyon**: 1.0.0
**Durum**: ✅ Production Ready

