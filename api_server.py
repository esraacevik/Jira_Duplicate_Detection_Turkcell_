#!/usr/bin/env python3
"""
Bug Report Duplicate Detection API Server
==========================================
Flask API server for the hybrid search system
"""

import os
# Set cache directories for Hugging Face models BEFORE importing transformers/sentence-transformers
os.environ['HF_HOME'] = '/tmp/huggingface_cache'
os.environ['TRANSFORMERS_CACHE'] = '/tmp/transformers_cache'
os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/tmp/sentence_transformers_cache'

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from hybrid_search import HybridSearch
import logging
from typing import Dict, List, Optional
import time
from pathlib import Path
from src.text_feature_extractor import TextFeatureExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Increase max request size to 100MB (for large CSV uploads)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

# Initialize search system (singleton)
search_system = None

# Global variable to store custom uploaded data PER USER
# Structure: user_data_stores[user_id] = { data, fileName, rowCount, ... }
user_data_stores = {}

# Initialize feature extractor
feature_extractor = TextFeatureExtractor()

# Data directory - use /tmp in production (Hugging Face Spaces), data/ locally
DATA_BASE_DIR = os.getenv('DATA_DIR', '/tmp' if os.getenv('SPACE_ID') else 'data')

def get_user_data_store(user_id: str) -> dict:
    """Get data store for a specific user - loads from disk if exists"""
    if user_id not in user_data_stores:
        # Check if user has data on disk
        user_embeddings_dir = Path(DATA_BASE_DIR) / 'user_embeddings' / user_id
        metadata_file = user_embeddings_dir / 'metadata.json'
        
        if metadata_file.exists():
            # Load from disk
            try:
                import json
                import pandas as pd
                
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Load the original data if available
                data_file = user_embeddings_dir / 'data.csv'
                df = None
                if data_file.exists():
                    df = pd.read_csv(data_file)
                    logger.info(f"📂 Loaded user data from disk for user: {user_id} ({len(df)} rows)")
                
                # Reconstruct user_data_store from metadata
                user_data_stores[user_id] = {
                    'data': df,
                    'fileName': metadata.get('fileName', 'uploaded_data.csv'),
                    'rowCount': metadata.get('recordCount', len(df) if df is not None else 0),
                    'columns': metadata.get('textColumns', []),
                    'selectedColumns': metadata.get('textColumns', []),
                    'metadataColumns': metadata.get('metadataColumns', []),
                    'uploadedAt': metadata.get('createdAt'),
                    'loaded': df is not None,
                    'userId': user_id,
                    'embeddingsCreated': True,  # If metadata exists, embeddings were created
                    'embeddingsReady': True,
                    'embeddingsPath': str(user_embeddings_dir)
                }
                logger.info(f"✅ Restored user data store from disk for user: {user_id}")
            except Exception as e:
                logger.error(f"❌ Error loading user data from disk: {e}")
                # Fall through to create empty store
                user_data_stores[user_id] = {
    'data': None,
    'fileName': None,
    'rowCount': 0,
    'columns': [],
                    'selectedColumns': [],
                    'metadataColumns': [],
    'uploadedAt': None,
                    'loaded': False,
                    'userId': user_id
                }
        else:
            # Create empty store
            user_data_stores[user_id] = {
                'data': None,
                'fileName': None,
                'rowCount': 0,
                'columns': [],
                'selectedColumns': [],
                'metadataColumns': [],
                'uploadedAt': None,
                'loaded': False,
                'userId': user_id
            }
    return user_data_stores[user_id]

def set_user_data_store(user_id: str, data_store: dict):
    """Set data store for a specific user"""
    data_store['userId'] = user_id
    user_data_stores[user_id] = data_store

def clear_user_data_store(user_id: str):
    """Clear data store for a specific user"""
    if user_id in user_data_stores:
        del user_data_stores[user_id]
    logger.info(f"✅ Custom data cleared for user: {user_id}")

def get_search_system():
    """Get or initialize the search system"""
    global search_system
    if search_system is None:
        logger.info("🚀 Initializing Hybrid Search System...")
        search_system = HybridSearch()
        logger.info("✅ Search system ready!")
    return search_system


def update_embeddings_for_new_report(new_row_index):
    """
    Update embeddings and FAISS indices for a newly added report
    
    Args:
        new_row_index: Index of the new row in the DataFrame (0-based)
    """
    global search_system
    
    if search_system is None:
        logger.warning("⚠️ Search system not initialized, cannot update embeddings")
        return
    
    try:
        import numpy as np
        import faiss
        from pathlib import Path
        
        # Reload DataFrame to get the new report
        logger.info(f"📥 Reloading data to include new report...")
        search_system.load_data()
        
        # Get the new row
        if new_row_index >= len(search_system.df):
            logger.error(f"❌ Invalid row index: {new_row_index}, DataFrame has {len(search_system.df)} rows")
            return
        
        new_row = search_system.df.iloc[new_row_index]
        
        # Generate embedding for the new report
        logger.info(f"🔄 Generating embedding for new report: '{new_row.get('Summary', '')[:50]}...'")
        summary = str(new_row.get('Summary', ''))
        description = str(new_row.get('Description', ''))
        combined_text = f"{summary}. {description}".strip().lower()
        
        new_embedding = search_system.bi_encoder.encode(
            [combined_text],
            batch_size=1,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Load existing embeddings
        embeddings_path = Path(search_system.embeddings_dir) / "embeddings.npy"
        if embeddings_path.exists():
            existing_embeddings = np.load(embeddings_path)
            logger.info(f"📊 Loaded existing embeddings: {existing_embeddings.shape}")
            
            # Append new embedding
            updated_embeddings = np.vstack([existing_embeddings, new_embedding])
            logger.info(f"✅ New embeddings shape: {updated_embeddings.shape}")
            
            # Save updated embeddings
            np.save(embeddings_path, updated_embeddings)
            logger.info(f"💾 Saved updated embeddings to {embeddings_path}")
            
            # Update in-memory embeddings
            search_system.embeddings = updated_embeddings
            
            # Add to FAISS index
            platform = str(new_row.get('Platform', 'unknown')).lower()
            if platform not in ['android', 'ios', 'unknown']:
                platform = 'unknown'
            
            logger.info(f"🔄 Adding to FAISS index: {platform}")
            
            if platform in search_system.faiss_indices:
                # Normalize the embedding (FAISS uses cosine similarity with normalized vectors)
                normalized_embedding = new_embedding / np.linalg.norm(new_embedding)
                
                # Add to FAISS index
                search_system.faiss_indices[platform].add(normalized_embedding.astype('float32'))
                
                # Save updated FAISS index
                index_path = Path(search_system.embeddings_dir) / f"faiss_index_{platform}.index"
                faiss.write_index(search_system.faiss_indices[platform], str(index_path))
                logger.info(f"💾 Saved updated FAISS index to {index_path}")
                
                logger.info(f"✅ Successfully added new report to FAISS index ({platform})")
            else:
                logger.warning(f"⚠️ FAISS index not found for platform: {platform}")
        else:
            logger.warning(f"⚠️ Embeddings file not found: {embeddings_path}")
            logger.warning("⚠️ Please run embedding pipeline to generate embeddings")
            
    except Exception as e:
        logger.error(f"❌ Error updating embeddings: {e}")
        import traceback
        traceback.print_exc()
        raise


def search_custom_data(query, df, top_k=10, selected_columns=None, user_id=None):
    """
    Hybrid search on custom data using user's embeddings
    Falls back to text-based search if embeddings not available
    
    Args:
        query: Search query
        df: Custom DataFrame
        top_k: Number of results to return
        selected_columns: List of columns selected by user for search (priority)
        user_id: User ID (for loading embeddings)
    """
    import pandas as pd
    from difflib import SequenceMatcher
    import sys
    import os
    
    # Try hybrid search with embeddings first
    if user_id:
        try:
            # Add src to path
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
            from user_hybrid_search import search_user_data
            
            logger.info(f"🚀 Using Hybrid Search with embeddings for user: {user_id}")
            results = search_user_data(user_id, query, df, top_k)
            
            if results and len(results) > 0:
                logger.info(f"✅ Hybrid search returned {len(results)} results")
                return results
            else:
                logger.warning(f"⚠️ Hybrid search returned no results, falling back to text search")
        
        except Exception as e:
            logger.warning(f"⚠️ Hybrid search failed: {e}, falling back to text search")
    
    # Fallback: Simple text-based search
    logger.info(f"🔍 Using fallback text-based search")
    
    results = []
    query_lower = query.lower()
    
    # Determine which columns to search in
    text_columns = []
    
    # Priority 1: Use selected columns if provided
    if selected_columns and len(selected_columns) > 0:
        text_columns = [col for col in selected_columns if col in df.columns]
        logger.info(f"🎯 Using user-selected columns for search: {text_columns}")
    
    # Priority 2: Auto-detect text columns if no selection
    if not text_columns:
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['summary', 'description', 'title', 'özet', 'açıklama', 'başlık']):
                text_columns.append(col)
        logger.info(f"🔍 Auto-detected text columns: {text_columns}")
    
    # Priority 3: Use all string columns as fallback
    if not text_columns:
        text_columns = df.select_dtypes(include=['object']).columns.tolist()[:2]
        logger.info(f"⚠️ Using fallback columns: {text_columns}")
    
    logger.info(f"🔍 Searching in columns: {text_columns}")
    
    # Calculate similarity scores for each row
    for idx, row in df.iterrows():
        # Combine text from searchable columns
        text_parts = []
        for col in text_columns:
            if pd.notna(row[col]):
                text_parts.append(str(row[col]))
        
        combined_text = ' '.join(text_parts).lower()
        
        # Calculate similarity score (simple string matching)
        score = SequenceMatcher(None, query_lower, combined_text).ratio() * 10
        
        # Boost score if query words appear in text
        query_words = query_lower.split()
        word_matches = sum(1 for word in query_words if word in combined_text)
        score += word_matches * 2
        
        if score > 1.0:  # Minimum threshold
            # Build result object
            result = {
                'final_score': score,
                'cross_encoder_score': score,
                'version_similarity': 1.0,
                'platform_match': True,
                'language_match': True,
                'index': int(idx)
            }
            
            # Add all columns from the row
            for col in df.columns:
                # Map column names to expected format
                col_snake = col.lower().replace(' ', '_').replace('(', '').replace(')', '')
                result[col_snake] = row[col] if pd.notna(row[col]) else ''
            
            # Ensure required fields exist
            if 'summary' not in result:
                result['summary'] = result.get(text_columns[0].lower().replace(' ', '_'), 'N/A') if text_columns else 'N/A'
            if 'description' not in result:
                result['description'] = result.get(text_columns[1].lower().replace(' ', '_'), '') if len(text_columns) > 1 else ''
            if 'app_version' not in result:
                result['app_version'] = ''
            if 'platform' not in result:
                result['platform'] = 'unknown'
            if 'application' not in result:
                result['application'] = 'Custom'
            if 'priority' not in result:
                result['priority'] = 'medium'
            
            results.append(result)
    
    # Sort by score and return top_k
    results.sort(key=lambda x: x['final_score'], reverse=True)
    return results[:top_k]


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Bug Report API is running',
        'version': '1.0.0'
    })


@app.route('/api/search', methods=['POST'])
@cross_origin()
def search_reports():
    """
    Search for similar bug reports
    
    Request Body:
    {
        "query": str,              # Required: search query
        "application": str,        # Optional: BiP, TV+, Fizy, etc.
        "platform": str,           # Optional: android, ios
        "version": str,            # Optional: e.g., "3.70.19"
        "language": str,           # Optional: tr, en
        "top_k": int              # Optional: number of results (default: 10)
    }
    
    Response:
    {
        "success": bool,
        "query": str,
        "results": [...],
        "count": int,
        "search_time": float
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: query'
            }), 400
        
        query = data['query'].strip()
        
        if len(query) < 10:
            return jsonify({
                'success': False,
                'error': 'Query must be at least 10 characters long'
            }), 400
        
        # Extract search parameters
        application = data.get('application') or None
        platform = data.get('platform') or None
        version = data.get('version') or None
        language = data.get('language') or None
        top_k = data.get('top_k', 10)
        selected_columns = data.get('selected_columns', ['Summary', 'Description'])  # Get from frontend
        
        # Validate top_k
        if not isinstance(top_k, int) or top_k < 1 or top_k > 50:
            top_k = 10
        
        # Get user_id from request (required for user-specific search)
        user_id = data.get('user_id', 'anonymous')
        
        logger.info(f"🔍 Search request: query='{query[:50]}...', app={application}, platform={platform}, user_id={user_id}")
        
        # Get user-specific data store
        user_store = get_user_data_store(user_id)
        
        if user_store['loaded'] and user_store['data'] is not None:
            # Use custom data for search (hybrid search with user embeddings)
            cols_to_use = selected_columns if selected_columns != ['Summary', 'Description'] else user_store.get('selectedColumns', selected_columns)
            
            logger.info(f"📤 Using custom uploaded data: {user_store['fileName']}")
            logger.info(f"👤 User ID: {user_id}")
            logger.info(f"🎯 Selected columns for search: {cols_to_use}")
            
            start_time = time.time()
            results = search_custom_data(
                query, 
                user_store['data'], 
                top_k,
                selected_columns=cols_to_use,
                user_id=user_id  # Pass user_id for embedding-based search
            )
            search_time = time.time() - start_time
            logger.info(f"✅ Found {len(results)} results in custom data in {search_time:.2f}s")
        else:
            # No data loaded - user must upload their own data
            logger.warning(f"⚠️  No data uploaded for user: {user_id}")
            return jsonify({
                'success': False,
                'error': 'No data uploaded. Please upload your data first.',
                'message': 'You must upload your data before searching. Go to Data Upload page.',
                'userId': user_id
            }), 400
        
        # Clean NaN values from results (JSON doesn't support NaN)
        import math
        def clean_nan(obj):
            """Recursively replace NaN values with None or 0"""
            if isinstance(obj, dict):
                return {k: clean_nan(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan(item) for item in obj]
            elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
                return 0.0  # Replace NaN/Inf with 0
            else:
                return obj
        
        cleaned_results = clean_nan(results)
        
        # Return results
        return jsonify({
            'success': True,
            'query': query,
            'filters': {
                'application': application,
                'platform': platform,
                'version': version,
                'language': language
            },
            'results': cleaned_results,
            'count': len(cleaned_results),
            'search_time': round(search_time, 2)
        })
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get system statistics
    
    Response:
    {
        "total_reports": int,
        "platforms": {...},
        "applications": {...}
    }
    """
    try:
        # Get user_id from query parameter
        user_id = request.args.get('user_id', 'anonymous')
        
        # Get user-specific data store
        user_store = get_user_data_store(user_id)
        
        if user_store['loaded'] and user_store['data'] is not None:
            df = user_store['data']
            logger.info(f"📊 Getting stats from custom data for user {user_id}: {len(df)} rows")
            
            # Calculate statistics from custom data
            stats = {
                'total_reports': len(df),
                'platforms': {},
                'applications': {}
            }
            
            # Try to get platform info if column exists
            if 'Platform' in df.columns:
                stats['platforms'] = {
                    'android': int((df['Platform'].str.lower() == 'android').sum()),
                    'ios': int((df['Platform'].str.lower() == 'ios').sum()),
                    'unknown': int((~df['Platform'].str.lower().isin(['android', 'ios'])).sum())
                }
            
            # Try to get application info if column exists
            if 'Application' in df.columns:
                stats['applications'] = df['Application'].value_counts().to_dict()
            
            return jsonify({
                'success': True,
                'stats': stats,
                'customDataLoaded': True,
                'fileName': user_store['fileName'],
                'userId': user_id
            })
        else:
            # No data loaded for this user
            logger.info(f"⚠️  No data loaded for user: {user_id}")
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_reports': 0,
                    'platforms': {},
                    'applications': {}
                },
                'customDataLoaded': False,
                'message': 'No data uploaded. Please upload your data first.',
                'userId': user_id
            })
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/applications', methods=['GET'])
def get_applications():
    """Get list of available applications"""
    try:
        # Check if custom data is loaded
        if custom_data_store['loaded'] and custom_data_store['data'] is not None:
            df = custom_data_store['data']
            
            if 'Application' not in df.columns:
                applications = []
            else:
                applications = sorted(df['Application'].unique().tolist())
            
            return jsonify({
                'success': True,
                'applications': applications
            })
        else:
            # No data loaded
            return jsonify({
                'success': True,
                'applications': []
            })
        
    except Exception as e:
        logger.error(f"❌ Applications error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/applications_OLD', methods=['GET'])
def get_applications_old():
    """Get list of available applications - OLD VERSION"""
    try:
        search = get_search_system()
        
        if 'Application' not in search.df.columns:
            applications = []
        else:
            applications = sorted(search.df['Application'].unique().tolist())
        
        return jsonify({
            'success': True,
            'applications': applications
        })
        
    except Exception as e:
        logger.error(f"❌ Applications error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/create_report', methods=['POST'])
@cross_origin()
def create_report():
    """
    Create a new bug report and append to CSV
    
    Request Body:
    {
        "summary": str,
        "description": str,
        "component": str,
        "affects_version": str,
        "app_version": str,
        "priority": str,
        "severity": str,
        "frequency": str,
        "issue_type": str,
        "problem_type": str
    }
    """
    try:
        import pandas as pd
        import os
        from datetime import datetime
        
        # Get request data
        data = request.get_json()
        
        import uuid
        request_id = str(uuid.uuid4())[:8]
        
        logger.info(f"[{request_id}] 📥 Received create_report request with data keys: {list(data.keys()) if data else 'None'}")
        logger.info(f"[{request_id}] 📝 Full data: {data}")
        
        if data and 'replace_report' in data:
            logger.info(f"[{request_id}] 🔍 replace_report parameter found: {data.get('replace_report')}")
            logger.info(f"[{request_id}] 🔍 old_report_summary parameter: {data.get('old_report_summary')}")
        
        if not data:
            logger.error(f"[{request_id}] ❌ VALIDATION FAILED: No data received!")
            return jsonify({
                'success': False,
                'error': 'No data received'
            }), 400
        
        if 'summary' not in data:
            logger.error(f"[{request_id}] ❌ VALIDATION FAILED: Missing summary field. Data keys: {list(data.keys())}")
            return jsonify({
                'success': False,
                'error': 'Missing required field: summary'
            }), 400
        
        logger.info(f"[{request_id}] ✅ Validation passed: summary found = '{data['summary']}'")
        
        # Get user_id from request
        user_id = data.get('userId') or data.get('user_id', 'anonymous')
        logger.info(f"👤 Create report request from user: {user_id}")
        
        # Check if we're replacing an old report
        replace_report = data.get('replace_report', False)
        old_report_summary = data.get('old_report_summary', '')
        old_report_id = data.get('old_report_id', '')
        
        logger.info(f"🎯 replace_report={replace_report}, old_report_summary='{old_report_summary}'")
        
        # DEBUG: Check user store status
        user_store = get_user_data_store(user_id)
        logger.info(f"🔍 DEBUG user_store: loaded={user_store.get('loaded')}, data_is_none={user_store.get('data') is None}")
        if user_store.get('data') is not None:
            logger.info(f"🔍 DEBUG user_store data shape: {user_store['data'].shape}")
        
        # Detect application from summary
        summary_lower = data['summary'].lower()
        application = 'Unknown'
        if 'bip' in summary_lower:
            application = 'BiP'
        elif 'tv+' in summary_lower or 'tv plus' in summary_lower:
            application = 'TV+'
        elif 'fizy' in summary_lower:
            application = 'Fizy'
        elif 'paycell' in summary_lower:
            application = 'Paycell'
        elif 'lifebox' in summary_lower:
            application = 'LifeBox'
        elif 'hesabım' in summary_lower or 'hesabim' in summary_lower:
            application = 'Hesabım'
        elif 'dergilik' in summary_lower:
            application = 'Dergilik'
        
        # Extract app version enhanced (same logic as enhanced_version_extraction.py)
        app_version_enhanced = data.get('app_version', '')
        if not app_version_enhanced and data.get('affects_version'):
            # Try to extract from affects version
            import re
            version_match = re.search(r'(\d+\.\d+\.\d+)', data.get('affects_version', ''))
            if version_match:
                app_version_enhanced = version_match.group(1)
        
        # Create new row matching CSV format
        new_row = {
            'Affects Version': data.get('affects_version', ''),
            'Component': data.get('component', ''),
            'Description': data.get('description', ''),
            'Custom field (Frequency)': data.get('frequency', ''),
            'Issue Type': data.get('issue_type', 'Bug'),
            'Priority': data.get('priority', 'None'),
            'Custom field (Severity)': data.get('severity', 'None'),
            'Custom field (Problem Type)': data.get('problem_type', ''),
            'Summary': data.get('summary', ''),
            'App Version': data.get('app_version', ''),
            'App Version Enhanced': app_version_enhanced,
            'Application': application
        }
        
        # User store already retrieved above (line 640)
        if user_store['loaded'] and user_store['data'] is not None:
            # Append to user's custom data
            logger.info(f"📤 Appending to user {user_id}'s data: {user_store['fileName']}")
            
            # Create new row with custom data columns
            custom_row = {col: '' for col in user_store['data'].columns}
            
            # Map ALL form data fields to custom columns dynamically
            logger.info(f"🗺️  Mapping form data to columns:")
            logger.info(f"   Form data keys: {list(data.keys())}")
            logger.info(f"   Available columns: {user_store['data'].columns.tolist()}")
            
            for key, value in data.items():
                # Try to find matching column (exact match or partial match)
                for col in user_store['data'].columns:
                    col_lower = col.lower()
                    key_lower = key.lower()
                    
                    # Exact match or partial match
                    if col_lower == key_lower or key_lower in col_lower or col_lower in key_lower:
                        custom_row[col] = value
                        logger.info(f"   ✓ Mapped '{key}' → '{col}' = '{str(value)[:50]}'")
                        break
            
            # Also try common mappings - ALWAYS OVERRIDE with latest data
            for col in user_store['data'].columns:
                col_lower = col.lower()
                if 'summary' in col_lower or 'özet' in col_lower:
                    # Always use the data from form, override any existing value
                    if 'summary' in data or 'özet' in data:
                        custom_row[col] = data.get('summary', data.get('özet', ''))
                elif 'description' in col_lower or 'açıklama' in col_lower:
                    if 'description' in data or 'açıklama' in data:
                        custom_row[col] = data.get('description', data.get('açıklama', ''))
                elif 'priority' in col_lower or 'öncelik' in col_lower:
                    if 'priority' in data or 'öncelik' in data:
                        custom_row[col] = data.get('priority', data.get('öncelik', ''))
                elif 'component' in col_lower or 'platform' in col_lower:
                    if 'component' in data or 'platform' in data:
                        custom_row[col] = data.get('component', data.get('platform', ''))
                elif 'application' in col_lower or 'uygulama' in col_lower:
                    if 'application' in data or 'uygulama' in data:
                        custom_row[col] = data.get('application', data.get('uygulama', application))
            
            # If replacing an old report, delete it first
            if replace_report and old_report_summary:
                logger.info(f"🔄 Replacing old report: '{old_report_summary}'")
                logger.info(f"📊 Current DataFrame shape: {user_store['data'].shape}")
                logger.info(f"📋 Available columns: {user_store['data'].columns.tolist()}")
                
                # Find the summary column (case-insensitive)
                summary_col = None
                for col in user_store['data'].columns:
                    if 'summary' in col.lower() or 'özet' in col.lower():
                        summary_col = col
                        logger.info(f"✓ Found summary column: '{summary_col}'")
                        break
                
                if summary_col:
                    # Find and remove rows with matching summary
                    mask = user_store['data'][summary_col].astype(str).str.lower().str.contains(
                        old_report_summary.lower(), 
                        na=False,
                        regex=False
                    )
                    rows_before = len(user_store['data'])
                    matching_rows = user_store['data'][mask]
                    logger.info(f"🔍 Found {len(matching_rows)} matching row(s):")
                    for idx, row in matching_rows.iterrows():
                        logger.info(f"   Row {idx}: {row[summary_col][:80]}")
                    
                    user_store['data'] = user_store['data'][~mask]
                    rows_after = len(user_store['data'])
                    logger.info(f"🗑️  Deleted {rows_before - rows_after} old report(s)")
                else:
                    logger.warning(f"⚠️  Could not find summary column in: {user_store['data'].columns.tolist()}")
            
            # Append to DataFrame
            user_store['data'] = pd.concat([
                user_store['data'],
                pd.DataFrame([custom_row])
            ], ignore_index=True)
            
            user_store['rowCount'] = len(user_store['data'])
            report_id = user_store['rowCount']
            
            # Save to user's CSV file (both in user_data and user_embeddings)
            csv_path = f"{DATA_BASE_DIR}/user_data/{user_store.get('fileName', 'custom_data.csv')}"
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            user_store['data'].to_csv(csv_path, index=False, encoding='utf-8')
            
            # Also save to user_embeddings directory for persistence
            user_embeddings_dir = Path(DATA_BASE_DIR) / 'user_embeddings' / user_id
            user_embeddings_dir.mkdir(parents=True, exist_ok=True)
            user_data_file = user_embeddings_dir / 'data.csv'
            user_store['data'].to_csv(user_data_file, index=False)
            
            # CRITICAL: Reload data from disk to ensure consistency
            # This ensures subsequent searches use the updated data
            user_store['data'] = pd.read_csv(user_data_file)
            user_store['rowCount'] = len(user_store['data'])
            
            # Update user store
            set_user_data_store(user_id, user_store)
            
            logger.info(f"✅ Report added to user {user_id}'s data and saved. New count: {report_id}")
            logger.info(f"🔄 Data reloaded from disk to ensure consistency")
            
            # CRITICAL: Regenerate embeddings for updated data
            # Do this SYNCHRONOUSLY to ensure search results are correct
            logger.info(f"🔄 Regenerating embeddings for user {user_id}...")
            
            try:
                from src.user_embedding_pipeline import create_user_embeddings
                
                # Get text columns from metadata
                text_columns = user_store.get('textColumns', ['Summary', 'Description'])
                
                logger.info(f"📝 Using text columns: {text_columns}")
                
                # Regenerate embeddings SYNCHRONOUSLY
                success = create_user_embeddings(
                    user_id=user_id,
                    df=user_store['data'],
                    text_columns=text_columns
                )
                
                if success:
                    logger.info(f"✅ Embeddings regenerated successfully for user {user_id}")
                    embeddings_updated = True
                else:
                    logger.warning(f"⚠️  Embedding regeneration failed for user {user_id}")
                    embeddings_updated = False
                    
            except Exception as e:
                logger.error(f"❌ Error regenerating embeddings: {e}")
                logger.exception(e)
                embeddings_updated = False
        else:
            # Use default CSV path
            csv_path = 'data/data_with_application.csv'
            
            # Read existing CSV
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
                
                # If replacing an old report, delete it first
                if replace_report and old_report_summary:
                    logger.info(f"🔄 Replacing old report in default data: '{old_report_summary}'")
                    logger.info(f"📊 Current DataFrame shape: {df.shape}")
                    
                    # Find and remove rows with matching summary
                    mask = df['Summary'].astype(str).str.lower().str.contains(
                        old_report_summary.lower(), 
                        na=False,
                        regex=False
                    )
                    rows_before = len(df)
                    matching_rows = df[mask]
                    logger.info(f"🔍 Found {len(matching_rows)} matching row(s):")
                    for idx, row in matching_rows.iterrows():
                        logger.info(f"   Row {idx}: {row['Summary'][:80]}")
                    
                    df = df[~mask]
                    rows_after = len(df)
                    logger.info(f"🗑️  Deleted {rows_before - rows_after} old report(s)")
                
                # Append new row
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                
                # Save back to CSV
                df.to_csv(csv_path, sep=';', encoding='utf-8', index=False)
                
                report_id = len(df)  # New ID is the row count
            else:
                return jsonify({
                    'success': False,
                    'error': 'CSV file not found'
                }), 500
        
        logger.info(f"✅ New report created: ID={report_id}, App={application}, Summary={data['summary'][:50]}...")
        
        # NOTE: Embeddings should NOT be updated here for user-specific mode
        # Users should re-upload their data or we should implement incremental embedding updates
        
        return jsonify({
            'success': True,
            'message': 'Report created successfully',
            'report_id': report_id,
            'application': application,
            'userId': user_id,
            'embeddings_updated': False  # Embeddings not auto-updated in user-specific mode
        })
        
    except Exception as e:
        logger.error(f"❌ Create report error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/upload_data', methods=['POST'])
@cross_origin()
def upload_data():
    """
    Upload custom data from frontend
    
    Now supports both JSON and FormData (multipart/form-data) uploads
    
    FormData fields:
        - file: CSV file
        - userId: User ID
        - username: Username
        - fileName: File name
        - rowCount: Row count (optional)
        - columns: JSON string of columns (optional)
    """
    try:
        import pandas as pd
        from datetime import datetime
        import os
        import json
        import sys
        import io
        
        # Add src to path for imports
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from user_embedding_pipeline import create_user_embeddings
        
        # Check if request is FormData (multipart/form-data) or JSON
        if request.files and 'file' in request.files:
            # FormData upload (for large files)
            logger.info("📁 Received FormData upload (CSV file)")
            
            file = request.files['file']
            user_id = request.form.get('userId', 'anonymous')
            username = request.form.get('username', 'demo')
            file_name = request.form.get('fileName', file.filename)
            
            logger.info(f"📥 Upload request from user: {user_id}")
            logger.info(f"📁 File: {file_name} ({file.content_length} bytes)")
            
            # Read CSV file directly with pandas
            try:
                # Read file content as bytes
                file_content = file.read()
                file_size_mb = len(file_content) / (1024 * 1024)
                logger.info(f"📦 File content read: {file_size_mb:.2f} MB")
                
                if len(file_content) == 0:
                    raise ValueError("File is empty (0 bytes)")
                
                # Try different delimiters and encodings
                delimiters = [',', ';', '\t', '|']
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                
                df = None
                for delimiter in delimiters:
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(
                                io.BytesIO(file_content), 
                                encoding=encoding,
                                delimiter=delimiter,
                                on_bad_lines='skip',  # Skip problematic lines
                                skipinitialspace=True,
                                engine='python'  # Python engine is more forgiving
                            )
                            # Check if we got valid data
                            if len(df) > 0 and len(df.columns) > 1:
                                logger.info(f"✅ CSV parsed successfully: encoding={encoding}, delimiter='{delimiter}'")
                                logger.info(f"📊 DataFrame loaded: {len(df)} rows, {len(df.columns)} columns")
                                break
                        except (UnicodeDecodeError, pd.errors.ParserError) as e:
                            continue
                    if df is not None and len(df) > 0:
                        break
                
                if df is None or len(df) == 0:
                    raise ValueError("Could not parse CSV file with any encoding/delimiter combination")
                
            except Exception as e:
                logger.error(f"❌ Error reading CSV: {e}")
                return jsonify({
                    'success': False,
                    'error': f'CSV okuma hatası: {str(e)}'
                }), 400
            
            user_data_store = {
                'data': df,
                'fileName': file_name,
                'rowCount': len(df),
                'columns': df.columns.tolist(),
                'uploadedAt': datetime.now().isoformat(),
                'loaded': True,
                'userId': user_id,
                'selectedColumns': [],
                'metadataColumns': []
            }
            
        else:
            # JSON upload (for backwards compatibility with small files)
            logger.info("📝 Received JSON upload")
            data = request.get_json()
            
            if not data or 'data' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing data field'
                }), 400
            
            # Get user ID (REQUIRED)
            user_id = data.get('userId') or data.get('username', 'anonymous')
            username = data.get('username', 'demo')
            logger.info(f"📥 Upload request from user: {user_id}")
            
            # Store custom data for THIS USER
            df = pd.DataFrame(data['data'])
            user_data_store = {
                'data': df,
                'fileName': data.get('fileName', 'uploaded_data.csv'),
                'rowCount': len(data['data']),
                'columns': data.get('columns', list(data['data'][0].keys()) if data['data'] else []),
                'uploadedAt': datetime.now().isoformat(),
                'loaded': True,
                'userId': user_id,
                'selectedColumns': [],
                'metadataColumns': []
            }
        
        # Save to user-specific store
        set_user_data_store(user_id, user_data_store)
        
        # Save to user-specific datasets list
        username = data.get('username', 'demo')
        user_datasets_dir = os.path.join(DATA_BASE_DIR, 'user_datasets')
        os.makedirs(user_datasets_dir, exist_ok=True)
        
        user_datasets_file = os.path.join(user_datasets_dir, f'{username}.json')
        
        # Load existing datasets or create new list
        if os.path.exists(user_datasets_file):
            with open(user_datasets_file, 'r') as f:
                user_datasets = json.load(f)
        else:
            user_datasets = []
        
        # Add new dataset to user's list
        dataset_info = {
            'name': user_data_store['fileName'].replace('.csv', '').replace('_', ' ').title(),
            'fileName': user_data_store['fileName'],
            'filePath': f'user_data/{username}/{user_data_store["fileName"]}',
            'rowCount': user_data_store['rowCount'],
            'columns': user_data_store['columns'],
            'columnCount': len(user_data_store['columns']),
            'fileSize': f"{len(str(data['data'])) / (1024*1024):.2f} MB",
            'lastModified': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'type': 'user',
            'owner': username
        }
        
        # Check if already exists, update or append
        exists = False
        for i, ds in enumerate(user_datasets):
            if ds.get('fileName') == user_data_store['fileName']:
                user_datasets[i] = dataset_info
                exists = True
                break
        
        if not exists:
            user_datasets.append(dataset_info)
        
        # Save updated datasets list
        with open(user_datasets_file, 'w') as f:
            json.dump(user_datasets, f, indent=2)
        
        logger.info(f"✅ Custom data uploaded and saved for user {user_id}: {user_data_store['fileName']}, {user_data_store['rowCount']} rows, {len(user_data_store['columns'])} columns")
        
        # 🔥 CRITICAL: Create embeddings for this user's data!
        try:
            logger.info(f"🔄 Creating embeddings for user: {user_id}")
            
            # Get text columns (from request or auto-detect)
            text_columns = data.get('textColumns')
            if text_columns:
                logger.info(f"📝 Using provided text columns: {text_columns}")
            else:
                logger.info(f"🔍 Auto-detecting text columns...")
            
            # Run embedding pipeline
            success = create_user_embeddings(
                user_id=user_id,
                df=df,
                text_columns=text_columns,
                config={
                    'fileName': user_data_store['fileName'],
                    'metadataColumns': user_data_store.get('metadataColumns', [])
                }
            )
            
            if success:
                logger.info(f"✅ Embeddings created successfully for user: {user_id}")
                
                # Save original data to disk for persistence
                user_embeddings_dir = Path(DATA_BASE_DIR) / 'user_embeddings' / user_id
                data_file = user_embeddings_dir / 'data.csv'
                try:
                    df.to_csv(data_file, index=False)
                    logger.info(f"💾 Saved user data to disk: {data_file}")
                except Exception as e:
                    logger.error(f"❌ Error saving user data to disk: {e}")
                
                # Update user store with embedding info
                user_store = get_user_data_store(user_id)
                user_store['embeddingsCreated'] = True
                user_store['embeddingsPath'] = f"{DATA_BASE_DIR}/user_embeddings/{user_id}"
                set_user_data_store(user_id, user_store)
            else:
                logger.warning(f"⚠️ Embedding creation failed for user: {user_id}")
                user_store = get_user_data_store(user_id)
                user_store['embeddingsCreated'] = False
                set_user_data_store(user_id, user_store)
                
        except Exception as e:
            logger.error(f"❌ Embedding creation error for user {user_id}: {e}")
            import traceback
            traceback.print_exc()
            user_store = get_user_data_store(user_id)
            user_store['embeddingsCreated'] = False
            set_user_data_store(user_id, user_store)
        
        # Get final user store for response
        final_user_store = get_user_data_store(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Data uploaded and embeddings created successfully',
            'info': {
                'fileName': final_user_store['fileName'],
                'rowCount': final_user_store['rowCount'],
                'columns': final_user_store['columns'],
                'uploadedAt': final_user_store['uploadedAt'],
                'embeddingsCreated': final_user_store.get('embeddingsCreated', False),
                'embeddingsPath': final_user_store.get('embeddingsPath', None),
                'userId': user_id
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Upload data error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/update_selected_columns', methods=['POST'])
@cross_origin()
def update_selected_columns():
    """
    Update selected columns for custom data search
    
    Request Body:
    {
        "userId": "user123",  # User ID
        "selectedColumns": ["Summary", "Description", ...],  # For cross-encoder
        "metadataColumns": ["Platform", "App Version", ...]  # For form display
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'selectedColumns' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing selectedColumns field'
            }), 400
        
        # Get user ID
        user_id = data.get('userId') or data.get('username', 'anonymous')
        user_store = get_user_data_store(user_id)
        
        # Update selected columns
        user_store['selectedColumns'] = data['selectedColumns']
        user_store['metadataColumns'] = data.get('metadataColumns', [])
        set_user_data_store(user_id, user_store)
        
        # Also update metadata.json for persistence
        try:
            user_embeddings_dir = Path(DATA_BASE_DIR) / 'user_embeddings' / user_id
            metadata_file = user_embeddings_dir / 'metadata.json'
            if metadata_file.exists():
                import json
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                metadata['textColumns'] = data['selectedColumns']
                metadata['metadataColumns'] = data.get('metadataColumns', [])
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                logger.info(f"💾 Updated metadata.json for user {user_id}")
        except Exception as e:
            logger.error(f"❌ Error updating metadata.json: {e}")
        
        logger.info(f"✅ Cross-encoder columns updated for user {user_id}: {user_store['selectedColumns']}")
        logger.info(f"✅ Metadata columns updated for user {user_id}: {user_store['metadataColumns']}")
        
        return jsonify({
            'success': True,
            'message': 'Selected columns updated',
            'selectedColumns': user_store['selectedColumns'],
            'metadataColumns': user_store['metadataColumns'],
            'userId': user_id
        })
        
    except Exception as e:
        logger.error(f"❌ Update selected columns error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/clear_custom_data', methods=['POST'])
@cross_origin()
def clear_custom_data():
    """Clear custom uploaded data"""
    try:
        global custom_data_store
        
        custom_data_store = {
            'data': None,
            'fileName': None,
            'rowCount': 0,
            'columns': [],
            'selectedColumns': [],
            'uploadedAt': None,
            'loaded': False
        }
        
        logger.info("✅ Custom data cleared")
        
        return jsonify({
            'success': True,
            'message': 'Custom data cleared'
        })
        
    except Exception as e:
        logger.error(f"❌ Clear data error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/data_status', methods=['GET'])
def data_status():
    """Get current data status for a specific user"""
    try:
        # Get user_id from query parameter
        user_id = request.args.get('user_id', 'anonymous')
        
        user_store = get_user_data_store(user_id)
        
        if user_store['loaded']:
            return jsonify({
                'success': True,
                'custom_data_loaded': True,
                'custom_data_columns': user_store['columns'],
                'fileName': user_store['fileName'],
                'rowCount': user_store['rowCount'],
                'userId': user_id,
                'embeddingsCreated': user_store.get('embeddingsCreated', user_store.get('embeddingsReady', False)),
                'embeddingsPath': user_store.get('embeddingsPath', None)
            })
        else:
            # No data loaded for this user
            return jsonify({
                'success': True,
                'custom_data_loaded': False,
                'message': 'No data uploaded for this user',
                'userId': user_id
            })
        
    except Exception as e:
        logger.error(f"❌ Data status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/column_values/<column_name>', methods=['GET'])
@cross_origin()
def get_column_values(column_name):
    """Get unique values for a specific column"""
    try:
        # Get user ID from query params
        user_id = request.args.get('user_id', 'anonymous')
        user_store = get_user_data_store(user_id)
        
        # Check if user has data
        if not user_store['loaded'] or user_store['data'] is None:
            return jsonify({
                'success': False,
                'error': 'No data uploaded. Please upload your data first.',
                'userId': user_id
            }), 400
        
        df = user_store['data']
        
        # Get unique values for the column
        if column_name in df.columns:
            unique_values = df[column_name].dropna().unique().tolist()
            # Sort values for better UX
            unique_values = sorted([str(v) for v in unique_values])
            
            return jsonify({
                'success': True,
                'column': column_name,
                'values': unique_values,
                'count': len(unique_values),
                'userId': user_id
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Column {column_name} not found',
                'userId': user_id
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Error getting column values: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/available_datasets', methods=['GET'])
@cross_origin()
def get_available_datasets():
    """Get list of available datasets"""
    try:
        import os
        import pandas as pd
        from datetime import datetime
        
        datasets = []
        data_dir = 'data'
        
        # Get username from query params (for user-specific datasets)
        username = request.args.get('username', 'default')
        
        # NO DEFAULT DATASETS - Users must upload their own data
        # Only show user-specific datasets
        
        logger.info(f"📋 Getting datasets for user: {username}")
        
        # Add user-specific datasets from localStorage data
        user_datasets_file = os.path.join(DATA_BASE_DIR, 'user_datasets', f'{username}.json')
        if os.path.exists(user_datasets_file):
            import json
            with open(user_datasets_file, 'r') as f:
                user_datasets = json.load(f)
                datasets.extend(user_datasets)
        
        return jsonify({
            'success': True,
            'datasets': datasets,
            'count': len(datasets)
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting available datasets: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/load_dataset/<dataset_name>', methods=['POST'])
@cross_origin()
def load_dataset(dataset_name):
    """Load a specific dataset for a user"""
    try:
        import os
        import pandas as pd
        from datetime import datetime
        
        # Get request body to extract user_id
        data = request.get_json() or {}
        user_id = data.get('userId') or data.get('username', 'anonymous')
        
        logger.info(f"📥 Load dataset request: {dataset_name} for user: {user_id}")
        
        # Get user's data store
        user_store = get_user_data_store(user_id)
        
        # Check if this dataset is already loaded for this user
        if (user_store.get('loaded') and 
            user_store.get('fileName') == dataset_name and 
            user_store.get('data') is not None):
            
            logger.info(f"✅ Dataset already loaded for user {user_id}: {dataset_name} ({user_store['rowCount']} rows)")
            
            return jsonify({
                'success': True,
                'message': f'Dataset {dataset_name} already loaded',
                'rowCount': user_store['rowCount'],
                'columns': user_store['columns'],
                'embeddingsCreated': user_store.get('embeddingsCreated', user_store.get('embeddingsReady', False))
            })
        else:
            # User data not loaded - this shouldn't happen if they got to this point
            logger.warning(f"⚠️ User {user_id} tried to load {dataset_name} but data not found")
            return jsonify({
                'success': False,
                'error': f'Dataset {dataset_name} not found for user. Please upload it first.'
            }), 404
        
    except Exception as e:
        logger.error(f"❌ Error loading dataset: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle 413 Payload Too Large errors"""
    return jsonify({
        'success': False,
        'error': 'Dosya çok büyük! Maksimum 100MB yükleyebilirsiniz. Lütfen daha küçük bir dosya deneyin veya veriyi birkaç parçaya bölün.'
    }), 413


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


# ============================================================================
# FEATURE EXTRACTION ENDPOINTS
# ============================================================================

@app.route('/api/available_extraction_types', methods=['GET'])
def get_available_extraction_types():
    """Get list of available feature types for extraction"""
    try:
        feature_types = feature_extractor.get_available_features()
        
        # Add descriptions
        descriptions = {
            'application': 'Uygulama adı (BiP, Whatsapp, Instagram, vb.)',
            'platform': 'Platform (iOS, Android, Windows, vb.)',
            'version': 'Versiyon numarası (14.5, 2.3.1, vb.)',
            'device': 'Cihaz modeli (iPhone 12, Samsung Galaxy S21, vb.)',
            'severity': 'Önem derecesi (Critical, High, Medium, Low)',
            'component': 'Bileşen/Modül (Login, Payment, Search, vb.)'
        }
        
        return jsonify({
            'success': True,
            'featureTypes': [
                {
                    'type': ft,
                    'description': descriptions.get(ft, ft)
                }
                for ft in feature_types
            ]
        })
    
    except Exception as e:
        logger.error(f"Error getting extraction types: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/suggest_extractions', methods=['POST'])
def suggest_extractions():
    """
    Analyze a text column and suggest which features can be extracted
    
    Request body:
    {
        "userId": "user123",
        "sourceColumn": "description"
    }
    
    Returns:
    {
        "success": true,
        "suggestions": {
            "application": 45,  // number of rows where this can be extracted
            "platform": 38,
            "version": 12
        }
    }
    """
    try:
        data = request.get_json()
        user_id = data.get('userId')
        source_column = data.get('sourceColumn')
        
        if not user_id or not source_column:
            return jsonify({
                'success': False,
                'error': 'userId and sourceColumn are required'
            }), 400
        
        # Get user data
        user_store = get_user_data_store(user_id)
        if not user_store.get('loaded'):
            return jsonify({
                'success': False,
                'error': 'No data loaded for this user'
            }), 404
        
        df = user_store['data']
        
        if source_column not in df.columns:
            return jsonify({
                'success': False,
                'error': f'Column "{source_column}" not found in data'
            }), 400
        
        # Analyze and suggest
        suggestions = feature_extractor.suggest_extractions(df, source_column)
        
        logger.info(f"Extraction suggestions for user {user_id}, column {source_column}: {suggestions}")
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'totalRows': len(df)
        })
    
    except Exception as e:
        logger.error(f"Error suggesting extractions: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extract_features', methods=['POST'])
def extract_features_endpoint():
    """
    Extract features from a text column and add as new columns
    
    Request body:
    {
        "userId": "user123",
        "sourceColumn": "description",
        "extractions": {
            "Application": "application",
            "Platform": "platform",
            "App_Version": "version"
        }
    }
    
    Returns:
    {
        "success": true,
        "extractedColumns": ["Application", "Platform", "App_Version"],
        "extractionStats": {
            "Application": 45,  // number of non-null values
            "Platform": 38,
            "App_Version": 12
        }
    }
    """
    try:
        data = request.get_json()
        user_id = data.get('userId')
        source_column = data.get('sourceColumn')
        extractions = data.get('extractions', {})
        
        if not user_id or not source_column or not extractions:
            return jsonify({
                'success': False,
                'error': 'userId, sourceColumn, and extractions are required'
            }), 400
        
        # Get user data
        user_store = get_user_data_store(user_id)
        if not user_store.get('loaded'):
            return jsonify({
                'success': False,
                'error': 'No data loaded for this user'
            }), 404
        
        df = user_store['data']
        
        if source_column not in df.columns:
            return jsonify({
                'success': False,
                'error': f'Column "{source_column}" not found in data'
            }), 400
        
        # Extract features
        logger.info(f"Extracting features for user {user_id}: {extractions}")
        df_extracted = feature_extractor.add_extracted_columns(df, source_column, extractions)
        
        # Calculate stats
        extraction_stats = {}
        for col_name in extractions.keys():
            if col_name in df_extracted.columns:
                non_null_count = df_extracted[col_name].notna().sum()
                extraction_stats[col_name] = int(non_null_count)
        
        # Update user store
        user_store['data'] = df_extracted
        user_store['columns'] = list(df_extracted.columns)
        
        # Save to disk
        user_embeddings_dir = Path(DATA_BASE_DIR) / 'user_embeddings' / user_id
        user_embeddings_dir.mkdir(parents=True, exist_ok=True)
        data_file = user_embeddings_dir / 'data.csv'
        df_extracted.to_csv(data_file, index=False)
        
        # Update metadata
        import json
        metadata_file = user_embeddings_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            metadata['extractedColumns'] = list(extractions.keys())
            metadata['extractionSource'] = source_column
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        logger.info(f"Feature extraction complete: {extraction_stats}")
        
        return jsonify({
            'success': True,
            'extractedColumns': list(extractions.keys()),
            'extractionStats': extraction_stats,
            'totalRows': len(df_extracted)
        })
    
    except Exception as e:
        logger.error(f"Error extracting features: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def main():
    """Main function to run the server"""
    # Load environment variables
    from dotenv import load_dotenv
    import base64
    load_dotenv()
    
    print("\n" + "=" * 80)
    print("🚀 BUG REPORT DUPLICATE DETECTION API SERVER")
    print("=" * 80)
    print("\n⚠️  USER-SPECIFIC MODE:")
    print("   • No default data loaded")
    print("   • Each user must upload their own data")
    print("   • Users can only see their own data")
    print("   • Embeddings are created per user")
    print("   • Firebase Storage caching enabled")
    
    # DO NOT pre-initialize search system - users will upload their own data
    # get_search_system()  # REMOVED: No default Turkcell data
    
    # Handle Firebase Service Account (base64 or file path)
    firebase_enabled = os.getenv('USE_FIREBASE_CACHE', 'True').lower() == 'true'
    if firebase_enabled:
        print("\n🔥 Firebase Configuration:")
        
        # Check for base64 encoded service account
        base64_service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT_BASE64')
        if base64_service_account:
            try:
                # Decode base64 and save to temp file
                decoded = base64.b64decode(base64_service_account)
                temp_path = '/tmp/firebase-service-account.json'
                with open(temp_path, 'w') as f:
                    f.write(decoded.decode('utf-8'))
                os.environ['FIREBASE_SERVICE_ACCOUNT'] = temp_path
                print(f"   ✅ Service Account decoded from base64 → {temp_path}")
            except Exception as e:
                print(f"   ⚠️  Failed to decode service account: {e}")
        
        service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT', 'Not set')
        storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET', 'Not set')
        print(f"   • Service Account: {service_account}")
        print(f"   • Storage Bucket: {storage_bucket}")
    
    print("\n" + "=" * 80)
    print("✅ SERVER READY!")
    print("=" * 80)
    
    # Get port from environment
    # Railway sets PORT, Hugging Face Spaces uses 7860, local default is 5001
    port = int(os.getenv('PORT', 7860))
    
    print(f"\n📍 Server will start on port: {port}")
    print("\n📍 Endpoints:")
    print(f"   • http://localhost:{port}/api/health     - Health check")
    print(f"   • http://localhost:{port}/api/search     - Search similar reports (POST)")
    print(f"   • http://localhost:{port}/api/stats      - Get system statistics")
    print(f"   • http://localhost:{port}/api/applications - Get available applications")
    print("\n🌐 Frontend:")
    print("   • Open web/index.html in your browser")
    print("\n💡 Usage:")
    print("   • Frontend will automatically connect to this API")
    print("   • Or use curl/Postman for direct API testing")
    print("\n" + "=" * 80)
    print("\n🔥 Starting Flask server...\n")
    
    # Run Flask server
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        threaded=True
    )


if __name__ == "__main__":
    main()

