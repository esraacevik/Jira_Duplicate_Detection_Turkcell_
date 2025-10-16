#!/usr/bin/env python3
"""
JIRA CSV to Parquet Preprocessing Script
========================================

This script processes JIRA CSV exports and converts them to Parquet format
with comprehensive text cleaning, PII masking, structure preservation,
and language detection.

Author: ML/Data Engineer
Version: 2.0
"""

import argparse
import logging
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import warnings
from urllib.parse import urlparse

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Language detection imports with fallback
try:
    import pycld3
    CLD3_AVAILABLE = True
except ImportError:
    CLD3_AVAILABLE = False
    warnings.warn("pycld3 not available, using fallback language detection")

try:
    import fasttext
    FASTTEXT_AVAILABLE = True
except ImportError:
    FASTTEXT_AVAILABLE = False
    warnings.warn("fasttext not available, using fallback language detection")

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0  # For deterministic results
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    warnings.warn("langdetect not available, using fallback language detection")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Expected input columns
EXPECTED_COLUMNS: List[str] = [
    "Affects Version", "Component", "Description",
    "Custom field (Frequency)", "Issue Type", "Priority",
    "Custom field (Severity)", "Custom field (Problem Type)", "Summary", "App Version Enhanced"
]

# Regex patterns for various cleaning tasks
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b(?:\+?90|0)?5\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b')
MSISDN_PATTERN = re.compile(r'(?i)\b(Msisdn)\s*:\s*\+?\d{7,15}\b')
IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
ID_PATTERN = re.compile(r'\b[A-Z0-9]{8,}\b')  # Generic ID pattern

# Enhanced URL pattern for better masking
URL_PATTERN = re.compile(
    r'((?:https?|ftp)://[^\s<>()\[\]{}"\'`]+|www\.[^\s<>()\[\]{}"\'`]+)',
    re.IGNORECASE
)

# Structure preservation patterns - remove decorative asterisks only
TEST_STEPS_PATTERN = re.compile(r'^\s*\*(Test\s*Steps?)\s*:\s*\*\s*$', re.IGNORECASE | re.MULTILINE)
ACTUAL_RESULT_PATTERN = re.compile(r'^\s*\*(Actual\s*Result)\s*:\s*\*\s*$', re.IGNORECASE | re.MULTILINE)
EXPECTED_RESULT_PATTERN = re.compile(r'^\s*\*(Expected\s*Result)\s*:\s*\*\s*$', re.IGNORECASE | re.MULTILINE)

# Orphan asterisk pattern
ORPHAN_ASTERISK_PATTERN = re.compile(r'^\s*\*\s*$', re.MULTILINE)

# Metadata extraction patterns
METADATA_PATTERNS = {
    'Application Version': re.compile(r'Application\s+Version\s*:\s*([^\n\r]+)', re.IGNORECASE),
    'MSISDN': re.compile(r'MSISDN\s*:\s*([^\n\r]+)', re.IGNORECASE),
    'Carrier': re.compile(r'Carrier\s*:\s*([^\n\r]+)', re.IGNORECASE),
    'Device': re.compile(r'Device\s*:\s*([^\n\r]+)', re.IGNORECASE),
    'Device OS': re.compile(r'Device\s+OS\s*:\s*([^\n\r]+)', re.IGNORECASE),
    'Language': re.compile(r'Language\s*:\s*([^\n\r]+)', re.IGNORECASE),
    'Network status': re.compile(r'Network\s+status\s*:\s*([^\n\r]+)', re.IGNORECASE),
    'Logs URL': re.compile(r'LOGS_UPLOADED_TO_SERVER_URL:\s*([^\n\r]+)', re.IGNORECASE)
}

# Platform/OS normalization patterns (case-insensitive)
PLATFORM_PATTERNS = {
    r'\bIOS\b': 'iOS',
    r'\bAndroid\b': 'Android',
    r'\biPhone\b': 'iPhone',
    r'\biPad\b': 'iPad'
}

# Semver protection pattern (negative lookahead/behind)
SEMVER_PATTERN = re.compile(r'(?<!\d)(\d+\.\d+\.\d+)(?!\d)')
WIFI_PATTERN = re.compile(r'\bWi-Fi\b', re.IGNORECASE)


class LanguageDetector:
    """Robust language detection with multiple fallback mechanisms."""
    
    def __init__(self):
        self.fasttext_model = None
        self._load_fasttext_model()
    
    def _load_fasttext_model(self):
        """Load fastText model with automatic download."""
        if not FASTTEXT_AVAILABLE:
            return
        
        try:
            model_path = Path.home() / '.fasttext' / 'lid.176.ftz'
            model_path.parent.mkdir(exist_ok=True)
            
            if not model_path.exists():
                logger.info("Downloading fastText language identification model...")
                import urllib.request
                urllib.request.urlretrieve(
                    'https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz',
                    str(model_path)
                )
            
            self.fasttext_model = fasttext.load_model(str(model_path))
            logger.info("fastText model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load fastText model: {e}")
            self.fasttext_model = None
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language with fallback mechanisms.
        Returns (language_code, confidence_score)
        """
        if not text or len(text.strip()) < 10:
            return 'unknown', 0.0
        
        # Remove metadata block for cleaner detection
        text_for_detection = self._remove_metadata_for_detection(text)
        
        # Try CLD3 first (highest accuracy)
        if CLD3_AVAILABLE:
            try:
                result = pycld3.get_language(text_for_detection)
                if result and result[1] >= 0.80:
                    return result[0], result[1]
            except Exception as e:
                logger.debug(f"CLD3 detection failed: {e}")
        
        # Try fastText
        if self.fasttext_model:
            try:
                predictions = self.fasttext_model.predict(text_for_detection, k=1)
                if predictions and len(predictions[0]) > 0:
                    lang_code = predictions[0][0].replace('__label__', '')
                    confidence = float(predictions[1][0])
                    if confidence >= 0.80:
                        return lang_code, confidence
            except Exception as e:
                logger.debug(f"fastText detection failed: {e}")
        
        # Fallback to langdetect
        if LANGDETECT_AVAILABLE:
            try:
                lang_code = detect(text_for_detection)
                return lang_code, 0.75  # Default confidence for langdetect
            except Exception as e:
                logger.debug(f"langdetect failed: {e}")
        
        # Final fallback
        return 'unknown', 0.0
    
    def _remove_metadata_for_detection(self, text: str) -> str:
        """Remove metadata patterns from text for language detection."""
        if not text:
            return ""
        
        # Remove key-value patterns (metadata lines)
        # Pattern: "Key: Value" or "KEY: Value" or "KEY_VALUE: Value"
        metadata_pattern = re.compile(r'^\s*\w[\w ]+:\s+.+$', re.MULTILINE)
        text = metadata_pattern.sub('', text)
        
        # Remove URL patterns and placeholders
        url_pattern = re.compile(r'\[.*?PRESENT.*?\]', re.IGNORECASE)
        text = url_pattern.sub('', text)
        
        # Remove short uppercase abbreviations (≤4 chars) and model/version tokens
        short_abbrev_pattern = re.compile(r'\b[A-Z]{1,4}\b')
        text = short_abbrev_pattern.sub('', text)
        
        # Remove version/model tokens (LTE, SMS, SM-J710FQ, 3.70.16, etc.)
        version_pattern = re.compile(r'\b(?:LTE|SMS|SM-[A-Z0-9,]+|\d+\.\d+(?:\.\d+)*)\b')
        text = version_pattern.sub('', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text


class TextCleaner:
    """Comprehensive text cleaning with structure preservation."""
    
    def __init__(self):
        self.language_detector = LanguageDetector()
    
    def normalize_linebreaks(self, text: str) -> str:
        """Normalize line breaks (CRLF -> LF, multiple newlines -> single)."""
        if not text:
            return ""
        
        # Convert CRLF to LF
        text = text.replace('\r\n', '\n')
        # Convert CR to LF
        text = text.replace('\r', '\n')
        # Collapse multiple newlines to single newline
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        return text
    
    def collapse_whitespace_but_preserve_newlines(self, text: str) -> str:
        """Collapse multiple spaces/tabs but preserve newlines."""
        if not text:
            return ""
        
        # Replace multiple spaces/tabs with single space, but preserve newlines
        text = re.sub(r'[ \t]+', ' ', text)
        # Remove trailing spaces from lines
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
        return text
    
    def mask_urls(self, text: str) -> str:
        """Mask URLs while preserving domain signals and sentence structure."""
        if not text:
            return ""
        
        def url_replacer(match):
            url = match.group(1)
            
            # Handle trailing punctuation
            trailing_punct = ""
            if url.endswith(('.', ',', ';', ':', '!', '?', ')', ']', '}')):
                trailing_punct = url[-1]
                url = url[:-1]
            
            try:
                # Parse URL
                if url.startswith('www.'):
                    # Handle www. URLs
                    hostname = url[4:]  # Remove www.
                else:
                    # Handle full URLs
                    parsed = urlparse(url)
                    hostname = parsed.hostname or parsed.netloc
                
                # Remove www. prefix if present
                if hostname and hostname.startswith('www.'):
                    hostname = hostname[4:]
                
                # Keep hostname as is (IDNA handling removed for simplicity)
                
                return f'[PRESENT domain={hostname}]' + trailing_punct
                
            except Exception:
                # Fallback for malformed URLs
                return '[PRESENT]' + trailing_punct
        
        return URL_PATTERN.sub(url_replacer, text)
    
    def mask_pii(self, text: str) -> str:
        """Mask PII while preserving information signals."""
        if not text:
            return ""
        
        # Mask emails
        text = EMAIL_PATTERN.sub('[PRESENT]', text)
        
        # Mask phone numbers
        text = PHONE_PATTERN.sub('[PRESENT]', text)
        
        # Mask MSISDN with proper format
        text = MSISDN_PATTERN.sub(r'\1: [PRESENT]', text)
        
        # Mask IP addresses
        text = IP_PATTERN.sub('[PRESENT]', text)
        
        # Mask URLs with enhanced domain preservation
        text = self.mask_urls(text)
        
        # Mask generic IDs
        text = ID_PATTERN.sub('[PRESENT]', text)
        
        return text
    
    def normalize_platform_os_device(self, text: str) -> str:
        """Normalize platform/OS/device names while preserving specific formats."""
        if not text:
            return ""
        
        # Apply platform normalizations (case-insensitive)
        for pattern, replacement in PLATFORM_PATTERNS.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Additional case-insensitive normalizations
        # iOS variations
        text = re.sub(r'\bios\b', 'iOS', text, flags=re.IGNORECASE)
        text = re.sub(r'\biphone\b', 'iPhone', text, flags=re.IGNORECASE)
        text = re.sub(r'\bipad\b', 'iPad', text, flags=re.IGNORECASE)
        
        # Android variations
        text = re.sub(r'\bandroid\b', 'Android', text, flags=re.IGNORECASE)
        
        return text
    
    def normalize_semver_in_text(self, text: str) -> str:
        """Normalize semver versions while preserving dots."""
        if not text:
            return ""
        
        # Clean up version strings but preserve the dots
        def clean_version(match):
            version = match.group(1)
            # Remove extra spaces around dots but keep the dots
            cleaned = re.sub(r'\s*\.\s*', '.', version)
            return cleaned
        
        text = SEMVER_PATTERN.sub(clean_version, text)
        return text
    
    def extract_and_normalize_sections(self, text: str) -> str:
        """Extract and normalize Test Steps, Actual Result, Expected Result sections."""
        if not text:
            return ""
        
        # Canonicalize headers to exact format
        # Test Steps variations -> Test Steps:
        text = re.sub(r'^\s*\*?Test\s*Steps?\*?\s*:\s*', 'Test Steps:\n', text, flags=re.MULTILINE | re.IGNORECASE)
        # Actual Result variations -> Actual Result:
        text = re.sub(r'^\s*\*?Actual\s*Result\*?\s*:\s*', 'Actual Result:\n', text, flags=re.MULTILINE | re.IGNORECASE)
        # Expected Result variations -> Expected Result:
        text = re.sub(r'^\s*\*?Expected\s*Result\*?\s*:\s*', 'Expected Result:\n', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Remove orphan asterisks (standalone * lines)
        text = ORPHAN_ASTERISK_PATTERN.sub('', text)
        
        # Remove decorative # symbols from list items (but preserve content)
        # Pattern: # at start of line or after whitespace, followed by space
        text = re.sub(r'^\s*#\s+', '', text, flags=re.MULTILINE)
        
        # Ensure blank lines around headers
        # Before Test Steps
        text = re.sub(r'(\n|^)(Test Steps:)', r'\1\n\2', text)
        # Before Actual Result
        text = re.sub(r'(\n|^)(Actual Result:)', r'\1\n\2', text)
        # Before Expected Result
        text = re.sub(r'(\n|^)(Expected Result:)', r'\1\n\2', text)
        
        return text
    
    def normalize_unicode_and_quotes(self, text: str) -> str:
        """Normalize Unicode and smart quotes for embedding compatibility."""
        if not text:
            return ""
        
        # NFKC normalization
        text = unicodedata.normalize('NFKC', text)
        
        # Convert smart quotes to regular quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('–', '-').replace('—', '-')
        
        return text
    
    def clean_jira_markup(self, text: str) -> str:
        """Clean Jira/Confluence markup."""
        if not text:
            return ""
        
        # Remove h\d. headers (h1., h2., h3., h4., etc.)
        text = re.sub(r'^h\d+\.\s*', '', text, flags=re.MULTILINE)
        
        # Remove macro/markup patterns
        text = re.sub(r'\{code\}.*?\{code\}', '', text, flags=re.DOTALL)
        text = re.sub(r'\{panel\}.*?\{panel\}', '', text, flags=re.DOTALL)
        text = re.sub(r'^bq\.\s*', '', text, flags=re.MULTILINE)
        
        # Remove standalone markdown asterisks
        text = re.sub(r'^\s*\*+\s*$', '', text, flags=re.MULTILINE)
        
        return text
    
    def fix_permission_spacing(self, text: str) -> str:
        """Fix permission key spacing."""
        if not text:
            return ""
        
        # Fix permission spacing: CONTACT_PERMISSION:true -> CONTACT_PERMISSION: true
        permission_patterns = [
            r'CONTACT_PERMISSION:true',
            r'STORAGE_PERMISSION:true',
            r'SMS_PERMISSION:true',
            r'BATTERY_OPTIMIZATION:true'
        ]
        
        for pattern in permission_patterns:
            text = re.sub(pattern, pattern.replace(':', ': '), text)
        
        return text
    
    def standardize_metadata_keys(self, text: str) -> str:
        """Standardize metadata keys."""
        if not text:
            return ""
        
        # App Version -> Application Version
        text = re.sub(r'App Version:', 'Application Version:', text)
        
        return text
    
    def clean_description(self, text: str) -> str:
        """Clean description with structure preservation for embedding compatibility."""
        if not text:
            return ""
        
        # Step 1: Normalize Unicode and quotes
        text = self.normalize_unicode_and_quotes(text)
        
        # Step 2: Clean Jira/Confluence markup
        text = self.clean_jira_markup(text)
        
        # Step 3: Normalize line breaks
        text = self.normalize_linebreaks(text)
        
        # Step 4: Normalize sections (remove decorative asterisks only)
        text = self.extract_and_normalize_sections(text)
        
        # Step 5: Mask PII (including URLs with domain preservation)
        text = self.mask_pii(text)
        
        # Step 6: Fix permission spacing
        text = self.fix_permission_spacing(text)
        
        # Step 7: Standardize metadata keys
        text = self.standardize_metadata_keys(text)
        
        # Step 8: Normalize platform/OS/device names
        text = self.normalize_platform_os_device(text)
        
        # Step 9: Normalize semver (protect version numbers)
        text = self.normalize_semver_in_text(text)
        
        # Step 10: Case normalization for consistent embeddings
        text = text.lower()
        
        # Step 11: Collapse whitespace but preserve structure
        text = self.collapse_whitespace_but_preserve_newlines(text)
        
        return text.strip()
    
    def clean_summary(self, text: str) -> str:
        """Clean summary text for embedding compatibility."""
        if not text:
            return ""
        
        # Step 1: Normalize Unicode and quotes
        text = self.normalize_unicode_and_quotes(text)
        
        # Step 2: Clean Jira/Confluence markup
        text = self.clean_jira_markup(text)
        
        # Step 3: Mask PII (keep original case)
        text = self.mask_pii(text)
        
        # Step 4: Normalize platform/OS/device names
        text = self.normalize_platform_os_device(text)
        
        # Step 5: Normalize semver (protect version numbers)
        text = self.normalize_semver_in_text(text)
        
        # Step 6: Case normalization for consistent embeddings
        text = text.lower()
        
        # Step 7: Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """Detect language of the text."""
        return self.language_detector.detect_language(text)


def normalize_semver(version: str) -> str:
    """Normalize semver version strings."""
    if not version:
        return ""
    
    # Remove 'v' prefix and extra spaces
    version = re.sub(r'^v\s*', '', version.strip())
    # Normalize dots (remove spaces around dots)
    version = re.sub(r'\s*\.\s*', '.', version)
    return version.strip()


def load_csv_robust(file_path: str) -> pd.DataFrame:
    """Load CSV file with robust encoding/separator detection."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    encoding_options = ["utf-8", "iso-8859-1", "cp1252", "utf-8-sig"]
    separator_options = [";", ",", "\t", "|"]  # Semicolon first for JIRA exports
    
    logger.info(f"Loading CSV file: {file_path}")
    
    for encoding in encoding_options:
        for sep in separator_options:
            try:
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    sep=sep,
                    dtype=str,
                    na_values=["", "NULL", "null", "None", "N/A", "#N/A"],
                    keep_default_na=True
                )
                if len(df.columns) >= 5:
                    logger.info(f"CSV loaded successfully - Encoding: {encoding}, Separator: '{sep}'")
                    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)
                    return df
            except Exception as e:
                logger.debug(f"Attempt failed - Encoding: {encoding}, Sep: '{sep}', Error: {e}")
                continue
    
    raise ValueError("CSV file could not be loaded with any encoding/separator combination")


def validate_columns(df: pd.DataFrame) -> None:
    """Validate that all expected columns are present."""
    missing_columns = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_columns:
        available_cols = list(df.columns)
        logger.error(f"Missing columns: {missing_columns}")
        logger.info(f"Available columns: {available_cols}")
        raise ValueError(f"Required columns missing: {missing_columns}")
    logger.info("All required columns present")


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Main data processing function."""
    logger.info("Starting data processing...")
    
    # Select only required columns
    processed_df = df[EXPECTED_COLUMNS].copy()
    
    # Convert to string and handle NaN values
    for col in EXPECTED_COLUMNS:
        processed_df[col] = processed_df[col].astype(str).replace(["nan", "None", "NULL"], "")
    
    # Initialize text cleaner
    cleaner = TextCleaner()
    
    # Process each row
    logger.info("Processing text cleaning...")
    
    # Clean summaries
    processed_df["summary_clean"] = processed_df["Summary"].apply(cleaner.clean_summary)
    
    # Clean descriptions
    processed_df["description_clean"] = processed_df["Description"].apply(cleaner.clean_description)
    
    # Detect language
    logger.info("Detecting languages...")
    language_results = processed_df["description_clean"].apply(cleaner.detect_language)
    processed_df["language"] = [f"{code} ({conf:.2f})" for code, conf in language_results]
    
    # Normalize specific columns
    processed_df["Affects Version"] = processed_df["Affects Version"].apply(normalize_semver)
    
    # Rename App Version Enhanced to App Version
    if "App Version Enhanced" in processed_df.columns:
        processed_df["App Version"] = processed_df["App Version Enhanced"]
        processed_df = processed_df.drop(columns=["App Version Enhanced"])
    
    # Strip and normalize other columns
    for col in ["Component", "Issue Type", "Priority", "Custom field (Severity)", 
                "Custom field (Problem Type)", "Custom field (Frequency)", "App Version"]:
        processed_df[col] = processed_df[col].str.strip()
        processed_df[col] = processed_df[col].str.replace(r'\s+', ' ', regex=True)
    
    # Remove completely empty rows
    initial_rows = len(processed_df)
    processed_df = processed_df[
        (processed_df["summary_clean"].str.len() > 0) | 
        (processed_df["description_clean"].str.len() > 0)
    ].copy()
    removed_rows = initial_rows - len(processed_df)
    if removed_rows > 0:
        logger.info(f"Removed {removed_rows} completely empty rows")
    
    # Log masking statistics
    url_masked_count = processed_df["description_clean"].str.contains(r'\[PRESENT domain=', na=False).sum()
    present_masked_count = processed_df["description_clean"].str.contains(r'\[PRESENT\]', na=False).sum()
    msisdn_masked_count = processed_df["description_clean"].str.contains(r'MSISDN: \[PRESENT\]', na=False).sum()
    
    logger.info(f"PII masking statistics:")
    logger.info(f"  URLs masked: {url_masked_count}")
    logger.info(f"  PII items masked: {present_masked_count}")
    logger.info(f"  MSISDN masked: {msisdn_masked_count}")
    
    # Log language statistics
    lang_stats = {}
    for lang_str in processed_df["language"]:
        lang_code = lang_str.split()[0]
        lang_stats[lang_code] = lang_stats.get(lang_code, 0) + 1
    
    logger.info(f"Language detection summary: {lang_stats}")
    logger.info(f"Processing completed. Final size: {processed_df.shape}")
    
    return processed_df


def save_to_parquet(df: pd.DataFrame, output_path: Path) -> None:
    """Save DataFrame to Parquet format."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Define schema - EXCLUDING text_hash and text_combined
        schema = pa.schema([
            ("Affects Version", pa.string()),
            ("Component", pa.string()),
            ("Description", pa.string()),
            ("Custom field (Frequency)", pa.string()),
            ("Issue Type", pa.string()),
            ("Priority", pa.string()),
            ("Custom field (Severity)", pa.string()),
            ("Custom field (Problem Type)", pa.string()),
            ("Summary", pa.string()),
            ("App Version", pa.string()),
            ("summary_clean", pa.string()),
            ("description_clean", pa.string()),
            ("language", pa.string()),
        ])
        
        table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
        pq.write_table(table, output_path, compression="snappy")
        logger.info(f"Parquet file saved: {output_path}")
    except Exception as e:
        logger.error(f"Parquet save error: {e}")
        raise


def run_preprocessing(input_csv: Path, output_parquet: Path) -> None:
    """Main processing function."""
    df = load_csv_robust(str(input_csv))
    validate_columns(df)
    processed_df = process_dataframe(df)
    save_to_parquet(processed_df, output_parquet)
    logger.info("Processing completed successfully!")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert JIRA CSV to Parquet with comprehensive preprocessing"
    )
    default_input = Path(__file__).resolve().parent.parent / "data" / "data_cleaned.csv"
    default_output = Path(__file__).resolve().parent.parent / "data" / "preprocessed" / "issues_preprocessed.parquet"
    
    parser.add_argument(
        "--input_csv", 
        type=str, 
        default=str(default_input), 
        help="Input CSV file path"
    )
    parser.add_argument(
        "--output_parquet", 
        type=str, 
        default=str(default_output), 
        help="Output Parquet file path"
    )
    
    args = parser.parse_args()
    run_preprocessing(Path(args.input_csv), Path(args.output_parquet))


if __name__ == "__main__":
    main()
