"""
Text Feature Extractor
======================
Extract structured information from text columns (description, summary, etc.)
"""

import re
import pandas as pd
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TextFeatureExtractor:
    """Extract features from text columns using regex patterns"""
    
    def __init__(self):
        # Common patterns for extraction
        self.patterns = {
            'application': [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:uygulaması|application|app)',
                r'(?:uygulama|app):\s*([A-Za-z0-9\s]+)',
                r'\b(BiP|Whatsapp|Instagram|Facebook|Twitter|Gmail|YouTube)\b',
                r'\b([A-Z][a-z]{2,})\s+(?:çalışmıyor|açılmıyor|donuyor)',
            ],
            'platform': [
                r'\b(iOS|Android|Windows|macOS|Linux|Web)\b',
                r'\b(iPhone|iPad|Samsung|Huawei)\b',
            ],
            'version': [
                r'(?:version|versiyon|v\.?)\s*:?\s*(\d+(?:\.\d+)*)',
                r'\b(\d+\.\d+(?:\.\d+)?)\b',  # 14.5, 1.2.3
                r'iOS\s+(\d+(?:\.\d+)*)',
                r'Android\s+(\d+(?:\.\d+)*)',
            ],
            'device': [
                r'\b(iPhone\s+\d+(?:\s+Pro)?(?:\s+Max)?)\b',
                r'\b(iPad(?:\s+Pro)?(?:\s+Air)?)\b',
                r'\b(Samsung\s+Galaxy\s+[A-Z]\d+)\b',
                r'\b(Huawei\s+[A-Z0-9]+)\b',
            ],
            'severity': [
                r'\b(critical|kritik|acil|urgent)\b',
                r'\b(high|yüksek|önemli)\b',
                r'\b(medium|orta|normal)\b',
                r'\b(low|düşük|minor)\b',
            ],
            'component': [
                r'(?:component|bileşen|modül):\s*([A-Za-z0-9\s]+)',
                r'\b(Login|Register|Payment|Checkout|Search|Profile)\b',
            ]
        }
        
        # Severity mapping
        self.severity_map = {
            'critical': 'Critical', 'kritik': 'Critical', 'acil': 'Critical', 'urgent': 'Critical',
            'high': 'High', 'yüksek': 'High', 'önemli': 'High',
            'medium': 'Medium', 'orta': 'Medium', 'normal': 'Medium',
            'low': 'Low', 'düşük': 'Low', 'minor': 'Low',
        }
    
    def extract_feature(self, text: str, feature_type: str) -> Optional[str]:
        """
        Extract a specific feature from text
        
        Args:
            text: Input text
            feature_type: Type of feature to extract (application, platform, version, etc.)
        
        Returns:
            Extracted feature value or None
        """
        if not isinstance(text, str) or not text.strip():
            return None
        
        patterns = self.patterns.get(feature_type, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                
                # Normalize severity
                if feature_type == 'severity':
                    value = self.severity_map.get(value.lower(), value)
                
                return value
        
        return None
    
    def extract_all_features(self, text: str, feature_types: List[str]) -> Dict[str, Optional[str]]:
        """
        Extract multiple features from text
        
        Args:
            text: Input text
            feature_types: List of feature types to extract
        
        Returns:
            Dictionary of extracted features
        """
        return {
            feature_type: self.extract_feature(text, feature_type)
            for feature_type in feature_types
        }
    
    def add_extracted_columns(
        self,
        df: pd.DataFrame,
        source_column: str,
        extract_features: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Add extracted columns to DataFrame
        
        Args:
            df: Input DataFrame
            source_column: Column to extract from (e.g., 'description')
            extract_features: Dict mapping new column name to feature type
                             Example: {'Application': 'application', 'Platform': 'platform'}
        
        Returns:
            DataFrame with new extracted columns
        """
        if source_column not in df.columns:
            logger.warning(f"Source column '{source_column}' not found in DataFrame")
            return df
        
        df = df.copy()
        
        for new_column, feature_type in extract_features.items():
            if feature_type not in self.patterns:
                logger.warning(f"Unknown feature type: {feature_type}")
                continue
            
            logger.info(f"Extracting '{feature_type}' from '{source_column}' -> '{new_column}'")
            
            # Extract feature from each row
            df[new_column] = df[source_column].apply(
                lambda text: self.extract_feature(text, feature_type)
            )
            
            extracted_count = df[new_column].notna().sum()
            logger.info(f"Extracted {extracted_count}/{len(df)} values for '{new_column}'")
        
        return df
    
    def get_available_features(self) -> List[str]:
        """Get list of available feature types"""
        return list(self.patterns.keys())
    
    def suggest_extractions(self, df: pd.DataFrame, text_column: str) -> Dict[str, int]:
        """
        Analyze text column and suggest which features can be extracted
        
        Args:
            df: Input DataFrame
            text_column: Column to analyze
        
        Returns:
            Dictionary of feature types and count of extractable values
        """
        if text_column not in df.columns:
            return {}
        
        suggestions = {}
        sample_size = min(100, len(df))  # Sample for performance
        sample_texts = df[text_column].dropna().head(sample_size)
        
        for feature_type in self.patterns.keys():
            count = sum(
                1 for text in sample_texts
                if self.extract_feature(text, feature_type) is not None
            )
            if count > 0:
                # Extrapolate to full dataset
                estimated_count = int(count * len(df) / sample_size)
                suggestions[feature_type] = estimated_count
        
        return suggestions


# Example usage
if __name__ == "__main__":
    extractor = TextFeatureExtractor()
    
    # Test examples
    test_texts = [
        "BiP uygulaması iOS 14.5'te açılmıyor. iPhone 12'de test edildi.",
        "Whatsapp Android 11'de çöküyor. Kritik hata!",
        "Login component'inde bug var. Version 2.3.1",
    ]
    
    for text in test_texts:
        print(f"\nText: {text}")
        features = extractor.extract_all_features(
            text,
            ['application', 'platform', 'version', 'device', 'severity', 'component']
        )
        print(f"Extracted: {features}")

