#!/usr/bin/env python3
"""
Pre-download HuggingFace emotion model to avoid first-run delays.
Run this once before deploying or testing.
"""

from transformers import pipeline
from config import MODEL_NAME

print(f"Pre-downloading model: {MODEL_NAME}")
print("This may take 5-10 minutes on first run...")

try:
    classifier = pipeline(
        "text-classification",
        model=MODEL_NAME,
        return_all_scores=True,
        device=-1,  # CPU
    )
    print("✓ Model downloaded and cached successfully!")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Location: ~/.cache/huggingface/")
except Exception as e:
    print(f"✗ Error downloading model: {e}")
    exit(1)
