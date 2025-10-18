"""
Firebase Storage Manager for Embedding Artifacts
Handles upload/download of user embeddings to Firebase Storage
"""

import os
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class FirebaseStorageManager:
    """Manage embedding artifacts in Firebase Storage"""
    
    def __init__(self):
        """Initialize Firebase Admin SDK"""
        self.initialized = False
        self.bucket = None
        
        try:
            import firebase_admin
            from firebase_admin import credentials, storage
            
            # Check if already initialized
            if not firebase_admin._apps:
                # Try to get credentials from environment or service account file
                cred_path = os.getenv('FIREBASE_SERVICE_ACCOUNT')
                
                if cred_path and os.path.exists(cred_path):
                    logger.info(f"🔥 Initializing Firebase with service account: {cred_path}")
                    cred = credentials.Certificate(cred_path)
                else:
                    logger.info("🔥 Initializing Firebase with default credentials")
                    cred = credentials.ApplicationDefault()
                
                # Get storage bucket from environment
                bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET')
                if not bucket_name:
                    logger.warning("⚠️  FIREBASE_STORAGE_BUCKET not set, using default")
                    bucket_name = None
                
                firebase_admin.initialize_app(cred, {
                    'storageBucket': bucket_name
                })
            
            # Get storage bucket
            self.bucket = storage.bucket()
            self.initialized = True
            logger.info(f"✅ Firebase Storage initialized: {self.bucket.name}")
            
        except Exception as e:
            logger.warning(f"⚠️  Firebase Storage not available: {e}")
            logger.warning("📝 Running in local-only mode")
            self.initialized = False
    
    def get_user_artifacts_path(self, user_id: str) -> str:
        """Get the Firebase Storage path for user artifacts"""
        return f"user_embeddings/{user_id}"
    
    def upload_user_artifacts(self, user_id: str, local_dir: Path) -> bool:
        """
        Upload user embedding artifacts to Firebase Storage
        
        Args:
            user_id: User ID
            local_dir: Local directory containing artifacts
        
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            logger.warning("⚠️  Firebase Storage not initialized, skipping upload")
            return False
        
        try:
            logger.info(f"📤 Uploading artifacts for user {user_id}...")
            
            # Files to upload
            files_to_upload = [
                'embeddings.npy',
                'faiss_index.bin',
                'metadata.json',
                'data.csv'
            ]
            
            remote_path = self.get_user_artifacts_path(user_id)
            uploaded_count = 0
            
            for filename in files_to_upload:
                local_file = local_dir / filename
                
                if not local_file.exists():
                    logger.warning(f"⚠️  File not found: {local_file}")
                    continue
                
                # Upload to Firebase Storage
                blob = self.bucket.blob(f"{remote_path}/{filename}")
                blob.upload_from_filename(str(local_file))
                
                logger.info(f"✅ Uploaded: {filename} ({local_file.stat().st_size} bytes)")
                uploaded_count += 1
            
            logger.info(f"✅ Uploaded {uploaded_count}/{len(files_to_upload)} files for user {user_id}")
            return uploaded_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error uploading artifacts: {e}")
            return False
    
    def download_user_artifacts(self, user_id: str, local_dir: Path) -> bool:
        """
        Download user embedding artifacts from Firebase Storage
        
        Args:
            user_id: User ID
            local_dir: Local directory to save artifacts
        
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            logger.warning("⚠️  Firebase Storage not initialized, skipping download")
            return False
        
        try:
            logger.info(f"📥 Downloading artifacts for user {user_id}...")
            
            # Create local directory
            local_dir.mkdir(parents=True, exist_ok=True)
            
            # Files to download
            files_to_download = [
                'embeddings.npy',
                'faiss_index.bin',
                'metadata.json',
                'data.csv'
            ]
            
            remote_path = self.get_user_artifacts_path(user_id)
            downloaded_count = 0
            
            for filename in files_to_download:
                local_file = local_dir / filename
                blob = self.bucket.blob(f"{remote_path}/{filename}")
                
                # Check if file exists
                if not blob.exists():
                    logger.warning(f"⚠️  Remote file not found: {remote_path}/{filename}")
                    continue
                
                # Download from Firebase Storage
                blob.download_to_filename(str(local_file))
                
                logger.info(f"✅ Downloaded: {filename} ({local_file.stat().st_size} bytes)")
                downloaded_count += 1
            
            if downloaded_count == len(files_to_download):
                logger.info(f"✅ Downloaded all {downloaded_count} files for user {user_id}")
                return True
            elif downloaded_count > 0:
                logger.warning(f"⚠️  Partial download: {downloaded_count}/{len(files_to_download)} files")
                return False
            else:
                logger.warning(f"⚠️  No artifacts found for user {user_id}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error downloading artifacts: {e}")
            return False
    
    def check_artifacts_exist(self, user_id: str) -> bool:
        """
        Check if embedding artifacts exist in Firebase Storage
        
        Args:
            user_id: User ID
        
        Returns:
            True if artifacts exist, False otherwise
        """
        if not self.initialized:
            return False
        
        try:
            remote_path = self.get_user_artifacts_path(user_id)
            
            # Check for essential files
            essential_files = ['embeddings.npy', 'faiss_index.bin', 'metadata.json']
            
            for filename in essential_files:
                blob = self.bucket.blob(f"{remote_path}/{filename}")
                if not blob.exists():
                    return False
            
            logger.info(f"✅ Artifacts exist for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking artifacts: {e}")
            return False
    
    def get_artifact_metadata(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for user's artifacts
        
        Args:
            user_id: User ID
        
        Returns:
            Metadata dict or None
        """
        if not self.initialized:
            return None
        
        try:
            remote_path = self.get_user_artifacts_path(user_id)
            blob = self.bucket.blob(f"{remote_path}/metadata.json")
            
            if not blob.exists():
                return None
            
            # Download and parse metadata
            metadata_content = blob.download_as_string()
            metadata = json.loads(metadata_content)
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Error getting metadata: {e}")
            return None
    
    def delete_user_artifacts(self, user_id: str) -> bool:
        """
        Delete user's artifacts from Firebase Storage
        
        Args:
            user_id: User ID
        
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            logger.warning("⚠️  Firebase Storage not initialized, skipping delete")
            return False
        
        try:
            logger.info(f"🗑️  Deleting artifacts for user {user_id}...")
            
            remote_path = self.get_user_artifacts_path(user_id)
            
            # List all blobs with this prefix
            blobs = self.bucket.list_blobs(prefix=remote_path)
            
            deleted_count = 0
            for blob in blobs:
                blob.delete()
                deleted_count += 1
            
            logger.info(f"✅ Deleted {deleted_count} files for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting artifacts: {e}")
            return False


# Global instance
_storage_manager = None

def get_storage_manager() -> FirebaseStorageManager:
    """Get or create Firebase Storage Manager singleton"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = FirebaseStorageManager()
    return _storage_manager

