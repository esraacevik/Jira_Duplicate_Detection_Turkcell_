#!/usr/bin/env python3
"""
Unit tests for JIRA preprocessing script
========================================

Tests all acceptance criteria and functionality of the preprocessing pipeline.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from preprocess_jira import (
    TextCleaner, LanguageDetector, normalize_semver,
    load_csv_robust, validate_columns, process_dataframe,
    save_to_parquet, run_preprocessing
)


class TestTextCleaner:
    """Test TextCleaner functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.cleaner = TextCleaner()
    
    def test_semver_and_device_preservation(self):
        """Test that semver and device names are preserved correctly."""
        test_description = """
        *Test Steps:*
        UserA (Android) opens social tab
        joins a social group chat
        Sends messages
        UserB (IOS) user joins chat
        Last 50 posts do not appear for UserB (IOS)

        *Actual Result:*
        The last 50 messages do not appear on the IOS device. The last 20 messages appear.

        *Expected Result:*
        The last 50 messages are expected to appear as on the Android device.

        Application Version : 3.70.16
        Msisdn : 905368658527
        Carrier : Turkcell
        Device : iPhone12,5
        Device OS : 14.3
        Language 
        : tr-DE
        Network status : Wi-Fi
        LOGS_UPLOADED_TO_SERVER_URL: https://swf.tvoip.turkcell.com.tr/v1/AUTH_8b55f84760274c9599382d2e337a57cf/3c65843d0c79b98c6d2a66a6ce349c3e/logs/29122020/09/logs/applicationlogs.zip
        """
        
        result = self.cleaner.clean_description(test_description)
        
        # Acceptance criteria assertions
        assert "3.70.16" in result, "Semver version should be preserved"
        assert "iPhone12,5" in result, "Device name should be preserved"
        assert "Wi-Fi" in result, "Wi-Fi should be preserved"
    
    def test_platform_normalization(self):
        """Test platform name normalization."""
        test_text = "UserA (Android) opens social tab, UserB (IOS) user joins chat"
        result = self.cleaner.clean_description(test_text)
        
        assert "(Android)" in result, "Android should be normalized"
        assert "(iOS)" in result, "IOS should be normalized to iOS"
    
    def test_structure_headers(self):
        """Test that structure headers are properly formatted."""
        test_description = """
        *Test Steps:*
        UserA opens app
        
        *Actual Result:*
        App crashes
        
        *Expected Result:*
        App should work
        """
        
        result = self.cleaner.clean_description(test_description)
        
        assert "## TEST_STEPS" in result, "Test Steps header should be normalized"
        assert "## ACTUAL_RESULT" in result, "Actual Result header should be normalized"
        assert "## EXPECTED_RESULT" in result, "Expected Result header should be normalized"
    
    def test_metadata_extraction(self):
        """Test metadata extraction and formatting."""
        test_description = """
        Some description text here.
        
        Application Version : 3.70.16
        Msisdn : 905368658527
        Carrier : Turkcell
        Device : iPhone12,5
        Device OS : 14.3
        Language : tr-DE
        Network status : Wi-Fi
        LOGS_UPLOADED_TO_SERVER_URL: https://swf.tvoip.turkcell.com.tr/v1/AUTH_8b55f84760274c9599382d2e337a57cf/3c65843d0c79b98c6d2a66a6ce349c3e/logs/29122020/09/logs/applicationlogs.zip
        """
        
        result = self.cleaner.clean_description(test_description)
        
        assert "## METADATA" in result, "Metadata block should be present"
        assert "Application_Version=3.70.16" in result, "Application version should be extracted"
        assert "MSISDN=[PRESENT]" in result, "MSISDN should be masked"
        assert "Carrier=Turkcell" in result, "Carrier should be extracted"
        assert "Device=iPhone12,5" in result, "Device should be extracted"
        assert "Device_OS=14.3" in result, "Device OS should be extracted"
        assert "Language_Code=tr-DE" in result, "Language should be extracted and normalized"
        assert "Network_Status=Wi-Fi" in result, "Network status should be extracted"
        assert "Logs_URL=[PRESENT domain=swf.tvoip.turkcell.com.tr]" in result, "Logs URL should be masked with domain"
    
    def test_pii_masking(self):
        """Test PII masking functionality."""
        test_text = """
        Contact us at test@example.com or call 905368658527
        Visit https://example.com/path for more info
        IP: 192.168.1.1
        """
        
        result = self.cleaner.clean_description(test_text)
        
        # PII should be masked
        assert "905368658527" not in result, "Phone number should be masked"
        assert "test@example.com" not in result, "Email should be masked"
        assert "192.168.1.1" not in result, "IP address should be masked"
        assert "https://example.com/path" not in result, "Full URL should be masked"
        
        # But signals should be preserved
        assert "[EMAIL_PRESENT]" in result, "Email presence signal should be preserved"
        assert "[PHONE_PRESENT]" in result, "Phone presence signal should be preserved"
        assert "[IP_PRESENT]" in result, "IP presence signal should be preserved"
        assert "[PRESENT domain=example.com]" in result, "URL domain signal should be preserved"
    
    def test_line_break_normalization(self):
        """Test line break normalization."""
        test_text = "Line 1\r\nLine 2\r\n\r\nLine 3"
        result = self.cleaner.normalize_linebreaks(test_text)
        expected = "Line 1\nLine 2\n\nLine 3"
        assert result == expected, "Line breaks should be normalized"
    
    def test_whitespace_collapse_preserve_newlines(self):
        """Test whitespace collapse while preserving newlines."""
        test_text = "Line 1   with   spaces\n\nLine 2\twith\ttabs"
        result = self.cleaner.collapse_whitespace_but_preserve_newlines(test_text)
        expected = "Line 1 with spaces\n\nLine 2 with tabs"
        assert result == expected, "Whitespace should be collapsed but newlines preserved"


class TestLanguageDetector:
    """Test language detection functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.detector = LanguageDetector()
    
    def test_english_detection(self):
        """Test English language detection."""
        english_text = """
        This is a test description in English.
        The application should work properly.
        User reported an issue with the login functionality.
        """
        
        code, confidence = self.detector.detect_language(english_text)
        assert code == "en", f"Expected 'en', got '{code}'"
        assert confidence >= 0.80, f"Expected confidence >= 0.80, got {confidence}"
    
    def test_metadata_removal_for_detection(self):
        """Test that metadata is removed for language detection."""
        text_with_metadata = """
        This is English text for testing.
        
        ## METADATA
        Application_Version=3.70.16
        MSISDN=[PRESENT]
        """
        
        # The detection should work on the English part, not be confused by metadata
        code, confidence = self.detector.detect_language(text_with_metadata)
        assert code == "en", f"Expected 'en', got '{code}'"
        assert confidence >= 0.50, f"Expected reasonable confidence, got {confidence}"


class TestNormalizeSemver:
    """Test semver normalization."""
    
    def test_basic_semver_normalization(self):
        """Test basic semver normalization."""
        assert normalize_semver("v 3.70.16 ") == "3.70.16"
        assert normalize_semver("3.70.16") == "3.70.16"
        assert normalize_semver("v3.70.16") == "3.70.16"
        assert normalize_semver("") == ""
        assert normalize_semver(None) == ""


class TestDataProcessing:
    """Test data processing pipeline."""
    
    def test_output_schema(self):
        """Test that output schema is correct (no text_hash, text_combined)."""
        # Create test data
        test_data = {
            "Affects Version": ["3.70.16"],
            "Component": ["Android Client"],
            "Description": ["Test description"],
            "Custom field (Frequency)": ["High"],
            "Issue Type": ["Bug"],
            "Priority": ["High"],
            "Custom field (Severity)": ["Critical"],
            "Custom field (Problem Type)": ["Functional"],
            "Summary": ["Test summary"]
        }
        
        df = pd.DataFrame(test_data)
        processed_df = process_dataframe(df)
        
        # Check that required columns are present
        required_columns = [
            "Affects Version", "Component", "Description",
            "Custom field (Frequency)", "Issue Type", "Priority",
            "Custom field (Severity)", "Custom field (Problem Type)", "Summary",
            "summary_clean", "description_clean", "language"
        ]
        
        for col in required_columns:
            assert col in processed_df.columns, f"Required column '{col}' missing"
        
        # Check that forbidden columns are NOT present
        forbidden_columns = ["text_hash", "text_combined"]
        for col in forbidden_columns:
            assert col not in processed_df.columns, f"Forbidden column '{col}' should not be present"
    
    def test_empty_row_removal(self):
        """Test that completely empty rows are removed."""
        test_data = {
            "Affects Version": ["3.70.16", "", ""],
            "Component": ["Android Client", "", ""],
            "Description": ["Test description", "", ""],
            "Custom field (Frequency)": ["High", "", ""],
            "Issue Type": ["Bug", "", ""],
            "Priority": ["High", "", ""],
            "Custom field (Severity)": ["Critical", "", ""],
            "Custom field (Problem Type)": ["Functional", "", ""],
            "Summary": ["Test summary", "", ""]
        }
        
        df = pd.DataFrame(test_data)
        processed_df = process_dataframe(df)
        
        # Should have only 1 row (the non-empty one)
        assert len(processed_df) == 1, f"Expected 1 row, got {len(processed_df)}"
    
    def test_language_column_format(self):
        """Test that language column has correct format."""
        test_data = {
            "Affects Version": ["3.70.16"],
            "Component": ["Android Client"],
            "Description": ["This is a test description in English for language detection."],
            "Custom field (Frequency)": ["High"],
            "Issue Type": ["Bug"],
            "Priority": ["High"],
            "Custom field (Severity)": ["Critical"],
            "Custom field (Problem Type)": ["Functional"],
            "Summary": ["Test summary"]
        }
        
        df = pd.DataFrame(test_data)
        processed_df = process_dataframe(df)
        
        language_value = processed_df["language"].iloc[0]
        # Should be in format "en (0.95)" or similar
        assert "(" in language_value and ")" in language_value, f"Language format incorrect: {language_value}"
        assert language_value.split()[0] in ["en", "unknown"], f"Expected 'en' or 'unknown', got {language_value.split()[0]}"


class TestCSVLoading:
    """Test CSV loading functionality."""
    
    def test_csv_loading_with_semicolon(self):
        """Test CSV loading with semicolon separator."""
        # Create temporary CSV file
        test_data = """Affects Version;Component;Description;Custom field (Frequency);Issue Type;Priority;Custom field (Severity);Custom field (Problem Type);Summary
3.70.16;Android Client;Test description;High;Bug;High;Critical;Functional;Test summary"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(test_data)
            temp_path = f.name
        
        try:
            df = load_csv_robust(temp_path)
            assert len(df) == 1, "Should load 1 row"
            assert "Affects Version" in df.columns, "Should have correct columns"
        finally:
            os.unlink(temp_path)
    
    def test_column_validation(self):
        """Test column validation."""
        # Test with correct columns
        correct_data = {
            "Affects Version": ["3.70.16"],
            "Component": ["Android Client"],
            "Description": ["Test description"],
            "Custom field (Frequency)": ["High"],
            "Issue Type": ["Bug"],
            "Priority": ["High"],
            "Custom field (Severity)": ["Critical"],
            "Custom field (Problem Type)": ["Functional"],
            "Summary": ["Test summary"]
        }
        
        df = pd.DataFrame(correct_data)
        # Should not raise exception
        validate_columns(df)
        
        # Test with missing columns
        incomplete_data = {
            "Affects Version": ["3.70.16"],
            "Component": ["Android Client"]
        }
        
        df_incomplete = pd.DataFrame(incomplete_data)
        with pytest.raises(ValueError, match="Required columns missing"):
            validate_columns(df_incomplete)


class TestParquetSaving:
    """Test Parquet saving functionality."""
    
    def test_parquet_schema(self):
        """Test that Parquet schema is correct."""
        test_data = {
            "Affects Version": ["3.70.16"],
            "Component": ["Android Client"],
            "Description": ["Test description"],
            "Custom field (Frequency)": ["High"],
            "Issue Type": ["Bug"],
            "Priority": ["High"],
            "Custom field (Severity)": ["Critical"],
            "Custom field (Problem Type)": ["Functional"],
            "Summary": ["Test summary"],
            "summary_clean": ["test summary"],
            "description_clean": ["test description"],
            "language": ["en (0.95)"]
        }
        
        df = pd.DataFrame(test_data)
        
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            save_to_parquet(df, temp_path)
            
            # Read back and verify
            import pyarrow.parquet as pq
            table = pq.read_table(temp_path)
            
            # Check schema
            schema = table.schema
            expected_fields = [
                "Affects Version", "Component", "Description",
                "Custom field (Frequency)", "Issue Type", "Priority",
                "Custom field (Severity)", "Custom field (Problem Type)", "Summary",
                "summary_clean", "description_clean", "language"
            ]
            
            for field in expected_fields:
                assert field in schema.names, f"Field '{field}' missing from schema"
            
            # Check that forbidden fields are not in schema
            forbidden_fields = ["text_hash", "text_combined"]
            for field in forbidden_fields:
                assert field not in schema.names, f"Forbidden field '{field}' should not be in schema"
                
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestIntegration:
    """Integration tests for the complete pipeline."""
    
    def test_complete_pipeline(self):
        """Test the complete preprocessing pipeline."""
        # Create test CSV data
        test_csv_data = """Affects Version;Component;Description;Custom field (Frequency);Issue Type;Priority;Custom field (Severity);Custom field (Problem Type);Summary
3.70.16;Android Client;"*Test Steps:*
UserA (Android) opens social tab
joins a social group chat
Sends messages
UserB (IOS) user joins chat
Last 50 posts do not appear for UserB (IOS)

*Actual Result:*
The last 50 messages do not appear on the IOS device. The last 20 messages appear.

*Expected Result:*
The last 50 messages are expected to appear as on the Android device.

Application Version : 3.70.16
Msisdn : 905368658527
Carrier : Turkcell
Device : iPhone12,5
Device OS : 14.3
Language : tr-DE
Network status : Wi-Fi
LOGS_UPLOADED_TO_SERVER_URL: https://swf.tvoip.turkcell.com.tr/v1/AUTH_8b55f84760274c9599382d2e337a57cf/3c65843d0c79b98c6d2a66a6ce349c3e/logs/29122020/09/logs/applicationlogs.zip";High;Bug;High;Critical;Functional;Test summary"""
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as csv_file:
            csv_file.write(test_csv_data)
            csv_path = Path(csv_file.name)
        
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as parquet_file:
            parquet_path = Path(parquet_file.name)
        
        try:
            # Run the complete pipeline
            run_preprocessing(csv_path, parquet_path)
            
            # Verify output
            assert parquet_path.exists(), "Output parquet file should exist"
            
            # Read and verify the output
            import pyarrow.parquet as pq
            table = pq.read_table(parquet_path)
            df = table.to_pandas()
            
            assert len(df) == 1, "Should have 1 row"
            
            # Check the processed description
            description_clean = df["description_clean"].iloc[0]
            
            # All acceptance criteria
            assert "3.70.16" in description_clean, "Semver should be preserved"
            assert "iPhone12,5" in description_clean, "Device name should be preserved"
            assert "Wi-Fi" in description_clean, "Wi-Fi should be preserved"
            assert "(Android)" in description_clean, "Android should be normalized"
            assert "(iOS)" in description_clean, "IOS should be normalized to iOS"
            assert "## TEST_STEPS" in description_clean, "Test Steps header should be present"
            assert "## ACTUAL_RESULT" in description_clean, "Actual Result header should be present"
            assert "## EXPECTED_RESULT" in description_clean, "Expected Result header should be present"
            assert "## METADATA" in description_clean, "Metadata block should be present"
            assert "905368658527" not in description_clean, "Phone number should be masked"
            assert "http" not in description_clean, "URL should be masked"
            assert "[PRESENT" in description_clean, "PII signals should be preserved"
            
            # Check language detection
            language = df["language"].iloc[0]
            assert "en" in language, f"Expected English detection, got {language}"
            
            # Check schema
            assert "text_hash" not in df.columns, "text_hash should not be in output"
            assert "text_combined" not in df.columns, "text_combined should not be in output"
            
        finally:
            # Cleanup
            if csv_path.exists():
                csv_path.unlink()
            if parquet_path.exists():
                parquet_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

