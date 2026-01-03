#!/usr/bin/env python3
"""
Setup script to download required NLTK data
Run this once: python3 setup_nltk.py
"""

import nltk
import ssl

# Fix SSL certificate issues on some systems
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

print("Downloading required NLTK data...")
print("This may take a minute...")

# Download required packages
try:
    nltk.download('punkt', quiet=False)
    print("✓ Downloaded 'punkt' tokenizer")
except Exception as e:
    print(f"✗ Error downloading punkt: {e}")

try:
    nltk.download('stopwords', quiet=False)
    print("✓ Downloaded 'stopwords'")
except Exception as e:
    print(f"✗ Error downloading stopwords: {e}")

try:
    nltk.download('punkt_tab', quiet=False)
    print("✓ Downloaded 'punkt_tab' (additional tokenizer data)")
except Exception as e:
    print(f"Note: punkt_tab download failed (this is optional): {e}")

print("\n✓ NLTK setup complete!")
print("You can now run the main application.")