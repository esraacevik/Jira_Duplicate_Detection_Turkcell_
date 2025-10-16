# 🔍 JIRA Duplicate Bug Detection System

<div align="center">

**Turkcell için geliştirilmiş, yapay zeka destekli JIRA bug raporu duplicate detection sistemi**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Özellikler](#-özellikler) • [Kurulum](#-kurulum) • [Kullanım](#-kullanım) • [Dokümantasyon](#-dokümantasyon)

</div>

---

## 📊 Proje Özeti

Bu sistem, JIRA bug raporlarındaki **duplicate (tekrarlanan) kayıtları** yapay zeka ile tespit eder. Turkcell'in ihtiyaçlarına özel olarak geliştirilmiş olup, **çok dilli destek**, **platform/versiyon bazlı filtreleme** ve **modern web arayüzü** sunar.

### 🎯 Temel Amaç
- Yeni bir bug raporu girildiğinde, benzer mevcut raporları otomatik bulmak
- Duplicate bug raporlarını minimize etmek
- Geliştirici ve test ekiplerinin verimliliğini artırmak

---

## ✨ Özellikler

### 🤖 Yapay Zeka ve Arama
- **Cross-Encoder Model**: `mmarco-mMiniLMv2-L12-H384-v1` ile yüksek doğruluklu semantic similarity
- **FAISS Indexing**: Hızlı ve ölçeklenebilir arama
- **Hybrid Scoring**: Keyword + Semantic + Version + Platform + Language similarity
- **Multilingual Support**: Türkçe, İngilizce ve diğer diller için optimize

### 💻 Modern Web Arayüzü
- **Turkcell Tema**: Sarı (#FFCC00), Siyah (#000000) ve Turuncu (#FF9500) marka renkleri
- **Glassmorphism Design**: Modern, saydam card'lar ve blur efektleri
- **Animated Background**: Hacker tarzı arka plan ve yıldız animasyonları
- **Real-time Search**: Anlık arama sonuçları (debouncing ile optimize)
- **Responsive Design**: Mobil ve desktop uyumlu

### 📤 Veri Yönetimi
- **Custom Data Upload**: CSV/Excel ile kendi verilerinizi yükleyin
- **Dynamic Column Mapping**: Hangi sütunların karşılaştırılacağını seçin
- **Dataset Selection**: Farklı veri setleri arasında geçiş yapın
- **User-specific Data**: Her kullanıcı kendi verilerini yönetir

### 🔄 Duplicate Yönetimi
- **Replace Report**: Eski bir raporu yenisiyle değiştirin
- **Similarity Score**: Detaylı benzerlik puanları
- **Platform/Version Match**: Platform ve versiyon bazlı filtreleme
- **Language Detection**: Otomatik dil tespiti

### 🌐 Tam Türkçe Destek
- Tüm arayüz Türkçe
- Türkçe karakter desteği (ç, ğ, ı, ö, ş, ü)
- Türkçe bug raporlarında yüksek doğruluk

---

## 🚀 Kurulum

### Gereksinimler
- Python 3.8 veya üzeri
- pip (Python package manager)
- 4GB+ RAM (model yükleme için)

### Adım 1: Repository'yi Klonlayın
```bash
git clone https://github.com/KULLANICI_ADIN/bug-deduplication.git
cd bug-deduplication
```

### Adım 2: Virtual Environment Oluşturun
```bash
# Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Adım 3: Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### Adım 4: Backend'i Başlatın
```bash
# Otomatik başlatma (önerilen)
bash start_web_app.sh

# veya manuel
python api_server.py
```

Backend `http://localhost:5001` adresinde çalışacaktır.

### Adım 5: Web Arayüzünü Açın
```bash
# Basit HTTP server ile frontend'i servis edin
cd web
python -m http.server 8000
```

Tarayıcınızda açın: `http://localhost:8000/intro.html`

---

## 📖 Kullanım

### 1️⃣ Giriş Yapın
- **Demo Kullanıcı**: `demo` / `test123`
- **Admin Kullanıcı**: `admin` / `admin123`

### 2️⃣ Veri Kaynağı Seçin
İki seçenek:
- **Mevcut Veri Setini Kullan**: Hazır JIRA verisi
- **Yeni Veri Yükle**: Kendi CSV/Excel dosyanızı yükleyin

### 3️⃣ Sütunları Yapılandırın
- **Cross-Encoder Sütunları**: Arama için kullanılacak (örn: Summary, Description)
- **Form Metadata Sütunları**: Karşılaştırma için kullanılacak (örn: Platform, App Version)

### 4️⃣ Bug Raporu Oluşturun
1. `create_report.html` sayfasına gidin
2. Formu doldurun (Summary, Platform, Version, vb.)
3. **Benzer Raporlar** otomatik gösterilir
4. İsterseniz mevcut bir raporu değiştirebilirsiniz
5. "Raporu Kaydet" ile kaydedin

### 5️⃣ Benzer Raporları Arayın
1. `index.html` sayfasına gidin
2. Arama kriterlerini girin
3. Sonuçları inceleyin (similarity score, platform match, vb.)

---

## 📚 Dokümantasyon

Detaylı dokümantasyon için:

- **[KULLANIM_KILAVUZU.md](KULLANIM_KILAVUZU.md)**: Adım adım kullanım kılavuzu
- **[WEB_APP_README.md](WEB_APP_README.md)**: Web uygulaması mimarisi ve API
- **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)**: Proje yapısı ve teknik detaylar
- **[CUSTOM_DATA_INTEGRATION.md](CUSTOM_DATA_INTEGRATION.md)**: Kendi verilerinizi nasıl yüklersiniz
- **[COLUMN_SELECTION_GUIDE.md](COLUMN_SELECTION_GUIDE.md)**: Sütun seçimi rehberi
- **[DUPLICATE_REPLACEMENT_FEATURE.md](DUPLICATE_REPLACEMENT_FEATURE.md)**: Duplicate değiştirme özelliği

---

## 🏗️ Proje Yapısı

```
bug-deduplication/
├── api_server.py              # Flask backend server
├── hybrid_search.py           # Hybrid search sistemi (core)
├── test_hybrid_search.py      # Test dosyası
├── requirements.txt           # Python bağımlılıkları
├── start_web_app.sh           # Otomatik başlatma script'i
│
├── src/                       # Kaynak kod
│   ├── preprocess_jira.py     # JIRA veri preprocessing
│   ├── embedding_pipeline.py  # Embedding generation
│   ├── run_pipeline.py        # Pipeline orchestrator
│   ├── utils.py               # Yardımcı fonksiyonlar
│   └── duplike_preprocess/    # Duplike veri preprocessing
│
├── web/                       # Frontend (HTML/JS/CSS)
│   ├── intro.html             # Landing page
│   ├── login.html             # Giriş sayfası
│   ├── data_selection.html    # Veri kaynağı seçimi
│   ├── dataset_selection.html # Dataset seçimi
│   ├── data_upload.html       # Veri yükleme
│   ├── column_mapping.html    # Sütun yapılandırma
│   ├── index.html             # Arama sayfası
│   ├── create_report.html     # Rapor oluşturma
│   ├── app.js                 # Ana JavaScript
│   ├── create_report.js       # Rapor JS
│   ├── stars.js               # Animasyon JS
│   └── style.css              # Global CSS
│
├── data/                      # Veri dosyaları
│   ├── *.csv                  # CSV veri
│   ├── *.xlsx                 # Excel veri
│   ├── preprocessed/          # Preprocessing çıktıları
│   └── user_data/             # Kullanıcı verileri
│
├── tests/                     # Test dosyaları
│   └── test_preprocessing.py
│
└── notebooks/                 # Jupyter notebooks
    └── 01_data_exploration.ipynb
```

---

## 🔧 API Endpoints

Backend API (`http://localhost:5001/api`):

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/health` | GET | Sistem health check |
| `/search` | POST | Bug raporu arama |
| `/stats` | GET | İstatistikler |
| `/create_report` | POST | Yeni rapor oluştur |
| `/upload_data` | POST | Custom data yükle |
| `/data_status` | GET | Veri durumu |
| `/column_values/<column>` | GET | Sütun değerleri |
| `/available_datasets` | GET | Mevcut dataset'ler |
| `/load_dataset/<name>` | POST | Dataset yükle |

Detaylar için: [WEB_APP_README.md](WEB_APP_README.md)

---

## 🧪 Test

```bash
# Hybrid search testleri
python test_hybrid_search.py

# Preprocessing testleri
pytest tests/test_preprocessing.py

# API testleri (backend çalışır durumda olmalı)
curl http://localhost:5001/api/health
```

---

## 🎨 Tasarım ve UX

### Turkcell Renk Paleti
```css
--primary-color: #FFCC00;   /* Sarı */
--secondary-color: #000000; /* Siyah */
--warning-color: #FF9500;   /* Turuncu */
--accent-blue: #0A0E27;     /* Lacivert (arka plan) */
```

### Animasyonlar
- **Stars Background**: 100 animasyonlu yıldız
- **Glassmorphism**: Saydam, blur'lü card'lar
- **Hover Effects**: Glow ve transform efektleri
- **Loading States**: Smooth geçişler

---

## 🔐 Güvenlik Notları

⚠️ **Üretim ortamına geçmeden önce:**

1. **Şifreleri Değiştirin**: `login.html` içindeki demo şifreleri değiştirin
2. **CORS Ayarları**: `api_server.py` içinde CORS'u production için kısıtlayın
3. **Database**: CSV yerine gerçek bir veritabanı kullanın (PostgreSQL, MongoDB)
4. **Authentication**: JWT veya OAuth2 ekleyin
5. **HTTPS**: SSL sertifikası ile güvenli bağlantı

---

## 📝 Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

## 👨‍💻 Geliştirici

**Turkcell AI Team**

- 📧 Email: ai-team@turkcell.com.tr
- 🌐 Website: https://www.turkcell.com.tr

---

## 🙏 Teşekkürler

Bu proje aşağıdaki açık kaynak projeleri kullanmaktadır:

- [Sentence Transformers](https://www.sbert.net/) - Multilingual embeddings
- [FAISS](https://github.com/facebookresearch/faiss) - Similarity search
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Pandas](https://pandas.pydata.org/) - Data processing

---

## 📮 Destek

Sorularınız için:
- GitHub Issues açın
- Dokümantasyona bakın
- AI Team ile iletişime geçin

---

<div align="center">

**⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!**

Made with ❤️ by Turkcell AI Team

</div>
