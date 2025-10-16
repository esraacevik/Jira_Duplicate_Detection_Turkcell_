
#!/usr/bin/env python3
"""
JIRA Duplicate Records Preprocessing Script (Excel input)
========================================================

This script processes JIRA duplicate records exported to Excel (.xlsx) and
converts them to Parquet and CSV with comprehensive text cleaning, PII masking,
URL masking with hostname preservation (including URL-encoded forms), structure
preservation, and language detection.

It keeps all preprocessing steps identical to the current duplicate
preprocessing logic and applies URL masking consistently to both
`description_clean` and `summary_clean`.

Author: ML/Data Engineer
Version: 1.0
"""

import argparse
import logging
import re
import unicodedata
from pathlib import Path
from typing import List, Tuple
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

# Expected input columns (matches the Excel file structure)
EXPECTED_COLUMNS: List[str] = [
    "Issue Type", "Priority", "Custom field (Severity)",
    "Affects Version/s", "Component/s", "Custom field (Frequency)", "Summary", "Description"
]

# Regex patterns for various cleaning tasks (kept identical)
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b(?:\+?90|0)?5\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b')
MSISDN_PATTERN = re.compile(r'(?i)\b(Msisdn)\s*:\s*\+?\d{7,15}\b')
IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
ID_PATTERN = re.compile(r'\b[A-Z0-9]{8,}\b')  # Generic ID pattern

# Enhanced URL pattern including encoded variants (from preprocess_jira.py)
URL_PATTERN = re.compile(
    r'((?:https?|ftp)://[^\s<>()\[\]{}"\'`]+|www\.[^\s<>()\[\]{}"\'`]+|https?%3A%2F%2F[^\s<>()\[\]{}"\'`]+|http%3A%2F%2F[^\s<>()\[\]{}"\'`]+)',
    re.IGNORECASE
)

# Structure preservation patterns - remove decorative asterisks only
TEST_STEPS_PATTERN = re.compile(r'^\s*\*(Test\s*Steps?)\s*:\s*\*\s*$', re.IGNORECASE | re.MULTILINE)
ACTUAL_RESULT_PATTERN = re.compile(r'^\s*\*(Actual\s*Result)\s*:\s*\*\s*$', re.IGNORECASE | re.MULTILINE)
EXPECTED_RESULT_PATTERN = re.compile(r'^\s*\*(Expected\s*Result)\s*:\s*\*\s*$', re.IGNORECASE | re.MULTILINE)

# Orphan asterisk pattern
ORPHAN_ASTERISK_PATTERN = re.compile(r'^\s*\*\s*$', re.MULTILINE)

# Platform/OS normalization patterns
PLATFORM_PATTERNS = {
    r'\bIOS\b': 'iOS',
    r'\bAndroid\b': 'Android',
    r'\biPhone\b': 'iPhone',
    r'\biPad\b': 'iPad'
}

# Semver protection pattern (negative lookahead/behind)
SEMVER_PATTERN = re.compile(r'(?<!\d)(\d+\.\d+\.\d+)(?!\d)')

TURKISH_CHAR_MAPPINGS = {}


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

        text_for_detection = self._remove_metadata_for_detection(text)

        if CLD3_AVAILABLE:
            try:
                result = pycld3.get_language(text_for_detection)
                if result and result[1] >= 0.80:
                    return result[0], result[1]
            except Exception as e:
                logger.debug(f"CLD3 detection failed: {e}")

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

        if LANGDETECT_AVAILABLE:
            try:
                lang_code = detect(text_for_detection)
                return lang_code, 0.75
            except Exception as e:
                logger.debug(f"langdetect failed: {e}")

        return 'unknown', 0.0

    def _remove_metadata_for_detection(self, text: str) -> str:
        """Remove metadata patterns from text for language detection."""
        if not text:
            return ""

        metadata_pattern = re.compile(r'^\s*\w[\w ]+:\s+.+$', re.MULTILINE)
        text = metadata_pattern.sub('', text)

        url_pattern = re.compile(r'\[.*?PRESENT.*?\]', re.IGNORECASE)
        text = url_pattern.sub('', text)

        short_abbrev_pattern = re.compile(r'\b[A-Z]{1,4}\b')
        text = short_abbrev_pattern.sub('', text)

        version_pattern = re.compile(r'\b(?:LTE|SMS|SM-[A-Z0-9,]+|\d+\.\d+(?:\.\d+)*)\b')
        text = version_pattern.sub('', text)

        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text


def fix_turkish_characters(text: str) -> str:
    # No-op to mirror preprocessnew/preprocess_duplicates.py behavior
    return text


class TextCleaner:
    """Comprehensive text cleaning with structure preservation."""

    def __init__(self):
        self.language_detector = LanguageDetector()

    def normalize_linebreaks(self, text: str) -> str:
        """Normalize line breaks (CRLF -> LF, multiple newlines -> single)."""
        if not text:
            return ""
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        return text

    def collapse_whitespace_but_preserve_newlines(self, text: str) -> str:
        """Collapse multiple spaces/tabs but preserve newlines."""
        if not text:
            return ""
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
        return text

    def mask_urls(self, text: str) -> str:
        """Mask URLs while preserving domain signals and sentence structure."""
        if not text:
            return ""

        def url_replacer(match):
            url = match.group(1)

            trailing_punct = ""
            if url.endswith(('.', ',', ';', ':', '!', '?', ')', ']', '}')):
                trailing_punct = url[-1]
                url = url[:-1]

            try:
                # Handle URL-encoded variants (https%3A%2F%2F...)
                if url.startswith(('http%3A%2F%2F', 'https%3A%2F%2F')):
                    import urllib.parse
                    decoded_url = urllib.parse.unquote(url)
                    parsed = urlparse(decoded_url)
                    hostname = parsed.hostname or parsed.netloc
                elif url.startswith('www.'):
                    hostname = url[4:]
                else:
                    parsed = urlparse(url)
                    hostname = parsed.hostname or parsed.netloc

                if hostname and hostname.startswith('www.'):
                    hostname = hostname[4:]

                return f'[PRESENT domain={hostname}]' + trailing_punct
            except Exception:
                return '[PRESENT]' + trailing_punct

        return URL_PATTERN.sub(url_replacer, text)

    def mask_pii(self, text: str) -> str:
        """Mask PII while preserving information signals."""
        if not text:
            return ""
        text = EMAIL_PATTERN.sub('[PRESENT]', text)
        text = PHONE_PATTERN.sub('[PRESENT]', text)
        text = MSISDN_PATTERN.sub(r'\1: [PRESENT]', text)
        text = IP_PATTERN.sub('[PRESENT]', text)
        text = self.mask_urls(text)
        text = ID_PATTERN.sub('[PRESENT]', text)
        return text

    def normalize_platform_os_device(self, text: str) -> str:
        if not text:
            return ""
        for pattern, replacement in PLATFORM_PATTERNS.items():
            text = re.sub(pattern, replacement, text)
        return text

    def normalize_semver_in_text(self, text: str) -> str:
        if not text:
            return ""
        def clean_version(match):
            version = match.group(1)
            cleaned = re.sub(r'\s*\.\s*', '.', version)
            return cleaned
        text = SEMVER_PATTERN.sub(clean_version, text)
        return text

    def extract_and_normalize_sections(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'^\s*\*?Test\s*Steps\*?\s*:\s*', 'Test Steps:\n', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'^\s*\*?Actual\s*Result\*?\s*:\s*', 'Actual Result:\n', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'^\s*\*?Expected\s*Result\*?\s*:\s*', 'Expected Result:\n', text, flags=re.MULTILINE | re.IGNORECASE)
        text = ORPHAN_ASTERISK_PATTERN.sub('', text)
        text = re.sub(r'^\s*#\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'(\n|^)(Test Steps:)', r'\1\n\2', text)
        text = re.sub(r'(\n|^)(Actual Result:)', r'\1\n\2', text)
        text = re.sub(r'(\n|^)(Expected Result:)', r'\1\n\2', text)
        return text

    def normalize_unicode_and_quotes(self, text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize('NFKC', text)
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('’', "'").replace('‘', "'")
        text = text.replace('–', '-').replace('—', '-')
        return text

    def clean_jira_markup(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'^h\d+\.\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\{code\}.*?\{code\}', '', text, flags=re.DOTALL)
        text = re.sub(r'\{panel\}.*?\{panel\}', '', text, flags=re.DOTALL)
        text = re.sub(r'^bq\.\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\*+\s*$', '', text, flags=re.MULTILINE)
        return text

    def fix_permission_spacing(self, text: str) -> str:
        if not text:
            return ""
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
        if not text:
            return ""
        text = re.sub(r'App Version:', 'Application Version:', text)
        return text

    def clean_description(self, text: str) -> str:
        if not text:
            return ""
        text = self.normalize_unicode_and_quotes(text)
        text = self.clean_jira_markup(text)
        text = self.normalize_linebreaks(text)
        text = self.extract_and_normalize_sections(text)
        text = self.mask_pii(text)
        text = self.fix_permission_spacing(text)
        text = self.standardize_metadata_keys(text)
        text = self.normalize_platform_os_device(text)
        text = self.normalize_semver_in_text(text)
        text = self.collapse_whitespace_but_preserve_newlines(text)
        return text.strip()

    def clean_summary(self, text: str) -> str:
        if not text:
            return ""
        text = self.normalize_unicode_and_quotes(text)
        text = self.clean_jira_markup(text)
        text = self.mask_pii(text)
        text = self.normalize_platform_os_device(text)
        text = self.normalize_semver_in_text(text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def detect_language(self, text: str) -> Tuple[str, float]:
        return self.language_detector.detect_language(text)


def normalize_semver(version: str) -> str:
    if not version:
        return ""
    version = re.sub(r'^v\s*', '', version.strip())
    version = re.sub(r'\s*\.\s*', '.', version)
    return version.strip()


def load_excel_robust(file_path: str) -> pd.DataFrame:
    """Load Excel (.xlsx) file with robust settings."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Loading Excel file: {file_path}")
    try:
        df = pd.read_excel(
            file_path,
            dtype=str,
            engine=None  # Let pandas choose available engine
        )
        # Normalize column names (strip BOMs/spaces)
        df.columns = df.columns.astype(str).str.strip().str.replace("\ufeff", "", regex=False)
        return df
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        raise


def validate_columns(df: pd.DataFrame) -> None:
    missing_columns = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_columns:
        available_cols = list(df.columns)
        logger.error(f"Missing columns: {missing_columns}")
        logger.info(f"Available columns: {available_cols}")
        raise ValueError(f"Required columns missing: {missing_columns}")
    logger.info("All required columns present")


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting data processing...")

    # Select only required columns
    processed_df = df[EXPECTED_COLUMNS].copy()

    # Convert to string and handle NaN values
    for col in EXPECTED_COLUMNS:
        processed_df[col] = processed_df[col].astype(str).replace(["nan", "None", "NULL"], "")

    # No issue-type filtering in preprocessnew/preprocess_duplicates.py

    # Initialize text cleaner
    cleaner = TextCleaner()

    # Process text cleaning
    logger.info("Processing text cleaning...")
    processed_df["summary_clean"] = processed_df["Summary"].apply(cleaner.clean_summary)
    processed_df["description_clean"] = processed_df["Description"].apply(cleaner.clean_description)

    # Detect language
    logger.info("Detecting languages...")
    language_results = processed_df["description_clean"].apply(cleaner.detect_language)
    processed_df["language"] = [f"{code} ({conf:.2f})" for code, conf in language_results]

    # Normalize specific columns
    processed_df["Affects Version/s"] = processed_df["Affects Version/s"].apply(normalize_semver)

    # Strip and normalize other columns
    for col in ["Component/s", "Issue Type", "Priority", "Custom field (Severity)",
                "Custom field (Frequency)"]:
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

    logger.info("PII masking statistics:")
    logger.info(f"  URLs masked: {url_masked_count}")
    logger.info(f"  PII items masked: {present_masked_count}")
    logger.info(f"  MSISDN masked: {msisdn_masked_count}")

    # Language stats
    lang_stats = {}
    for lang_str in processed_df["language"]:
        lang_code = lang_str.split()[0]
        lang_stats[lang_code] = lang_stats.get(lang_code, 0) + 1
    logger.info(f"Language detection summary: {lang_stats}")
    logger.info(f"Processing completed. Final size: {processed_df.shape}")

    return processed_df


def save_to_parquet(df: pd.DataFrame, output_path: Path) -> None:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        schema = pa.schema([
            ("Issue Type", pa.string()),
            ("Priority", pa.string()),
            ("Custom field (Severity)", pa.string()),
            ("Affects Version/s", pa.string()),
            ("Component/s", pa.string()),
            ("Custom field (Frequency)", pa.string()),
            ("Summary", pa.string()),
            ("Description", pa.string()),
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


def save_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8', sep=';')
        logger.info(f"CSV file saved: {output_path}")
    except Exception as e:
        logger.error(f"CSV save error: {e}")
        raise


def run_preprocessing(input_xlsx: Path, output_parquet: Path, output_csv: Path) -> None:
    df = load_excel_robust(str(input_xlsx))
    validate_columns(df)
    processed_df = process_dataframe(df)
    save_to_parquet(processed_df, output_parquet)
    save_to_csv(processed_df, output_csv)
    logger.info("Processing completed successfully!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preprocess JIRA duplicate records from Excel and save Parquet/CSV"
    )

    # Defaults aligned with project structure
    project_root = Path(__file__).resolve().parents[3]
    data_dir = project_root / "bug-deduplication" / "data"
    default_input = data_dir / "duplike1full.xlsx"
    default_output_parquet = data_dir / "preprocessed" / "duplicates_preprocessed.parquet"
    default_output_csv = data_dir / "preprocessed" / "duplicates_preprocessed.csv"

    parser.add_argument(
        "--input_xlsx",
        type=str,
        default=str(default_input),
        help="Input Excel (.xlsx) file path"
    )
    parser.add_argument(
        "--output_parquet",
        type=str,
        default=str(default_output_parquet),
        help="Output Parquet file path"
    )
    parser.add_argument(
        "--output_csv",
        type=str,
        default=str(default_output_csv),
        help="Output CSV file path"
    )

    args = parser.parse_args()
    run_preprocessing(Path(args.input_xlsx), Path(args.output_parquet), Path(args.output_csv))


if __name__ == "__main__":
    main()


