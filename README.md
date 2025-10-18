---
title: JIRA Duplicate Detection
emoji: 🔍
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# 🔍 JIRA Duplicate Detection System

AI-powered bug report duplicate detection system using semantic search and hybrid matching.

## 🎯 Features

- **Semantic Search**: FAISS-based vector similarity search
- **Hybrid Matching**: Bi-encoder + Cross-encoder re-ranking
- **Multi-language Support**: Turkish + English
- **User-specific Data**: Each user manages their own data
- **Feature Extraction**: Automatically extract metadata from text
- **Real-time Embedding**: Dynamic embedding generation

## 🚀 API Endpoints

### Health Check
```
GET /api/health
```

### Search Similar Reports
```
POST /api/search
```

### Upload Data
```
POST /api/upload_data
```

### Extract Features
```
POST /api/extract_features
```

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **AI/ML**: sentence-transformers, FAISS, scikit-learn
- **Frontend**: HTML/CSS/JavaScript
- **Auth**: Firebase Authentication
- **Hosting**: Hugging Face Spaces (Docker)

## 📖 Documentation

- [Feature Extraction Guide](./FEATURE_EXTRACTION_GUIDE.md)
- [Hugging Face Deployment](./HUGGINGFACE_DEPLOY.md)
- [User Guide](./KULLANIM_KILAVUZU.md)

## 🔐 Security

- Firebase Authentication required
- User-specific data isolation
- No default data loaded

## 📞 Support

GitHub: [Jira_Duplicate_Detection_Turkcell_](https://github.com/esraacevik/Jira_Duplicate_Detection_Turkcell_)

---

**Made with ❤️ for Turkcell**
