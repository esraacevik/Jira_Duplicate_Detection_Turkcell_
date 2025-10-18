# 🔍 Feature Extraction Guide

## 📋 Özet

Kullanıcıların yüklediği verilerde **Application**, **Platform**, **App_Version** gibi sütunlar eksik olabilir. Ama bu bilgiler **Description** veya **Summary** sütununda gizli olabilir!

**Feature Extraction** sistemi bu bilgileri otomatik olarak çıkarıp yeni sütunlar oluşturur.

---

## 🎯 Örnek Senaryo

###Örnek 1: BiP Uygulaması

**Veri (Before):**
| ID | Description |
|----|-------------|
| 1 | BiP uygulaması iOS 14.5'te açılmıyor. iPhone 12'de test edildi. |
| 2 | Whatsapp Android 11'de çöküyor. Kritik hata! |

**Feature Extraction Sonrası (After):**
| ID | Description | **Application** | **Platform** | **App_Version** | **Device** | **Severity** |
|----|-------------|-----------------|--------------|-----------------|------------|--------------|
| 1 | BiP uygulaması iOS 14.5'te açılmıyor... | **BiP** | **iOS** | **14.5** | **iPhone 12** | - |
| 2 | Whatsapp Android 11'de çöküyor... | **Whatsapp** | **Android** | **11** | - | **Critical** |

---

## 🛠️ Nasıl Çalışır?

### 1. **Regex Pattern Matching**

Sistem şu pattern'ları kullanır:

**Application:**
```regex
\b([A-Z][a-z]+)\s+(?:uygulaması|application)
\b(BiP|Whatsapp|Instagram|Facebook)\b
```

**Platform:**
```regex
\b(iOS|Android|Windows|macOS)\b
```

**Version:**
```regex
(?:version|v\.?)\s*(\d+\.\d+(?:\.\d+)?)
iOS\s+(\d+(?:\.\d+)*)
```

**Device:**
```regex
\b(iPhone\s+\d+(?:\s+Pro)?(?:\s+Max)?)\b
\b(Samsung\s+Galaxy\s+[A-Z]\d+)\b
```

**Severity:**
```regex
\b(critical|kritik|acil|urgent)\b
\b(high|yüksek|önemli)\b
```

**Component:**
```regex
\b(Login|Register|Payment|Checkout)\b
```

---

## 📊 Kullanım (Frontend)

### Data Upload Akışı

```
1. Kullanıcı CSV yükler
2. "Feature Extraction" sayfası açılır (opsiyonel)
3. Kaynak sütun seçer (örn: Description)
4. Hangi feature'ları çıkarmak istediğini seçer
5. "Suggest" butonuna basar → Sistem öneride bulunur
6. "Extract" butonuna basar → Yeni sütunlar oluşturulur
7. Column Mapping'e geçer
8. Embedding yapılır
```

---

## 🌐 API Endpoints

### 1. Get Available Extraction Types

```http
GET /api/available_extraction_types
```

**Response:**
```json
{
  "success": true,
  "featureTypes": [
    {
      "type": "application",
      "description": "Uygulama adı (BiP, Whatsapp, vb.)"
    },
    {
      "type": "platform",
      "description": "Platform (iOS, Android, vb.)"
    },
    ...
  ]
}
```

### 2. Suggest Extractions

```http
POST /api/suggest_extractions
Content-Type: application/json

{
  "userId": "user123",
  "sourceColumn": "description"
}
```

**Response:**
```json
{
  "success": true,
  "suggestions": {
    "application": 45,  // 45 satırda bulunabilir
    "platform": 38,
    "version": 12
  },
  "totalRows": 50
}
```

### 3. Extract Features

```http
POST /api/extract_features
Content-Type: application/json

{
  "userId": "user123",
  "sourceColumn": "description",
  "extractions": {
    "Application": "application",
    "Platform": "platform",
    "App_Version": "version"
  }
}
```

**Response:**
```json
{
  "success": true,
  "extractedColumns": ["Application", "Platform", "App_Version"],
  "extractionStats": {
    "Application": 45,  // 45 satırda çıkarıldı
    "Platform": 38,
    "App_Version": 12
  },
  "totalRows": 50
}
```

---

## 🎨 UI Flow

### Feature Extraction Page (data_extraction.html - Yeni Sayfa)

**Adımlar:**
1. **Kaynak Sütun Seçimi**
   - Dropdown: Description, Summary, vb. text sütunları
   
2. **Feature Type Seçimi**
   - Checkboxlar: Application, Platform, Version, Device, Severity, Component
   
3. **Öneri Al (Suggest)**
   - "Suggest" butonu → Backend'e istek
   - Her feature için kaç satırda bulunabileceğini gösterir
   - "Application (45/50 satır bulundu)"
   
4. **Çıkar (Extract)**
   - "Extract" butonu → Backend'e istek
   - Yeni sütunlar oluşturulur
   - Başarı mesajı: "3 yeni sütun eklendi!"
   
5. **Devam Et**
   - "Continue to Column Mapping" butonu
   - column_mapping.html'e yönlenir

---

## 🔧 Backend Implementation

### `src/text_feature_extractor.py`

**Ana Sınıf:**
```python
class TextFeatureExtractor:
    def extract_feature(text, feature_type) -> str
    def extract_all_features(text, feature_types) -> dict
    def add_extracted_columns(df, source_column, extractions) -> DataFrame
    def suggest_extractions(df, text_column) -> dict
```

**Kullanım:**
```python
extractor = TextFeatureExtractor()

# Öneri al
suggestions = extractor.suggest_extractions(df, 'description')
# {'application': 45, 'platform': 38}

# Feature çıkar
df_new = extractor.add_extracted_columns(
    df, 
    'description',
    {'Application': 'application', 'Platform': 'platform'}
)
```

---

## ✅ Avantajlar

1. **Otomatik**: Kullanıcı manuel girmek zorunda değil
2. **Hızlı**: Regex ile hızlı extraction
3. **Akıllı**: Pattern matching ile %70-80 doğruluk
4. **Esnek**: Yeni pattern'lar eklenebilir
5. **User-friendly**: Öneri sistemi ile kullanıcı bilgilendirilir

---

## 🐛 Sınırlamalar

1. **Regex-based**: NLP/LLM kadar akıllı değil
2. **Pattern bağımlı**: Yeni format'lar pattern eklemek gerekir
3. **%100 doğruluk değil**: Bazı satırlar missed olabilir
4. **Dil bağımlı**: Şu an Türkçe + İngilizce

---

## 🚀 Gelecek Geliştirmeler

1. **LLM Integration**: GPT-4 ile daha akıllı extraction
2. **Custom Patterns**: Kullanıcı kendi pattern ekleyebilir
3. **Multi-language**: Daha fazla dil desteği
4. **Confidence Score**: Her extraction için güven skoru
5. **Manual Override**: Kullanıcı düzeltme yapabilir

---

## 📞 Kullanım Örnekleri

### Örnek 1: Turkcell Bug Reports

```
Description: "BiP iOS 15.2'de mesaj gönderilmiyor. iPhone 13 Pro'da"
↓
Application: BiP
Platform: iOS
App_Version: 15.2
Device: iPhone 13 Pro
```

### Örnek 2: E-commerce

```
Description: "Checkout ödeme sayfası çöküyor. Critical bug!"
↓
Component: Checkout
Severity: Critical
```

### Örnek 3: Banking App

```
Description: "Login ekranı Android 12'de yavaş. Version 3.5.1"
↓
Component: Login
Platform: Android
Version: 3.5.1
```

---

**🎉 Feature Extraction ile veri zenginleştirme artık kolay!**

