import os
import glob
import pandas as pd
from datetime import datetime
from preprocess_jira import run_preprocessing, load_csv_robust, validate_columns, process_dataframe, save_to_parquet
from pathlib import Path

INPUT_FILE = "/Users/cemirhans/Downloads/JIRA_DUPLICATE_DETECTION-main-2/bug-deduplication/data/data_with_enhanced_app_version.csv"
OUTPUT_DIR = "data/preprocessed/"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "issues_preprocessed.parquet")

def clean_old_files():
    """Eski parquet dosyalarını temizle"""
    parquet_files = glob.glob(os.path.join(OUTPUT_DIR, "*.parquet"))
    for f in parquet_files:
        try:
            os.remove(f)
            print(f"🗑️ Deleted old file: {f}")
        except Exception as e:
            print(f"⚠️ Could not delete {f}: {e}")

def run_preprocess():
    """CSV'den oku, preprocess et ve yeni parquet yaz"""
    print(f"📥 Reading from {INPUT_FILE}")
    
    # Use the robust CSV loading from preprocess.py
    df = load_csv_robust(INPUT_FILE)
    validate_columns(df)
    
    print("🔄 Running preprocess pipeline...")
    df = process_dataframe(df)
    
    print("💾 Saving to parquet...")
    save_to_parquet(df, Path(OUTPUT_FILE))
    
    return df

def verify_output(df):
    """Temizlik sonrası kontrol amaçlı örnek çıktılar"""
    print(f"\n✅ Final shape: {df.shape}")
    print("\n✅ Available columns:", list(df.columns))
    
    # Check which columns are available
    summary_col = 'Summary' if 'Summary' in df.columns else 'summary'
    description_col = 'Description' if 'Description' in df.columns else 'description'
    
    if 'summary_clean' in df.columns and summary_col in df.columns:
        print(f"\n✅ Verification ({summary_col} vs summary_clean):")
        print(df[[summary_col, 'summary_clean']].head(3).to_string(index=False))
    
    if 'description_clean' in df.columns and description_col in df.columns:
        print(f"\n✅ Verification ({description_col} vs description_clean):")
        print(df[[description_col, 'description_clean']].head(3).to_string(index=False))
    
    # Check for any remaining URLs in cleaned fields
    for col in ['summary_clean', 'description_clean']:
        if col in df.columns:
            has_urls = df[col].str.contains(r'https?://|www\.', regex=True, na=False).sum()
            print(f"\n✅ URLs in {col}: {has_urls}")
    
    # Show language detection results
    if 'language' in df.columns:
        print(f"\n✅ Language detection results:")
        print(df['language'].value_counts().head())

if __name__ == "__main__":
    print("🚀 Starting pipeline...")
    clean_old_files()
    df = run_preprocess()
    verify_output(df)
    print("\n🎉 Pipeline completed successfully!")
