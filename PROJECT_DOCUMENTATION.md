# JIRA Duplicate Detection Project - Proje Dokümantasyonu

## 📋 Proje Özeti

Bu proje, JIRA ticket'larından duplikasyonları tespit etmek ve temizlemek için geliştirilmiş bir Python tabanlı veri işleme pipeline'ıdır. Proje, CSV formatındaki JIRA verilerini alıp, metin temizleme, dil tespiti ve duplikasyon kaldırma işlemlerini gerçekleştirerek optimize edilmiş Parquet formatında çıktı üretir.

## 🏗️ Proje Yapısı

```
bug-deduplication/
├── data/                           # Veri dosyaları
│   ├── data_cleaned.csv           # Ham JIRA verisi (12.8 MB)
│   └── preprocessed/              # İşlenmiş veriler
│       └── issues_preprocessed.parquet
├── notebooks/                      # Jupyter notebook'lar
│   └── 01_data_exploration.ipynb  # Veri keşfi
├── src/                           # Kaynak kod
│   ├── __pycache__/              # Python cache
│   ├── db.py                     # Veritabanı işlemleri
│   ├── preprocess.py             # Ana ön işleme modülü
│   ├── run_pipeline.py           # Pipeline çalıştırma
│   └── utils.py                  # Yardımcı fonksiyonlar
├── .venv/                        # Virtual environment
├── requirements.txt              # Python bağımlılıkları
├── README.md                     # Temel README
└── PROJECT_DOCUMENTATION.md      # Bu dokümantasyon
```

## 🛠️ Teknoloji Stack'i

### Python Paketleri
- **pandas (2.2.2)**: Veri manipülasyonu ve analizi
- **numpy (2.2.6)**: Sayısal hesaplamalar
- **pyarrow (16.1.0)**: Parquet format desteği
- **SQLAlchemy (2.0.32)**: Veritabanı ORM
- **langdetect (1.0.9)**: Dil tespiti
- **langid (1.1.6)**: Alternatif dil tespiti

### Geliştirme Ortamı
- **Python Virtual Environment**: `.venv` klasöründe aktif
- **PowerShell**: Windows terminal ortamı
- **Jupyter Notebook**: Veri keşfi için

## 📊 Veri Yapısı

### Giriş Verisi (data_cleaned.csv)
JIRA'dan export edilen CSV dosyası aşağıdaki sütunları içerir:
- `Affects Version`: Etkilenen versiyon
- `Component`: Bileşen
- `Description`: Açıklama
- `Custom field (Frequency)`: Sıklık
- `Issue Type`: Ticket türü
- `Priority`: Öncelik
- `Custom field (Severity)`: Önem derecesi
- `Custom field (Problem Type)`: Problem türü
- `Summary`: Özet

### Çıkış Verisi (issues_preprocessed.parquet)
İşlenmiş veri aşağıdaki ek sütunları içerir:
- `summary_clean`: Temizlenmiş özet
- `description_clean`: Temizlenmiş açıklama
- `text_combined`: Birleştirilmiş metin
- `text_hash`: Benzersiz hash değeri
- `language`: Tespit edilen dil

## 🔧 Ana Modüller

### 1. preprocess.py
**Ana ön işleme modülü** - En kritik dosya
- **load_csv_robust()**: Farklı encoding/separator kombinasyonlarıyla CSV yükleme
- **validate_columns()**: Gerekli sütunların varlığını kontrol
- **preprocess_dataframe()**: Ana veri işleme pipeline'ı
- **detect_language_safe()**: Stabil dil tespiti (langid + fallback)
- **create_stable_hash()**: Duplikasyon tespiti için hash oluşturma
- **save_to_parquet()**: Optimize edilmiş Parquet formatında kaydetme

### 2. utils.py
**Metin temizleme yardımcı fonksiyonları**
- **basic_text_clean()**: Ana metin temizleme pipeline'ı
- **normalize_unicode()**: Unicode normalizasyonu
- **strip_html()**: HTML etiketlerini kaldırma
- **remove_code_blocks()**: Kod bloklarını temizleme
- **redact_sensitive()**: Hassas bilgileri maskeleme (email, URL, IP)
- **remove_markup()**: Markdown/Jira işaretlerini temizleme
- **remove_special_chars_and_lowercase()**: Özel karakter temizleme

### 3. run_pipeline.py
**Pipeline çalıştırma ve yönetimi**
- **clean_old_files()**: Eski parquet dosyalarını temizleme
- **run_preprocess()**: Ana işleme fonksiyonu
- **verify_output()**: Çıktı doğrulama ve örnekleme

### 4. db.py
**Veritabanı işlemleri** (henüz kullanılmıyor)

## 🚀 Kullanım

### Virtual Environment Aktivasyonu
```powershell
cd bug-deduplication
.venv\Scripts\Activate.ps1
```

### Pipeline Çalıştırma
```powershell
python src/run_pipeline.py
```

### Manuel Ön İşleme
```powershell
python src/preprocess.py --input data/data_cleaned.csv --output data/preprocessed/issues_preprocessed.parquet
```

## 📈 İşlem Adımları

1. **Veri Yükleme**: CSV dosyası farklı encoding/separator kombinasyonlarıyla yüklenir
2. **Sütun Doğrulama**: Gerekli sütunların varlığı kontrol edilir
3. **Sütun Normalizasyonu**: Sütun isimleri standartlaştırılır
4. **Metin Temizleme**: 
   - HTML etiketleri kaldırılır
   - Kod blokları temizlenir
   - Hassas bilgiler maskelenir
   - Markdown/Jira işaretleri temizlenir
   - Özel karakterler kaldırılır
5. **Metin Birleştirme**: Summary ve description birleştirilir
6. **Dil Tespiti**: Her metin için dil tespit edilir
7. **Hash Oluşturma**: Duplikasyon tespiti için benzersiz hash
8. **Duplikasyon Kaldırma**: Aynı hash'e sahip kayıtlar kaldırılır
9. **Parquet Kaydetme**: Optimize edilmiş formatta kaydetme

## 📊 Veri İstatistikleri

- **Ham Veri**: 12.8 MB CSV dosyası
- **İşlenmiş Veri**: Parquet formatında (daha küçük boyut)
- **Dil Desteği**: Türkçe ve İngilizce tespiti
- **Duplikasyon Tespiti**: SHA-256 hash tabanlı

## 🔍 Özellikler

### Metin Temizleme
- Unicode normalizasyonu
- HTML etiket temizleme
- Kod blok temizleme
- Hassas bilgi maskeleme (email, URL, IP, hex)
- Markdown/Jira markup temizleme
- Özel karakter temizleme
- Whitespace normalizasyonu

### Dil Tespiti
- **langid** kütüphanesi ile ana tespit
- Güven skoru kontrolü
- Fallback mekanizması (Türkçe karakter kontrolü)
- Kısa metinler için özel işlem

### Duplikasyon Tespiti
- Temizlenmiş metinden hash oluşturma
- Scoped hash (issue:: prefix)
- SHA-256 algoritması
- İlk kayıt korunur, diğerleri kaldırılır

## 🎯 Gelecek Geliştirmeler

1. **Veritabanı Entegrasyonu**: db.py modülünün aktifleştirilmesi
2. **Gelişmiş Duplikasyon Algoritmaları**: Semantic similarity
3. **Web Arayüzü**: Flask/FastAPI tabanlı
4. **Batch İşleme**: Büyük veri setleri için
5. **Monitoring**: İşlem logları ve metrikler
6. **API Entegrasyonu**: JIRA REST API bağlantısı

## 🐛 Bilinen Sorunlar

- Dil tespiti bazen düşük güven skoru verebilir
- Çok kısa metinler için dil tespiti zorlaşabilir
- Bazı özel karakterler temizleme sırasında kaybolabilir

## 📝 Notlar

- Virtual environment başarıyla kuruldu ve aktif
- Tüm gerekli paketler yüklü
- Pipeline test edildi ve çalışır durumda
- Veri işleme süreci optimize edilmiş
- Parquet formatı kullanımı performans artışı sağlıyor

---

**Son Güncelleme**: 3 Eylül 2025  
**Proje Durumu**: Aktif Geliştirme  
**Versiyon**: 1.0.0
