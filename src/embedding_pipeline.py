#!/usr/bin/env python3
"""
Embedding Pipeline for JIRA Bug Deduplication

This module generates embeddings for JIRA issues and creates FAISS indices
for efficient similarity search across different platforms (Android, iOS, Unknown).
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from tqdm import tqdm

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))
from utils import setup_logging

logger = logging.getLogger(__name__)

class EmbeddingPipeline:
    """Main embedding pipeline class"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 64):
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = None
        self.embeddings = None
        self.id_map = {}
        self.platform_indices = {}
        
    def load_model(self):
        """Load the sentence transformer model"""
        logger.info(f"Loading model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        logger.info(f"Model loaded successfully. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        
    def load_data(self, input_path: str) -> pd.DataFrame:
        """Load preprocessed data from parquet file"""
        logger.info(f"Loading data from: {input_path}")
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} records")
        
        # Ensure required columns exist
        required_cols = ['summary_clean', 'description_clean']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        # Create platform column from Component if it doesn't exist
        if 'platform' not in df.columns:
            if 'Component' in df.columns:
                # Map Component to platform
                def map_component_to_platform(component):
                    if pd.isna(component):
                        return 'unknown'
                    component_str = str(component).lower()
                    if 'android' in component_str:
                        return 'android'
                    elif 'ios' in component_str or 'iphone' in component_str:
                        return 'ios'
                    else:
                        return 'unknown'
                df['platform'] = df['Component'].apply(map_component_to_platform)
            else:
                # Default to 'unknown' if no Component column
                df['platform'] = 'unknown'
            
        return df
    
    def prepare_text(self, df: pd.DataFrame) -> List[str]:
        """Prepare text for embedding by combining summary and description"""
        texts = []
        for _, row in df.iterrows():
            summary = str(row.get('summary_clean', ''))
            description = str(row.get('description_clean', ''))
            
            # Combine summary and description
            combined_text = f"{summary}. {description}".strip()
            
            # Ensure case normalization for consistent embeddings
            combined_text = combined_text.lower()
            
            texts.append(combined_text)
            
        return texts
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for all texts"""
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        logger.info(f"Generated embeddings shape: {embeddings.shape}")
        return embeddings
    
    def create_platform_indices(self, df: pd.DataFrame, embeddings: np.ndarray) -> Dict[str, faiss.Index]:
        """Create separate FAISS indices for each platform"""
        logger.info("Creating platform-specific FAISS indices...")
        
        # Get unique platforms
        platforms = df['platform'].unique()
        logger.info(f"Found platforms: {platforms}")
        
        indices = {}
        embedding_dim = embeddings.shape[1]
        
        for platform in platforms:
            # Filter data for this platform
            platform_mask = df['platform'] == platform
            platform_embeddings = embeddings[platform_mask]
            
            if len(platform_embeddings) == 0:
                logger.warning(f"No embeddings found for platform: {platform}")
                continue
                
            # Create FAISS index
            index = faiss.IndexFlatIP(embedding_dim)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(platform_embeddings)
            index.add(platform_embeddings.astype('float32'))
            
            indices[platform] = index
            logger.info(f"Created index for {platform}: {len(platform_embeddings)} vectors")
            
        return indices
    
    def create_id_mapping(self, df: pd.DataFrame) -> Dict[str, int]:
        """Create mapping from original IDs to embedding indices"""
        id_map = {}
        for idx, row in df.iterrows():
            original_id = row.get('id', idx)  # Use 'id' column or fallback to index
            id_map[str(original_id)] = idx
            
        return id_map
    
    def save_outputs(self, output_dir: str, df: pd.DataFrame, embeddings: np.ndarray, 
                    id_map: Dict, indices: Dict[str, faiss.Index], config: Dict):
        """Save all pipeline outputs"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving outputs to: {output_dir}")
        
        # Save embeddings with original data
        df_with_embeddings = df.copy()
        df_with_embeddings['embedding'] = embeddings.tolist()
        df_with_embeddings.to_parquet(output_path / "with_embeddings.parquet")
        
        # Save raw embeddings
        np.save(output_path / "embeddings.npy", embeddings)
        
        # Save ID mapping
        with open(output_path / "id_map.json", 'w') as f:
            json.dump(id_map, f, indent=2)
            
        # Save FAISS indices
        for platform, index in indices.items():
            index_path = output_path / f"faiss_index_{platform.lower()}.index"
            faiss.write_index(index, str(index_path))
            logger.info(f"Saved FAISS index: {index_path}")
            
        # Save configuration
        with open(output_path / "config_used.json", 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info("All outputs saved successfully")
    
    def run_pipeline(self, input_path: str, output_dir: str, test_mode: bool = False):
        """Run the complete embedding pipeline"""
        logger.info("Starting embedding pipeline...")
        
        # Load model
        self.load_model()
        
        # Load data
        df = self.load_data(input_path)
        
        if test_mode:
            logger.info("Running in test mode - limiting to 1000 records")
            df = df.head(1000)
            
        # Prepare text
        texts = self.prepare_text(df)
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Create platform indices
        indices = self.create_platform_indices(df, embeddings)
        
        # Create ID mapping
        id_map = self.create_id_mapping(df)
        
        # Prepare configuration
        config = {
            "model_name": self.model_name,
            "batch_size": self.batch_size,
            "embedding_dimension": embeddings.shape[1],
            "total_records": len(df),
            "platforms": list(indices.keys()),
            "test_mode": test_mode
        }
        
        # Save outputs
        self.save_outputs(output_dir, df, embeddings, id_map, indices, config)
        
        logger.info("Embedding pipeline completed successfully!")
        return config

def main():
    parser = argparse.ArgumentParser(description="JIRA Bug Deduplication Embedding Pipeline")
    parser.add_argument("--input", required=True, help="Input parquet file path")
    parser.add_argument("--outputs", required=True, help="Output directory path")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Sentence transformer model name")
    parser.add_argument("--batch_size", type=int, default=64, help="Batch size for embedding generation")
    parser.add_argument("--test_mode", action="store_true", help="Run in test mode with limited data")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Create and run pipeline
    pipeline = EmbeddingPipeline(
        model_name=args.model,
        batch_size=args.batch_size
    )
    
    try:
        config = pipeline.run_pipeline(
            input_path=args.input,
            output_dir=args.outputs,
            test_mode=args.test_mode
        )
        
        print("\n✅ Embedding pipeline completed successfully!")
        print(f"📊 Processed {config['total_records']} records")
        print(f"🔧 Model: {config['model_name']}")
        print(f"📐 Embedding dimension: {config['embedding_dimension']}")
        print(f"📱 Platforms: {config['platforms']}")
        print(f"📁 Output directory: {args.outputs}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
