JIRA Duplicate Detection System

AI-powered bug report duplicate detection system using semantic search and hybrid matching.

--Primary Objective

Automatically surface similar existing reports when a new bug report is submitted

Minimize duplicate bug reports

Improve the productivity of development and QA/testing teams

 ##Real-Time Data Management

Hugging Face Spaces: Data is stored and updated in real time on Hugging Face Spaces

Cloud-Based Embeddings: Embedding generation runs in Hugging Face Spaces

Automatic Synchronization: Two-way automatic sync between local systems and the cloud

## Features

- **Semantic Search**: FAISS-based vector similarity search
- **Hybrid Matching**: Bi-encoder + Cross-encoder re-ranking
- **Multi-language Support**: Turkish + English
- **User-specific Data**: Each user manages their own data, which is securely stored in isolated environments within Hugging Face Spaces.
All user-specific embeddings, session histories, and vector representations are maintained in separate namespaces, ensuring complete data isolation and privacy.
- **Feature Extraction**: Automatically extract metadata from text
- **Real-time Embedding**: Dynamic embedding generation

- 📤 Data Management

Custom Data Upload: Upload your own data via CSV/Excel

Dynamic Column Mapping: Choose which columns to compare

Dataset Selection: Switch between different datasets

User-Specific Data: Each user manages their own data

Cloud Storage: Data is securely stored on Hugging Face Spaces

Automatic Backup: Data is automatically backed up to the cloud

🔄 Duplicate Management

Replace Report: Replace an old report with a new one

Similarity Score: Detailed similarity scoring

Platform/Version Match: Filter by platform and version

Language Detection: Automatic language detection

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

## Security

- Firebase Authentication required
- User-specific data isolation

Quick Start

To get started quickly, visit:
https://jira-duplicate-detection.web.app/login.html

🧪 Demo Account

Email: test01@example.com

Password: test01

Note: The current demo account is reserved for Turkcell QA engineers. If you’re not within Turkcell, please create a new account and upload your own dataset to begin.

🚀 Alternative: Start with Your Own Account

Create a new account

Upload your data via CSV/Excel

##Getting Started with Your Own Data

Before uploading your CSV/Excel file, make sure to fill in column names that match your data (e.g., title, description, platform, version, etc.).

Once the upload is complete, embeddings are generated in real time.

Depending on dataset size, this may take a few minutes (typically ~5 min).

After processing finishes, you can start testing similarity searches.

  

## Support

GitHub: [Jira_Duplicate_Detection_Turkcell_](https://github.com/esraacevik/Jira_Duplicate_Detection_Turkcell_)

---

**Made with ❤️ for Turkcell**
