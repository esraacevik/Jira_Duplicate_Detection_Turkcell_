#!/usr/bin/env python3
"""
CSV Encoding Fix Script
=======================

This script detects and fixes encoding issues in CSV files, particularly
for mixed English-Turkish content that has been corrupted during export.

Author: ML/Data Engineer
Version: 1.0
"""

import argparse
import logging
try:
    import chardet  # optional
except Exception:  # pragma: no cover
    chardet = None
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
import warnings

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Common encodings to try for Turkish content
TURKISH_ENCODINGS = [
    'utf-8',
    'utf-8-sig',
    'iso-8859-9',  # Latin-5 (Turkish)
    'cp1254',      # Windows Turkish
    'latin1',      # ISO-8859-1
    'cp1252',      # Windows Western European
    'iso-8859-1',
    'ascii'
]

# Character mapping for common Turkish encoding issues
TURKISH_CHAR_MAPPINGS = {
    # Common corrupted Turkish characters
    'Ã§': 'ç',
    'Ã¼': 'ü',
    'Ã¶': 'ö',
    'Ã': 'ı',
    'Ã': 'ş',
    'Ã': 'ğ',
    'Ã': 'İ',
    'Ã': 'Ş',
    'Ã': 'Ğ',
    'Ã': 'Ü',
    'Ã': 'Ö',
    'Ã': 'Ç',
    
    # Double-encoded patterns
    'ÃƒÂ§': 'ç',
    'ÃƒÂ¼': 'ü',
    'ÃƒÂ¶': 'ö',
    'ÃƒÂ': 'ı',
    'ÃƒÂ': 'ş',
    'ÃƒÂ': 'ğ',
    'ÃƒÂ': 'İ',
    'ÃƒÂ': 'Ş',
    'ÃƒÂ': 'Ğ',
    'ÃƒÂ': 'Ü',
    'ÃƒÂ': 'Ö',
    'ÃƒÂ': 'Ç',
    
    # More complex patterns
    'Ãƒ1â„4ÃƒÂ§': 'ç',
    'Ãƒ1â„4ÃƒÂ¼': 'ü',
    'Ãƒ1â„4ÃƒÂ¶': 'ö',
    'Ãƒ1â„4ÃƒÂ': 'ı',
    'Ãƒ1â„4ÃƒÂ': 'ş',
    'Ãƒ1â„4ÃƒÂ': 'ğ',
    'Ãƒ1â„4ÃƒÂ': 'İ',
    'Ãƒ1â„4ÃƒÂ': 'Ş',
    'Ãƒ1â„4ÃƒÂ': 'Ğ',
    'Ãƒ1â„4ÃƒÂ': 'Ü',
    'Ãƒ1â„4ÃƒÂ': 'Ö',
    'Ãƒ1â„4ÃƒÂ': 'Ç',
    
    # Additional patterns found in your data
    'KÃƒ1â„4ÃƒÂ§Ãƒ1â„4k': 'Kıçık',  # Example from your data
    'ÃƒÂ§Ãƒ1â„4k': 'çık',
    'ÃƒÂ¼Ãƒ1â„4': 'ü',
    'ÃƒÂ¶Ãƒ1â„4': 'ö',
    'ÃƒÂÃƒ1â„4': 'ı',
    'ÃƒÂÃƒ1â„4': 'ş',
    'ÃƒÂÃƒ1â„4': 'ğ',
    
    # Specific patterns found in your data
    'AraÅtÄ±rma': 'Araştırma',
    'Ä°nceleme': 'İnceleme',
    'soralÄ±m': 'soralım',
    'Å': 'ş',
    'Ä': 'ı',
    'Ä°': 'İ',
    'Â': '',  # Remove this character
    'Â ': ' ',  # Replace with space
}


def detect_encoding(file_path: str) -> Tuple[str, float]:
    """
    Detect the encoding of a file using chardet.
    Returns (encoding, confidence)
    """
    logger.info(f"Detecting encoding for: {file_path}")
    
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()

        if chardet is not None:
            result = chardet.detect(raw_data)
            encoding = result.get('encoding')
            confidence = float(result.get('confidence', 0.0))
            logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
            return encoding or 'utf-8', confidence
        else:
            logger.info("chardet not available; defaulting to utf-8 detection fallback")
            return 'utf-8', 0.0
    except Exception as e:
        logger.warning(f"Encoding detection failed: {e}")
        return 'utf-8', 0.0


def try_encoding(file_path: str, encoding: str) -> Optional[pd.DataFrame]:
    """
    Try to read CSV with specific encoding.
    Returns DataFrame if successful, None if failed.
    """
    try:
        df = pd.read_csv(
            file_path,
            encoding=encoding,
            sep=';',
            dtype=str,
            na_values=["", "NULL", "null", "None", "N/A", "#N/A"],
            keep_default_na=True,
            on_bad_lines='skip'  # Skip bad lines instead of failing
        )
        logger.info(f"Successfully read with encoding: {encoding}")
        return df
    except Exception as e:
        logger.debug(f"Failed to read with encoding {encoding}: {e}")
        return None


def load_csv_with_encoding_detection(file_path: str) -> pd.DataFrame:
    """
    Load CSV file with automatic encoding detection and fallback.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # First, try chardet detection
    detected_encoding, confidence = detect_encoding(file_path)
    
    # Try detected encoding first
    if detected_encoding and confidence > 0.7:
        df = try_encoding(file_path, detected_encoding)
        if df is not None:
            return df
    
    # Try common Turkish encodings
    logger.info("Trying common Turkish encodings...")
    for encoding in TURKISH_ENCODINGS:
        if encoding == detected_encoding:
            continue  # Already tried
        
        df = try_encoding(file_path, encoding)
        if df is not None:
            logger.info(f"Successfully loaded with encoding: {encoding}")
            return df
    
    # If all else fails, try with errors='ignore'
    logger.warning("All encoding attempts failed, trying with errors='ignore'")
    try:
        df = pd.read_csv(
            file_path,
            encoding='utf-8',
            sep=';',
            dtype=str,
            na_values=["", "NULL", "null", "None", "N/A", "#N/A"],
            keep_default_na=True,
            on_bad_lines='skip',
            encoding_errors='ignore'
        )
        logger.warning("Loaded with UTF-8 and errors='ignore' - some characters may be lost")
        return df
    except Exception as e:
        raise ValueError(f"Could not load CSV file with any encoding: {e}")


def fix_turkish_characters(text: str) -> str:
    """
    Fix corrupted Turkish characters using mapping table.
    """
    if not isinstance(text, str) or pd.isna(text):
        return text
    
    # Apply character mappings
    for corrupted, correct in TURKISH_CHAR_MAPPINGS.items():
        text = text.replace(corrupted, correct)
    
    return text


def fix_dataframe_encoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix encoding issues in the entire DataFrame.
    """
    logger.info("Fixing Turkish character encoding...")
    
    # Create a copy to avoid modifying original
    fixed_df = df.copy()
    
    # Apply character fixing to all string columns
    for column in fixed_df.columns:
        if fixed_df[column].dtype == 'object':  # String columns
            logger.info(f"Fixing encoding in column: {column}")
            fixed_df[column] = fixed_df[column].apply(fix_turkish_characters)
    
    # Log some statistics
    total_cells = len(fixed_df) * len(fixed_df.columns)
    logger.info(f"Processed {total_cells} cells for encoding fixes")
    
    return fixed_df


def save_cleaned_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Save DataFrame to CSV with proper UTF-8 encoding.
    """
    logger.info(f"Saving cleaned CSV to: {output_path}")
    
    try:
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save with UTF-8 encoding and semicolon separator
        df.to_csv(
            output_path,
            index=False,
            encoding='utf-8',
            sep=';',
            na_rep=''
        )
        
        logger.info(f"Successfully saved cleaned CSV: {output_path}")
        
        # Log file size
        file_size = Path(output_path).stat().st_size
        logger.info(f"Output file size: {file_size:,} bytes")
        
    except Exception as e:
        logger.error(f"Failed to save CSV: {e}")
        raise


def log_sample_data(df: pd.DataFrame, num_rows: int = 3) -> None:
    """
    Log sample data to verify the fix worked.
    """
    logger.info("Sample of cleaned data:")
    
    for i in range(min(num_rows, len(df))):
        logger.info(f"Row {i+1}:")
        for col in df.columns:
            value = str(df.iloc[i][col])[:100]  # First 100 chars
            logger.info(f"  {col}: {value}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fix encoding issues in CSV files with Turkish characters"
    )
    
    project_root = Path(__file__).resolve().parents[3]
    data_dir = project_root / "bug-deduplication" / "data" / "preprocessed"
    default_input = data_dir / "duplicates_preprocessed.csv"
    default_output = data_dir / "duplicates_cleaned.csv"
    
    parser.add_argument(
        "--input_csv",
        type=str,
        default=str(default_input),
        help="Input CSV file path"
    )
    parser.add_argument(
        "--output_csv",
        type=str,
        default=str(default_output),
        help="Output cleaned CSV file path"
    )
    
    args = parser.parse_args()
    
    try:
        # Step 1: Load CSV with encoding detection
        logger.info("=" * 50)
        logger.info("STEP 1: Loading CSV with encoding detection")
        logger.info("=" * 50)
        df = load_csv_with_encoding_detection(args.input_csv)
        logger.info(f"Loaded DataFrame shape: {df.shape}")
        
        # Step 2: Fix Turkish character encoding
        logger.info("=" * 50)
        logger.info("STEP 2: Fixing Turkish character encoding")
        logger.info("=" * 50)
        fixed_df = fix_dataframe_encoding(df)
        
        # Step 3: Save cleaned CSV
        logger.info("=" * 50)
        logger.info("STEP 3: Saving cleaned CSV")
        logger.info("=" * 50)
        save_cleaned_csv(fixed_df, args.output_csv)
        
        # Step 4: Log sample data
        logger.info("=" * 50)
        logger.info("STEP 4: Verification")
        logger.info("=" * 50)
        log_sample_data(fixed_df)
        
        logger.info("=" * 50)
        logger.info("ENCODING FIX COMPLETED SUCCESSFULLY!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        raise


if __name__ == "__main__":
    main()
