"""Test script to diagnose PDF reading issues"""
import sys
from pathlib import Path
from pypdf import PdfReader

data_dir = Path(__file__).parent / "data"
pdf_files = list(data_dir.glob("*.pdf"))

print(f"Found {len(pdf_files)} PDF files:")
for pdf_path in pdf_files:
    print(f"\n{'='*60}")
    print(f"Testing: {pdf_path.name}")
    print(f"Size: {pdf_path.stat().st_size} bytes")
    
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            print(f"[OK] Successfully opened PDF")
            print(f"  Pages: {len(reader.pages)}")
            
            for i, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    print(f"  [OK] Page {i}: {len(text)} characters")
                except Exception as e:
                    print(f"  [ERROR] Page {i}: {e}")
                    
    except Exception as e:
        print(f"[ERROR] FAILED to open PDF: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*60}")
print("Test complete")
