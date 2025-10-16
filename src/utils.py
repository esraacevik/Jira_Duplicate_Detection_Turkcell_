import re
import unicodedata
import logging
from typing import Optional

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_PATTERN = re.compile(r"\bhttps?://\S+\b|\bwww\.[^\s]+\b", re.IGNORECASE)
IPV4_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HEX_PATTERN = re.compile(r"\b[a-f0-9]{32,64}\b", re.IGNORECASE)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```|`[^`]+`", re.MULTILINE)
MULTI_WS_PATTERN = re.compile(r"\s+")
# Yeni regex: Markdown/Jira style cleanup (*, #, h1-h6, >, etc.)
MARKUP_PATTERN = re.compile(r"[*#>\-]+|h[1-6]\.", re.IGNORECASE)
# Yeni regex: Özel karakterleri temizle (|, ", ', -, _, vb.)
SPECIAL_CHARS_PATTERN = re.compile(r'[|"\'\-_\[\]{}()<>+=!@#$%^&*~`,.:;]')


def normalize_unicode(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFC", text)
    text = "".join(ch for ch in text if (ch == "\t" or ch == "\n" or not unicodedata.category(ch).startswith("C")))
    return text


def strip_html(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return HTML_TAG_PATTERN.sub(" ", text)


def remove_code_blocks(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return CODE_BLOCK_PATTERN.sub(" ", text)


def redact_sensitive(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = EMAIL_PATTERN.sub("[EMAIL]", text)
    text = URL_PATTERN.sub("[URL]", text)
    text = IPV4_PATTERN.sub("[IP]", text)
    text = HEX_PATTERN.sub("[HEX]", text)
    return text


def remove_markup(text: str) -> str:
    """Markdown ve Jira-style işaretleri temizle"""
    if not isinstance(text, str):
        return ""
    return MARKUP_PATTERN.sub(" ", text)


def remove_special_chars_and_lowercase(text: str) -> str:
    """Özel karakterleri kaldır ve küçük harfe çevir"""
    if not isinstance(text, str):
        return ""
    # Özel karakterleri kaldır (virgül, iki nokta, nokta dahil)
    text = SPECIAL_CHARS_PATTERN.sub(" ", text)
    # Küçük harfe çevir
    text = text.lower()
    return text


def collapse_whitespace(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = MULTI_WS_PATTERN.sub(" ", text)
    return text.strip()


def basic_text_clean(text: Optional[str]) -> str:
    """Embed için uygun temizleme pipeline"""
    if not text:
        return ""
    text = normalize_unicode(text)
    text = strip_html(text)
    text = remove_code_blocks(text)
    text = redact_sensitive(text)
    text = remove_markup(text)  # Yeni adım eklendi
    text = remove_special_chars_and_lowercase(text)
    text = collapse_whitespace(text)
    return text


def setup_logging(level=logging.INFO):
    """Setup logging configuration for the pipeline"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('pipeline.log')
        ]
    )
