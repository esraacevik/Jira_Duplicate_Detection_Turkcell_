#!/usr/bin/env python3
"""
User-Specific Embedding Pipeline
==================================
Her kullanıcının kendi verisi için embedding oluşturur.
Kullanıcılar birbirlerinin verilerini göremez.
"""

import pandas as pd
import numpy as np
import faiss
import os
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserEmbeddingPipeline:
    """Kullanıcıya özel embedding pipeline"""
    
    def __init__(self, user_id, model_name='paraphrase-multilingual-MiniLM-L12-v2', use_firebase_cache=True):
        """
        Args:
            user_id: Firebase user ID veya unique user identifier
            model_name: Embedding model adı
            use_firebase_cache: Firebase Storage cache kullanılsın mı?
        """
        self.user_id = user_id
        self.model_name = model_name
        self.model = None
        self.use_firebase_cache = use_firebase_cache
        
        # Kullanıcı için özel klasör - use /tmp in production (Hugging Face Spaces)
        import os
        data_base_dir = os.getenv('DATA_DIR', '/tmp' if os.getenv('SPACE_ID') else 'data')
        self.user_dir = Path(f"{data_base_dir}/user_embeddings/{user_id}")
        self.user_dir.mkdir(parents=True, exist_ok=True)
        
        # Firebase Storage Manager
        self.storage_manager = None
        if use_firebase_cache:
            try:
                from firebase_storage_manager import get_storage_manager
                self.storage_manager = get_storage_manager()
            except Exception as e:
                logger.warning(f"⚠️  Firebase Storage not available: {e}")
        
        logger.info(f"🔧 User Embedding Pipeline initialized for user: {user_id}")
    
    def load_model(self):
        """Embedding modelini yükle"""
        if self.model is None:
            logger.info(f"📥 Loading embedding model: {self.model_name}")
            # Use /tmp for cache on Hugging Face Spaces (writeable directory)
            cache_folder = '/tmp/sentence_transformers_cache'
            os.makedirs(cache_folder, exist_ok=True)
            self.model = SentenceTransformer(self.model_name, cache_folder=cache_folder)
            logger.info("✅ Model loaded successfully")
        return self.model
    
    def create_embeddings(self, df, text_columns=['Summary', 'Description']):
        """
        DataFrame'den embedding oluştur
        
        Args:
            df: Pandas DataFrame (kullanıcının verisi)
            text_columns: Embedding için kullanılacak text sütunları
        
        Returns:
            embeddings: numpy array (N x embedding_dim)
        """
        logger.info(f"🔄 Creating embeddings for {len(df)} records...")
        logger.info(f"📝 Using columns: {text_columns}")
        
        # Model'i yükle
        model = self.load_model()
        
        # Text'leri birleştir
        texts = []
        for _, row in df.iterrows():
            text_parts = []
            for col in text_columns:
                if col in df.columns and pd.notna(row[col]):
                    text_parts.append(str(row[col]))
            
            combined_text = '. '.join(text_parts).strip().lower()
            texts.append(combined_text if combined_text else 'empty')
        
        # Embeddings oluştur
        logger.info("🤖 Generating embeddings...")
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        logger.info(f"✅ Embeddings created: {embeddings.shape}")
        
        # Kaydet
        embeddings_path = self.user_dir / "embeddings.npy"
        np.save(embeddings_path, embeddings)
        logger.info(f"💾 Saved embeddings to: {embeddings_path}")
        
        return embeddings
    
    def create_faiss_index(self, embeddings):
        """
        FAISS index oluştur
        
        Args:
            embeddings: numpy array
        
        Returns:
            index: FAISS index
        """
        logger.info("🔄 Creating FAISS index...")
        
        # Normalize embeddings (cosine similarity için)
        normalized_embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # FAISS index oluştur (Inner Product - cosine similarity)
        embedding_dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(embedding_dim)
        
        # Embeddings'leri ekle
        index.add(normalized_embeddings.astype('float32'))
        
        logger.info(f"✅ FAISS index created: {index.ntotal} vectors")
        
        # Kaydet
        index_path = self.user_dir / "faiss_index.index"
        faiss.write_index(index, str(index_path))
        logger.info(f"💾 Saved FAISS index to: {index_path}")
        
        return index
    
    def save_metadata(self, df, text_columns, config=None):
        """
        Metadata kaydet
        
        Args:
            df: DataFrame
            text_columns: Kullanılan text sütunları
            config: Ek konfigürasyon (opsiyonel)
        """
        current_time = pd.Timestamp.now().isoformat()
        metadata = {
            'user_id': self.user_id,
            'num_records': len(df),
            'recordCount': len(df),  # For compatibility
            'num_columns': len(df.columns),
            'columns': df.columns.tolist(),
            'textColumns': text_columns,  # For compatibility
            'text_columns': text_columns,
            'metadataColumns': (config or {}).get('metadataColumns', []),
            'fileName': (config or {}).get('fileName', 'uploaded_data.csv'),
            'model_name': self.model_name,
            'embedding_dim': self.model.get_sentence_embedding_dimension() if self.model else None,
            'created_at': current_time,
            'createdAt': current_time,  # For compatibility
            'config': config or {}
        }
        
        metadata_path = self.user_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"💾 Saved metadata to: {metadata_path}")
    
    def process(self, df, text_columns=None, config=None):
        """
        Tam pipeline: embedding + FAISS index oluştur
        
        FIREBASE CACHE SYSTEM:
        1. Firebase Storage'da artifacts varsa indir ve kullan
        2. Yoksa embedding yap ve Firebase'e upload et
        
        Args:
            df: Pandas DataFrame
            text_columns: Text sütunları (None ise otomatik tespit)
            config: Ek konfigürasyon
        
        Returns:
            success: bool
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🚀 Starting User Embedding Pipeline for: {self.user_id}")
            logger.info(f"{'='*60}\n")
            
            # ===== FIREBASE CACHE CHECK =====
            if self.use_firebase_cache and self.storage_manager and self.storage_manager.initialized:
                logger.info("🔍 Checking Firebase Storage for cached embeddings...")
                
                # Check if artifacts exist in Firebase
                artifacts_exist = self.storage_manager.check_artifacts_exist(self.user_id)
                
                if artifacts_exist:
                    logger.info("✅ Found cached embeddings in Firebase Storage!")
                    
                    # Download artifacts from Firebase
                    download_success = self.storage_manager.download_user_artifacts(
                        self.user_id, 
                        self.user_dir
                    )
                    
                    if download_success:
                        logger.info("✅ Successfully downloaded embeddings from Firebase!")
                        logger.info("⏩ Skipping embedding generation - using cached version")
                        return True
                    else:
                        logger.warning("⚠️  Download failed, will regenerate embeddings")
                else:
                    logger.info("📝 No cached embeddings found, will generate new ones")
            
            # ===== GENERATE NEW EMBEDDINGS =====
            # Text sütunlarını tespit et
            if text_columns is None:
                text_columns = self._detect_text_columns(df)
            
            logger.info(f"📊 Data shape: {df.shape}")
            logger.info(f"📝 Text columns: {text_columns}")
            
            # 1. Embeddings oluştur
            embeddings = self.create_embeddings(df, text_columns)
            
            # 2. FAISS index oluştur
            self.create_faiss_index(embeddings)
            
            # 3. Metadata kaydet
            self.save_metadata(df, text_columns, config)
            
            # 4. Upload to Firebase Storage (if enabled)
            if self.use_firebase_cache and self.storage_manager and self.storage_manager.initialized:
                logger.info("📤 Uploading embeddings to Firebase Storage...")
                
                upload_success = self.storage_manager.upload_user_artifacts(
                    self.user_id, 
                    self.user_dir
                )
                
                if upload_success:
                    logger.info("✅ Embeddings cached to Firebase Storage!")
                else:
                    logger.warning("⚠️  Firebase upload failed, but local artifacts are saved")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Pipeline completed successfully!")
            logger.info(f"📁 Output directory: {self.user_dir}")
            logger.info(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _detect_text_columns(self, df):
        """Otomatik text sütunlarını tespit et"""
        text_keywords = ['summary', 'description', 'title', 'özet', 'açıklama', 'başlık', 'content']
        text_columns = []
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in text_keywords):
                text_columns.append(col)
        
        # En az 1 sütun bulunmalı
        if not text_columns:
            # İlk string sütunu kullan
            for col in df.columns:
                if df[col].dtype == 'object':
                    text_columns.append(col)
                    if len(text_columns) >= 2:
                        break
        
        return text_columns if text_columns else [df.columns[0]]


def create_user_embeddings(user_id, df, text_columns=None, config=None):
    """
    Kullanıcı için embedding oluştur (helper function)
    
    Args:
        user_id: User ID
        df: DataFrame
        text_columns: Text sütunları (None ise otomatik)
        config: Konfigürasyon
    
    Returns:
        success: bool
    """
    pipeline = UserEmbeddingPipeline(user_id)
    return pipeline.process(df, text_columns, config)


if __name__ == "__main__":
    # Test için örnek kullanım
    print("🧪 Testing User Embedding Pipeline...")
    
    # Örnek veri
    test_data = pd.DataFrame({
        'Summary': ['Test bug 1', 'Test bug 2', 'Test bug 3'],
        'Description': ['Desc 1', 'Desc 2', 'Desc 3'],
        'Priority': ['High', 'Medium', 'Low']
    })
    
    # Test kullanıcısı için pipeline
    success = create_user_embeddings(
        user_id='test_user_123',
        df=test_data,
        text_columns=['Summary', 'Description']
    )
    
    if success:
        print("✅ Test successful!")
    else:
        print("❌ Test failed!")

