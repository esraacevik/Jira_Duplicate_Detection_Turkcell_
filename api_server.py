#!/usr/bin/env python3
"""
Bug Report Duplicate Detection API Server
==========================================
Flask API server for the hybrid search system
"""

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from hybrid_search import HybridSearch
import logging
from typing import Dict, List, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Initialize search system (singleton)
search_system = None

# Global variable to store custom uploaded data
custom_data_store = {
    'data': None,
    'fileName': None,
    'rowCount': 0,
    'columns': [],
    'selectedColumns': [],  # Columns to use for cross-encoder search
    'metadataColumns': [],  # Columns to show in form for comparison
    'uploadedAt': None,
    'loaded': False
}

def get_search_system():
    """Get or initialize the search system"""
    global search_system
    if search_system is None:
        logger.info("🚀 Initializing Hybrid Search System...")
        search_system = HybridSearch()
        logger.info("✅ Search system ready!")
    return search_system


def search_custom_data(query, df, top_k=10, selected_columns=None):
    """
    Simple text-based search on custom data
    Returns results in the same format as hybrid search
    
    Args:
        query: Search query
        df: Custom DataFrame
        top_k: Number of results to return
        selected_columns: List of columns selected by user for search (priority)
    """
    import pandas as pd
    from difflib import SequenceMatcher
    
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
        
        logger.info(f"🔍 Search request: query='{query[:50]}...', app={application}, platform={platform}, columns={selected_columns}")
        
        # Check if custom data is loaded
        global custom_data_store
        
        if custom_data_store['loaded'] and custom_data_store['data'] is not None:
            # Use custom data for search (simple text matching for now)
            # Prefer selectedColumns from request, fallback to stored config
            cols_to_use = selected_columns if selected_columns != ['Summary', 'Description'] else custom_data_store.get('selectedColumns', selected_columns)
            logger.info(f"📤 Using custom uploaded data: {custom_data_store['fileName']}")
            logger.info(f"🎯 Selected columns for search: {cols_to_use}")
            start_time = time.time()
            results = search_custom_data(
                query, 
                custom_data_store['data'], 
                top_k,
                selected_columns=cols_to_use
            )
            search_time = time.time() - start_time
            logger.info(f"✅ Found {len(results)} results in custom data in {search_time:.2f}s")
        else:
            # Use default hybrid search system
            logger.info(f"📁 Using default data")
            logger.info(f"🎯 Selected columns for search: {selected_columns}")
            start_time = time.time()
            search = get_search_system()
            results = search.search(
                query=query,
                application=application,
                platform=platform,
                version=version,
                language=language,
                top_k=top_k,
                selected_columns=selected_columns  # Pass selected columns
            )
            search_time = time.time() - start_time
            logger.info(f"✅ Found {len(results)} results in {search_time:.2f}s")
        
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
            'results': results,
            'count': len(results),
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
        # Check if custom data is loaded
        if custom_data_store['loaded'] and custom_data_store['data'] is not None:
            df = custom_data_store['data']
            logger.info(f"📊 Getting stats from custom data: {len(df)} rows")
            
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
                'fileName': custom_data_store['fileName']
            })
        else:
            # Use default search system
            search = get_search_system()
            
            # Calculate statistics
            stats = {
                'total_reports': len(search.df),
                'platforms': {
                    'android': int((search.df['Platform'] == 'android').sum()),
                    'ios': int((search.df['Platform'] == 'ios').sum()),
                    'unknown': int((search.df['Platform'] == 'unknown').sum())
                },
                'applications': search.df['Application'].value_counts().to_dict() if 'Application' in search.df.columns else {}
            }
            
            return jsonify({
                'success': True,
                'stats': stats,
                'customDataLoaded': False
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
        
        logger.info(f"📥 Received create_report request with data keys: {list(data.keys()) if data else 'None'}")
        if data and 'replace_report' in data:
            logger.info(f"🔍 replace_report parameter found: {data.get('replace_report')}")
            logger.info(f"🔍 old_report_summary parameter: {data.get('old_report_summary')}")
        
        if not data or 'summary' not in data or 'description' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: summary, description'
            }), 400
        
        # Check if we're replacing an old report
        replace_report = data.get('replace_report', False)
        old_report_summary = data.get('old_report_summary', '')
        old_report_id = data.get('old_report_id', '')
        
        logger.info(f"🎯 replace_report={replace_report}, old_report_summary='{old_report_summary}'")
        
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
        
        # Check if custom data is loaded
        global custom_data_store
        
        if custom_data_store['loaded'] and custom_data_store['data'] is not None:
            # Append to custom data
            logger.info(f"📤 Appending to custom data: {custom_data_store['fileName']}")
            
            # Create new row with custom data columns
            custom_row = {col: '' for col in custom_data_store['data'].columns}
            
            # Map ALL form data fields to custom columns dynamically
            for key, value in data.items():
                # Try to find matching column (exact match or partial match)
                for col in custom_data_store['data'].columns:
                    col_lower = col.lower()
                    key_lower = key.lower()
                    
                    # Exact match or partial match
                    if col_lower == key_lower or key_lower in col_lower or col_lower in key_lower:
                        custom_row[col] = value
                        break
            
            # Also try common mappings
            for col in custom_data_store['data'].columns:
                col_lower = col.lower()
                if 'summary' in col_lower or 'özet' in col_lower:
                    if not custom_row[col]:  # Only if not already set
                        custom_row[col] = data.get('summary', data.get('özet', ''))
                elif 'description' in col_lower or 'açıklama' in col_lower:
                    if not custom_row[col]:
                        custom_row[col] = data.get('description', data.get('açıklama', ''))
                elif 'priority' in col_lower or 'öncelik' in col_lower:
                    if not custom_row[col]:
                        custom_row[col] = data.get('priority', data.get('öncelik', ''))
                elif 'component' in col_lower or 'platform' in col_lower:
                    if not custom_row[col]:
                        custom_row[col] = data.get('component', data.get('platform', ''))
                elif 'application' in col_lower or 'uygulama' in col_lower:
                    if not custom_row[col]:
                        custom_row[col] = data.get('application', data.get('uygulama', application))
            
            # If replacing an old report, delete it first
            if replace_report and old_report_summary:
                logger.info(f"🔄 Replacing old report: '{old_report_summary}'")
                logger.info(f"📊 Current DataFrame shape: {custom_data_store['data'].shape}")
                logger.info(f"📋 Available columns: {custom_data_store['data'].columns.tolist()}")
                
                # Find the summary column (case-insensitive)
                summary_col = None
                for col in custom_data_store['data'].columns:
                    if 'summary' in col.lower() or 'özet' in col.lower():
                        summary_col = col
                        logger.info(f"✓ Found summary column: '{summary_col}'")
                        break
                
                if summary_col:
                    # Find and remove rows with matching summary
                    mask = custom_data_store['data'][summary_col].astype(str).str.lower().str.contains(
                        old_report_summary.lower(), 
                        na=False,
                        regex=False
                    )
                    rows_before = len(custom_data_store['data'])
                    matching_rows = custom_data_store['data'][mask]
                    logger.info(f"🔍 Found {len(matching_rows)} matching row(s):")
                    for idx, row in matching_rows.iterrows():
                        logger.info(f"   Row {idx}: {row[summary_col][:80]}")
                    
                    custom_data_store['data'] = custom_data_store['data'][~mask]
                    rows_after = len(custom_data_store['data'])
                    logger.info(f"🗑️  Deleted {rows_before - rows_after} old report(s)")
                else:
                    logger.warning(f"⚠️  Could not find summary column in: {custom_data_store['data'].columns.tolist()}")
            
            # Append to DataFrame
            custom_data_store['data'] = pd.concat([
                custom_data_store['data'],
                pd.DataFrame([custom_row])
            ], ignore_index=True)
            
            custom_data_store['rowCount'] = len(custom_data_store['data'])
            report_id = custom_data_store['rowCount']
            
            # CRITICAL: Save to CSV file!
            csv_path = f"data/user_data/{custom_data_store.get('fileName', 'custom_data.csv')}"
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            custom_data_store['data'].to_csv(csv_path, index=False, encoding='utf-8')
            
            logger.info(f"✅ Report added to custom data and saved to {csv_path}. New count: {report_id}")
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
        
        return jsonify({
            'success': True,
            'message': 'Report created successfully',
            'report_id': report_id,
            'application': application
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
    
    Request Body:
    {
        "data": [...],  # Array of objects
        "fileName": "data.csv",
        "columns": ["col1", "col2", ...],
        "rowCount": 100
    }
    """
    try:
        import pandas as pd
        from datetime import datetime
        import os
        import json
        
        global custom_data_store
        
        # Get request data
        data = request.get_json()
        
        if not data or 'data' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing data field'
            }), 400
        
        # Store custom data
        custom_data_store['data'] = pd.DataFrame(data['data'])
        custom_data_store['fileName'] = data.get('fileName', 'uploaded_data.csv')
        custom_data_store['rowCount'] = len(data['data'])
        custom_data_store['columns'] = data.get('columns', list(data['data'][0].keys()) if data['data'] else [])
        custom_data_store['uploadedAt'] = datetime.now().isoformat()
        custom_data_store['loaded'] = True
        
        # Save to user-specific datasets list
        username = data.get('username', 'demo')
        user_datasets_dir = os.path.join('data', 'user_datasets')
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
            'name': custom_data_store['fileName'].replace('.csv', '').replace('_', ' ').title(),
            'fileName': custom_data_store['fileName'],
            'filePath': f'user_data/{username}/{custom_data_store["fileName"]}',
            'rowCount': custom_data_store['rowCount'],
            'columns': custom_data_store['columns'],
            'columnCount': len(custom_data_store['columns']),
            'fileSize': f"{len(str(data['data'])) / (1024*1024):.2f} MB",
            'lastModified': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'type': 'user',
            'owner': username
        }
        
        # Check if already exists, update or append
        exists = False
        for i, ds in enumerate(user_datasets):
            if ds.get('fileName') == custom_data_store['fileName']:
                user_datasets[i] = dataset_info
                exists = True
                break
        
        if not exists:
            user_datasets.append(dataset_info)
        
        # Save updated datasets list
        with open(user_datasets_file, 'w') as f:
            json.dump(user_datasets, f, indent=2)
        
        logger.info(f"✅ Custom data uploaded and saved: {custom_data_store['fileName']}, {custom_data_store['rowCount']} rows, {len(custom_data_store['columns'])} columns")
        
        return jsonify({
            'success': True,
            'message': 'Data uploaded successfully',
            'info': {
                'fileName': custom_data_store['fileName'],
                'rowCount': custom_data_store['rowCount'],
                'columns': custom_data_store['columns'],
                'uploadedAt': custom_data_store['uploadedAt']
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
        "selectedColumns": ["Summary", "Description", ...],  # For cross-encoder
        "metadataColumns": ["Platform", "App Version", ...]  # For form display
    }
    """
    try:
        global custom_data_store
        
        data = request.get_json()
        
        if not data or 'selectedColumns' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing selectedColumns field'
            }), 400
        
        # Update selected columns
        custom_data_store['selectedColumns'] = data['selectedColumns']
        custom_data_store['metadataColumns'] = data.get('metadataColumns', [])
        
        logger.info(f"✅ Cross-encoder columns updated: {custom_data_store['selectedColumns']}")
        logger.info(f"✅ Metadata columns updated: {custom_data_store['metadataColumns']}")
        
        return jsonify({
            'success': True,
            'message': 'Selected columns updated',
            'selectedColumns': custom_data_store['selectedColumns'],
            'metadataColumns': custom_data_store['metadataColumns']
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
    """Get current data status (custom or default)"""
    try:
        global custom_data_store
        
        if custom_data_store['loaded']:
            return jsonify({
                'success': True,
                'custom_data_loaded': True,
                'custom_data_columns': custom_data_store['columns'],
                'fileName': custom_data_store['fileName'],
                'rowCount': custom_data_store['rowCount']
            })
        else:
            # Get default data columns from HybridSearch system
            try:
                search = get_search_system()
                default_columns = list(search.df.columns)
            except Exception as e:
                logger.warning(f"Could not load default data info: {e}")
                default_columns = [
                    'Summary', 'Description', 'Affects Version', 'Component', 
                    'Priority', 'Custom field (Severity)', 'Custom field (Problem Type)', 
                    'Custom field (Frequency)', 'Application', 'App Version'
                ]
            
            return jsonify({
                'success': True,
                'custom_data_loaded': False,
                'default_data_columns': default_columns
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
        global custom_data_store
        
        # Use custom data if loaded, otherwise use default
        if custom_data_store['loaded'] and custom_data_store['data'] is not None:
            df = custom_data_store['data']
        else:
            search = get_search_system()
            df = search.df
        
        # Get unique values for the column
        if column_name in df.columns:
            unique_values = df[column_name].dropna().unique().tolist()
            # Sort values for better UX
            unique_values = sorted([str(v) for v in unique_values])
            
            return jsonify({
                'success': True,
                'column': column_name,
                'values': unique_values,
                'count': len(unique_values)
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Column {column_name} not found'
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
        
        # List of default CSV files
        csv_files = [
            'data_with_application.csv',
            'data_with_enhanced_app_version.csv',
            'data_with_app_version.csv',
            'data_cleaned.csv'
        ]
        
        # Add default datasets
        for csv_file in csv_files:
            file_path = os.path.join(data_dir, csv_file)
            if os.path.exists(file_path):
                try:
                    # Read first few rows to get info (with semicolon delimiter)
                    df = pd.read_csv(file_path, nrows=5, encoding='utf-8', sep=';', on_bad_lines='skip')
                    file_stats = os.stat(file_path)
                    
                    # Get full row count (faster method using line count)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        row_count = sum(1 for line in f) - 1  # -1 for header
                    
                    datasets.append({
                        'name': csv_file.replace('.csv', '').replace('_', ' ').title(),
                        'fileName': csv_file,
                        'filePath': file_path,
                        'rowCount': row_count,
                        'columns': df.columns.tolist(),
                        'columnCount': len(df.columns),
                        'fileSize': f"{file_stats.st_size / (1024*1024):.2f} MB",
                        'lastModified': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M'),
                        'type': 'default',
                        'owner': 'system'
                    })
                except Exception as e:
                    logger.error(f"Error reading {csv_file}: {e}")
                    continue
        
        # Add user-specific datasets from localStorage data
        user_datasets_file = os.path.join(data_dir, 'user_datasets', f'{username}.json')
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
    """Load a specific dataset"""
    try:
        import os
        import pandas as pd
        from datetime import datetime
        
        global custom_data_store
        
        # Check if this dataset is already loaded in custom_data_store
        if (custom_data_store.get('loaded') and 
            custom_data_store.get('fileName') == dataset_name and 
            custom_data_store.get('data') is not None):
            
            logger.info(f"✅ Dataset already loaded: {dataset_name} ({custom_data_store['rowCount']} rows)")
            
            return jsonify({
                'success': True,
                'message': f'Dataset {dataset_name} already loaded',
                'rowCount': custom_data_store['rowCount'],
                'columns': custom_data_store['columns']
            })
        
        # Try to load from file system (default datasets)
        data_dir = 'data'
        file_path = os.path.join(data_dir, dataset_name)
        
        if os.path.exists(file_path):
            # Load the dataset (with semicolon delimiter)
            df = pd.read_csv(file_path, encoding='utf-8', sep=';', on_bad_lines='skip')
            
            # Store in custom_data_store
            custom_data_store = {
                'data': df,
                'fileName': dataset_name,
                'rowCount': len(df),
                'columns': df.columns.tolist(),
                'selectedColumns': [],
                'metadataColumns': [],
                'uploadedAt': datetime.now().isoformat(),
                'loaded': True
            }
            
            logger.info(f"✅ Loaded dataset from file: {dataset_name} ({len(df)} rows)")
            
            return jsonify({
                'success': True,
                'message': f'Dataset {dataset_name} loaded successfully',
                'rowCount': len(df),
                'columns': df.columns.tolist()
            })
        else:
            # Dataset not found in file system or custom_data_store
            return jsonify({
                'success': False,
                'error': f'Dataset {dataset_name} not found. Please upload it first.'
            }), 404
        
    except Exception as e:
        logger.error(f"❌ Error loading dataset: {e}")
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


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


def main():
    """Main function to run the server"""
    print("\n" + "=" * 80)
    print("🚀 BUG REPORT DUPLICATE DETECTION API SERVER")
    print("=" * 80)
    print("\nInitializing...")
    
    # Pre-initialize search system
    get_search_system()
    
    print("\n" + "=" * 80)
    print("✅ SERVER READY!")
    print("=" * 80)
    print("\n📍 Endpoints:")
    print("   • http://localhost:5000/api/health     - Health check")
    print("   • http://localhost:5000/api/search     - Search similar reports (POST)")
    print("   • http://localhost:5000/api/stats      - Get system statistics")
    print("   • http://localhost:5000/api/applications - Get available applications")
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
        port=5001,  # Using 5001 because macOS AirPlay uses 5000
        debug=False,  # Set to True for development
        threaded=True
    )


if __name__ == "__main__":
    main()

