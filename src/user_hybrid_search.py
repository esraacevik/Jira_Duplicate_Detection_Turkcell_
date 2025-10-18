#!/usr/bin/env python3
"""
User-Specific Hybrid Search
============================
Kullanıcıya özel embeddings kullanarak hybrid search
"""

import numpy as np
import pandas as pd
import faiss
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserHybridSearch:
    """Kullanıcıya özel hybrid search sistemi"""
    
    def __init__(self, user_id):
        """
        Args:
            user_id: Firebase user ID veya unique user identifier
        """
        self.user_id = user_id
        self.user_dir = Path(f"data/user_embeddings/{user_id}")
        
        self.bi_encoder = None
        self.cross_encoder = None
        self.faiss_index = None
        self.embeddings = None
        self.metadata = None
        self.df = None
        
        logger.info(f"🔍 User Hybrid Search initialized for: {user_id}")
    
    def load_models(self):
        """Load models"""
        if self.bi_encoder is None:
            logger.info("📥 Loading bi-encoder...")
            self.bi_encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        if self.cross_encoder is None:
            logger.info("📥 Loading cross-encoder...")
            self.cross_encoder = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')
    
    def load_user_data(self):
        """Load user's embeddings, FAISS index, and metadata"""
        try:
            # Load metadata
            metadata_path = self.user_dir / "metadata.json"
            if not metadata_path.exists():
                raise FileNotFoundError(f"Metadata not found for user: {self.user_id}")
            
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
            
            logger.info(f"✅ Loaded metadata: {self.metadata['num_records']} records")
            
            # Load embeddings
            embeddings_path = self.user_dir / "embeddings.npy"
            self.embeddings = np.load(embeddings_path)
            logger.info(f"✅ Loaded embeddings: {self.embeddings.shape}")
            
            # Load FAISS index
            index_path = self.user_dir / "faiss_index.index"
            self.faiss_index = faiss.read_index(str(index_path))
            logger.info(f"✅ Loaded FAISS index: {self.faiss_index.ntotal} vectors")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading user data: {e}")
            return False
    
    def search(self, query, df=None, top_k=10, rerank_k=50):
        """
        Hybrid search: FAISS + Cross-Encoder
        
        Args:
            query: Search query string
            df: DataFrame (kullanıcının verisi)
            top_k: Final sonuç sayısı
            rerank_k: FAISS'ten kaç candidate alınacak
        
        Returns:
            results: List of dicts
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 User Hybrid Search: {self.user_id}")
            logger.info(f"📝 Query: {query[:50]}...")
            logger.info(f"{'='*60}\n")
            
            # Load models
            self.load_models()
            
            # Load user data
            if not self.load_user_data():
                return []
            
            # Encode query
            logger.info("🔄 Encoding query...")
            query_embedding = self.bi_encoder.encode([query.lower()], convert_to_numpy=True)
            
            # Normalize for cosine similarity
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            
            # FAISS search (Stage 1)
            logger.info(f"🔍 FAISS search (top {rerank_k} candidates)...")
            scores, indices = self.faiss_index.search(query_embedding.astype('float32'), rerank_k)
            
            candidates = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(df):
                    candidates.append({
                        'index': int(idx),
                        'faiss_score': float(score),
                        'row': df.iloc[idx].to_dict()
                    })
            
            logger.info(f"✅ Found {len(candidates)} candidates from FAISS")
            
            # Cross-Encoder re-ranking (Stage 2)
            if len(candidates) > 0:
                logger.info("🔄 Cross-Encoder re-ranking...")
                
                # Prepare pairs for cross-encoder
                text_col = self.metadata['text_columns'][0] if self.metadata['text_columns'] else df.columns[0]
                pairs = []
                for candidate in candidates:
                    row_text = str(candidate['row'].get(text_col, ''))
                    pairs.append([query, row_text])
                
                # Get cross-encoder scores
                ce_scores = self.cross_encoder.predict(pairs)
                
                # Add scores to candidates
                for i, candidate in enumerate(candidates):
                    candidate['cross_encoder_score'] = float(ce_scores[i])
                    candidate['final_score'] = float(ce_scores[i])  # Can be combined with FAISS score
                
                # Sort by final score
                candidates.sort(key=lambda x: x['final_score'], reverse=True)
                
                logger.info(f"✅ Re-ranking completed")
            
            # Format results
            results = []
            for candidate in candidates[:top_k]:
                result = {
                    'index': candidate['index'],
                    'final_score': candidate['final_score'],
                    'cross_encoder_score': candidate['cross_encoder_score'],
                    'faiss_score': candidate['faiss_score'],
                    'version_similarity': 1.0,
                    'platform_match': True,
                    'language_match': True
                }
                
                # Add all row data
                result.update(candidate['row'])
                
                results.append(result)
            
            logger.info(f"✅ Returning {len(results)} results\n")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            import traceback
            traceback.print_exc()
            return []


def search_user_data(user_id, query, df, top_k=10):
    """
    Helper function for user hybrid search
    
    Args:
        user_id: User ID
        query: Search query
        df: User's DataFrame
        top_k: Number of results
    
    Returns:
        results: List of dicts
    """
    searcher = UserHybridSearch(user_id)
    return searcher.search(query, df, top_k)

